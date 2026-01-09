import logging
from alembic import command
from alembic.config import Config

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """
    Run Alembic migrations programmatically.
    Used for dev/test environments where shell access is unavailable.
    """
    try:
        alembic_cfg = Config("alembic.ini")
        logger.info("Running database migrations (alembic upgrade head)")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Failed to run migrations automatically: {e}")
        raise
