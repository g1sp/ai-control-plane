"""Pytest configuration and fixtures."""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

from src.database import Base, AuditRequest, AuditViolation, AgentExecution, ToolCall, ToolApproval
from src.tools.registry import ToolRegistry
from src.tools.executors import HttpToolExecutor, SearchToolExecutor, PythonToolExecutor
from src.agents.models import AgentRequest


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine."""
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="function")
def db(db_engine):
    """Create test database session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)(
    )

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_db_session(db_engine):
    """Provide test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    Base.metadata.create_all(bind=db_engine)
    db = TestingSessionLocal()

    yield db

    db.close()
    Base.metadata.drop_all(bind=db_engine)


@pytest.fixture
def tool_registry():
    """Create test tool registry with built-in tools."""
    registry = ToolRegistry()

    # Register built-in tools
    registry.register(
        name="http_get",
        func=HttpToolExecutor.http_get,
        description="Make HTTP GET request",
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "headers": {"type": "object", "description": "Optional headers"}
            },
            "required": ["url"]
        }
    )

    registry.register(
        name="search",
        func=SearchToolExecutor.search,
        description="Search for information",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results"}
            },
            "required": ["query"]
        }
    )

    registry.register(
        name="python_eval",
        func=PythonToolExecutor.python_eval,
        description="Execute Python code",
        input_schema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code"},
                "safe_mode": {"type": "boolean", "description": "Enable safety checks"}
            },
            "required": ["code"]
        },
        requires_approval=True
    )

    return registry


@pytest.fixture
def agent_request():
    """Create test agent request."""
    return AgentRequest(
        goal="Test goal",
        user_id="test@example.com",
        budget_usd=0.50,
        max_iterations=5,
        timeout_seconds=30
    )
