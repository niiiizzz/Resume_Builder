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


def _upgrade_schema():
    """
    Add columns that were introduced after initial table creation.
    SQLAlchemy's create_all() only creates NEW tables — it does not
    ALTER existing tables.  This function safely adds missing columns
    using raw SQL so the app works with databases created by older
    versions of the code.
    """
    import logging
    _log = logging.getLogger(__name__)

    # (table, column, sql_type, default_expr)
    _MIGRATIONS = [
        ("resumes", "resume_type", "VARCHAR(50)", "'original'"),
    ]

    from sqlalchemy import text, inspect as sa_inspect
    insp = sa_inspect(engine)

    for table, column, col_type, default in _MIGRATIONS:
        if table not in insp.get_table_names():
            continue  # table doesn't exist yet; create_all will handle it
        existing_cols = {c["name"] for c in insp.get_columns(table)}
        if column in existing_cols:
            continue  # already present
        alter_sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type} DEFAULT {default}"
        try:
            with engine.begin() as conn:
                conn.execute(text(alter_sql))
            _log.info("Schema upgrade: added %s.%s", table, column)
        except Exception as exc:
            _log.warning("Schema upgrade skipped %s.%s: %s", table, column, exc)


def init_db():
    """Create all tables defined in models.py (safe to call multiple times)."""
    from database.models import User, Resume, ATSScore, CoverLetter  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _upgrade_schema()
