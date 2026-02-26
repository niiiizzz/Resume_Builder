"""
Centralized dashboard data synchronization.
Queries all tables and provides a single refresh function
to keep dashboard metrics and recent items up to date.
Every call queries the LIVE database — no stale cache.
Result is also stored in st.session_state["dashboard_data"]
so the dashboard page can read it immediately after saves.
"""

import logging
import streamlit as st
from database.db import SessionLocal
from database.models import Resume, ATSScore, CoverLetter

logger = logging.getLogger(__name__)


def refresh_user_dashboard(user_id: int) -> dict:
    """
    Query all tables for user data and return a structured dashboard dict.
    Also caches the result in st.session_state["dashboard_data"] for
    immediate access by the dashboard page.

    Returns:
        {
            "resume_count": int,
            "cover_letter_count": int,
            "ats_count": int,
            "recent_cover_letters": list[dict],
            "recent_ats_scores": list[dict],
            "recent_resumes": list[dict],
        }
    """
    db = SessionLocal()
    try:
        resume_count = db.query(Resume).filter(Resume.user_id == user_id).count()
        cover_count = db.query(CoverLetter).filter(CoverLetter.user_id == user_id).count()
        ats_count = db.query(ATSScore).filter(ATSScore.user_id == user_id).count()

        # Last 5 cover letters
        recent_cls = (
            db.query(CoverLetter)
            .filter(CoverLetter.user_id == user_id)
            .order_by(CoverLetter.created_at.desc())
            .limit(5)
            .all()
        )
        recent_cover_letters = [
            {
                "id": cl.id,
                "company": cl.company,
                "role": cl.role,
                "content": cl.content,
                "snippet": cl.content[:120] + "…" if len(cl.content) > 120 else cl.content,
                "created_at": cl.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for cl in recent_cls
        ]

        # Last 5 ATS scores
        recent_ats = (
            db.query(ATSScore)
            .filter(ATSScore.user_id == user_id)
            .order_by(ATSScore.created_at.desc())
            .limit(5)
            .all()
        )
        recent_ats_scores = [
            {
                "id": s.id,
                "score": s.ats_score,
                "missing_keywords": s.missing_keywords,
                "created_at": s.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for s in recent_ats
        ]

        # Last 5 resumes
        recent_res = (
            db.query(Resume)
            .filter(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
            .limit(5)
            .all()
        )
        recent_resumes = [
            {
                "id": r.id,
                "resume_type": getattr(r, "resume_type", "original"),
                "snippet": r.resume_content[:120] + "…" if len(r.resume_content) > 120 else r.resume_content,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for r in recent_res
        ]

        data = {
            "resume_count": resume_count,
            "cover_letter_count": cover_count,
            "ats_count": ats_count,
            "recent_cover_letters": recent_cover_letters,
            "recent_ats_scores": recent_ats_scores,
            "recent_resumes": recent_resumes,
        }

        # Cache in session_state for immediate access
        st.session_state["dashboard_data"] = data
        logger.info(
            "Dashboard refreshed for user %d: %d resumes, %d CLs, %d ATS",
            user_id, resume_count, cover_count, ats_count,
        )
        return data

    except Exception as e:
        logger.error("Dashboard refresh failed: %s", e)
        return st.session_state.get("dashboard_data", {
            "resume_count": 0,
            "cover_letter_count": 0,
            "ats_count": 0,
            "recent_cover_letters": [],
            "recent_ats_scores": [],
            "recent_resumes": [],
        })
    finally:
        db.close()
