from datetime import date, datetime, time, timedelta

from models import FileStatus, TaskStatus
from pydantic import BaseModel


class PlexLogin(BaseModel):
    username: str
    password: str


class PlexAuth(BaseModel):
    success: bool


class ServerName(BaseModel):
    server: str


class TaskBase(BaseModel):
    id: int | None
    name: str
    func: str
    args: list
    kwargs: dict
    created: datetime | None
    started: datetime | None
    finished: datetime | None
    progress: float | None
    total: float | None
    status: TaskStatus = TaskStatus.PENDING


class Task(TaskBase):
    class Config:
        from_attributes = True


class TaskCreate(TaskBase):
    id: None = None
    created: None = None
    started: None = None
    finished: None = None
    func: str
    progress: None = None
    total: None = None


class TaskUpdate(TaskBase):
    id: None = None
    name: None = None
    func: None = None
    args: None = None
    kwargs: None = None
    created: None = None
    started: None = None
    finished: None = None
    progress: None = None
    total: None = None
    status: TaskStatus = TaskStatus.PENDING


class StorageDeviceBase(BaseModel):
    id: int
    name: str
    base_path: str
    sync_on_deck: bool
    sync_continue_watching: bool
    sync_playlist: str | None
    connected: bool | None = None


class StorageDevice(StorageDeviceBase):
    class Config:
        from_attributes = True


class StorageDeviceCreate(StorageDeviceBase):
    id: None = None
    connected: None = None
    name: str
    base_path: str
    sync_on_deck: bool
    sync_continue_watching: bool
    sync_playlist: str | None = None


class FileStatusUpdate(BaseModel):
    status: FileStatus
    file_ids: list[int]


class FileBase(BaseModel):
    id: int
    storage_device_id: int
    title: str
    remote_path: str
    storage_path: str | None
    rating_key: int
    file_size: int
    status: FileStatus = FileStatus.MISSING


class File(FileBase):
    class Config:
        from_attributes = True


class FileUpdate(FileBase):
    id: int
    storage_device_id: None = None
    title: None = None
    remote_path: None = None
    storage_path: None = None
    rating_key: None = None
    file_size: None = None
    status: FileStatus = FileStatus.MISSING


class PlexServer(BaseModel):
    device: str
    name: str
    presence: bool
    product: str
    publicAddressMatches: bool
    sourceTitle: str | None

    class Config:
        from_attributes = True
