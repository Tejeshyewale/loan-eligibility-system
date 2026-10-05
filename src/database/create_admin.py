"""Create or promote the bootstrap admin user.

Reads ADMIN_EMAIL / ADMIN_PASSWORD from .env (see .env.example).
Run:  python -m src.database.create_admin
"""
import sys

from src.api.auth import hash_password
from src.core.settings import ADMIN_EMAIL, ADMIN_PASSWORD
from src.database.db import SessionLocal
from src.database.models import User
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> int:
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        logger.error("ADMIN_EMAIL and ADMIN_PASSWORD must be set in .env")
        return 1
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == ADMIN_EMAIL).first()
        if user:
            user.password = hash_password(ADMIN_PASSWORD)
            user.role = "admin"
            logger.info("Promoted existing user '%s' to admin.", ADMIN_EMAIL)
        else:
            db.add(User(
                username=ADMIN_EMAIL,
                password=hash_password(ADMIN_PASSWORD),
                role="admin",
            ))
            logger.info("Created admin user '%s'.", ADMIN_EMAIL)
        db.commit()
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
