import enum
import os

import sqlalchemy as sa
from dotenv import load_dotenv
from sqlalchemy.ext.hybrid import hybrid_property

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
    created = sa.Column(sa.DateTime, nullable=True, default=sa.func.now())
    started = sa.Column(sa.DateTime, nullable=True)
    finished = sa.Column(sa.DateTime, nullable=True)
    func = sa.Column(sa.String, nullable=False)
    args = sa.Column(sa.JSON, nullable=False)
    kwargs = sa.Column(sa.JSON, nullable=False)
    progress = sa.Column(sa.Float, nullable=False, default=0.0)
    total = sa.Column(sa.Float, nullable=False, default=0.0)
    status = sa.Column(sa.Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)

    # @property
    # def time_elapsed(self):
    #     if self.started is None:
    #         return None
    #     if self.finished is None:
    #         return sa.func.now() - self.started
    #     return self.finished - self.started

    # @time_elapsed.setter
    # def time_elapsed(self, value):
    #     pass

    # @property
    # def estimated_time_remaining(self):
    #     if self.started is None:
    #         return None
    #     if self.finished is None:
    #         return None
    #     if self.progress == 0:
    #         return None
    #     return self.time_elapsed * (self.total - self.progress) / self.progress

    # @property
    # def estimated_time_total(self):
    #     if self.started is None:
    #         return None
    #     if self.finished is None:
    #         return None
    #     if self.progress == 0:
    #         return None
    #     return self.time_elapsed * self.total / self.progress

    # @property
    # def percent_complete(self):
    #     if self.total == 0:
    #         return 0
    #     return self.progress / self.total

    # @property
    # def estimated_completion(self):
    #     if self.started is None:
    #         return None
    #     if self.finished is None:
    #         return None
    #     return self.started + self.estimated_time_total

    # @property
    # def speed(self):
    #     if self.time_elapsed is None:
    #         return None
    #     if self.progress == 0:
    #         return None
    #     return self.progress / self.time_elapsed


class StorageDevice(Base):
    __tablename__ = "storage_device"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String, nullable=False)
    base_path = sa.Column(sa.String, nullable=False)
    sync_on_deck = sa.Column(sa.Boolean, nullable=False, default=True)
    sync_continue_watching = sa.Column(sa.Boolean, nullable=False, default=True)
    sync_all_episodes = sa.Column(sa.Boolean, nullable=False, default=True)
    sync_playlist = sa.Column(sa.String, nullable=True)

    def get_drive_path(self, path):
        if not path.startswith(SERVER_BASE_PATH):
            raise Exception("Path does not start with server base path")
        return path.replace(SERVER_BASE_PATH, self.base_path)

    def eject(self):
        os.system("udiskie-umount {}".format(self.base_path))

    @property
    def connected(self):
        return os.path.exists(self.base_path)

    @connected.setter
    def connected(self, value):
        pass


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
    storage_device = sa.orm.relationship(StorageDevice, backref="files")
    title = sa.Column(sa.String, nullable=False)
    remote_path = sa.Column(sa.String, nullable=False)
    rating_key = sa.Column(sa.Integer, nullable=False, index=True, unique=True)
    file_size = sa.Column(sa.Integer, nullable=False)
    status = sa.Column(sa.Enum(FileStatus), nullable=False, default=FileStatus.MISSING)

    constraints = [
        "UNIQUE(storage_device_id, rating_key)",
    ]

    @property
    def local_path(self):
        return get_local_path(self.remote_path)

    @property
    def storage_path(self):
        return self.storage_device.get_drive_path(self.remote_path)
