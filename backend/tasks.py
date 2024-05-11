import asyncio
import logging
import math
import os
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from time import sleep

import database
import sqlalchemy as sa
from models import File, FileStatus, StorageDevice, Task, TaskStatus, get_local_path
from plex_api import get_client
from plexapi.exceptions import NotFound

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
stream_handler.setFormatter(logging.Formatter(log_format))
logger.addHandler(stream_handler)

MAX_WORKERS = 10


try:
    O_BINARY = os.O_BINARY
except:
    O_BINARY = 0
READ_FLAGS = os.O_RDONLY | O_BINARY
WRITE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | O_BINARY
BUFFER_SIZE = 1024 * 1024 * 10  # 10MB


# Task queue using a thread-safe queue
task_queue = queue.Queue()


# Function to add a task to the queue
def add_task_to_queue(task_id):
    task_queue.put(task_id)


def worker(task_id):
    logger.info("Worker started for task {}".format(task_id))
    with database.SessionLocal() as session:
        task = session.execute(
            sa.select(Task).where(Task.id == task_id)
        ).scalar_one_or_none()
        if task is None:
            logger.warning("Task {} not found".format(task_id))
            task_queue.task_done()
        logger.info("Starting task {}".format(task.name))
        task.progress = 0
        task.status = TaskStatus.RUNNING
        task.started = sa.func.now()
        args = task.args
        session.commit()
        logger.debug("Task args: {}".format(args))
        try:
            func = globals().get(task.func)
            if func is not None and callable(func):
                for progress, increment, total, status in func(*args):
                    if task.status == TaskStatus.STOPPED:
                        logger.info("Task {} stopped".format(task.name))
                        break
                    if progress:
                        task.progress = progress
                    elif increment:
                        task.progress += increment
                    if total:
                        task.total = total
                    task.status = status
                    if status == TaskStatus.SUCCESS:
                        task.finished = sa.func.now()
                    session.commit()
            else:
                logger.warning("Unknown function {}".format(task.func))
        except Exception as e:
            logger.error("Task failed {}".format(task.name))
            logger.exception(e)
            if task is None:
                logger.warning("Task {} not found".format(task_id))
                task_queue.task_done()
            task.finished = sa.func.now()
            task.status = TaskStatus.FAILED
            session.commit()
            task_queue.task_done()


# Function to retrieve and process tasks from the queue
def process_task_queue():
    logger.info("Fixing Old Tasks")
    with database.SessionLocal() as session:
        session.execute(
            sa.update(Task)
            .where(Task.status != TaskStatus.SUCCESS)
            .values(status=TaskStatus.PENDING, progress=0)
        )
        session.commit()
        # add pending tasks to queue
        tasks = (
            session.execute(sa.select(Task).where(Task.status == TaskStatus.PENDING))
            .scalars()
            .all()
        )
        for task in tasks:
            add_task_to_queue(task.id)
            logger.info("Added task {} to queue".format(task.name))
    logger.info("Starting Task Queue")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        while True and threading.main_thread().is_alive():
            try:
                task_id = task_queue.get(block=False)
                logger.info("Starting task {}".format(task_id))
                executor.submit(worker, task_id)
                logger.info("Task {} submitted".format(task_id))
            except queue.Empty:
                # logger.debug("Queue is empty")
                sleep(0.1)
            except KeyboardInterrupt:
                logger.info("Stopping task queue")
                executor.shutdown(wait=False)
                return
            except Exception as e:
                logger.error("Task failed")
                logger.exception(e)
                sleep(1)


# Stop the task queue
def stop_task_queue():
    task_queue.join()


def get_files(sd_id):
    plex_client = get_client()
    logger.info("Getting files for {}".format(sd_id))
    with database.SessionLocal() as session:
        sd = session.execute(
            sa.select(StorageDevice).where(StorageDevice.id == sd_id)
        ).scalar_one_or_none()
        to_download = list()
        if sd.sync_on_deck:
            to_download.extend(plex_client.library.onDeck())
        if sd.sync_continue_watching:
            to_download.extend(plex_client.continueWatching())
        if sd.sync_playlist:
            to_download.extend(plex_client.playlist(sd.sync_playlist).items())
        session.commit()
        for item in to_download:
            rating_key = item.ratingKey
            file = session.execute(
                sa.select(File).where(
                    File.storage_device_id == sd.id, File.rating_key == rating_key
                )
            ).scalar_one_or_none()
            if file is None:
                local_path = get_local_path(item.media[0].parts[0].file)
                if item.type == "episode":
                    title = "{series} | {season_episode} | {title}".format(
                        series=item.grandparentTitle,
                        season_episode=item.seasonEpisode,
                        title=item.title,
                    )
                else:
                    title = item.title
                file = File(
                    title=title,
                    rating_key=item.ratingKey,
                    remote_path=item.media[0].parts[0].file,
                    storage_device_id=sd.id,
                    file_size=os.path.getsize(local_path),
                )
                session.add(file)
                session.commit()
                logger.info("File added for {}".format(item.title))
            else:
                logger.info("File already exists for {}".format(item.title))
                file.remote_path = item.media[0].parts[0].file
                file.file_size = os.path.getsize(file.local_path)
                session.commit()
                if (
                    file.status == FileStatus.WATCHED
                    and not item.isPlayed
                    and not os.path.exists(file.storage_path)
                ):
                    file.status = FileStatus.MISSING
                    session.commit()
            if item.type == "episode" and sd.sync_all_episodes:
                for episode in item.show().episodes(played=False):
                    if (
                        episode.seasonEpisode > item.seasonEpisode
                        and to_download.count(episode) == 0
                    ):
                        to_download.append(episode)
            yield None, 1, len(to_download), TaskStatus.RUNNING
        yield None, 0, None, TaskStatus.SUCCESS


def remove_empty_folders(path):
    walk = list(os.walk(path))
    for path, _, _ in walk[::-1]:
        if len(os.listdir(path)) == 0:
            os.rmdir(path)


def check_files(sd_id):
    plex_client = get_client()
    with database.SessionLocal() as session:
        sd = session.execute(
            sa.select(StorageDevice).where(StorageDevice.id == sd_id)
        ).scalar_one_or_none()
        files = (
            session.execute(
                sa.select(File).where(
                    File.storage_device_id == sd.id
                    and File.status != FileStatus.MISSING
                )
            )
            .scalars()
            .all()
        )
        yield 0, 0, len(files), TaskStatus.RUNNING
        for file in files:
            try:
                item = plex_client.library.fetchItem(file.rating_key)
                if item.type == "episode":
                    file.title = "{series} | {season_episode} | {title}".format(
                        series=item.grandparentTitle,
                        season_episode=item.seasonEpisode,
                        title=item.title,
                    )
                session.commit()
                if os.path.exists(file.storage_path):
                    if item.isPlayed:
                        logger.info(
                            "Removing '{}' as it's been played".format(file.title)
                        )
                        os.remove(file.storage_path)
                        file.status = FileStatus.WATCHED
                    else:
                        if os.path.getsize(file.storage_path) != file.file_size:
                            logger.info(
                                "Removing '{}' as it's been changed".format(file.title)
                            )
                            os.remove(file.storage_path)
                            file.status = FileStatus.MISSING
                        else:
                            logger.info(
                                "Keeping '{}' as it's not been played".format(
                                    file.title
                                )
                            )
                            if file.status != FileStatus.IGNORED:
                                file.status = FileStatus.SYNCED
                else:
                    if item.isPlayed:
                        logger.info("Marking '{}' as played".format(file.title))
                        item.markPlayed()
                        file.status = FileStatus.WATCHED
                        try:
                            plex_client.playlist(sd.sync_playlist).removeItems([item])
                        except NotFound:
                            pass
                    else:
                        logger.info(
                            "Adding '{}' as it's missing been played".format(file.title)
                        )
                        file.status = FileStatus.MISSING
            except NotFound:
                logger.info("Removing '{}' as it's been deleted".format(file.title))
                try:
                    os.remove(file.storage_path)
                    file.status = FileStatus.WATCHED
                except FileNotFoundError:
                    logger.info(
                        "{} is not present on the disk".format(file.storage_path)
                    )
                    session.delete(file)
            yield None, 1, None, TaskStatus.RUNNING
            session.commit()
        remove_empty_folders(sd.base_path)
        yield None, None, None, TaskStatus.SUCCESS


def transfer_file(file_id):
    with database.SessionLocal() as session:
        file = session.execute(
            sa.select(File).where(File.id == file_id)
        ).scalar_one_or_none()
        local_path = file.local_path
        storage_path = file.storage_path
        if not os.path.exists(os.path.dirname(storage_path)):
            os.makedirs(os.path.dirname(storage_path))
        total = os.path.getsize(local_path)
        yield None, None, total, TaskStatus.RUNNING
        session.commit()
        try:
            file_in = os.open(local_path, READ_FLAGS)
            stat = os.fstat(file_in)
            file_out = os.open(storage_path, WRITE_FLAGS, stat.st_mode)
            for i, x in enumerate(iter(lambda: os.read(file_in, BUFFER_SIZE), b"")):
                os.write(file_out, x)
                # for every 1% update the transfer
                if i % math.ceil(total / 100 / BUFFER_SIZE) == 0:
                    progress = os.lseek(file_in, 0, os.SEEK_CUR)
                    logger.info(
                        "{file} {progress:0.2%}.{i}".format(
                            file=local_path, progress=progress / total, i=i
                        )
                    )
                    yield progress, None, None, TaskStatus.RUNNING
            logger.info("Finished transferring {}".format(local_path))
            yield total, None, None, TaskStatus.SUCCESS
            session.commit()
            logger.info("Finished syncing {}".format(local_path))
        except Exception as e:
            logger.error("Unable to transfer {}".format(local_path))
            logger.exception(e)
            file.status = FileStatus.MISSING
            session.commit()
            yield 0, None, None, TaskStatus.FAILED
        finally:
            try:
                os.close(file_in)
            except Exception as e:
                logger.error("Unable to close file_in")
                logger.exception(e)
            try:
                os.close(file_out)
            except Exception as e:
                logger.error("Unable to close file_out")
                logger.exception(e)


def eject_sd(sd_id):
    with database.SessionLocal() as session:
        yield 0, 1, TaskStatus.RUNNING
        sd = session.execute(
            sa.select(StorageDevice).where(StorageDevice.id == sd_id)
        ).scalar_one_or_none()
        sd.eject()
        session.commit()
        yield 1, 1, TaskStatus.SUCCESS


def transfer_files(sd_id):
    with database.SessionLocal() as session:
        sd = session.execute(
            sa.select(StorageDevice).where(StorageDevice.id == sd_id)
        ).scalar_one_or_none()
        files = (
            session.execute(
                sa.select(File).where(
                    File.storage_device_id == sd.id, File.status == FileStatus.MISSING
                )
            )
            .scalars()
            .all()
        )
        file_ids = [file.id for file in files]
        return transfer_some_files(sd_id, file_ids)


def transfer_some_files(sd_id, file_ids):
    with database.SessionLocal() as session:
        sd = session.execute(
            sa.select(StorageDevice).where(StorageDevice.id == sd_id)
        ).scalar_one_or_none()
        files = (
            session.execute(sa.select(File).where(File.id.in_(file_ids)))
            .scalars()
            .all()
        )
        yield 0, None, len(files), TaskStatus.RUNNING
        for file in files:
            if not os.path.exists(file.local_path):
                logger.error(
                    "Unable to sync {} as it can't be found".format(file.local_path)
                )
            if (not os.path.exists(file.storage_path)) or (
                file.file_size != os.path.getsize(file.storage_path)
            ):
                task = Task(
                    name="Transfer {} to {}".format(file.title, sd.name),
                    func="transfer_file",
                    args=[file.id],
                    kwargs={},
                    total=file.file_size,
                )
                session.add(task)

                session.commit()
                add_task_to_queue(task.id)
            else:
                file.status = FileStatus.SYNCED
                session.commit()
            yield None, 1, None, TaskStatus.RUNNING
        yield None, None, None, TaskStatus.SUCCESS
