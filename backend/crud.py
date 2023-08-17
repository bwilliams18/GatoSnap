import models
from plex_api import get_account, get_client, save_auth_token
from sqlalchemy.orm import Session
from tasks import start_task


def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    # return db.query(models.Task).offset(skip).limit(limit).all()
    return db.query(models.Task).all()


def create_task(db: Session, task):
    db_task = models.Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    start_task(db_task.id)
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    db.delete(db_task)
    db.commit()
    return True


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
        db.query(models.File)
        .filter(models.File.storage_device_id == device_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_files(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.File).offset(skip).limit(limit).all()


def save_plex_auth(username: str, password: str):
    save_auth_token(username, password)
    get_account()
    return True


def save_plex_server(base_url: str):
    save_auth_token(base_url)
    get_client()
    return True


def get_servers():
    account = get_account()
    return [res for res in account.resources() if res.provides == "server"]


def sign_in_with_plex(username: str, password: str):
    pass
