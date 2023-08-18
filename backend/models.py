import enum
import os

import dotenv
import sqlalchemy as sa
from dotenv import load_dotenv

load_dotenv()

SERVER_BASE_PATH = os.environ.get("SERVER_BASE_PATH", "/media/")
LOCAL_BASE_PATH = os.environ.get("LOCAL_BASE_PATH", "/Volumes/Media/")
STORAGE_BASE_PATH = os.environ.get("STORAGE_BASE_PATH", "/Volumes/")


if not os.path.exists(LOCAL_BASE_PATH):
    raise Exception("Local base path does not exist: {}".format(LOCAL_BASE_PATH))


from database import Base


class TaskStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class Task(Base):
    __tablename__ = "task"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    func = sa.Column(sa.String, nullable=False)
    args = sa.Column(sa.JSON, nullable=False)
    kwargs = sa.Column(sa.JSON, nullable=False)
    progress = sa.Column(sa.Float, nullable=False, default=0.0)
    total = sa.Column(sa.Float, nullable=False, default=0.0)
    status = sa.Column(sa.Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)


class StorageDevice(Base):
    __tablename__ = "storage_device"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    base_path = sa.Column(sa.String, nullable=False)
    sync_on_deck = sa.Column(sa.Boolean, nullable=False)
    sync_continue_watching = sa.Column(sa.Boolean, nullable=False)
    sync_playlist = sa.Column(sa.String, nullable=True)

    def get_drive_path(self, path):
        if not path.startswith(SERVER_BASE_PATH):
            raise Exception("Path does not start with server base path")
        if not os.path.exists(self.base_path):
            raise Exception("Path does not exist: {}".format(path))
        return path.replace(SERVER_BASE_PATH, self.base_path)


class FileStatus(enum.Enum):
    MISSING = "missing"
    SYNCED = "synced"
    WATCHED = "watched"


def get_local_path(remote_path):
    if not remote_path.startswith(SERVER_BASE_PATH):
        raise Exception("Path does not start with server base path")
    return remote_path.replace(SERVER_BASE_PATH, LOCAL_BASE_PATH)


class File(Base):
    __tablename__ = "file"
    id = sa.Column(sa.Integer, primary_key=True)
    storage_device_id = sa.Column(
        sa.Integer, sa.ForeignKey(StorageDevice.id), nullable=False
    )
    title = sa.Column(sa.String, nullable=False)
    remote_path = sa.Column(sa.String, nullable=False)
    storage_path = sa.Column(sa.String, nullable=True)
    rating_key = sa.Column(sa.Integer, nullable=False)
    file_size = sa.Column(sa.Integer, nullable=False)
    status = sa.Column(sa.Enum(FileStatus), nullable=False, default=FileStatus.MISSING)

    constraints = [
        "UNIQUE(storage_device_id, rating_key)",
    ]

    @property
    def local_path(self):
        return get_local_path(self.remote_path)
