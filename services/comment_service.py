"""Comments and activity timeline workflows."""
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from database.models import Comment, Ticket, TicketHistory, User
from services.permission_service import require_ticket_access
from services.ticket_service import _history
from services.notification_service import notify
from utils.validators import required_text


def add_comment(session: Session, actor: User, ticket_id: int, text: str) -> Comment:
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        raise ValueError("Ticket not found.")
    require_ticket_access(actor, ticket)
    if ticket.status == "Closed":
        raise ValueError("Closed tickets cannot receive comments.")
    body = required_text(text, "Comment", 5000)
    comment = Comment(ticket_id=ticket_id, user_id=actor.user_id, comment_text=body)
    session.add(comment)
    _history(session, ticket, actor, "Comment added", None, body[:500])
    recipient = ticket.created_by if actor.user_id != ticket.created_by else ticket.assigned_to
    if recipient:
        notify(session, recipient, f"New comment on ticket {ticket.ticket_number}.", ticket.ticket_id)
    session.commit()
    session.refresh(comment)
    return comment


def ticket_activity(session: Session, actor: User, ticket_id: int):
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        raise ValueError("Ticket not found.")
    require_ticket_access(actor, ticket)
    comments = list(session.scalars(select(Comment).options(joinedload(Comment.user)).where(Comment.ticket_id == ticket_id).order_by(Comment.created_at)))
    history = list(session.scalars(select(TicketHistory).options(joinedload(TicketHistory.actor)).where(TicketHistory.ticket_id == ticket_id).order_by(TicketHistory.changed_at)))
    return comments, history
