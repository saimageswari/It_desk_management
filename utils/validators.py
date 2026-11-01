"""Input validation for user supplied values."""
import re
from email_validator import EmailNotValidError, validate_email


def normalized_email(value: str) -> str:
    try:
        return validate_email(value.strip(), check_deliverability=False).normalized.lower()
    except EmailNotValidError as exc:
        raise ValueError("Enter a valid email address.") from exc


def validate_password(password: str) -> None:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must be no more than 72 UTF-8 bytes.")
    if len(password) < 10 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ValueError("Password must be at least 10 characters and include a letter and a number.")


def required_text(value: str, field: str, max_length: int) -> str:
    clean = value.strip()
    if not clean:
        raise ValueError(f"{field} is required.")
    if len(clean) > max_length:
        raise ValueError(f"{field} must be {max_length} characters or fewer.")
    return clean
