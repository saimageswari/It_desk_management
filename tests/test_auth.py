import pytest
from services.auth_service import authenticate, register_user
from utils.security import verify_password


def test_registration_hashes_password_and_authenticates(session):
    user = register_user(session, "Asha Rao", "asha@example.com", "Support12345")
    assert user.password_hash != "Support12345"
    assert verify_password("Support12345", user.password_hash)
    assert authenticate(session, "ASHA@example.com", "Support12345").user_id == user.user_id


def test_duplicate_registration_rejected(session):
    register_user(session, "Asha Rao", "asha@example.com", "Support12345")
    with pytest.raises(ValueError, match="already exists"):
        register_user(session, "Other", "asha@example.com", "Support12345")


def test_inactive_user_cannot_authenticate(session):
    user = register_user(session, "Asha Rao", "asha@example.com", "Support12345")
    user.is_active = False
    session.commit()
    with pytest.raises(ValueError):
        authenticate(session, user.email, "Support12345")
