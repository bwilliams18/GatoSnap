import models
import schemas
from plex_api import get_account, get_client, save_auth_token, save_base_url
from sqlalchemy.orm import Session
from tasks import add_task_to_queue


def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    # return db.query(models.Task).offset(skip).limit(limit).all()
    return db.query(models.Task).all()


def create_task(db: Session, task):
    db_task = models.Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    add_task_to_queue(db_task.id)
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    db.delete(db_task)
    db.commit()
    return True


def update_task(db: Session, task_id: int, task: schemas.TaskUpdate):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    db_task.status = task.status
    db.commit()
    db.refresh(db_task)
    if db_task.status == schemas.TaskStatus.PENDING:
        add_task_to_queue(db_task.id)
    return db_task


def get_storage_devices(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.StorageDevice).offset(skip).limit(limit).all()


def create_storage_device(db: Session, storage_device):
    db_storage_device = models.StorageDevice(**storage_device.dict())
    db.add(db_storage_device)
    db.commit()
    db.refresh(db_storage_device)
    return db_storage_device


def get_files_for_storage_device(
    db: Session, device_id: int, skip: int = 0, limit: int = 100
):
    return (
        db.query(models.File).filter(models.File.storage_device_id == device_id).all()
    )


def get_files(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.File).offset(skip).limit(limit).all()


def update_file(db: Session, file_id: int, file: schemas.FileUpdate):
    db_file = db.query(models.File).filter(models.File.id == file_id).first()
    db_file.status = file.status
    db.commit()
    db.refresh(db_file)
    return db_file


def update_files_status(db: Session, status: schemas.FileStatus, file_ids: list[int]):
    db_files = (
        db.query(models.File)
        .filter(models.File.id.in_(file_ids))
        .update({"status": status})
    )
    db.commit()
    return file_ids


def check_config():
    try:
        auth_token = get_account()
    except:
        auth_token = None
    try:
        server = get_client()
    except:
        server = None
    return {"auth_token": bool(auth_token), "server": bool(server)}


def save_plex_auth(login: schemas.PlexLogin):
    save_auth_token(login.username, login.password)
    get_account()
    return {"success": True}


def save_plex_server(server: schemas.PlexServer):
    account = get_account()
    resource = account.resource(server.server)
    _server = resource.connect()
    save_base_url(_server._baseurl)
    get_client()
    return {"success": True}


def get_servers():
    account = get_account()
    return [res for res in account.resources() if res.provides == "server"]


def sign_in_with_plex(username: str, password: str):
    pass
