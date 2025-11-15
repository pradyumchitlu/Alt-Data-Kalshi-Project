"""
Automated scheduler for data collection
Runs data collection at specified intervals
"""
import schedule
import time
import logging
from datetime import datetime
from main_collector import DataCollectionOrchestrator
from billboard_scraper import BillboardScraper
from config import COLLECTION_INTERVAL_HOURS

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_daily_collection():
    """Run daily data collection job"""
    logger.info("=" * 80)
    logger.info(f"Starting scheduled data collection at {datetime.now()}")
    logger.info("=" * 80)
    
    orchestrator = DataCollectionOrchestrator()
    orchestrator.run_daily_collection()
    
    logger.info("Scheduled collection complete")


def run_billboard_collection():
    """Run Billboard chart collection (weekly on Saturdays)"""
    logger.info("Running Billboard Hot 100 collection")
    scraper = BillboardScraper()
    scraper.collect_chart_data()


def main():
    """Set up and run scheduler"""
    logger.info("Starting data collection scheduler")
    logger.info(f"Collection interval: Every {COLLECTION_INTERVAL_HOURS} hours")
    
    # Schedule daily data collection
    # Run every N hours (configured in config.py)
    schedule.every(COLLECTION_INTERVAL_HOURS).hours.do(run_daily_collection)
    
    # Schedule Billboard chart collection (Saturdays at 2 PM ET)
    schedule.every().saturday.at("14:00").do(run_billboard_collection)
    
    # Also run immediately on startup
    logger.info("Running initial data collection...")
    run_daily_collection()
    
    # Keep the scheduler running
    logger.info("Scheduler is now running. Press Ctrl+C to stop.")
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(300)  # Wait 5 minutes before retrying


if __name__ == "__main__":
    main()

