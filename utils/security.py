"""Password hashing helpers."""
import bcrypt


def hash_password(password: str) -> str:
    """Return a bcrypt hash for a validated password."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Check a password against a bcrypt hash without raising on malformed data."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False
