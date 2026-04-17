"""Tool input validation and sanitization."""

import re
import json
from typing import Any, Dict, Optional
from urllib.parse import urlparse, urlsplit
from jsonschema import validate, ValidationError


class ToolValidator:
    """Base validator for tool inputs."""

    @staticmethod
    def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """Validate data against JSON schema.

        Args:
            data: Input data to validate
            schema: JSON schema

        Raises:
            ValueError: If validation fails
        """
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            raise ValueError(f"Schema validation failed: {e.message}")

    @staticmethod
    def validate_string_length(value: str, min_len: int = 1, max_len: int = 5000) -> None:
        """Validate string length."""
        if not isinstance(value, str):
            raise ValueError("Value must be a string")
        if len(value) < min_len:
            raise ValueError(f"String too short (min {min_len} chars)")
        if len(value) > max_len:
            raise ValueError(f"String too long (max {max_len} chars)")


class HttpValidator(ToolValidator):
    """Validate HTTP tool inputs."""

    BLOCKED_DOMAINS = {
        "localhost", "127.0.0.1", "0.0.0.0",
        "internal", "192.168", "10.0", "172.16",
        "169.254",  # Link-local
        "::1", "[::1]",  # IPv6 localhost
    }

    DANGEROUS_HEADERS = {
        "authorization", "cookie", "x-api-key", "x-auth-token"
    }

    @classmethod
    def validate_url(cls, url: str, allowed_domains: Optional[list] = None) -> None:
        """Validate HTTP URL for safety.

        Args:
            url: URL to validate
            allowed_domains: Optional whitelist of allowed domains

        Raises:
            ValueError: If URL is unsafe
        """
        cls.validate_string_length(url, max_len=2000)

        try:
            parsed = urlparse(url)
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")

        # Check scheme
        if parsed.scheme not in ["http", "https"]:
            raise ValueError(f"Invalid scheme: {parsed.scheme}")

        # Check domain
        domain = parsed.netloc.lower()
        if not domain:
            raise ValueError("URL must include a domain")

        # Whitelist check
        if allowed_domains:
            is_allowed = any(allowed_domain in domain for allowed_domain in allowed_domains)
            if not is_allowed:
                raise ValueError(f"Domain not in whitelist: {domain}")
        else:
            # Default: block known unsafe domains
            for blocked in cls.BLOCKED_DOMAINS:
                if blocked in domain:
                    raise ValueError(f"Blocked domain: {domain}")

    @classmethod
    def validate_headers(cls, headers: Optional[Dict[str, str]]) -> None:
        """Validate HTTP headers for safety.

        Args:
            headers: Headers dictionary

        Raises:
            ValueError: If headers contain dangerous values
        """
        if not headers:
            return

        if not isinstance(headers, dict):
            raise ValueError("Headers must be a dictionary")

        if len(headers) > 20:
            raise ValueError("Too many headers (max 20)")

        for key, value in headers.items():
            # Check header name length
            if len(key) > 100:
                raise ValueError(f"Header name too long: {key}")

            # Check for dangerous headers
            if key.lower() in cls.DANGEROUS_HEADERS:
                raise ValueError(f"Dangerous header not allowed: {key}")

            # Check header value length
            if not isinstance(value, str) or len(value) > 1000:
                raise ValueError(f"Header value too long: {key}")

    @classmethod
    def validate_http_get_args(cls, url: str, headers: Optional[Dict[str, str]] = None) -> None:
        """Validate HTTP GET arguments."""
        cls.validate_url(url)
        cls.validate_headers(headers)

    @classmethod
    def validate_http_post_args(
        cls, url: str, body: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None
    ) -> None:
        """Validate HTTP POST arguments."""
        cls.validate_url(url)
        cls.validate_headers(headers)

        if body is not None:
            if not isinstance(body, dict):
                raise ValueError("Body must be a dictionary")
            if len(json.dumps(body)) > 10000:
                raise ValueError("Request body too large (max 10KB)")


class PythonValidator(ToolValidator):
    """Validate Python code execution."""

    BANNED_MODULES = {
        "os", "sys", "subprocess", "importlib", "importlib_metadata",
        "pkgutil", "modulefinder", "runpy", "imp", "imp_module"
    }

    BANNED_BUILTINS = {
        "__import__", "eval", "exec", "compile", "globals", "locals",
        "vars", "dir", "__builtins__"
    }

    BANNED_PATTERNS = [
        r"import\s+",  # import statements
        r"from\s+.+\s+import",  # from X import Y
        r"__",  # Double underscore (private access)
        r"\.\.\/",  # Directory traversal
        r"open\s*\(",  # File operations
        r"socket\.",  # Network operations
    ]

    @classmethod
    def validate_code(cls, code: str, safe_mode: bool = True) -> None:
        """Validate Python code for safety.

        Args:
            code: Python code to validate
            safe_mode: Enable strict validation

        Raises:
            ValueError: If code contains dangerous patterns
        """
        cls.validate_string_length(code, min_len=1, max_len=2000)

        if not isinstance(code, str):
            raise ValueError("Code must be a string")

        code_lower = code.lower()

        # Check banned modules
        for module in cls.BANNED_MODULES:
            if f"{module} " in code_lower or f" {module}" in code_lower:
                raise ValueError(f"Module import not allowed: {module}")

        # Check banned builtins
        for builtin in cls.BANNED_BUILTINS:
            if builtin in code_lower:
                raise ValueError(f"Builtin not allowed: {builtin}")

        # Check patterns
        if safe_mode:
            for pattern in cls.BANNED_PATTERNS:
                if re.search(pattern, code, re.IGNORECASE):
                    raise ValueError(f"Dangerous pattern detected: {pattern}")

    @classmethod
    def validate_python_eval_args(cls, code: str, safe_mode: bool = True) -> None:
        """Validate Python eval arguments."""
        cls.validate_code(code, safe_mode=safe_mode)


class SearchValidator(ToolValidator):
    """Validate search tool inputs."""

    @classmethod
    def validate_search_args(cls, query: str, limit: Optional[int] = None) -> None:
        """Validate search arguments.

        Args:
            query: Search query
            limit: Max results

        Raises:
            ValueError: If arguments invalid
        """
        cls.validate_string_length(query, min_len=1, max_len=500)

        if limit is not None:
            if not isinstance(limit, int):
                raise ValueError("Limit must be an integer")
            if limit < 1 or limit > 100:
                raise ValueError("Limit must be between 1 and 100")


class SqlValidator(ToolValidator):
    """Validate SQL query execution (for future use)."""

    ALLOWED_KEYWORDS = {"select", "where", "from", "join", "group by", "order by", "limit"}
    DANGEROUS_KEYWORDS = {"drop", "delete", "truncate", "alter", "update", "insert", "exec", "execute"}

    @classmethod
    def validate_query(cls, query: str, allowed_operations: Optional[list] = None) -> None:
        """Validate SQL query for safety.

        Args:
            query: SQL query
            allowed_operations: List of allowed operations (select, etc)

        Raises:
            ValueError: If query is dangerous
        """
        cls.validate_string_length(query, min_len=5, max_len=5000)

        query_lower = query.upper()

        # Check for dangerous keywords
        for keyword in cls.DANGEROUS_KEYWORDS:
            if keyword.upper() in query_lower:
                raise ValueError(f"Dangerous operation not allowed: {keyword}")

        # Whitelist check
        if allowed_operations:
            is_allowed = any(op.upper() in query_lower for op in allowed_operations)
            if not is_allowed:
                raise ValueError(f"Operation not in whitelist")

    @classmethod
    def validate_sql_query_args(cls, query: str, database: str, allowed_operations: Optional[list] = None) -> None:
        """Validate SQL query execution arguments."""
        cls.validate_query(query, allowed_operations=allowed_operations)
        cls.validate_string_length(database, min_len=1, max_len=100)
