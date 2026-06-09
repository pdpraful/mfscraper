import requests
import pandas as pd
import time
from datetime import datetime
from database.db import get_db_session
from database.models import Fund, AUMHistory
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class AmfiScraper:
    def __init__(self):
        self.nav_url = settings.AMFI_NAV_URL
        
    def fetch_nav_data(self) -> pd.DataFrame:
        """Fetch and parse daily NAV data from AMFI with retry logic."""
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Fetching NAV data from {self.nav_url} (attempt {attempt}/{max_retries})")
                response = requests.get(self.nav_url, timeout=30)
                response.raise_for_status()
                
                lines = response.text.split('\n')
                data = []
                current_category = "Unknown"
                current_amc = "Unknown"
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Headers or category names often don't have semicolons
                    if ';' not in line:
                        if 'Mutual Fund' in line:
                            current_amc = line
                        else:
                            current_category = line
                        continue
                    
                    parts = line.split(';')
                    if len(parts) == 6 and parts[0] != 'Scheme Code':
                        scheme_code, isin_growth, isin_reinv, scheme_name, nav, date_str = parts
                        
                        data.append({
                            'scheme_code': scheme_code,
                            'isin': isin_growth if isin_growth != '-' else None,
                            'name': scheme_name,
                            'nav': float(nav) if nav not in ('N.A.', '-') else None,
                            'date': date_str,
                            'category': current_category,
                            'amc': current_amc
                        })
                        
                df = pd.DataFrame(data)
                return df
                
            except requests.RequestException as e:
                logger.warning(f"AMFI fetch attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    time.sleep(5)
                else:
                    logger.error(f"All {max_retries} AMFI fetch attempts failed.")
                    return pd.DataFrame()
            except Exception as e:
                logger.error(f"Error parsing AMFI NAV data: {e}")
                return pd.DataFrame()

    def is_international_fund(self, name: str, category: str) -> bool:
        """Determine if a fund is international based on name and category."""
        text_to_check = f"{name} {category}".lower()
        for keyword in settings.INTL_KEYWORDS:
            if keyword in text_to_check:
                return True
        return False

    def update_database(self, df: pd.DataFrame) -> None:
        """Update the SQLite database with the scraped funds."""
        if df.empty:
            logger.warning("Empty DataFrame received, skipping DB update.")
            return

        try:
            with get_db_session() as db:
                added_count = 0
                for _, row in df.iterrows():
                    is_intl = self.is_international_fund(row['name'], row['category'])
                    
                    # Only track international funds (or potential ones)
                    if not is_intl:
                        continue
                        
                    fund = db.query(Fund).filter(Fund.name == row['name']).first()
                    if not fund:
                        fund = Fund(
                            name=row['name'],
                            amc=row['amc'],
                            category=row['category'],
                            isin=row['isin'],
                            is_international=True
                        )
                        db.add(fund)
                        added_count += 1
                
                logger.info(f"Added {added_count} new international funds to tracking.")
                
        except Exception as e:
            logger.error(f"Database error during AMFI update: {e}", exc_info=True)

    def run(self):
        """Main execution method."""
        df = self.fetch_nav_data()
        self.update_database(df)
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = AmfiScraper()
    scraper.run()
