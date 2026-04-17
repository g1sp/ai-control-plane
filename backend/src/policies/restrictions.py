"""Tool execution restrictions and policies."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import yaml


@dataclass
class ToolRestrictions:
    """Restrictions for a specific tool."""

    tool_name: str
    enabled: bool = True
    requires_approval: bool = False

    # HTTP tool restrictions
    allowed_domains: List[str] = field(default_factory=list)
    blocked_domains: List[str] = field(default_factory=list)
    allowed_methods: List[str] = field(default_factory=list)

    # Python tool restrictions
    banned_imports: List[str] = field(default_factory=list)
    max_execution_time_seconds: int = 5
    max_memory_mb: int = 100

    # SQL tool restrictions
    allowed_databases: List[str] = field(default_factory=list)
    allowed_operations: List[str] = field(default_factory=list)
    blocked_tables: List[str] = field(default_factory=list)

    # General restrictions
    rate_limit_per_minute: int = 10
    rate_limit_per_day: int = 100
    max_request_size_kb: int = 100
    max_response_size_kb: int = 1000
    timeout_seconds: int = 30

    # Cost restrictions
    max_cost_usd_per_day: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Export restrictions as dictionary."""
        return {
            "tool_name": self.tool_name,
            "enabled": self.enabled,
            "requires_approval": self.requires_approval,
            "allowed_domains": self.allowed_domains,
            "blocked_domains": self.blocked_domains,
            "allowed_methods": self.allowed_methods,
            "banned_imports": self.banned_imports,
            "max_execution_time_seconds": self.max_execution_time_seconds,
            "max_memory_mb": self.max_memory_mb,
            "allowed_databases": self.allowed_databases,
            "allowed_operations": self.allowed_operations,
            "blocked_tables": self.blocked_tables,
            "rate_limit_per_minute": self.rate_limit_per_minute,
            "rate_limit_per_day": self.rate_limit_per_day,
            "max_request_size_kb": self.max_request_size_kb,
            "max_response_size_kb": self.max_response_size_kb,
            "timeout_seconds": self.timeout_seconds,
            "max_cost_usd_per_day": self.max_cost_usd_per_day,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolRestrictions":
        """Create from dictionary."""
        return cls(**data)


class ToolRestrictionsManager:
    """Manage tool restrictions globally and per-user."""

    # Default restrictions for built-in tools
    DEFAULT_RESTRICTIONS = {
        "http_get": ToolRestrictions(
            tool_name="http_get",
            enabled=True,
            blocked_domains=["localhost", "127.0.0.1", "internal", "192.168"],
            allowed_methods=["GET"],
            rate_limit_per_minute=10,
            timeout_seconds=10,
            max_response_size_kb=1000,
        ),
        "http_post": ToolRestrictions(
            tool_name="http_post",
            enabled=True,
            blocked_domains=["localhost", "127.0.0.1", "internal", "192.168"],
            allowed_methods=["POST"],
            rate_limit_per_minute=5,
            timeout_seconds=10,
            max_request_size_kb=100,
            requires_approval=True,  # POST is riskier
        ),
        "python_eval": ToolRestrictions(
            tool_name="python_eval",
            enabled=True,
            requires_approval=True,
            banned_imports=["os", "sys", "subprocess"],
            max_execution_time_seconds=5,
            max_memory_mb=50,
            rate_limit_per_minute=3,
            rate_limit_per_day=50,
        ),
        "sql_query": ToolRestrictions(
            tool_name="sql_query",
            enabled=False,  # Disabled by default
            requires_approval=True,
            allowed_operations=["SELECT"],
            blocked_tables=["users", "secrets", "credentials"],
            rate_limit_per_minute=5,
        ),
        "search": ToolRestrictions(
            tool_name="search",
            enabled=True,
            rate_limit_per_minute=20,
            timeout_seconds=15,
        ),
    }

    def __init__(self, restrictions_file: Optional[str] = None):
        """Initialize restrictions manager.

        Args:
            restrictions_file: Optional YAML file with custom restrictions
        """
        self.global_restrictions = self.DEFAULT_RESTRICTIONS.copy()
        self.user_restrictions: Dict[str, Dict[str, ToolRestrictions]] = {}

        if restrictions_file:
            self.load_from_file(restrictions_file)

    def load_from_file(self, filepath: str) -> None:
        """Load restrictions from YAML file.

        Args:
            filepath: Path to YAML file
        """
        try:
            with open(filepath, "r") as f:
                data = yaml.safe_load(f)
                if data and "tools" in data:
                    for tool_name, restrictions in data["tools"].items():
                        self.global_restrictions[tool_name] = ToolRestrictions.from_dict(
                            {**restrictions, "tool_name": tool_name}
                        )
        except Exception as e:
            raise RuntimeError(f"Failed to load restrictions: {str(e)}")

    def get_restriction(self, tool_name: str, user_id: Optional[str] = None) -> Optional[ToolRestrictions]:
        """Get restrictions for a tool.

        Args:
            tool_name: Tool name
            user_id: Optional user (checks user-specific, then global)

        Returns:
            ToolRestrictions or None if not found
        """
        # Check user-specific restrictions
        if user_id and user_id in self.user_restrictions:
            if tool_name in self.user_restrictions[user_id]:
                return self.user_restrictions[user_id][tool_name]

        # Fall back to global
        return self.global_restrictions.get(tool_name)

    def is_tool_enabled(self, tool_name: str, user_id: Optional[str] = None) -> bool:
        """Check if tool is enabled.

        Args:
            tool_name: Tool name
            user_id: Optional user

        Returns:
            True if tool is enabled
        """
        restriction = self.get_restriction(tool_name, user_id)
        return restriction.enabled if restriction else False

    def set_user_restriction(self, user_id: str, tool_name: str, restriction: ToolRestrictions) -> None:
        """Set user-specific restriction.

        Args:
            user_id: User ID
            tool_name: Tool name
            restriction: ToolRestrictions object
        """
        if user_id not in self.user_restrictions:
            self.user_restrictions[user_id] = {}
        self.user_restrictions[user_id][tool_name] = restriction

    def set_global_restriction(self, tool_name: str, restriction: ToolRestrictions) -> None:
        """Set global restriction.

        Args:
            tool_name: Tool name
            restriction: ToolRestrictions object
        """
        self.global_restrictions[tool_name] = restriction

    def export_config(self, filepath: str) -> None:
        """Export current restrictions to YAML.

        Args:
            filepath: Output file path
        """
        config = {
            "tools": {
                name: restrictions.to_dict()
                for name, restrictions in self.global_restrictions.items()
            }
        }

        with open(filepath, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

    def get_all_restrictions(self) -> Dict[str, ToolRestrictions]:
        """Get all global restrictions."""
        return self.global_restrictions.copy()


# Example YAML structure for restrictions.yaml:
"""
tools:
  http_get:
    enabled: true
    allowed_domains:
      - api.example.com
      - data.provider.com
    blocked_domains:
      - localhost
      - 127.0.0.1
      - internal
    rate_limit_per_minute: 20
    timeout_seconds: 15

  python_eval:
    enabled: true
    requires_approval: true
    banned_imports:
      - os
      - sys
      - subprocess
      - socket
    max_execution_time_seconds: 5
    max_memory_mb: 50
    rate_limit_per_minute: 3

  sql_query:
    enabled: true
    requires_approval: true
    allowed_databases:
      - analytics
      - public
    allowed_operations:
      - SELECT
    blocked_tables:
      - users
      - secrets
      - credentials
    rate_limit_per_minute: 5
"""
