"""
AI-powered resume generator.
Produces ATS-friendly, structured markdown resumes from user details.
"""

from ai.ai_client import call_ai
from utils.helpers import format_markdown, sanitize_input

SYSTEM_PROMPT = """You are an expert resume writer with 15+ years of experience in HR and talent acquisition.
You create ATS-optimized, professional resumes that pass automated screening systems.

RULES:
- Use strong action verbs (Led, Engineered, Optimized, Delivered, Spearheaded)
- Quantify achievements with numbers, percentages, and metrics wherever possible
- Use clean markdown formatting with clear section headers
- Structure: Contact Info → Professional Summary → Skills → Experience → Education → Projects → Achievements
- Use bullet points for experience and projects
- Keep it concise — max 2 pages worth of content
- Tailor the summary and skills to the target role
- Do NOT include images, tables, or complex formatting that ATS cannot parse
- Output ONLY the resume content in markdown. No explanations before or after."""


def generate_resume(details: dict) -> str:
    """
    Generate a professional resume from user-provided details.

    Expected keys in `details`:
        name, email, phone, location, linkedin,
        summary, skills, education, experience,
        projects, achievements, target_role
    """
    user_prompt = _build_prompt(details)
    raw = call_ai(SYSTEM_PROMPT, user_prompt)
    return format_markdown(raw)


def _build_prompt(d: dict) -> str:
    """Assemble a structured user prompt from the details dict."""
    sections = []

    sections.append(f"**Target Role:** {sanitize_input(d.get('target_role', 'Software Engineer'))}")
    sections.append(f"**Full Name:** {sanitize_input(d.get('name', ''))}")
    sections.append(f"**Email:** {sanitize_input(d.get('email', ''))}")
    sections.append(f"**Phone:** {sanitize_input(d.get('phone', ''))}")
    sections.append(f"**Location:** {sanitize_input(d.get('location', ''))}")
    sections.append(f"**LinkedIn:** {sanitize_input(d.get('linkedin', ''))}")

    if d.get("summary"):
        sections.append(f"\n**Professional Summary / Objective:**\n{sanitize_input(d['summary'])}")

    if d.get("skills"):
        sections.append(f"\n**Skills:**\n{sanitize_input(d['skills'])}")

    if d.get("education"):
        sections.append(f"\n**Education:**\n{sanitize_input(d['education'])}")

    if d.get("experience"):
        sections.append(f"\n**Work Experience:**\n{sanitize_input(d['experience'])}")

    if d.get("projects"):
        sections.append(f"\n**Projects:**\n{sanitize_input(d['projects'])}")

    if d.get("achievements"):
        sections.append(f"\n**Achievements / Certifications:**\n{sanitize_input(d['achievements'])}")

    return (
        "Generate a professional, ATS-optimized resume using the following details.\n\n"
        + "\n".join(sections)
    )
