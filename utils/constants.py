"""Domain constants shared by the UI and services."""
from enum import Enum


class Role(str, Enum):
    EMPLOYEE = "Employee"
    AGENT = "Agent"
    ADMIN = "Administrator"


class TicketStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    WAITING = "Waiting for Employee"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


PRIORITIES = ("Critical", "High", "Medium", "Low")
DEFAULT_CATEGORIES = (
    ("Hardware", "Laptops, desktops, printers, and peripherals"),
    ("Software", "Applications, installation, and licensing"),
    ("Network", "Connectivity, VPN, and Wi-Fi"),
    ("Account Access", "Accounts, passwords, and permissions"),
    ("Email", "Mailbox and email client issues"),
    ("Other", "Other IT support requests"),
)
TRANSITIONS = {
    "Open": {"In Progress", "Closed"},
    "In Progress": {"Waiting for Employee", "Resolved", "Open", "Closed"},
    "Waiting for Employee": {"In Progress", "Resolved", "Closed"},
    "Resolved": {"In Progress", "Closed"},
    "Closed": {"Open"},
}
