"""Read-only category query helpers."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from database.models import Category


def active_categories(session: Session) -> list[Category]:
    return list(session.scalars(select(Category).where(Category.is_active.is_(True)).order_by(Category.category_name)))
