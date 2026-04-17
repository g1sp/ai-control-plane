"""Tests for tool executors."""

import pytest
from src.tools.executors import HttpToolExecutor, PythonToolExecutor, SearchToolExecutor


class TestHttpToolExecutor:
    """Test HTTP tool executor."""

    def test_validate_url_valid(self):
        """Test validating valid URL."""
        HttpToolExecutor.validate_url("https://example.com/api")
        HttpToolExecutor.validate_url("http://example.com")

    def test_validate_url_invalid_scheme(self):
        """Test rejecting invalid URL scheme."""
        with pytest.raises(ValueError) as exc_info:
            HttpToolExecutor.validate_url("ftp://example.com")
        assert "Invalid URL scheme" in str(exc_info.value)

    def test_validate_url_blocked_localhost(self):
        """Test blocking localhost URLs."""
        with pytest.raises(ValueError) as exc_info:
            HttpToolExecutor.validate_url("http://localhost:8000")
        assert "Blocked domain" in str(exc_info.value)

    def test_validate_url_blocked_internal(self):
        """Test blocking internal network."""
        with pytest.raises(ValueError) as exc_info:
            HttpToolExecutor.validate_url("http://internal.company.com")
        assert "Blocked domain" in str(exc_info.value)

    def test_validate_url_blocked_private_ip(self):
        """Test blocking private IPs."""
        with pytest.raises(ValueError) as exc_info:
            HttpToolExecutor.validate_url("http://192.168.1.1")
        assert "Blocked domain" in str(exc_info.value)

    def test_validate_url_empty(self):
        """Test rejecting empty URL."""
        with pytest.raises(ValueError):
            HttpToolExecutor.validate_url("")


class TestPythonToolExecutor:
    """Test Python tool executor."""

    def test_validate_code_safe(self):
        """Test validating safe code."""
        PythonToolExecutor.validate_code("x = 1 + 2")
        PythonToolExecutor.validate_code("result = len([1, 2, 3])")

    def test_validate_code_import_blocked(self):
        """Test blocking import statements."""
        with pytest.raises(ValueError) as exc_info:
            PythonToolExecutor.validate_code("import os")
        assert "Forbidden keyword" in str(exc_info.value)

    def test_validate_code_subprocess_blocked(self):
        """Test blocking subprocess."""
        with pytest.raises(ValueError) as exc_info:
            PythonToolExecutor.validate_code("import subprocess")
        assert "Forbidden keyword" in str(exc_info.value)

    def test_validate_code_file_open_blocked(self):
        """Test blocking file operations."""
        with pytest.raises(ValueError) as exc_info:
            PythonToolExecutor.validate_code("f = open('/etc/passwd')")
        assert "Forbidden keyword" in str(exc_info.value)

    def test_validate_code_exec_blocked(self):
        """Test blocking exec."""
        with pytest.raises(ValueError) as exc_info:
            PythonToolExecutor.validate_code("exec('x = 1')")
        assert "Forbidden keyword" in str(exc_info.value)

    def test_validate_code_too_long(self):
        """Test rejecting overly long code."""
        long_code = "x = 1\n" * 500  # Create very long code
        with pytest.raises(ValueError) as exc_info:
            PythonToolExecutor.validate_code(long_code)
        assert "too long" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_python_eval_valid(self):
        """Test evaluating valid Python."""
        result = await PythonToolExecutor.python_eval("2 + 2")
        assert result == "4"

    @pytest.mark.asyncio
    async def test_python_eval_list(self):
        """Test evaluating list operations."""
        result = await PythonToolExecutor.python_eval("[1, 2, 3]")
        assert "[1, 2, 3]" in result

    @pytest.mark.asyncio
    async def test_python_eval_safe_mode_blocks_import(self):
        """Test safe mode blocks imports."""
        with pytest.raises(Exception) as exc_info:
            await PythonToolExecutor.python_eval("import os", safe_mode=True)
        assert "Forbidden keyword" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_python_eval_syntax_error(self):
        """Test handling syntax errors."""
        with pytest.raises(Exception) as exc_info:
            await PythonToolExecutor.python_eval("x = ", safe_mode=False)
        assert "Code execution failed" in str(exc_info.value)


class TestSearchToolExecutor:
    """Test search tool executor."""

    @pytest.mark.asyncio
    async def test_search_valid(self):
        """Test valid search."""
        result = await SearchToolExecutor.search("python", limit=3)
        assert isinstance(result, str)
        assert "python" in result.lower()
        assert "Result" in result

    @pytest.mark.asyncio
    async def test_search_default_limit(self):
        """Test search with default limit."""
        result = await SearchToolExecutor.search("test")
        assert isinstance(result, str)
        lines = result.split("\n")
        assert len(lines) <= 5

    @pytest.mark.asyncio
    async def test_search_empty_query(self):
        """Test rejecting empty query."""
        with pytest.raises(ValueError):
            await SearchToolExecutor.search("")

    @pytest.mark.asyncio
    async def test_search_query_too_long(self):
        """Test rejecting overly long query."""
        long_query = "x" * 1000
        with pytest.raises(ValueError):
            await SearchToolExecutor.search(long_query)
