import os

import crud
import database
import models
import schemas
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from plexapi.exceptions import Unauthorized
from sqlalchemy.orm import Session

app = FastAPI(title="my app root")
api_app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://borth",
    "http://borth:3000",
    "http://borth:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@api_app.get("/tasks/", response_model=list[schemas.Task])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tasks = crud.get_tasks(db, skip=skip, limit=limit)
    return tasks


@api_app.post("/tasks/", response_model=schemas.Task)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db=db, task=task)


@api_app.delete(
    "/tasks/{task_id}/",
)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    return crud.delete_task(db=db, task_id=task_id)


@api_app.get("/storage_devices/", response_model=list[schemas.StorageDevice])
def read_storage_devices(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return crud.get_storage_devices(db, skip=skip, limit=limit)


@api_app.post("/storage_devices/", response_model=schemas.StorageDevice)
def create_storage_device(
    storage_device: schemas.StorageDeviceCreate,
    db: Session = Depends(get_db),
):
    return crud.create_storage_device(db=db, storage_device=storage_device)


@api_app.get("/storage_devices/{device_id}/files/", response_model=list[schemas.File])
def read_files(
    device_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return crud.get_files_for_storage_device(
        db, device_id=device_id, skip=skip, limit=limit
    )


@api_app.patch(
    "/storage_devices/{device_id}/files/{file_id}/", response_model=schemas.File
)
def update_file(file_id: int, file: schemas.FileUpdate, db: Session = Depends(get_db)):
    return crud.update_file(db=db, file_id=file_id, file=file)


@api_app.get("/storage_paths/")
def read_storage_paths(path: str = models.STORAGE_BASE_PATH):
    if not path.startswith(models.STORAGE_BASE_PATH):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail="Invalid path")
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]


@api_app.get("/check_config/")
def check_config():
    return crud.check_config()


@api_app.post("/plex/auth/", response_model=schemas.PlexAuth)
def save_plex_auth(login: schemas.PlexLogin):
    try:
        return crud.save_plex_auth(login)
    except Unauthorized as e:
        raise HTTPException(status_code=401, detail=str(e))


@api_app.post(
    "/plex/servers/",
    response_model=schemas.PlexAuth,
)
def save_plex_server(server: schemas.ServerName):
    return crud.save_plex_server(server)


@api_app.get("/plex/servers/", response_model=list[schemas.PlexServer])
def get_plex_servers():
    return crud.get_servers()


app.mount("/api", api_app)

app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
