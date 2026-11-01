"""Notification creation and read-state operations."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from database.models import Notification


def notify(session: Session, user_id: int, message: str, ticket_id: int | None = None) -> None:
    session.add(Notification(user_id=user_id, ticket_id=ticket_id, message=message))


def mark_read(session: Session, notification_id: int, user_id: int) -> None:
    item = session.scalar(select(Notification).where(Notification.notification_id == notification_id, Notification.user_id == user_id))
    if item:
        item.is_read = True
        session.commit()
