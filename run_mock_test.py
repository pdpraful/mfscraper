from database.db import get_db_session
from database.models import Fund, Notice, NoticeType
from engine.capacity_engine import CapacityEngine
from datetime import datetime

def run_test():
    print("--- Starting Mock Test ---")
    
    with get_db_session() as db:
        # 1. Find a popular international fund
        fund = db.query(Fund).filter(Fund.name.ilike("%Motilal%Nasdaq%")).first()
        if not fund:
            print("Could not find Motilal Nasdaq fund, grabbing the first fund...")
            fund = db.query(Fund).filter(Fund.is_international == True).first()
            
        print(f"Target Fund: {fund.name} (Current Score: {fund.capacity_score})")
        
        # 2. Insert a mock Reopening Notice
        print("\nInjecting a mock REOPENING notice from the fund house...")
        mock_notice = Notice(
            fund_id=fund.id,
            amc=fund.amc,
            date=datetime.utcnow().date(),
            title="Resumption of Subscriptions in International Funds",
            url=f"https://mock-amc.com/notice_{datetime.utcnow().timestamp()}",
            notice_type=NoticeType.REOPENING,
            summary="The AMC has decided to reopen subscriptions via lump sum due to enhanced overseas limit availability."
        )
        db.add(mock_notice)
        
        # 3. Run the Capacity Engine
        print("Running Capacity Scoring Engine...\n")
        engine = CapacityEngine()
        new_score = engine.evaluate_fund(fund, db)
        
        print("--- Test Results ---")
        print(f"Fund Name: {fund.name}")
        print(f"New Capacity Score: {new_score}")
        print(f"New Status: {fund.current_status.value}")
        
        # Show reasons
        history = fund.score_history[-1] if fund.score_history else None
        if history:
            print(f"Reasoning: {history.reasoning}")
            print(f"Confidence: {history.confidence}")

if __name__ == "__main__":
    run_test()
