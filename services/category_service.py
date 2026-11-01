"""Administrator-only category management."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from database.models import Category, User
from services.permission_service import require_role
from utils.constants import Role
from utils.validators import required_text


def list_categories(session: Session, actor: User) -> list[Category]:
    require_role(actor, Role.ADMIN.value)
    return list(session.scalars(select(Category).order_by(Category.category_name)))


def save_category(session: Session, actor: User, name: str, description: str = "") -> Category:
    require_role(actor, Role.ADMIN.value)
    clean_name = required_text(name, "Category name", 80)
    if session.scalar(select(Category).where(func.lower(Category.category_name) == clean_name.lower())):
        raise ValueError("That category already exists.")
    category = Category(category_name=clean_name, description=description.strip()[:255])
    session.add(category)
    session.commit()
    return category


def set_category_active(session: Session, actor: User, category_id: int, active: bool) -> Category:
    require_role(actor, Role.ADMIN.value)
    category = session.get(Category, category_id)
    if not category:
        raise ValueError("Category not found.")
    category.is_active = active
    session.commit()
    return category
