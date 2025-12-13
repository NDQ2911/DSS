import json
import os
from datetime import date
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dss.db")


class Base(DeclarativeBase):
    pass


engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from . import models

    Base.metadata.create_all(bind=engine)
    _seed_with_sample_data(models)

def _seed_with_sample_data(models_module) -> None:
    sample_dir = Path(__file__).resolve().parent / "sample_data"
    if not sample_dir.exists():
        return

    db = SessionLocal()
    try:
        if db.query(models_module.Student).count() == 0:
            students_file = sample_dir / "students.json"
            if students_file.exists():
                students = json.loads(students_file.read_text(encoding='utf-8'))
                for entry in students:
                    birthday = entry.get("birthday")
                    if isinstance(birthday, str):
                        entry["birthday"] = date.fromisoformat(birthday)
                    db.add(models_module.Student(**entry))

        if db.query(models_module.Room).count() == 0:
            rooms_file = sample_dir / "rooms.json"
            if rooms_file.exists():
                rooms = json.loads(rooms_file.read_text(encoding='utf-8'))
                for entry in rooms:
                    db.add(models_module.Room(**entry))

        db.commit()
    finally:
        db.close()
