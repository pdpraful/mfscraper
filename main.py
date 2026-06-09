import logging
import argparse
import os

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(_PROJECT_DIR, "mfscraper.log")),
            logging.StreamHandler()
        ]
    )

# Must setup logging BEFORE internal imports so they inherit the root config
setup_logging()
logger = logging.getLogger(__name__)

from database.db import init_db
from core.scheduler import start_scheduler, daily_workflow

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="International MF Capacity Scraper")
    parser.add_argument('--run-once', '--runonce', dest='run_once', action='store_true', help="Run the daily workflow manually once and exit")
    parser.add_argument('--daemon', action='store_true', help="Start the background scheduler for daily runs (default behavior)")
    args = parser.parse_args()
    
    logger.info("Initializing database...")
    init_db()
    
    if args.run_once:
        logger.info("Manual execution triggered. Running workflow once...")
        daily_workflow()
        logger.info("Manual run complete. Exiting.")
    else:
        logger.info("Starting background scheduler (Daemon mode)...")
        start_scheduler()
