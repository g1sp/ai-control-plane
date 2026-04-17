"""Tests for tool registry system."""

import pytest
from src.tools.registry import ToolRegistry


class TestToolRegistry:
    """Test tool registry functionality."""

    def test_register_tool(self, tool_registry):
        """Test registering a new tool."""
        assert "http_get" in tool_registry.list_tools()
        assert "search" in tool_registry.list_tools()
        assert "python_eval" in tool_registry.list_tools()

    def test_get_tool_definitions(self, tool_registry):
        """Test retrieving tool definitions for Claude."""
        definitions = tool_registry.get_tool_definitions()
        assert len(definitions) == 3
        assert all("name" in d and "description" in d and "input_schema" in d for d in definitions)

    def test_get_tool(self, tool_registry):
        """Test getting single tool definition."""
        tool = tool_registry.get_tool("http_get")
        assert tool is not None
        assert tool["description"] == "Make HTTP GET request"
        assert "input_schema" in tool

    def test_tool_not_found(self, tool_registry):
        """Test getting non-existent tool."""
        tool = tool_registry.get_tool("nonexistent")
        assert tool is None

    def test_list_tools(self, tool_registry):
        """Test listing all tools."""
        tools = tool_registry.list_tools()
        assert len(tools) == 3
        assert "http_get" in tools
        assert "search" in tools
        assert "python_eval" in tools

    def test_requires_approval(self, tool_registry):
        """Test approval requirement check."""
        assert not tool_registry.requires_approval("http_get")
        assert not tool_registry.requires_approval("search")
        assert tool_registry.requires_approval("python_eval")

    @pytest.mark.asyncio
    async def test_call_search_tool(self, tool_registry):
        """Test calling search tool."""
        result = await tool_registry.call("search", query="test query", limit=3)
        assert isinstance(result, str)
        assert "Result" in result
        assert "test query" in result

    @pytest.mark.asyncio
    async def test_call_nonexistent_tool(self, tool_registry):
        """Test calling non-existent tool raises error."""
        with pytest.raises(ValueError) as exc_info:
            await tool_registry.call("nonexistent", arg="value")
        assert "not found" in str(exc_info.value)

    def test_registry_to_dict(self, tool_registry):
        """Test exporting registry as dictionary."""
        data = tool_registry.to_dict()
        assert "tools" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["tools"]) == 3

    def test_register_custom_tool(self):
        """Test registering a custom tool."""
        registry = ToolRegistry()

        async def custom_tool(param: str) -> str:
            return f"Custom result: {param}"

        registry.register(
            name="custom",
            func=custom_tool,
            description="Custom test tool",
            input_schema={"type": "object", "properties": {"param": {"type": "string"}}},
        )

        assert "custom" in registry.list_tools()
        tool = registry.get_tool("custom")
        assert tool["description"] == "Custom test tool"
