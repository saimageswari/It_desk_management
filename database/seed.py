"""Seed categories and create the first administrator from environment variables."""
import logging
from sqlalchemy import select
from config import BOOTSTRAP_ADMIN_EMAIL, BOOTSTRAP_ADMIN_NAME, BOOTSTRAP_ADMIN_PASSWORD
from database.connection import SessionLocal, init_db
from database.models import Category
from services.auth_service import bootstrap_admin
from utils.constants import DEFAULT_CATEGORIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed() -> None:
    init_db()
    with SessionLocal() as session:
        for name, description in DEFAULT_CATEGORIES:
            if not session.scalar(select(Category).where(Category.category_name == name)):
                session.add(Category(category_name=name, description=description))
        session.commit()
        if BOOTSTRAP_ADMIN_EMAIL and BOOTSTRAP_ADMIN_PASSWORD:
            try:
                bootstrap_admin(session, BOOTSTRAP_ADMIN_NAME or "Helpdesk Administrator", BOOTSTRAP_ADMIN_EMAIL, BOOTSTRAP_ADMIN_PASSWORD)
                logger.info("Initial administrator created.")
            except ValueError as exc:
                if str(exc) != "An administrator already exists.":
                    raise
                logger.info("Administrator bootstrap skipped: %s", exc)


if __name__ == "__main__":
    seed()
