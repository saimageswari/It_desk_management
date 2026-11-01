"""Backend authorization guards. Call these in every service operation."""
from database.models import Ticket, User
from utils.constants import Role


def require_active(user: User) -> None:
    if not user.is_active:
        raise PermissionError("This account is inactive.")


def require_role(user: User, *roles: str) -> None:
    require_active(user)
    if user.role not in roles:
        raise PermissionError("You do not have permission to perform this action.")


def can_view_ticket(user: User, ticket: Ticket) -> bool:
    if not user.is_active:
        return False
    if user.role == Role.ADMIN.value:
        return True
    if user.role == Role.EMPLOYEE.value:
        return ticket.created_by == user.user_id
    if user.role == Role.AGENT.value:
        return ticket.assigned_to == user.user_id
    return False


def require_ticket_access(user: User, ticket: Ticket) -> None:
    if not can_view_ticket(user, ticket):
        raise PermissionError("You do not have access to this ticket.")
