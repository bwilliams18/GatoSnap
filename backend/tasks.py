import logging
import math
import os
import queue
import threading

import database
import sqlalchemy as sa
import zmq
from models import File, FileStatus, StorageDevice, Task, TaskStatus, get_local_path
from plex_api import get_client
from plexapi.exceptions import NotFound
from sqlalchemy import select

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

q = queue.Queue()


try:
    O_BINARY = os.O_BINARY
except:
    O_BINARY = 0
READ_FLAGS = os.O_RDONLY | O_BINARY
WRITE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | O_BINARY
BUFFER_SIZE = 128 * 1024


def start_task(task_id):
    context = zmq.Context()
    #  Socket to talk to server
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")
    socket.send(task_id.to_bytes(2, "little", signed=False))
    message = socket.recv()


def worker():
    while True:
        task_id = q.get()
        session = database.SessionLocal()
        task = session.execute(
            select(Task).where(Task.id == task_id)
        ).scalar_one_or_none()
        if task is None:
            logger.warning("Task {} not found".format(task_id))
            q.task_done()
            continue
        logger.info("Starting task {}".format(task.name))
        task.status = TaskStatus.RUNNING
        task.started = sa.func.now()
        session.commit()
        args = task.args
        session.close()
        try:
            if task.func == "transfer_file":
                transfer_file(*args, task_id)
            elif task.func == "get_files":
                get_files(*args, task_id)
            elif task.func == "check_files":
                check_files(*args, task_id)
            elif task.func == "remove_empty_folders":
                remove_empty_folders(*args)
            elif task.func == "transfer_files":
                transfer_files(*args, task_id)
            elif task.func == "eject_sd":
                eject_sd(*args)
            else:
                logger.warning("Unknown function {}".format(task.func))
        except Exception as e:
            logger.error("Task failed {}".format(task.name))
            logger.exception(e)
            session = database.SessionLocal()
            task = session.execute(
                select(Task).where(Task.id == task_id)
            ).scalar_one_or_none()
            if task is None:
                logger.warning("Task {} not found".format(task_id))
                q.task_done()
                continue
            task.finished = sa.func.now()
            task.status = TaskStatus.FAILED
            session.commit()
            q.task_done()
            continue
        session = database.SessionLocal()
        task = session.execute(
            select(Task).where(Task.id == task_id)
        ).scalar_one_or_none()
        task.finished = sa.func.now()
        task.status = TaskStatus.SUCCESS
        session.commit()
        session.close()
        q.task_done()


def get_files(sd_id, task_id):
    plex_client = get_client()
    with database.SessionLocal() as session:
        sd = session.execute(
            select(StorageDevice).where(StorageDevice.id == sd_id)
        ).scalar_one_or_none()
        task = session.execute(
            select(Task).where(Task.id == task_id)
        ).scalar_one_or_none()
        to_download = list()
        if sd.sync_on_deck:
            to_download.extend(plex_client.library.onDeck())
        if sd.sync_continue_watching:
            to_download.extend(plex_client.continueWatching())
        if sd.sync_playlist:
            to_download.extend(plex_client.playlist(sd.sync_playlist).items())
        task.total = len(to_download)
        session.commit()
        for item in to_download:
            rating_key = item.ratingKey
            file = session.execute(
                select(File).where(
                    File.storage_device_id == sd.id, File.rating_key == rating_key
                )
            ).scalar_one_or_none()
            if file is None:
                local_path = get_local_path(item.media[0].parts[0].file)
                if item.type == "episode":
                    title = "{series} | {seasonepisode} | {title}".format(
                        series=item.grandparentTitle,
                        seasonepisode=item.seasonEpisode,
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
            task.progress += 1
            task.total = len(to_download)
            session.commit()


def remove_empty_folders(path):
    walk = list(os.walk(path))
    for path, _, _ in walk[::-1]:
        if len(os.listdir(path)) == 0:
            os.rmdir(path)


def check_files(sd_id, task_id):
    plex_client = get_client()
    with database.SessionLocal() as session:
        sd = session.execute(
            select(StorageDevice).where(StorageDevice.id == sd_id)
        ).scalar_one_or_none()
        task = session.execute(
            select(Task).where(Task.id == task_id)
        ).scalar_one_or_none()
        files = (
            session.execute(
                select(File).where(
                    File.storage_device_id == sd.id
                    and File.status != FileStatus.MISSING
                )
            )
            .scalars()
            .all()
        )
        task.total = len(files)
        session.commit()
        for file in files:
            try:
                item = plex_client.library.fetchItem(file.rating_key)
                if item.type == "episode":
                    file.title = "{series} | {seasonepisode} | {title}".format(
                        series=item.grandparentTitle,
                        seasonepisode=item.seasonEpisode,
                        title=item.title,
                    )
                session.commit()
                if os.path.exists(file.storage_path):
                    if item.isPlayed:
                        logger.info("Removing '{}' as it's been played".format(file))
                        os.remove(file.storage_path)
                        file.status = FileStatus.WATCHED
                    else:
                        if os.path.getsize(file.storage_path) != file.file_size:
                            logger.info(
                                "Removing '{}' as it's been changed".format(file)
                            )
                            os.remove(file.storage_path)
                            file.status = FileStatus.MISSING
                        else:
                            logger.info(
                                "Keeping '{}' as it's not been played".format(file)
                            )
                            file.status = FileStatus.SYNCED
                else:
                    if item.isPlayed:
                        logger.info("Marking '{}' as played".format(file))
                        item.markPlayed()
                        file.status = FileStatus.WATCHED
                        try:
                            plex_client.playlist(sd.sync_playlist).removeItems([item])
                        except NotFound:
                            pass
                    else:
                        logger.info(
                            "Adding '{}' as it's missing been played".format(file)
                        )
                        file.status = FileStatus.MISSING
            except NotFound:
                logger.info("Removing '{}' as it's been deleted".format(file))
                try:
                    os.remove(file.storage_path)
                    file.status = FileStatus.WATCHED
                except FileNotFoundError:
                    logger.info(
                        "{} is not present on the disk".format(file.storage_path)
                    )
                    session.delete(file)
            task.progress += 1
            session.commit()
        remove_empty_folders(sd.base_path)


def transfer_file(file_id, task_id):
    with database.SessionLocal() as session:
        file = session.execute(
            select(File).where(File.id == file_id)
        ).scalar_one_or_none()
        task = session.execute(
            select(Task).where(Task.id == task_id)
        ).scalar_one_or_none()
        local_path = file.local_path
        storage_path = file.storage_path
        if not os.path.exists(os.path.dirname(storage_path)):
            os.makedirs(os.path.dirname(storage_path))
        task.total = os.path.getsize(local_path)
        task.progress = 0
        session.commit()
        session.close()

    try:
        fin = os.open(local_path, READ_FLAGS)
        stat = os.fstat(fin)
        fout = os.open(storage_path, WRITE_FLAGS, stat.st_mode)
        for i, x in enumerate(iter(lambda: os.read(fin, BUFFER_SIZE), "")):
            os.write(fout, x)
            if i % 100 == 0:
                session = database.SessionLocal()
                task = session.execute(
                    select(Task).where(Task.id == task_id)
                ).scalar_one_or_none()
                task.progress = os.path.getsize(storage_path)
                session.commit()
                session.close()
    finally:
        try:
            os.close(fin)
        except:
            pass
        try:
            os.close(fout)
        except:
            pass
    logger.info("Finished transfering {}".format(local_path))
    session = database.SessionLocal()
    task = session.execute(select(Task).where(Task.id == task_id)).scalar_one_or_none()
    file = session.execute(select(File).where(File.id == file_id)).scalar_one_or_none()
    task.progress = task.total
    file.status = FileStatus.SYNCED
    session.commit()
    logger.info("Finished syncing {}".format(local_path))


def eject_sd(sd_id):
    with database.SessionLocal() as session:
        sd = session.execute(
            select(StorageDevice).where(StorageDevice.id == sd_id)
        ).scalar_one_or_none()
        sd.eject()
        session.commit()


def transfer_files(sd_id, task_id):
    with database.SessionLocal() as session:
        sd = session.execute(
            select(StorageDevice).where(StorageDevice.id == sd_id)
        ).scalar_one_or_none()
        p_task = session.execute(
            select(Task).where(Task.id == task_id)
        ).scalar_one_or_none()
        files = (
            session.execute(
                select(File).where(
                    File.storage_device_id == sd.id, File.status == FileStatus.MISSING
                )
            )
            .scalars()
            .all()
        )
        p_task.total = len(files)
        p_task.progress = 0
        session.commit()
        for file in files:
            if not os.path.exists(file.local_path):
                logger.error(
                    "Unalbe to sync {} as it can't be found".format(file.local_path)
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
                p_task.progress += 1
                session.commit()
                start_task(task.id)
            else:
                file.status = FileStatus.SYNCED
                session.commit()


if __name__ == "__main__":
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    # Turn-on the worker thread.
    with database.SessionLocal() as session:
        (
            session.execute(
                sa.update(Task)
                .where(Task.status == TaskStatus.RUNNING)
                .values(status=TaskStatus.FAILED, progress=0)
            )
        )
        session.commit()
        # delete pending tasks

    for i in range(3):
        threading.Thread(target=worker, daemon=True).start()
    while True:
        #  Wait for next request from client
        message = int.from_bytes(socket.recv(), "little", signed=False)
        logger.info("Received request: %s" % message)
        q.put(message)
        socket.send(b"Received")
