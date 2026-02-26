"""
Authentication utilities — password hashing, sign-up, sign-in, session helpers.
Uses bcrypt directly (avoids passlib compatibility issues with newer bcrypt versions).
"""

import bcrypt
import streamlit as st
from sqlalchemy.exc import IntegrityError
from database.db import SessionLocal
from database.models import User


# ---------------------------------------------------------------------------
# Password helpers (using bcrypt directly to avoid passlib 72-byte bug)
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given password."""
    pw_bytes = password.encode("utf-8")[:72]  # bcrypt limit
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    pw_bytes = plain.encode("utf-8")[:72]
    hashed_bytes = hashed.encode("utf-8")
    return bcrypt.checkpw(pw_bytes, hashed_bytes)


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------

def signup(name: str, email: str, password: str) -> dict | None:
    """
    Create a new user. Returns the user dict on success, None if email
    already exists, or raises on unexpected errors.
    """
    db = SessionLocal()
    try:
        user = User(
            name=name.strip(),
            email=email.strip().lower(),
            hashed_password=hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"id": user.id, "name": user.name, "email": user.email}
    except IntegrityError:
        db.rollback()
        return None
    finally:
        db.close()


def signin(email: str, password: str) -> dict | None:
    """
    Authenticate a user. Returns user dict on success, None on failure.
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.strip().lower()).first()
        if user and verify_password(password, user.hashed_password):
            return {"id": user.id, "name": user.name, "email": user.email}
        return None
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Session-state helpers (Streamlit)
# ---------------------------------------------------------------------------

def login_user(user_dict: dict):
    """Store the authenticated user in Streamlit session state."""
    st.session_state["authenticated"] = True
    st.session_state["user"] = user_dict


def logout_user():
    """Clear ALL app-related session state to prevent stale data."""
    _keys_to_clear = [
        "authenticated", "user", "dashboard_page",
        "generated_resume", "generated_cover_letter", "generated_portfolio",
        "dashboard_data",
    ]
    for key in _keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]


def get_current_user() -> dict | None:
    """Return the currently logged-in user dict, or None."""
    if st.session_state.get("authenticated"):
        return st.session_state.get("user")
    return None


def is_authenticated() -> bool:
    """Check whether a user is currently logged in."""
    return st.session_state.get("authenticated", False)
