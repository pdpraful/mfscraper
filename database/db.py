import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from core.config import settings

# Create engine
engine = create_engine(
    settings.MF_DATABASE_URL,
    connect_args={"check_same_thread": False} # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Create all tables if they don't exist."""
    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(settings.MF_DATABASE_URL.replace("sqlite:///", "")), exist_ok=True)
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db_session():
    """Context manager for safe database sessions."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
