from datetime import datetime, timedelta, timezone
from sqlalchemy import func
from database.db import get_db_session
from database.models import Fund, Notice, AUMHistory, NoticeType, FundStatus, CapacityScoreHistory
from core.config import settings
import logging

logger = logging.getLogger(__name__)

class CapacityEngine:
    def __init__(self):
        pass

    def evaluate_fund(self, fund: Fund, db_session) -> int:
        """
        Evaluate a fund and return a Capacity Score from 0 to 100.
        Logic based on Signals A-F.
        """
        score = 50 # Base unknown score
        reasons = []
        confidence = "MEDIUM"
        
        # Signal A: Is fresh purchase currently allowed? (From Notice data)
        # We look for the most recent suspension or reopening notice
        recent_notice = db_session.query(Notice).filter(
            Notice.fund_id == fund.id
        ).order_by(Notice.date.desc()).first()

        if recent_notice:
            if recent_notice.notice_type == NoticeType.SUSPENSION:
                score -= 30
                reasons.append(f"Suspension Notice on {recent_notice.date}")
                confidence = "HIGH"
            elif recent_notice.notice_type == NoticeType.REOPENING:
                score += 40
                reasons.append(f"Reopening Notice on {recent_notice.date}")
                confidence = "HIGH"

        # Signal C: Has AUM declined recently?
        # Get AUM from last 30 days
        thirty_days_ago = datetime.now(timezone.utc).date() - timedelta(days=30)
        aum_history = db_session.query(AUMHistory).filter(
            AUMHistory.fund_id == fund.id,
            AUMHistory.date >= thirty_days_ago
        ).order_by(AUMHistory.date.desc()).all()

        if len(aum_history) >= 2:
            latest_aum = aum_history[0].aum_cr
            oldest_aum = aum_history[-1].aum_cr
            
            if oldest_aum > 0:
                change_pct = ((latest_aum - oldest_aum) / oldest_aum) * 100
                if change_pct < -5:
                    score += 15 # Large outflow creates capacity
                    reasons.append(f"AUM declined by {abs(change_pct):.1f}% in 30 days")
                elif change_pct > 10:
                    score -= 10 # Rapid inflow eats capacity
                    reasons.append(f"AUM increased by {change_pct:.1f}% in 30 days")
        
        # Signal E: Is fund newly launched? (NFO)
        if fund.launch_date:
            days_since_launch = (datetime.now(timezone.utc).date() - fund.launch_date).days
            if days_since_launch < 90:
                score += 20
                reasons.append(f"Newly launched fund (NFO within last 90 days)")
        else:
            # If launch date is unknown, but we have an NFO notice
            nfo_notice = db_session.query(Notice).filter(
                Notice.fund_id == fund.id,
                Notice.notice_type == NoticeType.NFO
            ).first()
            if nfo_notice:
                score += 20
                reasons.append("Fund has recent NFO Notice")

        # Clamp score between 0 and 100
        score = max(0, min(100, score))
        
        # Update Fund Status based on score
        if score >= 90:
            fund.current_status = FundStatus.OPEN
        elif score >= 70:
            fund.current_status = FundStatus.PARTIAL
        elif score <= 30:
            fund.current_status = FundStatus.CLOSED
        else:
            fund.current_status = FundStatus.UNKNOWN
            
        fund.capacity_score = score
        fund.last_verified = datetime.now(timezone.utc)
        
        # Save score history (deduplicate: update if already scored today)
        existing = db_session.query(CapacityScoreHistory).filter(
            CapacityScoreHistory.fund_id == fund.id,
            func.date(CapacityScoreHistory.date) == datetime.now(timezone.utc).date()
        ).first()

        if existing:
            existing.score = score
            existing.reasoning = "; ".join(reasons)
            existing.confidence = confidence
        else:
            history = CapacityScoreHistory(
                fund_id=fund.id,
                score=score,
                reasoning="; ".join(reasons),
                confidence=confidence
            )
            db_session.add(history)
        
        return score

    def run_all(self) -> None:
        """Evaluate capacity for all tracked international funds."""
        try:
            with get_db_session() as db:
                funds = db.query(Fund).filter(Fund.is_international == True).all()
                success_count = 0
                
                for fund in funds:
                    try:
                        self.evaluate_fund(fund, db)
                        success_count += 1
                    except Exception as e:
                        logger.error(f"Error evaluating capacity for fund {fund.name} (ID: {fund.id}): {e}", exc_info=True)
                        # We don't rollback the whole transaction here, we just skip the bad fund
                        
                logger.info(f"Evaluated capacity for {success_count} out of {len(funds)} funds.")

                # Prune score history older than 90 days
                # SQLite often stores dates naively even with timezone.utc, so we compare naively
                cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).replace(tzinfo=None)
                pruned = db.query(CapacityScoreHistory).filter(CapacityScoreHistory.date < cutoff).delete()
                logger.info(f"Pruned {pruned} score history records older than 90 days.")
        except Exception as e:
            logger.error(f"Critical error during batch capacity evaluation: {e}", exc_info=True)
