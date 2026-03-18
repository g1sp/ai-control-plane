"""Database setup and management."""

import sqlite3
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

from .config import settings

# Create database directory if it doesn't exist
db_path = Path(settings.database_url.replace("sqlite:///./", ""))
db_path.parent.mkdir(parents=True, exist_ok=True)

# SQLAlchemy setup
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AuditRequest(Base):
    """Audit request record."""
    __tablename__ = "audit_requests"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String, index=True)
    prompt = Column(Text)  # Store encrypted in v2
    response = Column(Text)
    model_used = Column(String)
    tokens_in = Column(Integer)
    tokens_out = Column(Integer)
    cost_usd = Column(Float)
    policy_decision = Column(String)
    duration_ms = Column(Integer)
    error_message = Column(Text, nullable=True)


class AuditViolation(Base):
    """Policy violation record."""
    __tablename__ = "audit_violations"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    user_id = Column(String, index=True)
    violation_reason = Column(String)
    details = Column(Text)


def init_db():
    """Initialize database schema."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
