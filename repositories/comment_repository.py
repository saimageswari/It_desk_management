"""Read-only comment query helpers."""
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from database.models import Comment


def for_ticket(session: Session, ticket_id: int) -> list[Comment]:
    return list(session.scalars(select(Comment).options(joinedload(Comment.user)).where(Comment.ticket_id == ticket_id).order_by(Comment.created_at)))
