"""Database setup and management."""

import sqlite3
from pathlib import Path
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON
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


class AgentExecution(Base):
    """Agent execution record."""
    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, index=True)
    request_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True)
    goal = Column(Text)
    status = Column(String)  # completed, failed, timeout
    final_response = Column(Text)
    execution_trace = Column(JSON)  # List of steps
    tools_called = Column(JSON)  # List of tool calls
    total_cost_usd = Column(Float)
    duration_ms = Column(Integer)
    error_message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class ToolCall(Base):
    """Tool call record."""
    __tablename__ = "tool_calls"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, index=True)
    tool_name = Column(String)
    args = Column(JSON)
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class ToolApproval(Base):
    """Tool execution approval record."""
    __tablename__ = "tool_approvals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    tool_name = Column(String)
    args = Column(JSON, nullable=True)
    status = Column(String)  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    decided_at = Column(DateTime, nullable=True)
    decision_by = Column(String, nullable=True)


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
