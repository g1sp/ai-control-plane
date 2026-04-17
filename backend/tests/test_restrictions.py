"""Tests for tool restrictions."""

import pytest
import tempfile
import yaml
from src.policies.restrictions import ToolRestrictions, ToolRestrictionsManager


class TestToolRestrictions:
    """Test ToolRestrictions data class."""

    def test_create_restriction(self):
        """Test creating restriction."""
        restriction = ToolRestrictions(
            tool_name="http_get",
            enabled=True,
            allowed_domains=["example.com"]
        )

        assert restriction.tool_name == "http_get"
        assert restriction.enabled
        assert restriction.allowed_domains == ["example.com"]

    def test_restriction_defaults(self):
        """Test restriction defaults."""
        restriction = ToolRestrictions(tool_name="test")

        assert restriction.enabled
        assert not restriction.requires_approval
        assert restriction.rate_limit_per_minute == 10
        assert restriction.timeout_seconds == 30

    def test_restriction_to_dict(self):
        """Test exporting restriction to dict."""
        restriction = ToolRestrictions(
            tool_name="python_eval",
            enabled=True,
            requires_approval=True,
            banned_imports=["os", "sys"]
        )

        data = restriction.to_dict()

        assert data["tool_name"] == "python_eval"
        assert data["enabled"]
        assert data["requires_approval"]
        assert data["banned_imports"] == ["os", "sys"]

    def test_restriction_from_dict(self):
        """Test creating restriction from dict."""
        data = {
            "tool_name": "http_get",
            "enabled": True,
            "allowed_domains": ["api.example.com"],
            "timeout_seconds": 15
        }

        restriction = ToolRestrictions.from_dict(data)

        assert restriction.tool_name == "http_get"
        assert restriction.enabled
        assert restriction.allowed_domains == ["api.example.com"]
        assert restriction.timeout_seconds == 15


class TestToolRestrictionsManager:
    """Test restrictions manager."""

    def test_default_restrictions_loaded(self):
        """Test default restrictions are loaded."""
        manager = ToolRestrictionsManager()

        assert "http_get" in manager.get_all_restrictions()
        assert "http_post" in manager.get_all_restrictions()
        assert "python_eval" in manager.get_all_restrictions()
        assert "search" in manager.get_all_restrictions()

    def test_http_get_defaults(self):
        """Test http_get default restrictions."""
        manager = ToolRestrictionsManager()
        http_get = manager.get_restriction("http_get")

        assert http_get.enabled
        assert not http_get.requires_approval
        assert "localhost" in http_get.blocked_domains
        assert http_get.timeout_seconds == 10

    def test_python_eval_defaults(self):
        """Test python_eval default restrictions."""
        manager = ToolRestrictionsManager()
        python_eval = manager.get_restriction("python_eval")

        assert python_eval.enabled
        assert python_eval.requires_approval
        assert "os" in python_eval.banned_imports
        assert python_eval.max_execution_time_seconds == 5

    def test_sql_query_disabled_by_default(self):
        """Test sql_query is disabled by default."""
        manager = ToolRestrictionsManager()
        sql_query = manager.get_restriction("sql_query")

        assert not sql_query.enabled
        assert sql_query.requires_approval

    def test_get_restriction_not_found(self):
        """Test getting non-existent restriction."""
        manager = ToolRestrictionsManager()
        restriction = manager.get_restriction("nonexistent")

        assert restriction is None

    def test_is_tool_enabled(self):
        """Test checking if tool is enabled."""
        manager = ToolRestrictionsManager()

        assert manager.is_tool_enabled("http_get")
        assert manager.is_tool_enabled("python_eval")
        assert not manager.is_tool_enabled("sql_query")

    def test_is_tool_enabled_nonexistent(self):
        """Test checking non-existent tool."""
        manager = ToolRestrictionsManager()
        assert not manager.is_tool_enabled("nonexistent")

    def test_set_global_restriction(self):
        """Test setting global restriction."""
        manager = ToolRestrictionsManager()

        new_restriction = ToolRestrictions(
            tool_name="http_get",
            enabled=False,
            timeout_seconds=20
        )

        manager.set_global_restriction("http_get", new_restriction)

        updated = manager.get_restriction("http_get")
        assert not updated.enabled
        assert updated.timeout_seconds == 20

    def test_set_user_restriction(self):
        """Test setting user-specific restriction."""
        manager = ToolRestrictionsManager()

        user_restriction = ToolRestrictions(
            tool_name="sql_query",
            enabled=True,
            allowed_databases=["user_db"]
        )

        manager.set_user_restriction("alice@example.com", "sql_query", user_restriction)

        # User-specific should override global
        alice_sql = manager.get_restriction("sql_query", user_id="alice@example.com")
        assert alice_sql.enabled
        assert alice_sql.allowed_databases == ["user_db"]

        # Other users should see global (disabled)
        bob_sql = manager.get_restriction("sql_query", user_id="bob@example.com")
        assert not bob_sql.enabled

    def test_export_config(self):
        """Test exporting restrictions to YAML."""
        manager = ToolRestrictionsManager()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            manager.export_config(f.name)

            # Read back and verify
            with open(f.name, "r") as rf:
                data = yaml.safe_load(rf)

        assert "tools" in data
        assert "http_get" in data["tools"]
        assert data["tools"]["http_get"]["enabled"]

    def test_load_from_file(self):
        """Test loading restrictions from YAML file."""
        config = {
            "tools": {
                "custom_tool": {
                    "tool_name": "custom_tool",
                    "enabled": True,
                    "rate_limit_per_minute": 5,
                    "timeout_seconds": 20
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            f.flush()

            manager = ToolRestrictionsManager(f.name)

        restriction = manager.get_restriction("custom_tool")
        assert restriction is not None
        assert restriction.rate_limit_per_minute == 5

    def test_load_from_file_updates_existing(self):
        """Test loading from file updates existing restrictions."""
        config = {
            "tools": {
                "http_get": {
                    "tool_name": "http_get",
                    "enabled": False,
                    "timeout_seconds": 5
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            f.flush()

            manager = ToolRestrictionsManager(f.name)

        http_get = manager.get_restriction("http_get")
        assert not http_get.enabled
        assert http_get.timeout_seconds == 5

    def test_get_all_restrictions(self):
        """Test getting all restrictions."""
        manager = ToolRestrictionsManager()
        all_restrictions = manager.get_all_restrictions()

        assert len(all_restrictions) >= 4
        assert all(isinstance(r, ToolRestrictions) for r in all_restrictions.values())


class TestRestrictionScenarios:
    """Test real-world restriction scenarios."""

    def test_http_security_by_default(self):
        """Test HTTP is secure by default."""
        manager = ToolRestrictionsManager()
        http_get = manager.get_restriction("http_get")

        # Should block common internal domains
        assert "localhost" in http_get.blocked_domains
        assert "127.0.0.1" in http_get.blocked_domains
        assert "internal" in http_get.blocked_domains

    def test_python_restricted_by_default(self):
        """Test Python execution is restricted by default."""
        manager = ToolRestrictionsManager()
        python = manager.get_restriction("python_eval")

        # Should require approval
        assert python.requires_approval

        # Should have short timeout
        assert python.max_execution_time_seconds == 5

        # Should ban dangerous imports
        assert "os" in python.banned_imports
        assert "sys" in python.banned_imports
        assert "subprocess" in python.banned_imports

    def test_sql_disabled_by_default(self):
        """Test SQL is disabled by default."""
        manager = ToolRestrictionsManager()
        sql = manager.get_restriction("sql_query")

        assert not sql.enabled

    def test_user_override_scenario(self):
        """Test user override scenario."""
        manager = ToolRestrictionsManager()

        # Alice gets elevated permissions
        alice_sql = ToolRestrictions(
            tool_name="sql_query",
            enabled=True,
            allowed_databases=["alice_analytics", "alice_data"],
            allowed_operations=["SELECT", "INSERT"],
        )

        manager.set_user_restriction("alice@company.com", "sql_query", alice_sql)

        # Alice can use SQL
        assert manager.is_tool_enabled("sql_query", user_id="alice@company.com")

        # Bob cannot (global is disabled)
        assert not manager.is_tool_enabled("sql_query", user_id="bob@company.com")

        # Alice's restrictions are specific
        alice_restrictions = manager.get_restriction("sql_query", user_id="alice@company.com")
        assert alice_restrictions.allowed_databases == ["alice_analytics", "alice_data"]
