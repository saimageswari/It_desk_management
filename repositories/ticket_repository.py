"""Read-only ticket query helpers."""
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from database.models import Ticket


def get_ticket(session: Session, ticket_id: int) -> Ticket | None:
    return session.scalar(select(Ticket).options(joinedload(Ticket.category), joinedload(Ticket.creator), joinedload(Ticket.assignee)).where(Ticket.ticket_id == ticket_id))
