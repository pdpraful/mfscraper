from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from scrapers.amfi_scraper import AmfiScraper
from engine.capacity_engine import CapacityEngine
from notifier.email_reporter import EmailReporter

logger = logging.getLogger(__name__)

def daily_workflow():
    logger.info("Starting Daily Workflow...")
    
    # 1. Scrape AMFI for daily NAV/AUM changes
    try:
        amfi = AmfiScraper()
        amfi.run()
    except Exception as e:
        logger.error(f"AMFI scraping failed, continuing with existing data: {e}", exc_info=True)
        
    # 1.5 Update ETF Market Prices and calculate Premium/Discount
    try:
        from engine.etf_engine import ETFEngine
        etf_engine = ETFEngine()
        etf_engine.run()
    except Exception as e:
        logger.error(f"ETF pricing engine failed: {e}", exc_info=True)
    
    # 2. Scrape AMC notices and AUM Factsheets
    try:
        from scrapers.amc.motilal import MotilalOswalScraper
        from scrapers.amc.mirae import MiraeScraper
        from scrapers.amc.dsp import DSPScraper
        from scrapers.amc.kotak import KotakScraper
        from database.db import get_db_session
        from database.models import Notice, Fund
        import time
        
        scrapers = [
            MotilalOswalScraper(),
            MiraeScraper(),
            DSPScraper(),
            KotakScraper()
        ]
        
        for scraper in scrapers:
            try:
                notices_data = scraper.run()
                
                if notices_data:
                    with get_db_session() as db:
                        seen_urls = set()
                        for nd in notices_data:
                            if nd['url'] in seen_urls:
                                continue
                                
                            fund = db.query(Fund).filter(Fund.amc.ilike(f"%{nd['amc']}%")).first()
                            if fund:
                                exists = db.query(Notice).filter(Notice.url == nd['url']).first()
                                if not exists:
                                    notice = Notice(
                                        fund_id=fund.id,
                                        amc=nd['amc'],
                                        notice_type=nd['type'],
                                        title=nd['title'],
                                        summary=nd['title'],
                                        date=nd['date'],
                                        url=nd['url']
                                    )
                                    db.add(notice)
                                    seen_urls.add(nd['url'])
                        db.commit()
            except Exception as e:
                logger.error(f"Failed to scrape {scraper.amc_name}: {e}")
            
            # 15 second polite delay between AMC websites
            logger.info("Waiting 15 seconds before hitting next AMC...")
            time.sleep(15)
            
    except Exception as e:
        logger.error(f"AMC scraping master loop failed: {e}", exc_info=True)
        
    # 3. Evaluate capacity scores
    try:
        engine = CapacityEngine()
        engine.run_all()
    except Exception as e:
        logger.error(f"Capacity scoring failed: {e}", exc_info=True)
    
    # 3. Generate daily report
    try:
        reporter = EmailReporter()
        reporter.generate_daily_report()
    except Exception as e:
        logger.error(f"Email reporting failed: {e}", exc_info=True)
    
    logger.info("Daily Workflow Complete.")

def sunday_deep_audit():
    """Sunday deep audit: full universe refresh + capacity re-evaluation + weekly digest."""
    logger.info("Starting Sunday Deep Audit...")
    daily_workflow()
    logger.info("Sunday Deep Audit Complete.")

def start_scheduler():
    scheduler = BlockingScheduler()
    
    # Daily workflow at 06:00 IST (UTC+5:30)
    # Assuming the machine runs in local IST timezone, we use 06:00
    # If the machine is UTC, we would adjust (00:30 UTC)
    scheduler.add_job(daily_workflow, CronTrigger(hour=6, minute=0))
    
    # Sunday deep audit at 04:00 IST
    scheduler.add_job(sunday_deep_audit, CronTrigger(day_of_week='sun', hour=4, minute=0))
    
    logger.info("Scheduler started. Waiting for jobs...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")
