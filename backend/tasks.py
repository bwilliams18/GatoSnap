import hashlib
import json
import math
import os
import queue
import threading
import time

import database
import ormsgpack
import zmq
from models import File, FileStatus, StorageDevice, Task, TaskStatus, get_local_path
from plex_api import get_client
from plexapi.exceptions import NotFound
from sqlalchemy import select
from sqlalchemy.orm import Session

q = queue.Queue()


def start_task(task_id):
    context = zmq.Context()
    #  Socket to talk to server
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")
    socket.send(ormsgpack.packb(task_id))
    message = socket.recv()


def worker():
    while True:
        task_id = q.get()
        with Session(database.engine) as session:
            task = session.execute(
                select(Task).where(Task.id == task_id)
            ).scalar_one_or_none()
            print("Starting task {}".format(task.name))
            task.status = TaskStatus.RUNNING
            session.commit()
            try:
                if task.func == "transfer_file":
                    transfer_file(*task.args, task.id)
                elif task.func == "get_files":
                    get_files(*task.args, task.id)
                elif task.func == "check_files":
                    check_files(*task.args, task.id)
                elif task.func == "remove_empty_folders":
                    remove_empty_folders(*task.args)
                elif task.func == "transfer_files":
                    transfer_files(*task.args)
                else:
                    print("Unknown function {}".format(task.func))
            except Exception as e:
                print("Task failed {}".format(task.name))
                print(e)
                task.status = TaskStatus.FAILED
            task.status = TaskStatus.COMPLETE
            session.commit()
        q.task_done()


def get_files(sd_id, task_id):
    plex_client = get_client()
    with Session(database.engine) as session:
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
                with open(local_path, "rb") as f:
                    digest = hashlib.file_digest(f, "md5")
                    md5 = digest.hexdigest()
                file = File(
                    title=item.title,
                    rating_key=item.ratingKey,
                    remote_path=item.media[0].parts[0].file,
                    storage_device_id=sd.id,
                    file_size=os.path.getsize(local_path),
                    md5=md5,
                )
                session.add(file)
                session.commit()
                print("File added for {}".format(item.title))
            if item.type == "episode":
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
    with Session(database.engine) as session:
        sd = session.execute(
            select(StorageDevice).where(StorageDevice.id == sd_id)
        ).scalar_one_or_none()
        task = session.execute(
            select(Task).where(Task.id == task_id)
        ).scalar_one_or_none()
        files = (
            session.execute(
                select(File).where(
                    File.storage_device_id == sd.id, File.status == FileStatus.SYNCED
                )
            )
            .scalars()
            .all()
        )
        task.total = len(files)
        session.commit()
        for file in files:
            item = plex_client.library.fetchItem(file.rating_key)
            if os.path.exists(file.storage_path):
                if item.isPlayed:
                    print("Removing '{}' as it's been played".format(file))
                    os.remove(file.storage_path)
                    file.status = FileStatus.WATCHED
            else:
                print("Marking '{}' as played".format(file))
                item.markPlayed()
                file.status = FileStatus.WATCHED
                try:
                    plex_client.playlist(sd.sync_playlist).removeItems([item])
                except NotFound:
                    pass
            task.progress += 1
            session.commit()
        remove_empty_folders(sd.base_path)


def transfer_file(file_id, task_id):
    with Session(database.engine) as session:
        file = session.execute(
            select(File).where(File.id == file_id)
        ).scalar_one_or_none()
        src = file.local_path
        dst = file.storage_path
        if not os.path.exists(os.path.dirname(dst)):
            os.makedirs(os.path.dirname(dst))
        task = session.execute(
            select(Task).where(Task.id == task_id)
        ).scalar_one_or_none()
        task.total = os.path.getsize(src)
        task.progress = 0
        session.commit()
        with open(src, "rb") as fsrc:
            with open(dst, "wb") as fdst:
                while True:
                    chunk = fsrc.read(math.floor(task.total / 1000))
                    if not chunk:
                        break
                    fdst.write(chunk)
                    task.progress += len(chunk)
                    session.commit()
        file.status = FileStatus.SYNCED
        session.commit()


def transfer_files(sd_id):
    with Session(database.engine) as session:
        sd = session.execute(
            select(StorageDevice).where(StorageDevice.id == sd_id)
        ).scaler_one_or_none()
        files = (
            session.execute(
                select(File).where(
                    File.storage_device_id == sd.id, File.status == FileStatus.MISSING
                )
            )
            .scalars()
            .all()
        )
        for file in files:
            file.storage_path = sd.get_drive_path(file.remote_path)
            if not os.path.exists(file.local_path):
                raise Exception("File does not exist: {}".format(file.local_path))
            with open(file.storage_path, "rb") as f:
                digest = hashlib.file_digest(f, "md5")
                md5 = digest.hexdigest()
            if (not os.path.exists(file.storage_path)) or (file.md5 != md5):
                task = Task(
                    name="Transfer {} to {}".format(file.title, sd.name),
                    func="transfer_file",
                    args=[file.id],
                    kwargs={},
                    total=file.file_size,
                )
                session.add(task)
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
    with Session(database.engine) as session:
        tasks = (
            session.execute(select(Task).where(Task.status == TaskStatus.PENDING))
            .scalars()
            .all()
        )
        for task in tasks:
            q.put(task.id)

    for i in range(10):
        threading.Thread(target=worker, daemon=True).start()
    while True:
        #  Wait for next request from client
        message = ormsgpack.unpackb(socket.recv())
        print("Received request: %s" % message)
        q.put(message)
        socket.send(b"Received")
