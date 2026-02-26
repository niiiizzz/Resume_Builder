"""
Utility helpers — input sanitization and markdown formatting.
"""

import re


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Strip whitespace and enforce a maximum character length.
    Returns the cleaned string.
    """
    if not text:
        return ""
    cleaned = text.strip()
    return cleaned[:max_length]


def format_markdown(text: str) -> str:
    """
    Clean up AI-generated markdown so it renders well in Streamlit.
    - Removes leading/trailing whitespace
    - Normalises multiple blank lines to a single one
    - Strips stray code-fence wrappers if the content is not code
    """
    if not text:
        return ""
    # Remove wrapping code fences that some models add
    text = re.sub(r"^```(?:markdown)?\s*\n?", "", text, count=1)
    text = re.sub(r"\n?```\s*$", "", text, count=1)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def validate_email(email: str) -> bool:
    """Basic email format validation."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.
    Returns (is_valid, message).
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    return True, "Password is strong."
