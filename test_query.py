import sys
import os
from database.db import get_db_session
from database.models import Fund

def main():
    print("Connecting to database...")
    
    with get_db_session() as db:
        # 1. Check total tracked funds
        total_funds = db.query(Fund).filter(Fund.is_international == True).count()
        print(f"\n--- Total International Funds Tracked: {total_funds} ---\n")
        
        if total_funds == 0:
            print("No funds found in the database. You may need to run `python3 main.py` first to scrape AMFI data.")
            sys.exit(0)
        
        # 2. Get the top 10 funds by capacity score
        print("--- Top 10 Funds by Capacity Score ---")
        top_funds = db.query(Fund).filter(Fund.is_international == True).order_by(Fund.capacity_score.desc()).limit(10).all()
        
        print(f"{'Fund Name':<70} | {'Score':<5} | {'Status':<10}")
        print("-" * 90)
        for f in top_funds:
            print(f"{f.name[:68]:<70} | {f.capacity_score:<5} | {f.current_status.value:<10}")

if __name__ == "__main__":
    main()
