"""
SQLAlchemy ORM models for the Resume Builder application.
Compatible with both SQLite and PostgreSQL.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    ats_scores = relationship("ATSScore", back_populates="user", cascade="all, delete-orphan")
    cover_letters = relationship("CoverLetter", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_content = Column(Text, nullable=False)
    resume_type = Column(String(50), default="original")  # "original" | "optimized"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="resumes")

    def __repr__(self):
        return f"<Resume(id={self.id}, user_id={self.user_id})>"


class ATSScore(Base):
    __tablename__ = "ats_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_description = Column(Text, nullable=False)
    ats_score = Column(Float, nullable=False)
    missing_keywords = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="ats_scores")

    def __repr__(self):
        return f"<ATSScore(id={self.id}, score={self.ats_score})>"


class CoverLetter(Base):
    __tablename__ = "cover_letters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="cover_letters")

    def __repr__(self):
        return f"<CoverLetter(id={self.id}, company='{self.company}')>"
