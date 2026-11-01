import pytest
from database.models import Category
from services.auth_service import register_user
from services.comment_service import add_comment, ticket_activity
from services.ticket_service import create_ticket, get_ticket
from services.user_service import list_users
from utils.constants import Role


def test_employee_cannot_view_another_employees_ticket(session):
    owner = register_user(session, "Owner User", "owner@example.com", "OwnerPass12345")
    stranger = register_user(session, "Stranger User", "stranger@example.com", "StrangerPass12345")
    category = Category(category_name="Software", description="Apps")
    session.add(category)
    session.commit()
    ticket = create_ticket(session, owner, "App crash", "App crashes at launch.", category.category_id)
    with pytest.raises(PermissionError):
        get_ticket(session, stranger, ticket.ticket_id)
    with pytest.raises(PermissionError):
        add_comment(session, stranger, ticket.ticket_id, "Can I see this?")


def test_employee_cannot_assign_ticket(session):
    from services.ticket_service import assign_ticket
    employee = register_user(session, "Employee", "e@example.com", "Employee12345")
    category = Category(category_name="Network", description="Connectivity")
    session.add(category)
    session.commit()
    ticket = create_ticket(session, employee, "Wi-Fi", "No connection", category.category_id)
    with pytest.raises(PermissionError):
        assign_ticket(session, employee, ticket.ticket_id, None)


def test_employee_comment_is_saved_to_activity(session):
    employee = register_user(session, "Employee", "employee2@example.com", "Employee12345")
    category = Category(category_name="Email", description="Mail")
    session.add(category)
    session.commit()
    ticket = create_ticket(session, employee, "Email access", "Mailbox is unavailable", category.category_id)
    comment = add_comment(session, employee, ticket.ticket_id, "It started this morning.")
    comments, history = ticket_activity(session, employee, ticket.ticket_id)
    assert comments[0].comment_id == comment.comment_id
    assert any(item.event_type == "Comment added" for item in history)


def test_employee_cannot_use_admin_user_management(session):
    employee = register_user(session, "Employee", "employee3@example.com", "Employee12345")
    with pytest.raises(PermissionError):
        list_users(session, employee)
