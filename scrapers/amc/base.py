from playwright.sync_api import sync_playwright, Browser, Page, Playwright
import logging
import time
import random

logger = logging.getLogger(__name__)

class BaseAMCScraper:
    def __init__(self, amc_name: str, base_url: str):
        self.amc_name = amc_name
        self.base_url = base_url
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
        ]
        
    def random_delay(self, min_sec: float = 2.0, max_sec: float = 5.0):
        """Lenient scraping: pause randomly to avoid overburdening the server."""
        delay = random.uniform(min_sec, max_sec)
        logger.debug(f"[{self.amc_name}] Waiting for {delay:.2f} seconds...")
        time.sleep(delay)

    def fetch_notices(self, page: Page):
        """
        To be implemented by specific AMC scrapers.
        Should interact with the page, extract notices, and return a list of dictionaries.
        """
        raise NotImplementedError
        
    def run(self):
        logger.info(f"Starting Playwright scraper for {self.amc_name}")
        notices = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                
                # Use a realistic User-Agent
                context = browser.new_context(
                    user_agent=random.choice(self.user_agents),
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = context.new_page()
                
                # Initial delay before hitting the server
                self.random_delay(1.0, 3.0)
                
                logger.info(f"[{self.amc_name}] Navigating to {self.base_url}")
                page.goto(self.base_url, timeout=60000, wait_until="domcontentloaded")
                self.random_delay(2.0, 4.0)
                
                notices = self.fetch_notices(page)
                
                context.close()
                browser.close()
        except Exception as e:
            logger.error(f"Error scraping {self.amc_name}: {e}")
            
        return notices
