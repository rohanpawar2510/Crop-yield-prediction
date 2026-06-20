"""
database.py — SQLAlchemy database engine for MySQL / TiDB Cloud.
"""

from __future__ import annotations

import os
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

# ── Build DB URL from environment variables ──────────────────────────────

_HOST = os.getenv("DB_HOST", "localhost")
_PORT = os.getenv("DB_PORT", "3306")
_USER = os.getenv("DB_USER", "root")
_PASS = quote_plus(os.getenv("DB_PASSWORD", ""))
_NAME = os.getenv("DB_NAME", "crop_yield_db")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{_USER}:{_PASS}@{_HOST}:{_PORT}/{_NAME}?charset=utf8mb4"
)

# ── Engine (TiDB SSL Support) ────────────────────────────────────────────

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    echo=False,
    connect_args={
        "ssl": {
            "ssl_verify_cert": False,
            "ssl_verify_identity": False,
        }
    },
)

# ── Session Factory ──────────────────────────────────────────────────────

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ── Base Class ───────────────────────────────────────────────────────────

Base = declarative_base()

# ── Dependency ───────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── Initialize Database ──────────────────────────────────────────────────

def init_db():
    from models import db_models

    Base.metadata.create_all(bind=engine)

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    print(f"✅ Database connected: {_NAME} @ {_HOST}:{_PORT}")