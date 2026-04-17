import json
import asyncio
from typing import Callable, Dict, List, Any, Optional
from pydantic import BaseModel


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    requires_approval: bool = False


class ToolRegistry:
    """Central registry for agent tools. Tools are callable functions with JSON schemas."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._executors: Dict[str, Callable] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str,
        input_schema: Dict[str, Any],
        requires_approval: bool = False,
    ) -> None:
        """Register a new tool.

        Args:
            name: Tool identifier
            func: Async callable that executes the tool
            description: Human-readable description
            input_schema: JSON schema for input validation
            requires_approval: Whether tool calls need approval
        """
        self._tools[name] = {
            "description": description,
            "input_schema": input_schema,
            "requires_approval": requires_approval,
        }
        self._executors[name] = func

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions formatted for Claude's tool_use feature."""
        definitions = []
        for name, tool_info in self._tools.items():
            definitions.append({
                "name": name,
                "description": tool_info["description"],
                "input_schema": tool_info["input_schema"],
            })
        return definitions

    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a single tool definition."""
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        """Get all registered tool names."""
        return list(self._tools.keys())

    def requires_approval(self, tool_name: str) -> bool:
        """Check if tool requires approval."""
        tool = self._tools.get(tool_name)
        return tool["requires_approval"] if tool else False

    async def call(self, tool_name: str, **kwargs) -> str:
        """Execute a tool.

        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool arguments

        Returns:
            String result from tool execution

        Raises:
            ValueError: If tool not found
            Exception: If execution fails
        """
        if tool_name not in self._executors:
            raise ValueError(f"Tool '{tool_name}' not found")

        executor = self._executors[tool_name]

        try:
            result = executor(**kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            return str(result)
        except Exception as e:
            raise Exception(f"Tool '{tool_name}' execution failed: {str(e)}")

    def to_dict(self) -> Dict[str, Any]:
        """Export registry as dictionary."""
        return {
            "tools": self.get_tool_definitions(),
            "total": len(self._tools),
        }
