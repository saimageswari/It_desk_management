"""Authorization scoped reporting queries."""
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from database.models import Ticket, User
from services.permission_service import require_active
from utils.constants import Role


def report_tickets(session: Session, actor: User) -> list[Ticket]:
    require_active(actor)
    query = select(Ticket).options(joinedload(Ticket.category), joinedload(Ticket.assignee)).order_by(Ticket.created_at.desc())
    if actor.role == Role.AGENT.value:
        query = query.where(Ticket.assigned_to == actor.user_id)
    elif actor.role != Role.ADMIN.value:
        raise PermissionError("You do not have permission to view support reports.")
    return list(session.scalars(query).unique())
