from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

class FundStatus(enum.Enum):
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    CLOSED = "CLOSED"
    UNKNOWN = "UNKNOWN"

class NoticeType(enum.Enum):
    REOPENING = "REOPENING"
    SUSPENSION = "SUSPENSION"
    NFO = "NFO"
    SID_UPDATE = "SID_UPDATE"
    OTHER = "OTHER"

class Fund(Base):
    __tablename__ = "funds"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    amc = Column(String, index=True, nullable=False)
    category = Column(String, nullable=True)
    isin = Column(String, unique=True, index=True, nullable=True)
    launch_date = Column(Date, nullable=True)
    is_international = Column(Boolean, default=True)
    
    current_status = Column(Enum(FundStatus), default=FundStatus.UNKNOWN)
    capacity_score = Column(Integer, default=50) # 0-100
    last_verified = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    aum_history = relationship("AUMHistory", back_populates="fund", cascade="all, delete-orphan")
    notices = relationship("Notice", back_populates="fund")
    score_history = relationship("CapacityScoreHistory", back_populates="fund", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Fund(name='{self.name}', amc='{self.amc}', status={self.current_status})>"

class AUMHistory(Base):
    __tablename__ = "aum_history"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey("funds.id"), nullable=False)
    date = Column(Date, nullable=False, index=True)
    aum_cr = Column(Float, nullable=False) # AUM in Crores
    net_flow_cr = Column(Float, nullable=True) # Estimated flows
    
    fund = relationship("Fund", back_populates="aum_history")

class Notice(Base):
    __tablename__ = "notices"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey("funds.id"), nullable=True) # Can be null if notice is generic AMC wide
    amc = Column(String, index=True, nullable=False)
    date = Column(Date, nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, unique=True, nullable=False)
    notice_type = Column(Enum(NoticeType), default=NoticeType.OTHER)
    summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    fund = relationship("Fund", back_populates="notices")

class CapacityScoreHistory(Base):
    __tablename__ = "capacity_score_history"
    
    id = Column(Integer, primary_key=True, index=True)
    fund_id = Column(Integer, ForeignKey("funds.id"), nullable=False)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    score = Column(Integer, nullable=False)
    reasoning = Column(Text, nullable=True)
    confidence = Column(String, nullable=True) # HIGH, MEDIUM, LOW
    
    fund = relationship("Fund", back_populates="score_history")
