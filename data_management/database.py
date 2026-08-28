from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def _build_engine():
    database_url = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/golt")
    if database_url.startswith("sqlite"):
        return create_engine(database_url, connect_args={"check_same_thread": False}, future=True)
    return create_engine(database_url, future=True)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_engine():
    return engine


def get_session():
    return SessionLocal()


def init_db():
    Base.metadata.create_all(bind=engine)
    from .runtime_schema import metadata as runtime_metadata

    runtime_metadata.create_all(bind=engine)


def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def check_database_connection() -> bool:
    with engine.connect() as connection:
        connection.exec_driver_sql("SELECT 1")
    return True
