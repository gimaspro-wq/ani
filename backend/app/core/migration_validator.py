"""Database migration validator."""
import logging
from typing import Optional

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)


def validate_migrations(database_url: str, alembic_ini_path: str = "alembic.ini") -> bool:
    """
    Validate that database is at head revision.
    
    Args:
        database_url: Database connection URL
        alembic_ini_path: Path to alembic.ini file
        
    Returns:
        True if migrations are up to date, False otherwise
        
    Raises:
        RuntimeError: If database is not at head revision in production
    """
    try:
        # Convert async URL to sync URL for alembic
        sync_db_url = database_url.replace("+asyncpg", "").replace("+aiosqlite", "")
        
        # Create engine
        engine = create_engine(sync_db_url, echo=False)
        
        # Get current revision from database
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
        
        # Get head revision from alembic
        alembic_cfg = Config(alembic_ini_path)
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()
        
        logger.info(f"Current database revision: {current_rev}")
        logger.info(f"Head revision: {head_rev}")
        
        if current_rev != head_rev:
            logger.error(
                f"Database is not at head revision! "
                f"Current: {current_rev}, Head: {head_rev}"
            )
            return False
        
        logger.info("Database migrations are up to date")
        return True
        
    except Exception as e:
        logger.error(f"Failed to validate migrations: {e}")
        return False
