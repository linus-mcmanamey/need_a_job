#!/usr/bin/env python
"""
LinkedIn Job Poller CLI Script.

Runs the LinkedIn job poller for job discovery.

Usage:
    python scripts/run_linkedin_poller.py                    # Run continuously
    python scripts/run_linkedin_poller.py --once             # Run one cycle
    python scripts/run_linkedin_poller.py --interval 30      # Custom interval (minutes)
    python scripts/run_linkedin_poller.py --dry-run          # Dry run (no database writes)
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger

from app.config.loader import Config
from app.pollers.linkedin_poller import LinkedInPoller
from app.repositories.application_repository import ApplicationRepository
from app.repositories.database import initialize_database
from app.repositories.jobs_repository import JobsRepository


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging.

    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    logger.remove()  # Remove default handler

    log_level = "DEBUG" if verbose else "INFO"

    # Console logging
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
    )

    # File logging
    logger.add(
        "logs/linkedin_poller.log",
        rotation="1 day",
        retention="7 days",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )


def create_mock_mcp_client():
    """
    Create a mock MCP client for testing.

    In production, this would be replaced with actual MCP client.
    """
    from unittest.mock import Mock

    logger.warning("Using mock MCP client (for testing only)")

    mock_client = Mock()

    # Mock response with sample jobs
    mock_client.call_tool.return_value = {
        "jobs": [
            {
                "job_id": "mock-linkedin-123",
                "title": "Senior Data Engineer",
                "company": "Mock Tech Corp",
                "location": "Remote - Australia",
                "posted_date": "2025-01-15",
                "salary": "$1000-$1200/day",
                "job_url": "https://linkedin.com/jobs/view/mock-12345",
                "description": "Mock job description for testing...",
                "requirements": "Python, SQL, Cloud platforms",
                "responsibilities": "Design and build data pipelines",
            }
        ],
        "total_results": 1,
    }

    return mock_client


def main():
    """Main entry point for LinkedIn poller CLI."""
    parser = argparse.ArgumentParser(
        description="LinkedIn Job Poller - Discover and store job postings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                      Run continuously with default interval
  %(prog)s --once               Run one poll cycle and exit
  %(prog)s --interval 30        Run continuously with 30-minute interval
  %(prog)s --dry-run            Dry run mode (logs only, no database writes)
  %(prog)s --verbose            Enable verbose logging
        """,
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one poll cycle and exit (default: run continuously)",
    )

    parser.add_argument(
        "--interval",
        type=int,
        metavar="MINUTES",
        help="Polling interval in minutes (overrides config)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode: log what would be done without database writes",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose (DEBUG) logging"
    )

    parser.add_argument(
        "--config-path",
        type=Path,
        default=project_root / "config",
        help="Path to configuration directory (default: config/)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)

    logger.info("=" * 60)
    logger.info("LinkedIn Job Poller Starting")
    logger.info("=" * 60)

    if args.dry_run:
        logger.warning("DRY RUN MODE: No database writes will be performed")

    try:
        # Load configuration
        logger.info(f"Loading configuration from {args.config_path}")
        config_loader = Config()

        search_config = config_loader.search
        platforms_config = config_loader.platforms

        # Combine configs
        config = {"search": search_config, "linkedin": platforms_config.get("linkedin", {})}

        logger.info("Configuration loaded successfully")
        logger.debug(f"Search keywords: {search_config.get('keywords', {}).get('primary', [])}")
        logger.debug(f"Location: {search_config.get('locations', {}).get('primary', 'N/A')}")
        logger.debug(f"Job type: {search_config.get('job_type', 'N/A')}")

        # Initialize database
        if not args.dry_run:
            logger.info("Initializing database...")
            initialize_database()

            # Create repositories
            jobs_repo = JobsRepository()
            app_repo = ApplicationRepository()
        else:
            # Use mock repositories for dry run
            from unittest.mock import Mock

            jobs_repo = Mock()
            app_repo = Mock()
            logger.info("Using mock repositories (dry run mode)")

        # Create MCP client
        # TODO: Replace with actual MCP client when available
        mcp_client = create_mock_mcp_client()

        # Create poller
        logger.info("Initializing LinkedIn poller...")
        poller = LinkedInPoller(
            config=config,
            jobs_repository=jobs_repo,
            application_repository=app_repo,
            mcp_client=mcp_client,
        )

        # Run poller
        if args.once:
            logger.info("Running one poll cycle...")
            metrics = poller.run_once()

            logger.info("=" * 60)
            logger.info("Poll Cycle Complete")
            logger.info("=" * 60)
            logger.info(f"Jobs found: {metrics['jobs_found']}")
            logger.info(f"Jobs inserted: {metrics['jobs_inserted']}")
            logger.info(f"Duplicates skipped: {metrics['duplicates_skipped']}")
            logger.info(f"Errors: {metrics['errors']}")
            logger.info("=" * 60)

        else:
            logger.info("Starting continuous polling...")
            if args.interval:
                logger.info(f"Using custom interval: {args.interval} minutes")

            poller.run_continuously(interval_minutes=args.interval)

        logger.info("LinkedIn poller stopped")
        return 0

    except KeyboardInterrupt:
        logger.info("\nReceived keyboard interrupt, shutting down...")
        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        logger.exception("Traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
