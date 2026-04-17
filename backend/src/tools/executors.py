"""Built-in tool executors for agent use."""

import httpx
import json
import asyncio
import re
from typing import Dict, Any, Optional
from urllib.parse import urlparse


class HttpToolExecutor:
    """Execute HTTP requests safely."""

    BLOCKED_DOMAINS = ["localhost", "127.0.0.1", "0.0.0.0", "internal", "192.168"]
    TIMEOUT = 10

    @staticmethod
    def validate_url(url: str) -> None:
        """Validate URL for safety."""
        try:
            parsed = urlparse(url)
            if not parsed.scheme or parsed.scheme not in ["http", "https"]:
                raise ValueError(f"Invalid URL scheme: {parsed.scheme}")

            domain = parsed.netloc.lower()
            for blocked in HttpToolExecutor.BLOCKED_DOMAINS:
                if blocked in domain:
                    raise ValueError(f"Blocked domain: {domain}")
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")

    @staticmethod
    async def http_get(url: str, headers: Optional[Dict[str, str]] = None) -> str:
        """Make an HTTP GET request."""
        HttpToolExecutor.validate_url(url)

        headers = headers or {}
        # Security: limit headers
        safe_headers = {k: v for k, v in headers.items() if len(k) < 100 and len(v) < 1000}

        try:
            async with httpx.AsyncClient(timeout=HttpToolExecutor.TIMEOUT) as client:
                response = await client.get(url, headers=safe_headers)
                response.raise_for_status()
                return response.text[:10000]  # Limit response size
        except Exception as e:
            raise Exception(f"HTTP GET failed: {str(e)}")

    @staticmethod
    async def http_post(
        url: str, body: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None
    ) -> str:
        """Make an HTTP POST request."""
        HttpToolExecutor.validate_url(url)

        headers = headers or {}
        safe_headers = {k: v for k, v in headers.items() if len(k) < 100 and len(v) < 1000}
        body = body or {}

        try:
            async with httpx.AsyncClient(timeout=HttpToolExecutor.TIMEOUT) as client:
                response = await client.post(url, json=body, headers=safe_headers)
                response.raise_for_status()
                return response.text[:10000]
        except Exception as e:
            raise Exception(f"HTTP POST failed: {str(e)}")


class PythonToolExecutor:
    """Execute Python code in a sandboxed environment."""

    # Banned imports/modules for security
    BANNED_MODULES = {"os", "subprocess", "sys", "importlib", "eval", "exec", "compile", "__import__"}

    @staticmethod
    def validate_code(code: str) -> None:
        """Check code for dangerous patterns."""
        banned_keywords = {"__", "import ", "from ", "exec", "eval", "open", "socket", "subprocess"}

        code_lower = code.lower()
        for keyword in banned_keywords:
            if keyword in code_lower:
                raise ValueError(f"Forbidden keyword: {keyword}")

        if len(code) > 2000:
            raise ValueError("Code too long (max 2000 chars)")

    @staticmethod
    async def python_eval(code: str, safe_mode: bool = True) -> str:
        """Execute Python code safely."""
        if safe_mode:
            PythonToolExecutor.validate_code(code)

        try:
            # Run in timeout to prevent infinite loops
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, lambda: eval(code, {"__builtins__": {}})
                ),
                timeout=5.0
            )
            return str(result)
        except asyncio.TimeoutError:
            raise Exception("Code execution timeout (5 seconds)")
        except Exception as e:
            raise Exception(f"Code execution failed: {str(e)}")


class SearchToolExecutor:
    """Simple search tool - can be connected to real search APIs later."""

    @staticmethod
    async def search(query: str, limit: int = 5) -> str:
        """Search for information (simulated)."""
        if not query or len(query) > 500:
            raise ValueError("Invalid search query")

        # Placeholder - in production, connect to real search API
        results = [
            f"Result {i+1}: Found reference to '{query}' in database {i+1}"
            for i in range(min(limit, 5))
        ]
        return "\n".join(results)
