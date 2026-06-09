import logging
import yfinance as yf
from database.db import get_db_session
from database.models import Fund

logger = logging.getLogger(__name__)

class ETFEngine:
    """Fetches live market prices for ETFs and calculates the premium/discount vs NAV."""
    
    def run(self):
        logger.info("Starting ETF Engine...")
        
        with get_db_session() as db:
            # Get all funds that have a ticker mapped
            etfs = db.query(Fund).filter(Fund.ticker.isnot(None)).all()
            
            if not etfs:
                logger.info("No mapped ETFs found in the database.")
                return
                
            updated_count = 0
            for etf in etfs:
                try:
                    # Fetch live/close price from Yahoo Finance
                    ticker = yf.Ticker(etf.ticker)
                    last_price = ticker.fast_info.get("lastPrice")
                    
                    if not last_price:
                        # Fallback if fast_info fails
                        history = ticker.history(period="1d")
                        if not history.empty:
                            last_price = history['Close'].iloc[-1]
                    
                    if last_price:
                        etf.latest_price = round(float(last_price), 4)
                        
                        if etf.latest_nav and etf.latest_nav > 0:
                            # Calculate Premium/Discount %
                            premium = ((etf.latest_price - etf.latest_nav) / etf.latest_nav) * 100
                            etf.premium_discount = round(premium, 2)
                            logger.info(f"[ETF] {etf.name} ({etf.ticker}) | Price: ₹{etf.latest_price} | NAV: ₹{etf.latest_nav} | Premium: {etf.premium_discount}%")
                        else:
                            logger.warning(f"[ETF] {etf.name} lacks a valid latest_nav. Skipping Premium calculation.")
                            
                        updated_count += 1
                    else:
                        logger.warning(f"[ETF] Failed to fetch price for {etf.ticker}")
                        
                except Exception as e:
                    logger.error(f"[ETF] Error processing {etf.ticker}: {e}")
                    
            db.commit()
            logger.info(f"ETF Engine complete. Updated {updated_count} ETFs.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    engine = ETFEngine()
    engine.run()
