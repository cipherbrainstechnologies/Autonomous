from __future__ import annotations

import os
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session


Base = declarative_base()


def _load_database_url() -> str:
    """
    Resolve database URL from env or config/secrets.toml.
    Env var DATABASE_URL takes precedence. Example:
    postgresql+psycopg2://user:password@host:5432/dbname
    """
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    # Lazy import to avoid hard dependency if file missing
    try:
        import tomllib  # py311+
    except Exception:
        tomllib = None

    if tomllib:
        try:
            secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "secrets.toml")
            if os.path.exists(secrets_path):
                with open(secrets_path, "rb") as f:
                    data = tomllib.load(f)
                # Support either top-level or nested under database
                db_url = (
                    data.get("database_url")
                    or data.get("database", {}).get("url")
                    or ""
                )
                if db_url:
                    return db_url
        except Exception:
            # Fall through to default
            pass

    # Default to local dev sqlite if nothing configured (safe fallback for first run)
    return "sqlite:///./data/app.db"


_DATABASE_URL = _load_database_url()

# pool_pre_ping improves resilience across network hiccups
engine = create_engine(_DATABASE_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)


def get_session() -> Generator[Session, None, None]:
    """
    Context-managed session generator for dependency injection (e.g., in services/UI).
    Usage:
        with contextlib.closing(next(get_session())) as db:
            ...
    Or in FastAPI style:
        def dep():
            db = SessionLocal(); try: yield db; finally: db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database(create_all: bool = True) -> None:
    """
    Initialize database metadata. In production, prefer migrations (Alembic).
    """
    if create_all:
        Base.metadata.create_all(bind=engine)


