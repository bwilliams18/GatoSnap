import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

database_path = os.environ.get("DATABASE_PATH", "") + os.environ.get(
    "DATABASE_NAME", "database.db"
)

SQLALCHEMY_DATABASE_URL = "sqlite:///{}".format(database_path)
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
