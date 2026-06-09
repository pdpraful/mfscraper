import logging
from .base import BaseAMCScraper
from .pdf_helper import PDFExtractorMixin
from playwright.sync_api import Page
from database.models import NoticeType, Fund, AUMHistory
from database.db import get_db_session
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MotilalOswalScraper(BaseAMCScraper, PDFExtractorMixin):
    def __init__(self):
        super().__init__(
            amc_name="Motilal Oswal", 
            base_url="https://www.motilaloswalmf.com/downloads/mutual-fund/notices-and-addendums"
        )
        self.factsheet_url = "https://www.motilaloswalmf.com/downloads/mutual-fund/Factsheet"
        
    def fetch_notices(self, page: Page):
        notices_data = []
        
        # Scrape Notices
        logger.info(f"[{self.amc_name}] Scraping notices...")
        links = page.query_selector_all('a')
        count = 0
        for link in links:
            href = link.get_attribute('href')
            text = link.inner_text().strip()
            
            if href and '.pdf' in href.lower() and len(text) > 5:
                # Basic classification
                notice_type = NoticeType.OTHER
                text_lower = text.lower()
                if "suspension" in text_lower or "halt" in text_lower or "stop" in text_lower:
                    notice_type = NoticeType.SUSPENSION
                elif "reopening" in text_lower or "resumption" in text_lower or "lump sum" in text_lower or "sip" in text_lower:
                    notice_type = NoticeType.REOPENING
                    
                notices_data.append({
                    'title': text[:255],
                    'date': datetime.now(timezone.utc).date(), # Fallback date if not parsed
                    'url': f"https://www.motilaloswalmf.com{href}" if href.startswith('/') else href,
                    'type': notice_type,
                    'amc': self.amc_name
                })
                count += 1
                if count >= 10: # Only look at top 10 most recent links to avoid parsing entire history
                    break
                    
        logger.info(f"[{self.amc_name}] Found {len(notices_data)} recent notices.")
        
        # Scrape AUM Factsheet
        self.scrape_aum(page)
        
        return notices_data

    def scrape_aum(self, page: Page):
        """Finds the latest factsheet and extracts AUM for international funds."""
        logger.info(f"[{self.amc_name}] Navigating to Factsheet page...")
        page.goto(self.factsheet_url, timeout=60000, wait_until="networkidle")
        self.random_delay(2.0, 4.0)
        
        latest_factsheet_url = None
        links = page.query_selector_all('a')
        for link in links:
            href = link.get_attribute('href')
            text = link.inner_text().strip()
            if href and '.pdf' in href.lower() and 'factsheet' in href.lower():
                latest_factsheet_url = href
                break # First one is usually latest
                
        if not latest_factsheet_url:
            logger.warning(f"[{self.amc_name}] Could not find any Factsheet PDF link.")
            return
            
        logger.info(f"[{self.amc_name}] Found Factsheet: {latest_factsheet_url}")
        pdf_path = self.download_pdf(latest_factsheet_url)
        
        if pdf_path:
            with get_db_session() as db:
                funds = db.query(Fund).filter(
                    Fund.amc.ilike("%Motilal%"),
                    Fund.is_international == True
                ).all()
                
                for fund in funds:
                    # E.g. "Motilal Oswal Nasdaq 100 ETF" -> keywords: ["Nasdaq", "100"]
                    # Clean fund name to get critical keywords
                    keywords = [w for w in fund.name.split() if w.lower() not in ['motilal', 'oswal', 'fund', 'etf', 'fof', 'mutual', 'direct', 'growth', 'plan', 'fund of funds']]
                    
                    if not keywords:
                        continue
                        
                    aum_val = self.extract_aum_for_fund(pdf_path, fund_keywords=keywords[:2])
                    if aum_val:
                        logger.info(f"[{self.amc_name}] Extracted AUM for {fund.name}: ₹{aum_val} Cr")
                        
                        # Save to AUMHistory
                        history = AUMHistory(
                            fund_id=fund.id,
                            date=datetime.now(timezone.utc).date(),
                            aum_cr=aum_val
                        )
                        db.add(history)
                db.commit()

