#!/usr/bin/env python3
"""CLI entrypoint for the parser service."""
import asyncio
import logging
import sys
from argparse import ArgumentParser

from parser.orchestrator import ParserOrchestrator
from parser.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for the parser CLI."""
    parser = ArgumentParser(
        description="Anime parser service for importing from Kodik and Shikimori"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to process (default: all)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("=" * 80)
    logger.info("Anime Parser Service")
    logger.info("=" * 80)
    
    # Validate configuration
    try:
        # Check required settings (not defaults)
        if settings.INTERNAL_TOKEN == "test_token":
            logger.warning("Using default test token. Set INTERNAL_TOKEN in .env for production.")
        if settings.KODIK_API_TOKEN == "test_token":
            logger.warning("Using default test token. Set KODIK_API_TOKEN in .env for production.")
        
        logger.info(f"Backend URL: {settings.BACKEND_BASE_URL}")
        logger.info(f"Source name: {settings.SOURCE_NAME}")
        logger.info(f"Concurrency: {settings.CONCURRENCY}")
        logger.info(f"Rate limit: {settings.RATE_LIMIT_RPS} RPS")
        logger.info(f"Max retries: {settings.MAX_RETRIES}")
        logger.info(f"State path: {settings.STATE_PATH}")
        
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Run the orchestrator
    orchestrator = ParserOrchestrator()
    try:
        await orchestrator.run(max_pages=args.max_pages)
        logger.info("Parser completed successfully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Parser failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
