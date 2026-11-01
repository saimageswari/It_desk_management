import pytest
from database.models import Category, TicketHistory
from services.auth_service import register_user
from services.ticket_service import assign_ticket, create_ticket, update_status
from utils.constants import Role


def fixture_users(session):
    employee = register_user(session, "Employee One", "employee@example.com", "Employee12345")
    agent = register_user(session, "Agent One", "agent@example.com", "AgentPass12345")
    agent.role = Role.AGENT.value
    session.commit()
    admin = register_user(session, "Admin One", "admin@example.com", "AdminPass12345")
    admin.role = Role.ADMIN.value
    session.commit()
    category = Category(category_name="Hardware", description="Devices")
    session.add(category)
    session.commit()
    return employee, agent, admin, category


def test_create_assign_status_and_history(session):
    employee, agent, admin, category = fixture_users(session)
    ticket = create_ticket(session, employee, "Laptop won't start", "Power light is off.", category.category_id, "High")
    assert ticket.ticket_number.startswith("HD-")
    assign_ticket(session, admin, ticket.ticket_id, agent.user_id)
    update_status(session, agent, ticket.ticket_id, "In Progress")
    assert ticket.status == "In Progress"
    assert session.query(TicketHistory).filter_by(ticket_id=ticket.ticket_id).count() == 3


def test_invalid_transition_rejected(session):
    employee, agent, admin, category = fixture_users(session)
    ticket = create_ticket(session, employee, "VPN", "Cannot connect.", category.category_id)
    with pytest.raises(PermissionError, match="Employees may only reopen"):
        update_status(session, employee, ticket.ticket_id, "Resolved")


def test_agent_must_be_assigned_to_update(session):
    employee, agent, admin, category = fixture_users(session)
    another = register_user(session, "Agent Two", "agent2@example.com", "AgentPass12345")
    another.role = Role.AGENT.value
    session.commit()
    ticket = create_ticket(session, employee, "VPN", "Cannot connect.", category.category_id)
    assign_ticket(session, admin, ticket.ticket_id, agent.user_id)
    with pytest.raises(PermissionError):
        update_status(session, another, ticket.ticket_id, "In Progress")
