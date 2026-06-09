import os
from pathlib import Path

from pydantic import BaseModel

from dotenv import load_dotenv

load_dotenv()

_DEFAULT_DB_DIR = Path.home() / ".mfscraper" / "data"
_DEFAULT_DB_PATH = f"sqlite:///{_DEFAULT_DB_DIR / 'mfscraper.db'}"

class Settings(BaseModel):
    # Database
    MF_DATABASE_URL: str = os.getenv("MF_DATABASE_URL", _DEFAULT_DB_PATH)
    
    # Email / SMTP
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_TO: str = os.getenv("EMAIL_TO", "")
    
    # Scraping Config
    AMFI_NAV_URL: str = "https://www.amfiindia.com/spages/NAVAll.txt"
    
    # Keywords to identify international funds
    INTL_KEYWORDS: list[str] = [
        "us equity", "global equity", "nasdaq", "s&p 500", "s&p500",
        "developed market", "emerging market", "international", "overseas",
        "world", "global", "offshore", "fang", "hang seng", "nyse", 
        "japan", "taiwan", "europe"
    ]
    
    # Mapping of AMFI exact scheme names to NSE tickers for ETF pricing
    ETF_TICKER_MAP: dict[str, str] = {
        "Motilal Oswal Nasdaq 100 ETF (MOFN100)": "MON100.NS",
        "Motilal Oswal Nasdaq Q50 ETF": "MONQ50.NS",
        "Mirae Asset S&P 500 Top 50 ETF": "MASPTOP50.NS",
        "Mirae Asset Hang Seng TECH ETF": "MAHKTECH.NS",
        "Mirae Asset NYSE FANG+ ETF": "MAFANG.NS",
        "Nippon India ETF Hang Seng BeES": "HNGSNGBEES.NS"
    }
    
    # Target AMCs to scrape actively
    TARGET_AMCS: list[str] = [
        "Motilal Oswal",
        "Mirae",
        "Edelweiss",
        "Franklin",
        "DSP",
        "ICICI Prudential",
        "Nippon",
        "Aditya Birla Sun Life",
        "Kotak",
        "Axis",
        "SBI"
    ]

settings = Settings()
