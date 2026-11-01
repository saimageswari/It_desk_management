"""Registration, authentication, and privileged bootstrap operations."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from database.models import User
from utils.constants import Role
from utils.security import hash_password, verify_password
from utils.validators import normalized_email, required_text, validate_password

_DUMMY_PASSWORD_HASH = hash_password("constant-dummy-credential-never-used-123")


def register_user(session: Session, full_name: str, email: str, password: str) -> User:
    name = required_text(full_name, "Full name", 120)
    address = normalized_email(email)
    validate_password(password)
    if session.scalar(select(User).where(User.email == address)):
        raise ValueError("An account with this email already exists.")
    user = User(full_name=name, email=address, password_hash=hash_password(password), role=Role.EMPLOYEE.value)
    session.add(user)
    try:
        session.commit()
    except Exception as exc:
        session.rollback()
        from sqlalchemy.exc import IntegrityError
        if isinstance(exc, IntegrityError):
            raise ValueError("An account with this email already exists.") from exc
        raise
    session.refresh(user)
    return user


def authenticate(session: Session, email: str, password: str) -> User:
    try:
        address = normalized_email(email)
    except ValueError:
        address = email.strip().lower()
    user = session.scalar(select(User).where(User.email == address))
    password_hash = user.password_hash if user else _DUMMY_PASSWORD_HASH
    password_matches = verify_password(password, password_hash)
    if not user or not password_matches or not user.is_active:
        raise ValueError("Email or password is incorrect, or the account is inactive.")
    return user


def bootstrap_admin(session: Session, name: str, email: str, password: str) -> User:
    """Create the first administrator; refuses to run if an admin already exists."""
    if session.scalar(select(User).where(User.role == Role.ADMIN.value)):
        raise ValueError("An administrator already exists.")
    clean_name = required_text(name, "Full name", 120)
    address = normalized_email(email)
    validate_password(password)
    if session.scalar(select(User).where(User.email == address)):
        raise ValueError("An account with this email already exists.")
    user = User(full_name=clean_name, email=address, password_hash=hash_password(password), role=Role.ADMIN.value)
    session.add(user)
    session.commit()
    return user
