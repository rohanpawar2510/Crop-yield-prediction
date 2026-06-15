"""
database.py — SQLAlchemy database engine for MySQL.
"""

from __future__ import annotations

import os
from urllib.parse import quote_plus  # ✅ ADDED (IMPORTANT FIX)

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# ── Build MySQL URL from .env variables ───────────────────────────────────────
_HOST = os.getenv("DB_HOST", "localhost")
_PORT = os.getenv("DB_PORT", "3306")
_USER = os.getenv("DB_USER", "root")

# ✅ FIX: encode password to handle special characters like @
_PASS = quote_plus(os.getenv("DB_PASSWORD", "Rohan@2510"))

_NAME = os.getenv("DB_NAME", "crop_yield_db")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"mysql+pymysql://{_USER}:{_PASS}@{_HOST}:{_PORT}/{_NAME}?charset=utf8mb4"
)

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Base class ────────────────────────────────────────────────────────────────
Base = declarative_base()


# ── FastAPI dependency ────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from models import db_models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Verify connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    print(f"✅ MySQL connected — database: {_NAME} @ {_HOST}:{_PORT}")