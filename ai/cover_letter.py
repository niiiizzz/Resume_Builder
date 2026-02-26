"""
AI-powered cover letter generator.
Produces personalised, role-specific cover letters.
"""

from ai.ai_client import call_ai
from utils.helpers import format_markdown, sanitize_input

SYSTEM_PROMPT = """You are an expert cover letter writer with deep knowledge of hiring practices.
Write a compelling, personalised cover letter that:

- Opens with a strong, attention-grabbing statement
- Demonstrates genuine interest in the company
- Highlights 2-3 key strengths relevant to the role
- Uses a confident, professional but conversational tone
- Ends with a clear call to action
- Is 3-4 paragraphs long
- Does NOT use clichés like "I am writing to apply…"

Output ONLY the cover letter text in clean markdown. No meta-commentary."""


def generate_cover_letter(company: str, role: str, why_interested: str, strengths: str) -> str:
    """
    Generate a personalised cover letter.
    """
    user_prompt = (
        f"**Company:** {sanitize_input(company)}\n"
        f"**Role:** {sanitize_input(role)}\n"
        f"**Why I'm interested:** {sanitize_input(why_interested)}\n"
        f"**Key strengths / experiences:** {sanitize_input(strengths)}\n\n"
        "Write a compelling cover letter for this opportunity."
    )
    raw = call_ai(SYSTEM_PROMPT, user_prompt)
    return format_markdown(raw)
