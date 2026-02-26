"""
Database connection and session management.
Defaults to local SQLite (zero-config). Set DATABASE_URL env var
to use PostgreSQL or any other supported backend.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

# Default to SQLite so the app works out of the box without PostgreSQL
_DEFAULT_DB = "sqlite:///resume_builder.db"
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DB)

# SQLite needs check_same_thread=False for Streamlit's multi-thread model
_connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Yield a database session and ensure it is closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables defined in models.py (safe to call multiple times)."""
    from database.models import User, Resume, ATSScore, CoverLetter  # noqa: F401
    Base.metadata.create_all(bind=engine)
