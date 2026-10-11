from pathlib import Path
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from .models import CertificateJob, CertificateRecord  # noqa: F401

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
