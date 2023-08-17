from models import FileStatus, TaskStatus
from pydantic import BaseModel


class TaskBase(BaseModel):
    id: int | None
    name: str
    func: str
    args: list
    kwargs: dict
    progress: float | None
    total: float | None
    status: TaskStatus = TaskStatus.PENDING


class Task(TaskBase):
    class Config:
        orm_mode = True


class TaskCreate(TaskBase):
    id: None = None
    func: str
    progress: None = None
    total: None = None


class StorageDeviceBase(BaseModel):
    id: int
    name: str
    base_path: str
    sync_on_deck: bool
    sync_continue_watching: bool
    sync_playlist: str | None


class StorageDevice(StorageDeviceBase):
    class Config:
        orm_mode = True


class StorageDeviceCreate(StorageDeviceBase):
    id: None = None
    name: str
    base_path: str
    sync_on_deck: bool
    sync_continue_watching: bool
    sync_playlist: str | None = None


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
        orm_mode = True


class PlexServer(BaseModel):
    device: str
    name: str
    presence: bool
    product: str
    publicAddressMatches: bool
    sourceTitle: str | None

    class Config:
        orm_mode = True
