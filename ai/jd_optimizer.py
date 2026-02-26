"""
Job-description–based resume optimizer.
Extracts JD keywords, identifies gaps, and rewrites the resume to improve ATS alignment.
"""

from ai.ai_client import call_ai
from utils.helpers import format_markdown, sanitize_input

SYSTEM_PROMPT = """You are a senior career coach specialising in ATS optimization.
Given an existing resume and a target job description, your task is to:

1. Extract the critical keywords and phrases from the job description.
2. Identify which keywords are MISSING from the resume.
3. Rewrite the resume to naturally incorporate the missing keywords while maintaining authenticity.
4. Prioritize the most relevant skills and experiences for the target role.
5. Improve keyword density without keyword-stuffing.

OUTPUT FORMAT (use these exact headings):
## Optimized Resume
<the rewritten resume in clean markdown>

## Changes Made
- bullet list of specific changes

## Extracted Keywords
- comma-separated list of keywords from the JD

## Missing Keywords (Before Optimization)
- comma-separated list of keywords that were absent from the original resume

Do NOT add explanations outside the sections above."""


def optimize_resume(resume_text: str, jd_text: str) -> dict:
    """
    Optimize a resume against a job description.

    Returns dict with keys:
        optimized_resume, changes, extracted_keywords, missing_keywords
    """
    user_prompt = (
        "### Existing Resume\n"
        f"{sanitize_input(resume_text)}\n\n"
        "### Target Job Description\n"
        f"{sanitize_input(jd_text)}"
    )
    raw = call_ai(SYSTEM_PROMPT, user_prompt)
    return _parse_response(raw)


def _parse_response(text: str) -> dict:
    """Parse the structured AI response into a dict."""
    result = {
        "optimized_resume": "",
        "changes": "",
        "extracted_keywords": "",
        "missing_keywords": "",
    }

    sections = {
        "## Optimized Resume": "optimized_resume",
        "## Changes Made": "changes",
        "## Extracted Keywords": "extracted_keywords",
        "## Missing Keywords": "missing_keywords",
    }

    current_key = None
    lines: list[str] = []

    for line in text.split("\n"):
        matched = False
        for header, key in sections.items():
            if line.strip().startswith(header) or line.strip().startswith(header.replace("(Before Optimization)", "").strip()):
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
