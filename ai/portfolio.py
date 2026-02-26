"""
AI-powered portfolio content generator.
Produces About Me, professional bio, project descriptions, LinkedIn summary, and tagline.
"""

from ai.ai_client import call_ai
from utils.helpers import format_markdown, sanitize_input

SYSTEM_PROMPT = """You are a personal branding specialist and copywriter.
Generate portfolio content that is engaging, professional, and optimised for online presence.

OUTPUT FORMAT (use these exact headings):
## About Me
<2-3 paragraph about-me section>

## Professional Bio
<concise third-person bio, 3-4 sentences>

## Project Descriptions
<2-3 compelling project descriptions with impact>

## LinkedIn Summary
<optimised LinkedIn summary section, 150-200 words>

## Personal Tagline
<short memorable tagline, max 10 words>

Write in a confident, authentic voice. Output ONLY the formatted content."""


def generate_portfolio(details: dict) -> dict:
    """
    Generate portfolio content from user details.

    Expected keys: name, title, skills, experience, projects, interests
    Returns dict with keys: about_me, bio, projects, linkedin_summary, tagline
    """
    user_prompt = (
        f"**Name:** {sanitize_input(details.get('name', ''))}\n"
        f"**Professional Title:** {sanitize_input(details.get('title', ''))}\n"
        f"**Skills:** {sanitize_input(details.get('skills', ''))}\n"
        f"**Experience:** {sanitize_input(details.get('experience', ''))}\n"
        f"**Projects:** {sanitize_input(details.get('projects', ''))}\n"
        f"**Interests:** {sanitize_input(details.get('interests', ''))}\n\n"
        "Generate complete portfolio content for my professional website."
    )
    raw = call_ai(SYSTEM_PROMPT, user_prompt)
    return _parse_response(raw)


def _parse_response(text: str) -> dict:
    """Parse the structured AI response into separate sections."""
    result = {
        "about_me": "",
        "bio": "",
        "projects": "",
        "linkedin_summary": "",
        "tagline": "",
    }

    sections = {
        "## About Me": "about_me",
        "## Professional Bio": "bio",
        "## Project Descriptions": "projects",
        "## LinkedIn Summary": "linkedin_summary",
        "## Personal Tagline": "tagline",
    }

    current_key = None
    lines: list[str] = []

    for line in text.split("\n"):
        matched = False
        for header, key in sections.items():
            if line.strip().startswith(header):
                if current_key:
                    result[current_key] = format_markdown("\n".join(lines))
                current_key = key
                lines = []
                matched = True
                break
        if not matched and current_key is not None:
            lines.append(line)

    if current_key:
        result[current_key] = format_markdown("\n".join(lines))

    return result
