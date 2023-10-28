import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import StaticPool

load_dotenv()


database_path = os.environ.get("DATABASE_PATH", "") + os.environ.get(
    "DATABASE_NAME", "database.db"
)

SQLALCHEMY_DATABASE_URL = "sqlite:///{}".format(database_path)
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@postgresserver/db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


session_factory = sessionmaker(bind=engine)

SessionLocal = scoped_session(session_factory)

Base = declarative_base()
