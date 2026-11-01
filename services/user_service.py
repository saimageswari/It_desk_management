"""Administrator-only account management."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from database.models import User
from services.permission_service import require_role
from utils.constants import Role


def list_users(session: Session, actor: User) -> list[User]:
    require_role(actor, Role.ADMIN.value)
    return list(session.scalars(select(User).order_by(User.created_at.desc())))


def create_agent(session: Session, actor: User, full_name: str, email: str, password: str) -> User:
    require_role(actor, Role.ADMIN.value)
    from utils.security import hash_password
    from utils.validators import normalized_email, required_text, validate_password
    name = required_text(full_name, "Full name", 120)
    address = normalized_email(email)
    validate_password(password)
    if session.scalar(select(User).where(User.email == address)):
        raise ValueError("An account with this email already exists.")
    user = User(full_name=name, email=address, password_hash=hash_password(password), role=Role.AGENT.value)
    session.add(user)
    session.commit()
    return user


def set_user_active(session: Session, actor: User, user_id: int, active: bool) -> User:
    require_role(actor, Role.ADMIN.value)
    target = session.get(User, user_id)
    if not target:
        raise ValueError("User not found.")
    if target.user_id == actor.user_id and not active:
        raise ValueError("You cannot deactivate your own account.")
    if target.role == Role.ADMIN.value:
        from sqlalchemy import func
        count = session.scalar(select(func.count()).select_from(User).where(User.role == Role.ADMIN.value, User.is_active.is_(True)))
        if not active and count <= 1:
            raise ValueError("The last active administrator cannot be deactivated.")
    target.is_active = active
    session.commit()
    return target
