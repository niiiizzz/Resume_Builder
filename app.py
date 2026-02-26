"""
AI Resume & Portfolio Builder with ATS Optimization
====================================================
Main Streamlit application — routes between Landing, Auth, Dashboard, and all features.
"""

import logging

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils.navigation import render_back_to_dashboard
from utils.data_sync import refresh_user_dashboard

# ---------------------------------------------------------------------------
# Page config (MUST be the first Streamlit command)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Resume Builder",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Load custom CSS  (file-based + inline fallback for critical overrides)
# ---------------------------------------------------------------------------
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "styles", "theme.css")
    css = ""
    if os.path.exists(css_path):
        with open(css_path) as f:
            css = f.read()

    # Inline overrides to guarantee theming regardless of Streamlit version
    css += """
    /* ── Inline Critical Overrides ── */
    .stApp, [data-testid="stAppViewContainer"], .main {
        background: linear-gradient(180deg, #0A0A0A 0%, #111111 50%, #0A0A0A 100%) !important;
        background-attachment: fixed !important;
    }
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, #060a14 0%, #0a1226 50%, #060a14 100%) !important;
    }
    /* Fix password eye-button overlap */
    .stTextInput > div { position: relative !important; }
    .stTextInput > div > div > input {
        padding-right: 2.8rem !important;
    }
    .stTextInput button[kind="icon"] {
        position: absolute !important;
        right: 0.4rem !important;
        top: 50% !important;
        transform: translateY(-50%) !important;
        z-index: 2 !important;
        background: transparent !important;
        border: none !important;
    }
    /* Ensure label text never clips */
    .stTextInput label, .stTextArea label {
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: unset !important;
        margin-bottom: 0.35rem !important;
    }
    /* Form padding fix */
    [data-testid="stForm"] {
        padding: 1.5rem !important;
        background: rgba(10, 15, 26, 0.85) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(0,229,255,0.12) !important;
        border-radius: 14px !important;
    }
    """

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

load_css()

# ---------------------------------------------------------------------------
# Database initialisation (graceful — never crashes the app)
# ---------------------------------------------------------------------------
_DB_OK = False
try:
    from database.db import init_db, SessionLocal
    from database.models import User, Resume, ATSScore, CoverLetter
    init_db()
    _DB_OK = True
except Exception as _db_err:
    import logging
    logging.warning("Database init failed: %s", _db_err)

from auth.auth_utils import (
    signup, signin, login_user, logout_user,
    get_current_user, is_authenticated,
)
from utils.helpers import validate_email, validate_password, sanitize_input

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "authenticated": False,
    "user": None,
    "page": "landing",
    "dashboard_page": "dashboard_home",
    "show_pw_si": False,
    "show_pw_su": False,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  LANDING PAGE                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def render_landing():
    # --- Navbar ---
    nav_cols = st.columns([3, 1, 1, 1, 1])
    with nav_cols[0]:
        st.markdown("### ⚡ **AI Resume Builder**")
    with nav_cols[2]:
        if st.button("Features", key="nav_feat"):
            pass
    with nav_cols[3]:
        if st.button("About", key="nav_about"):
            pass
    with nav_cols[4]:
        if st.button("Sign In", key="nav_signin"):
            st.session_state["page"] = "auth"
            st.rerun()

    # --- Hero ---
    st.markdown("""
    <div class="hero">
        <h1>AI Resume & Portfolio Builder</h1>
        <p>
            Craft ATS-optimized resumes, tailor them to any job description,
            generate stunning cover letters, and build your professional portfolio
            — all powered by AI.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown('<div class="hero-btn-group">', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🚀  Get Started", key="hero_start", use_container_width=True):
                st.session_state["page"] = "auth"
                st.rerun()
        with col_b:
            st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
            if st.button("🔑  Sign In", key="hero_signin", use_container_width=True):
                st.session_state["page"] = "auth"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # --- Features ---
    st.markdown("## ✨ Key Features")
    features = [
        ("📝", "Resume Generator", "AI-crafted, ATS-optimized resumes using action verbs and quantified achievements."),
        ("🎯", "JD Optimization", "Tailor your resume to any job description — boost keyword match and ATS score."),
        ("✉️", "Cover Letter Generator", "Personalised, role-specific cover letters that stand out."),
        ("🌐", "Portfolio Builder", "Professional About Me, bios, project descriptions, and LinkedIn summaries."),
        ("📊", "ATS Score Analyzer", "Simulate ATS screening — get your score, missing keywords, and actionable tips."),
        ("🔒", "Secure & Private", "Your data is encrypted and stored securely. Only you can access your content."),
    ]

    rows = [features[i:i + 3] for i in range(0, len(features), 3)]
    for row in rows:
        cols = st.columns(len(row))
        for col, (icon, title, desc) in zip(cols, row):
            with col:
                st.markdown(f"""
                <div class="feature-card">
                    <div class="feature-icon">{icon}</div>
                    <div class="feature-title">{title}</div>
                    <div class="feature-desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # --- Benefits ---
    st.markdown("## 🏆 Why Choose Us")
    b1, b2, b3 = st.columns(3)
    with b1:
        st.markdown("""
        <div class="benefit-card">
            <h4>⚡ Lightning Fast</h4>
            <p>Generate professional documents in seconds, not hours.</p>
        </div>
        """, unsafe_allow_html=True)
    with b2:
        st.markdown("""
        <div class="benefit-card">
            <h4>🤖 AI-Powered</h4>
            <p>Backed by state-of-the-art language models for human-quality output.</p>
        </div>
        """, unsafe_allow_html=True)
    with b3:
        st.markdown("""
        <div class="benefit-card">
            <h4>📈 ATS Optimized</h4>
            <p>Every resume is engineered to pass automated screening systems.</p>
        </div>
        """, unsafe_allow_html=True)

    # --- Footer ---
    st.markdown("""
    <div class="footer">
        © 2026 AI Resume Builder — Built with ❤️ and AI
    </div>
    """, unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  AUTHENTICATION PAGE                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def render_auth():
    if not _DB_OK:
        st.error("⚠️ Database is not available. Please check your DATABASE_URL configuration.")
        if st.button("← Back to Home"):
            st.session_state["page"] = "landing"
            st.rerun()
        return

    # Top spacer
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1.2, 1.6, 1.2])
    with col_m:
        # Header card
        st.markdown("""
        <div style="text-align:center; margin-bottom:1.8rem;">
            <h1 style="
                font-size:2rem;
                font-weight:800;
                background: linear-gradient(135deg, #00E5FF, #00B8D9);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom:0.4rem;
            ">📄 AI Resume Builder</h1>
            <p style="color:#7A8BA8; font-size:0.95rem;">
                Sign in to your account or create a new one
            </p>
        </div>
        """, unsafe_allow_html=True)

        tab_signin, tab_signup = st.tabs(["🔑 Sign In", "📝 Sign Up"])

        # --- Sign In ---
        with tab_signin:
            with st.form("signin_form", clear_on_submit=False):
                st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
                email = st.text_input("Email Address", placeholder="you@example.com", key="si_email")
                st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
                password = st.text_input(
                    "Password",
                    type="default" if st.session_state["show_pw_si"] else "password",
                    placeholder="Enter your password",
                    key="si_pass",
                )
                st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
                submitted = st.form_submit_button("⚡ Sign In", use_container_width=True)

            # Toggle button OUTSIDE the form
            toggle_label = "🙈 Hide password" if st.session_state["show_pw_si"] else "👁 Show password"
            st.markdown('<div class="pw-toggle">', unsafe_allow_html=True)
            if st.button(toggle_label, key="toggle_pw_si"):
                st.session_state["show_pw_si"] = not st.session_state["show_pw_si"]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            if submitted:
                if not email or not password:
                    st.error("Please fill in all fields.")
                else:
                    try:
                        user = signin(email.strip(), password)
                        if user:
                            login_user(user)
                            st.session_state["page"] = "dashboard"
                            st.rerun()
                        else:
                            st.error("❌ Invalid email or password. Please try again.")
                    except Exception as e:
                        st.error(f"Login error: {e}")

        # --- Sign Up ---
        with tab_signup:
            with st.form("signup_form", clear_on_submit=False):
                st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
                name = st.text_input("Full Name", placeholder="John Doe", key="su_name")
                st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
                email_su = st.text_input("Email Address", placeholder="you@example.com", key="su_email")
                st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
                pw1 = st.text_input(
                    "Password",
                    type="default" if st.session_state["show_pw_su"] else "password",
                    key="su_pw1",
                    placeholder="Min 8 chars, 1 uppercase, 1 number",
                )
                st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
                pw2 = st.text_input(
                    "Confirm Password",
                    type="default" if st.session_state["show_pw_su"] else "password",
                    key="su_pw2",
                    placeholder="Re-enter your password",
                )
                st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
                submitted_su = st.form_submit_button("🚀 Create Account", use_container_width=True)

            # Toggle button OUTSIDE the form
            toggle_label_su = "🙈 Hide passwords" if st.session_state["show_pw_su"] else "👁 Show passwords"
            st.markdown('<div class="pw-toggle">', unsafe_allow_html=True)
            if st.button(toggle_label_su, key="toggle_pw_su"):
                st.session_state["show_pw_su"] = not st.session_state["show_pw_su"]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            if submitted_su:
                if not name or not email_su or not pw1:
                    st.error("Please fill in all fields.")
                elif not validate_email(email_su):
                    st.error("Please enter a valid email address.")
                elif pw1 != pw2:
                    st.error("Passwords do not match.")
                else:
                    valid, msg = validate_password(pw1)
                    if not valid:
                        st.error(msg)
                    else:
                        try:
                            result = signup(name.strip(), email_su.strip(), pw1)
                            if result:
                                login_user(result)
                                st.session_state["page"] = "dashboard"
                                st.success("✅ Account created! Redirecting…")
                                st.rerun()
                            else:
                                st.error("An account with this email already exists.")
                        except Exception as e:
                            st.error(f"Signup error: {e}")

        # Back button
        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="secondary-btn">', unsafe_allow_html=True)
        if st.button("← Back to Home", key="auth_back", use_container_width=True):
            st.session_state["page"] = "landing"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  DASHBOARD & FEATURES                                                 ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def render_dashboard():
    user = get_current_user()
    if not user:
        st.session_state["page"] = "auth"
        st.rerun()
        return

    # --- Sidebar ---
    with st.sidebar:
        st.markdown(f"### 👋 Hi, {user['name']}")
        st.markdown("---")
        pages = {
            "🏠 Dashboard": "dashboard_home",
            "📝 Resume Generator": "resume_gen",
            "🎯 JD Optimization": "jd_opt",
            "✉️ Cover Letter": "cover_letter",
            "🌐 Portfolio Generator": "portfolio",
            "📊 ATS Analyzer": "ats_analyzer",
            "👤 Profile": "profile",
        }
        for label, key in pages.items():
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state["dashboard_page"] = key
                st.rerun()

        st.markdown("---")
        if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
            logout_user()
            st.session_state["page"] = "landing"
            st.rerun()

    # --- Route ---
    page = st.session_state.get("dashboard_page", "dashboard_home")
    page_map = {
        "dashboard_home": _page_dashboard_home,
        "resume_gen": _page_resume_generator,
        "jd_opt": _page_jd_optimizer,
        "cover_letter": _page_cover_letter,
        "portfolio": _page_portfolio,
        "ats_analyzer": _page_ats_analyzer,
        "profile": _page_profile,
    }
    page_map.get(page, _page_dashboard_home)()


# ── Dashboard Home ────────────────────────────────────────────────────────

def _page_dashboard_home():
    user = get_current_user()
    st.markdown(f"# Welcome back, {user['name']}! 👋")
    st.markdown("Use the sidebar to access all tools.")
    st.markdown("---")

    # Centralized data refresh
    dash = refresh_user_dashboard(user["id"])

    c1, c2 = st.columns(2)
    with c1:
        st.metric("📝 Resumes Saved", dash["resume_count"])
    with c2:
        st.metric("📊 ATS Analyses", dash["ats_count"])

    st.markdown("---")

    st.markdown("### 🚀 Quick Actions")
    cols = st.columns(3)
    with cols[0]:
        if st.button("📝 Create Resume", use_container_width=True):
            st.session_state["dashboard_page"] = "resume_gen"
            st.rerun()
    with cols[1]:
        if st.button("🎯 Optimize for JD", use_container_width=True):
            st.session_state["dashboard_page"] = "jd_opt"
            st.rerun()
    with cols[2]:
        if st.button("📊 Analyze ATS Score", use_container_width=True):
            st.session_state["dashboard_page"] = "ats_analyzer"
            st.rerun()

    # --- Recent Cover Letters ---
    if dash["recent_cover_letters"]:
        st.markdown("---")
        st.markdown("### ✉️ Recent Cover Letters")
        for cl in dash["recent_cover_letters"]:
            with st.expander(f"**{cl['company']}** — {cl['role']}  ·  {cl['created_at']}"):
                st.markdown(cl["content"])

    # --- Recent ATS Scores ---
    if dash["recent_ats_scores"]:
        st.markdown("---")
        st.markdown("### 📊 Recent ATS Scores")
        for s in dash["recent_ats_scores"]:
            col_s, col_p = st.columns([1, 3])
            with col_s:
                st.metric("Score", f"{s['score']}%")
            with col_p:
                st.progress(min(s["score"] / 100, 1.0))
                if s["missing_keywords"]:
                    st.caption(f"Missing: {s['missing_keywords'][:80]}…")


# ── Resume Generator ─────────────────────────────────────────────────────

def _page_resume_generator():
    render_back_to_dashboard()
    st.markdown("# 📝 Resume Generator")
    st.markdown("Fill in your details and let AI craft a professional, ATS-optimized resume.")
    st.markdown("---")

    with st.form("resume_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name", value=get_current_user()["name"])
            email = st.text_input("Email", value=get_current_user()["email"])
            phone = st.text_input("Phone Number")
        with c2:
            location = st.text_input("Location")
            linkedin = st.text_input("LinkedIn URL")
            target_role = st.text_input("Target Role", placeholder="e.g. Senior Software Engineer")

        summary = st.text_area("Professional Summary", height=100,
                               placeholder="Brief overview of your career and goals…")
        skills = st.text_area("Skills", height=80,
                              placeholder="Python, React, AWS, Machine Learning, …")
        education = st.text_area("Education", height=100,
                                 placeholder="B.Tech in CS — XYZ University, 2020–2024\nRelevant coursework: …")
        experience = st.text_area("Work Experience", height=150,
                                  placeholder="Software Engineer @ Company (2022–Present)\n- Led development of…")
        projects = st.text_area("Projects", height=120,
                                placeholder="Project Name — Description, technologies, impact…")
        achievements = st.text_area("Achievements / Certifications", height=80,
                                    placeholder="AWS Certified Solutions Architect\nHackathon Winner — …")

        submitted = st.form_submit_button("✨ Generate Resume", use_container_width=True)

    if submitted:
        if not name or not target_role:
            st.error("Name and Target Role are required.")
            return

        details = {
            "name": name, "email": email, "phone": phone, "location": location,
            "linkedin": linkedin, "target_role": target_role, "summary": summary,
            "skills": skills, "education": education, "experience": experience,
            "projects": projects, "achievements": achievements,
        }

        with st.spinner("🤖 AI is crafting your resume…"):
            try:
                from ai.resume_generator import generate_resume
                resume = generate_resume(details)
            except Exception as e:
                st.error(f"AI generation failed: {e}")
                return

        # Store in session state for download buttons
        st.session_state["generated_resume"] = resume

    # --- Display generated resume if available ---
    if st.session_state.get("generated_resume"):
        resume = st.session_state["generated_resume"]

        st.markdown("---")
        st.markdown("### 📄 Your Generated Resume")
        st.markdown(resume)

        st.markdown("---")
        col_save, col_pdf, col_docx = st.columns(3)
        with col_save:
            if st.button("💾 Save to Account", key="save_resume", use_container_width=True):
                if _save_resume(resume):
                    st.toast("✅ Resume saved to your account!")
                else:
                    st.error("❌ Failed to save resume. Please try again.")
        with col_pdf:
            from utils.export import resume_to_pdf
            pdf_bytes = resume_to_pdf(resume)
            st.download_button(
                label="📄 Download PDF",
                data=pdf_bytes,
                file_name="resume.pdf",
                mime="application/pdf",
                key="dl_pdf",
                use_container_width=True,
            )
        with col_docx:
            from utils.export import resume_to_docx
            docx_bytes = resume_to_docx(resume)
            st.download_button(
                label="📝 Download DOCX",
                data=docx_bytes,
                file_name="resume.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="dl_docx",
                use_container_width=True,
            )


def _save_resume(content: str, resume_type: str = "original") -> bool:
    """Save a resume to the DB. Returns True on success, False on failure."""
    user = get_current_user()
    if not user:
        logging.error("_save_resume called without authenticated user")
        return False
    db = SessionLocal()
    try:
        obj = Resume(user_id=user["id"], resume_content=content, resume_type=resume_type)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        refresh_user_dashboard(user["id"])
        return True
    except Exception as e:
        db.rollback()
        logging.error("Failed to save resume: %s", e)
        return False
    finally:
        db.close()


# ── JD Optimizer ──────────────────────────────────────────────────────────

def _page_jd_optimizer():
    render_back_to_dashboard()
    st.markdown("# 🎯 JD-Based Resume Optimization")
    st.markdown("Upload your existing resume and paste a job description to get an optimized version.")
    st.markdown("---")

    # --- File Upload for Resume ---
    st.markdown("### 📎 Upload Resume")
    st.caption("Upload your resume as PDF, DOCX, or TXT. Max 5 MB.")
    uploaded_resume = st.file_uploader(
        "Upload your resume",
        type=["pdf", "docx", "txt"],
        key="jd_opt_file_upload",
        label_visibility="collapsed",
    )

    extracted_resume = ""
    if uploaded_resume is not None:
        file_bytes = uploaded_resume.read()
        file_name = uploaded_resume.name.lower()
        try:
            from utils.file_parser import (
                extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt,
            )
            if file_name.endswith(".pdf"):
                extracted_resume = extract_text_from_pdf(file_bytes)
            elif file_name.endswith(".docx"):
                extracted_resume = extract_text_from_docx(file_bytes)
            else:
                extracted_resume = extract_text_from_txt(file_bytes)

            with st.expander("📄 Extracted Resume Preview", expanded=False):
                st.text_area("Extracted content", value=extracted_resume, height=200,
                             disabled=True, key="jd_resume_preview")
            st.success(f"✅ Extracted {len(extracted_resume):,} characters from {uploaded_resume.name}")
        except ValueError as e:
            st.error(f"❌ {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

    st.markdown("---")

    with st.form("jd_opt_form"):
        jd_text = st.text_area("Target Job Description", height=200,
                               placeholder="Paste the job description here…")
        submitted = st.form_submit_button("⚡ Optimize Resume", use_container_width=True)

    if submitted:
        resume_text = extracted_resume
        if not resume_text:
            st.error("Please upload your resume file above.")
            return
        if not jd_text:
            st.error("Job description is required.")
            return

        with st.spinner("🤖 Analyzing and optimizing your resume…"):
            try:
                from ai.jd_optimizer import optimize_resume
                result = optimize_resume(resume_text, jd_text)
            except Exception as e:
                st.error(f"Optimization failed: {e}")
                return

        st.markdown("---")

        tab_resume, tab_changes, tab_kw = st.tabs(["📄 Optimized Resume", "📋 Changes Made", "🔑 Keywords"])

        with tab_resume:
            optimized = result.get("optimized_resume", "")
            st.markdown(optimized)
            if st.button("💾 Save Optimized Resume", key="save_opt_resume", use_container_width=True):
                if _save_resume(optimized, resume_type="optimized"):
                    st.toast("✅ Optimized resume saved to your account!")
                else:
                    st.error("❌ Failed to save optimized resume. Please try again.")

        with tab_changes:
            st.markdown(result.get("changes", "No changes listed."))

        with tab_kw:
            st.markdown("**Extracted Keywords from JD:**")
            st.markdown(result.get("extracted_keywords", "—"))
            st.markdown("**Keywords Missing from Original Resume:**")
            st.markdown(result.get("missing_keywords", "—"))


# ── Cover Letter ──────────────────────────────────────────────────────────

def _page_cover_letter():
    render_back_to_dashboard()
    st.markdown("# ✉️ Cover Letter Generator")
    st.markdown("Generate a personalized, role-specific cover letter in seconds.")
    st.markdown("---")

    with st.form("cover_form"):
        c1, c2 = st.columns(2)
        with c1:
            company = st.text_input("Company Name", placeholder="e.g. Google")
        with c2:
            role = st.text_input("Role", placeholder="e.g. Software Engineer")
        why_interested = st.text_area("Why are you interested?", height=100,
                                      placeholder="What excites you about this company/role…")
        strengths = st.text_area("Key Strengths", height=100,
                                 placeholder="List 2-3 relevant strengths or experiences…")
        submitted = st.form_submit_button("✨ Generate Cover Letter", use_container_width=True)

    if submitted:
        if not company or not role:
            st.error("Company and Role are required.")
            return

        with st.spinner("🤖 Writing your cover letter…"):
            try:
                from ai.cover_letter import generate_cover_letter
                letter = generate_cover_letter(company, role, why_interested, strengths)
            except Exception as e:
                st.error(f"Generation failed: {e}")
                return

        st.markdown("---")
        st.markdown("### ✉️ Your Cover Letter")
        st.markdown(letter)

        st.markdown("---")
        if st.button("💾 Save Cover Letter", key="save_cl", use_container_width=True):
            if _save_cover_letter(company, role, letter):
                st.toast("✅ Cover letter saved to your account!")
            else:
                st.error("❌ Failed to save cover letter. Please try again.")


def _save_cover_letter(company: str, role: str, content: str) -> bool:
    """Save a cover letter to the DB. Returns True on success, False on failure."""
    user = get_current_user()
    if not user:
        logging.error("_save_cover_letter called without authenticated user")
        return False
    db = SessionLocal()
    try:
        obj = CoverLetter(user_id=user["id"], company=company, role=role, content=content)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        refresh_user_dashboard(user["id"])
        return True
    except Exception as e:
        db.rollback()
        logging.error("Failed to save cover letter: %s", e)
        return False
    finally:
        db.close()


# ── Portfolio Generator ───────────────────────────────────────────────────

def _page_portfolio():
    render_back_to_dashboard()
    st.markdown("# 🌐 Portfolio Content Generator")
    st.markdown("Generate professional portfolio content for your website and LinkedIn.")
    st.markdown("---")

    with st.form("portfolio_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name", value=get_current_user()["name"])
            title = st.text_input("Professional Title", placeholder="e.g. Full-Stack Developer")
        with c2:
            skills = st.text_input("Key Skills", placeholder="Python, React, AI/ML…")
            interests = st.text_input("Interests / Hobbies", placeholder="Open source, blogging…")
        experience = st.text_area("Experience Summary", height=100,
                                  placeholder="3 years building web apps at…")
        projects = st.text_area("Notable Projects", height=100,
                                placeholder="Project name — short description…")
        submitted = st.form_submit_button("✨ Generate Portfolio Content", use_container_width=True)

    if submitted:
        if not name:
            st.error("Name is required.")
            return

        details = {
            "name": name, "title": title, "skills": skills,
            "experience": experience, "projects": projects, "interests": interests,
        }

        with st.spinner("🤖 Generating your portfolio content…"):
            try:
                from ai.portfolio import generate_portfolio
                result = generate_portfolio(details)
            except Exception as e:
                st.error(f"Generation failed: {e}")
                return

        st.markdown("---")

        tabs = st.tabs(["🙋 About Me", "📋 Bio", "📂 Projects", "💼 LinkedIn", "🏷️ Tagline"])

        with tabs[0]:
            st.markdown(result.get("about_me", ""))
        with tabs[1]:
            st.markdown(result.get("bio", ""))
        with tabs[2]:
            st.markdown(result.get("projects", ""))
        with tabs[3]:
            st.markdown(result.get("linkedin_summary", ""))
        with tabs[4]:
            st.markdown(f"### {result.get('tagline', '')}")


# ── ATS Analyzer ──────────────────────────────────────────────────────────

def _page_ats_analyzer():
    render_back_to_dashboard()
    st.markdown("# 📊 ATS Score Analyzer")
    st.markdown("Simulate ATS screening and see how well your resume matches a job description.")
    st.markdown("---")

    # --- File Upload Section ---
    st.markdown("### 📎 Upload Resume")
    st.caption("Upload your resume as PDF, DOCX, or TXT. Max 5 MB.")
    uploaded_file = st.file_uploader(
        "Upload your resume",
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
        key="ats_file_upload",
        label_visibility="collapsed",
    )

    extracted_text = ""
    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name.lower()
        try:
            from utils.file_parser import (
                extract_text_from_pdf, extract_text_from_image,
                extract_text_from_docx, extract_text_from_txt,
            )
            if file_name.endswith(".pdf"):
                extracted_text = extract_text_from_pdf(file_bytes)
            elif file_name.endswith(".docx"):
                extracted_text = extract_text_from_docx(file_bytes)
            elif file_name.endswith(".txt"):
                extracted_text = extract_text_from_txt(file_bytes)
            else:
                extracted_text = extract_text_from_image(file_bytes)

            with st.expander("📄 Extracted Text Preview", expanded=False):
                st.text_area("Extracted content", value=extracted_text, height=200,
                             disabled=True, key="ats_preview")
            st.success(f"✅ Extracted {len(extracted_text):,} characters from {uploaded_file.name}")
        except ValueError as e:
            st.error(f"❌ {e}")
            extracted_text = ""
        except Exception as e:
            st.error(f"❌ Unexpected error processing file: {e}")
            extracted_text = ""

    st.markdown("---")

    with st.form("ats_form"):
        resume_text = st.text_area(
            "Resume Text (edit if needed)", height=150,
            value=extracted_text,
            placeholder="Upload a file above — or paste your resume here…",
        )
        jd_text = st.text_area("Job Description", height=200,
                               placeholder="Paste the job description here…")
        submitted = st.form_submit_button("🔍 Analyze ATS Score", use_container_width=True)

    if submitted:
        if not resume_text or not jd_text:
            st.error("Both resume and job description are required.")
            return

        with st.spinner("🔍 Analyzing with 3-layer hybrid model…"):
            from ats.ats_engine import compute_ats_score
            result = compute_ats_score(resume_text, jd_text)

        st.markdown("---")

        # --- Overall Score Badge ---
        score = result["score"]
        if score >= 75:
            color, grade = "#00E5FF", "Strong"
        elif score >= 60:
            color, grade = "#4CAF50", "Moderate"
        elif score >= 45:
            color, grade = "#FFB300", "Weak"
        else:
            color, grade = "#FF3B5C", "Poor"

        st.markdown(f"""
        <div class="score-display">
            <div class="score-value" style="color:{color}">{score}%</div>
            <div class="score-label">ATS Compatibility Score — {grade}</div>
        </div>
        """, unsafe_allow_html=True)

        st.progress(min(score / 100, 1.0))

        # --- 4-Category Breakdown ---
        st.markdown("---")
        st.markdown("### 📈 Score Breakdown")

        cat_cols = st.columns(4)
        layer_items = [
            ("🔑 Keyword Match", result["exact_match_score"]),
            ("📊 TF-IDF Similarity", result["tfidf_score"]),
            ("🔤 Semantic Match", result["semantic_score"]),
        ]
        for col, (label, val) in zip(cat_cols[:3], layer_items):
            with col:
                lbl_color = "#00E5FF" if val >= 60 else "#FFB300" if val >= 35 else "#FF3B5C"
                st.markdown(f"**{label}**")
                st.markdown(f"<span style='font-size:1.4rem;font-weight:700;color:{lbl_color}'>{val}%</span>",
                            unsafe_allow_html=True)
                st.progress(min(val / 100, 1.0))

        # Category analyses
        categories = result.get("categories", {})
        if categories:
            with cat_cols[3]:
                avg_cat = sum(c["score"] for c in categories.values()) / max(len(categories), 1)
                avg_color = "#00E5FF" if avg_cat >= 65 else "#FFB300" if avg_cat >= 45 else "#FF3B5C"
                st.markdown("**📋 Overall Grade**")
                st.markdown(f"<span style='font-size:1.4rem;font-weight:700;color:{avg_color}'>{avg_cat:.0f}%</span>",
                            unsafe_allow_html=True)
                st.progress(min(avg_cat / 100, 1.0))

        # --- Category Detail Cards ---
        if categories:
            st.markdown("---")
            st.markdown("### 🏷️ Detailed Analysis")
            for key, cat in categories.items():
                status_icon = "🟢" if cat["status"] == "strong" else "🟡" if cat["status"] == "moderate" else "🔴"
                st.markdown(f"{status_icon} **{cat['label']}** — `{cat['score']}%` ({cat['status'].title()})")
                st.progress(min(cat["score"] / 100, 1.0))

        st.markdown("---")

        # --- Strengths & Weaknesses ---
        if categories:
            col_str, col_wk = st.columns(2)
            with col_str:
                st.markdown("#### ✅ Strengths")
                strengths = [c for c in categories.values() if c["status"] == "strong"]
                if strengths:
                    for s in strengths:
                        st.markdown(f"- 🟢 {s['label']}")
                else:
                    st.info("No strong areas yet — keep improving!")
            with col_wk:
                st.markdown("#### ⚠️ Areas for Improvement")
                weaknesses = [c for c in categories.values() if c["status"] in ("weak", "moderate")]
                if weaknesses:
                    for w in weaknesses:
                        icon = "🔴" if w["status"] == "weak" else "🟡"
                        st.markdown(f"- {icon} {w['label']}")
                else:
                    st.success("All categories are strong!")

        st.markdown("---")

        tab_match, tab_miss, tab_sug = st.tabs(["✅ Matched Keywords", "❌ Missing Keywords", "💡 Suggestions"])

        with tab_match:
            if result["matched_keywords"]:
                st.markdown(", ".join(f"`{kw}`" for kw in result["matched_keywords"]))
            else:
                st.info("No matched keywords found.")

        with tab_miss:
            if result["missing_keywords"]:
                st.markdown(", ".join(f"`{kw}`" for kw in result["missing_keywords"]))
            else:
                st.success("No missing keywords — great job!")

        with tab_sug:
            for s in result["suggestions"]:
                st.markdown(f"- {s}")

        st.markdown("---")
        if st.button("💾 Save ATS Analysis", key="save_ats", use_container_width=True):
            if _save_ats_score(jd_text, result):
                st.toast("✅ ATS analysis saved!")
            else:
                st.error("❌ Failed to save ATS analysis. Please try again.")


def _save_ats_score(jd_text: str, result: dict) -> bool:
    """Save an ATS score to the DB. Returns True on success, False on failure."""
    user = get_current_user()
    if not user:
        logging.error("_save_ats_score called without authenticated user")
        return False
    db = SessionLocal()
    try:
        obj = ATSScore(
            user_id=user["id"],
            job_description=jd_text,
            ats_score=result["score"],
            missing_keywords=", ".join(result["missing_keywords"]),
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        refresh_user_dashboard(user["id"])
        return True
    except Exception as e:
        db.rollback()
        logging.error("Failed to save ATS score: %s", e)
        return False
    finally:
        db.close()


# ── Profile ───────────────────────────────────────────────────────────────

def _page_profile():
    render_back_to_dashboard()
    user = get_current_user()
    st.markdown("# 👤 Profile")
    st.markdown("---")

    # --- Fetch user record from DB for created_at ---
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.id == user["id"]).first()
        created_at_str = (
            db_user.created_at.strftime("%B %d, %Y") if db_user and db_user.created_at else "N/A"
        )

        # --- Profile Card ---
        st.markdown(f"""
        <div class="profile-card">
            <h3>👤 {user['name']}</h3>
            <p>📧 {user['email']}</p>
            <p style="color:#7A8BA8; font-size:0.85rem; margin-top:0.5rem;">📅 Member since {created_at_str}</p>
        </div>
        """, unsafe_allow_html=True)

        # --- Stat Cards ---
        resumes_all = db.query(Resume).filter(Resume.user_id == user["id"]).all()
        ats_all = db.query(ATSScore).filter(ATSScore.user_id == user["id"]).all()

        st.markdown("")
        sc1, sc2 = st.columns(2)
        with sc1:
            st.metric("📝 Total Resumes", len(resumes_all))
        with sc2:
            st.metric("📊 Total ATS Analyses", len(ats_all))

        st.markdown("---")

        # --- Recent Activity Feed ---
        st.markdown("### 🕓 Recent Activity")
        activities = []
        recent_resumes = (
            db.query(Resume)
            .filter(Resume.user_id == user["id"])
            .order_by(Resume.created_at.desc())
            .limit(5)
            .all()
        )
        for r in recent_resumes:
            activities.append({
                "date": r.created_at,
                "label": f"📝 Saved a **{r.resume_type}** resume",
            })
        recent_ats = (
            db.query(ATSScore)
            .filter(ATSScore.user_id == user["id"])
            .order_by(ATSScore.created_at.desc())
            .limit(5)
            .all()
        )
        for s in recent_ats:
            activities.append({
                "date": s.created_at,
                "label": f"📊 ATS analysis — **{s.ats_score:.0f}%**",
            })
        activities.sort(key=lambda x: x["date"], reverse=True)
        if activities:
            for act in activities[:5]:
                ts = act["date"].strftime("%Y-%m-%d %H:%M")
                st.markdown(f"- `{ts}` — {act['label']}")
        else:
            st.info("No activity yet. Start creating resumes and running ATS analyses!")

        st.markdown("---")

        # --- Edit Profile ---
        with st.expander("✏️ Edit Profile"):
            with st.form("edit_profile"):
                new_name = st.text_input("Name", value=user["name"])
                submitted = st.form_submit_button("Update Name", use_container_width=True)
                if submitted and new_name.strip():
                    db_user_edit = db.query(User).filter(User.id == user["id"]).first()
                    if db_user_edit:
                        db_user_edit.name = new_name.strip()
                        db.commit()
                        st.session_state["user"]["name"] = new_name.strip()
                        st.success("Name updated!")
                        st.rerun()

        # --- Change Password ---
        with st.expander("🔒 Change Password"):
            with st.form("change_password"):
                from auth.auth_utils import hash_password, verify_password
                current_pw = st.text_input("Current Password", type="password", key="cp_current")
                new_pw = st.text_input("New Password", type="password", key="cp_new",
                                       placeholder="Min 8 chars, 1 uppercase, 1 number")
                confirm_pw = st.text_input("Confirm New Password", type="password", key="cp_confirm")
                pw_submitted = st.form_submit_button("Update Password", use_container_width=True)
                if pw_submitted:
                    if not current_pw or not new_pw or not confirm_pw:
                        st.error("Please fill in all fields.")
                    elif new_pw != confirm_pw:
                        st.error("New passwords do not match.")
                    else:
                        valid, msg = validate_password(new_pw)
                        if not valid:
                            st.error(msg)
                        else:
                            db_user_pw = db.query(User).filter(User.id == user["id"]).first()
                            if db_user_pw and verify_password(current_pw, db_user_pw.hashed_password):
                                db_user_pw.hashed_password = hash_password(new_pw)
                                db.commit()
                                st.success("✅ Password updated successfully!")
                            else:
                                st.error("❌ Current password is incorrect.")

        st.markdown("---")

        # --- Saved Items ---
        st.markdown("### 📝 Saved Resumes")
        resumes = db.query(Resume).filter(Resume.user_id == user["id"]).order_by(Resume.created_at.desc()).all()
        if resumes:
            for r in resumes:
                with st.expander(f"Resume — {r.created_at.strftime('%Y-%m-%d %H:%M')}"):
                    st.markdown(r.resume_content)
        else:
            st.info("No resumes saved yet.")

        st.markdown("### ✉️ Saved Cover Letters")
        letters = db.query(CoverLetter).filter(CoverLetter.user_id == user["id"]).order_by(CoverLetter.created_at.desc()).all()
        if letters:
            for cl in letters:
                with st.expander(f"{cl.company} — {cl.role} ({cl.created_at.strftime('%Y-%m-%d %H:%M')})"):
                    st.markdown(cl.content)
        else:
            st.info("No cover letters saved yet.")

        st.markdown("### 📊 ATS Score History")
        scores = db.query(ATSScore).filter(ATSScore.user_id == user["id"]).order_by(ATSScore.created_at.desc()).all()
        if scores:
            for s in scores:
                with st.expander(f"Score: {s.ats_score}% — {s.created_at.strftime('%Y-%m-%d %H:%M')}"):
                    st.markdown(f"**Score:** {s.ats_score}%")
                    st.progress(min(s.ats_score / 100, 1.0))
                    if s.missing_keywords:
                        st.markdown(f"**Missing Keywords:** {s.missing_keywords}")
        else:
            st.info("No ATS analyses saved yet.")
    finally:
        db.close()


# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  MAIN ROUTER                                                          ║
# ╚══════════════════════════════════════════════════════════════════════════╝

def main():
    page = st.session_state.get("page", "landing")

    if page == "landing":
        render_landing()
    elif page == "auth":
        render_auth()
    elif page == "dashboard":
        if is_authenticated():
            render_dashboard()
        else:
            st.session_state["page"] = "auth"
            st.rerun()
    else:
        render_landing()


if __name__ == "__main__":
    main()
