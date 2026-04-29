"""Tests for database migrations."""

import pytest
from pathlib import Path
from sqlalchemy import inspect, text
from src.database import SessionLocal, engine
from src.services.migration_runner import MigrationRunner


@pytest.fixture
def migration_runner():
    """Create migration runner instance."""
    return MigrationRunner()


class TestMigrationSetup:
    """Test migration framework setup."""

    def test_alembic_config_exists(self):
        """Test alembic.ini config exists."""
        config_path = Path(__file__).parent.parent.parent / "alembic.ini"
        assert config_path.exists()

    def test_alembic_env_exists(self):
        """Test alembic/env.py exists."""
        env_path = Path(__file__).parent.parent.parent / "alembic" / "env.py"
        assert env_path.exists()

    def test_initial_migration_exists(self):
        """Test initial migration file exists."""
        migration_path = Path(__file__).parent.parent.parent / "alembic" / "versions" / "000_initial_schema.py"
        assert migration_path.exists()


class TestMigrationRunner:
    """Test MigrationRunner service."""

    def test_migration_runner_init(self, migration_runner):
        """Test MigrationRunner initializes."""
        assert migration_runner.config is not None
        assert migration_runner is not None

    def test_get_migration_history(self, migration_runner):
        """Test retrieving migration history."""
        history = migration_runner.get_migration_history()
        assert len(history) >= 1
        assert history[0]["revision"] == "000_initial"

    def test_upgrade_creates_tables(self, migration_runner):
        """Test that upgrade creates all required tables."""
        migration_runner.upgrade_to_head()

        db = SessionLocal()
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert "audit_requests" in tables
        assert "audit_violations" in tables
        assert "agent_executions" in tables
        assert "tool_calls" in tables
        assert "tool_approvals" in tables

        db.close()

    def test_audit_requests_schema(self, migration_runner):
        """Test audit_requests table schema after migration."""
        migration_runner.upgrade_to_head()

        db = SessionLocal()
        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("audit_requests")}

        required_cols = {
            "id", "timestamp", "user_id", "prompt", "response",
            "model_used", "tokens_in", "tokens_out", "cost_usd",
            "policy_decision", "duration_ms", "error_message"
        }
        assert required_cols.issubset(columns)

        db.close()

    def test_agent_executions_schema(self, migration_runner):
        """Test agent_executions table schema."""
        migration_runner.upgrade_to_head()

        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("agent_executions")}

        required_cols = {
            "id", "agent_id", "request_id", "user_id", "goal",
            "status", "final_response", "execution_trace", "tools_called",
            "total_cost_usd", "duration_ms", "error_message", "timestamp"
        }
        assert required_cols.issubset(columns)

    def test_tool_approvals_schema(self, migration_runner):
        """Test tool_approvals table schema."""
        migration_runner.upgrade_to_head()

        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("tool_approvals")}

        required_cols = {
            "id", "user_id", "tool_name", "args",
            "status", "created_at", "decided_at", "decision_by"
        }
        assert required_cols.issubset(columns)

    def test_indexes_created(self, migration_runner):
        """Test that indexes are created."""
        migration_runner.upgrade_to_head()

        inspector = inspect(engine)

        audit_indexes = {idx["name"] for idx in inspector.get_indexes("audit_requests")}
        assert "ix_audit_requests_timestamp" in audit_indexes
        assert "ix_audit_requests_user_id" in audit_indexes

        agent_indexes = {idx["name"] for idx in inspector.get_indexes("agent_executions")}
        assert "ix_agent_executions_timestamp" in agent_indexes
        assert "ix_agent_executions_user_id" in agent_indexes

    def test_get_current_revision(self, migration_runner):
        """Test getting current database revision."""
        migration_runner.upgrade_to_head()
        current = migration_runner.get_current_revision()
        assert current == "000_initial"

    def test_downgrade_rollback(self, migration_runner):
        """Test rollback functionality."""
        migration_runner.upgrade_to_head()

        db = SessionLocal()
        inspector = inspect(engine)
        assert "audit_requests" in inspector.get_table_names()

        migration_runner.downgrade_one()

        inspector = inspect(engine)
        assert "audit_requests" not in inspector.get_table_names()

        migration_runner.upgrade_to_head()

        inspector = inspect(engine)
        assert "audit_requests" in inspector.get_table_names()

        db.close()

    def test_idempotent_migration(self, migration_runner):
        """Test that running migrations multiple times is safe."""
        migration_runner.upgrade_to_head()
        result1 = migration_runner.get_current_revision()

        migration_runner.upgrade_to_head()
        result2 = migration_runner.get_current_revision()

        assert result1 == result2 == "000_initial"

    def test_get_pending_migrations(self, migration_runner):
        """Test getting pending migrations."""
        migration_runner.downgrade_one()
        pending = migration_runner.get_pending_migrations()
        assert len(pending) > 0
        assert pending[0]["revision"] == "000_initial"

        migration_runner.upgrade_to_head()
        pending = migration_runner.get_pending_migrations()
        assert len(pending) == 0
