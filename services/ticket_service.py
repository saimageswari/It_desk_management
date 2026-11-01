"""Transactional ticket workflows with authorization and audit history."""
from datetime import datetime, timezone
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload
from database.models import Category, Notification, Ticket, TicketHistory, User
from services.notification_service import notify
from services.permission_service import require_role, require_ticket_access
from utils.constants import PRIORITIES, Role, TRANSITIONS
from utils.validators import required_text


def _history(session: Session, ticket: Ticket, actor: User, event: str, old: str | None, new: str | None) -> None:
    session.add(TicketHistory(ticket_id=ticket.ticket_id, changed_by=actor.user_id, event_type=event, old_value=old, new_value=new))


def create_ticket(session: Session, actor: User, title: str, description: str, category_id: int, priority: str = "Medium") -> Ticket:
    require_role(actor, Role.EMPLOYEE.value, Role.ADMIN.value)
    clean_title = required_text(title, "Title", 180)
    clean_description = required_text(description, "Description", 10000)
    if priority not in PRIORITIES:
        raise ValueError("Choose a valid priority.")
    category = session.get(Category, category_id)
    if not category or not category.is_active:
        raise ValueError("Choose an active category.")
    ticket = Ticket(ticket_number="PENDING", created_by=actor.user_id, category_id=category_id, title=clean_title,
                    description=clean_description, priority=priority, status="Open")
    session.add(ticket)
    session.flush()
    ticket.ticket_number = f"HD-{datetime.now(timezone.utc).year}-{ticket.ticket_id:05d}"
    _history(session, ticket, actor, "Created", None, ticket.status)
    session.commit()
    session.refresh(ticket)
    return ticket


def get_ticket(session: Session, actor: User, ticket_id: int) -> Ticket:
    ticket = session.scalar(select(Ticket).options(joinedload(Ticket.category), joinedload(Ticket.creator), joinedload(Ticket.assignee)).where(Ticket.ticket_id == ticket_id))
    if not ticket:
        raise ValueError("Ticket not found.")
    require_ticket_access(actor, ticket)
    return ticket


def _apply_filters(query, search: str | None, status: str | None, priority: str | None):
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(or_(Ticket.ticket_number.ilike(pattern), Ticket.title.ilike(pattern)))
    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    return query


def list_tickets(session: Session, actor: User, *, limit: int = 500, offset: int = 0,
                 search: str | None = None, status: str | None = None, priority: str | None = None) -> list[Ticket]:
    from services.permission_service import require_active
    require_active(actor)
    query = select(Ticket).options(joinedload(Ticket.category), joinedload(Ticket.creator), joinedload(Ticket.assignee)).order_by(Ticket.created_at.desc())
    if actor.role == Role.EMPLOYEE.value:
        query = query.where(Ticket.created_by == actor.user_id)
    elif actor.role == Role.AGENT.value:
        query = query.where(Ticket.assigned_to == actor.user_id)
    elif actor.role != Role.ADMIN.value:
        raise PermissionError("You do not have permission to view tickets.")
    query = _apply_filters(query, search, status, priority)
    return list(session.scalars(query.limit(max(1, min(limit, 500))).offset(max(0, offset))).unique())


def count_tickets(session: Session, actor: User, *, search: str | None = None,
                  status: str | None = None, priority: str | None = None) -> int:
    from services.permission_service import require_active
    require_active(actor)
    query = select(func.count()).select_from(Ticket)
    if actor.role == Role.EMPLOYEE.value:
        query = query.where(Ticket.created_by == actor.user_id)
    elif actor.role == Role.AGENT.value:
        query = query.where(Ticket.assigned_to == actor.user_id)
    elif actor.role != Role.ADMIN.value:
        raise PermissionError("You do not have permission to view tickets.")
    return session.scalar(_apply_filters(query, search, status, priority)) or 0


def assign_ticket(session: Session, actor: User, ticket_id: int, agent_id: int | None) -> Ticket:
    require_role(actor, Role.ADMIN.value)
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        raise ValueError("Ticket not found.")
    agent = session.get(User, agent_id) if agent_id is not None else None
    if agent_id is not None and (not agent or not agent.is_active or agent.role != Role.AGENT.value):
        raise ValueError("Choose an active support agent.")
    old = str(ticket.assigned_to) if ticket.assigned_to else None
    if ticket.assigned_to == agent_id:
        return ticket
    ticket.assigned_to = agent_id
    _history(session, ticket, actor, "Assignment changed", old, str(agent_id) if agent_id else None)
    if agent:
        notify(session, agent.user_id, f"Ticket {ticket.ticket_number} has been assigned to you.", ticket.ticket_id)
    session.commit()
    return ticket


def update_status(session: Session, actor: User, ticket_id: int, status: str) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if not ticket:
        raise ValueError("Ticket not found.")
    require_ticket_access(actor, ticket)
    if actor.role == Role.EMPLOYEE.value:
        if not (ticket.status == "Resolved" and status == "In Progress"):
            raise PermissionError("Employees may only reopen resolved tickets.")
    elif actor.role not in (Role.AGENT.value, Role.ADMIN.value):
        raise PermissionError("You do not have permission to change ticket status.")
    if actor.role == Role.AGENT.value and ticket.assigned_to != actor.user_id:
        raise PermissionError("Only the assigned agent can update this ticket.")
    if status not in TRANSITIONS.get(ticket.status, set()):
        raise ValueError(f"Cannot move a ticket from {ticket.status} to {status}.")
    old = ticket.status
    ticket.status = status
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if status == "Resolved":
        ticket.resolved_at = now
    elif old == "Resolved" and status == "In Progress":
        ticket.resolved_at = None
    ticket.updated_at = now
    _history(session, ticket, actor, "Status changed", old, status)
    recipient_id = ticket.created_by if actor.user_id != ticket.created_by else ticket.assigned_to
    if recipient_id:
        notify(session, recipient_id, f"Ticket {ticket.ticket_number} changed to {status}.", ticket.ticket_id)
    session.commit()
    return ticket


def unread_notifications(session: Session, actor: User) -> list[Notification]:
    from services.permission_service import require_active
    require_active(actor)
    return list(session.scalars(select(Notification).where(Notification.user_id == actor.user_id).order_by(Notification.created_at.desc())))
