"""Tests for tool input validators."""

import pytest
from src.tools.validators import HttpValidator, PythonValidator, SearchValidator, SqlValidator


class TestHttpValidator:
    """Test HTTP validator."""

    def test_validate_url_valid_https(self):
        """Test valid HTTPS URL."""
        HttpValidator.validate_url("https://api.example.com/v1/data")

    def test_validate_url_valid_http(self):
        """Test valid HTTP URL."""
        HttpValidator.validate_url("http://example.com")

    def test_validate_url_invalid_scheme(self):
        """Test rejecting invalid scheme."""
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_url("ftp://example.com")
        assert "scheme" in str(exc.value).lower()

    def test_validate_url_localhost(self):
        """Test blocking localhost."""
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_url("http://localhost:8000")
        assert "blocked" in str(exc.value).lower()

    def test_validate_url_127_0_0_1(self):
        """Test blocking 127.0.0.1."""
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_url("http://127.0.0.1:3000")
        assert "blocked" in str(exc.value).lower()

    def test_validate_url_internal(self):
        """Test blocking internal domains."""
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_url("http://internal.company.com")
        assert "blocked" in str(exc.value).lower()

    def test_validate_url_private_ip_192(self):
        """Test blocking private IP 192.168."""
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_url("http://192.168.1.1")
        assert "blocked" in str(exc.value).lower()

    def test_validate_url_private_ip_10(self):
        """Test blocking private IP 10."""
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_url("http://10.0.0.1")
        assert "blocked" in str(exc.value).lower()

    def test_validate_url_too_long(self):
        """Test rejecting overly long URL."""
        long_url = "http://example.com/" + "a" * 2000
        with pytest.raises(ValueError):
            HttpValidator.validate_url(long_url)

    def test_validate_url_empty(self):
        """Test rejecting empty URL."""
        with pytest.raises(ValueError):
            HttpValidator.validate_url("")

    def test_validate_url_no_scheme(self):
        """Test rejecting URL without scheme."""
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_url("example.com")
        assert "scheme" in str(exc.value).lower()

    def test_validate_url_whitelist(self):
        """Test URL whitelist."""
        # Allowed domain
        HttpValidator.validate_url(
            "https://api.example.com",
            allowed_domains=["example.com"]
        )

        # Not allowed
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_url(
                "https://other.com",
                allowed_domains=["example.com"]
            )
        assert "whitelist" in str(exc.value).lower()

    def test_validate_headers_valid(self):
        """Test valid headers."""
        HttpValidator.validate_headers({
            "User-Agent": "MyApp/1.0",
            "Accept": "application/json"
        })

    def test_validate_headers_dangerous_authorization(self):
        """Test blocking authorization header."""
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_headers({"Authorization": "Bearer token"})
        assert "dangerous" in str(exc.value).lower()

    def test_validate_headers_dangerous_cookie(self):
        """Test blocking cookie header."""
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_headers({"Cookie": "session=123"})
        assert "dangerous" in str(exc.value).lower()

    def test_validate_headers_dangerous_api_key(self):
        """Test blocking API key header."""
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_headers({"X-API-Key": "secret"})
        assert "dangerous" in str(exc.value).lower()

    def test_validate_headers_too_many(self):
        """Test rejecting too many headers."""
        headers = {f"Header-{i}": "value" for i in range(25)}
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_headers(headers)
        assert "too many" in str(exc.value).lower()

    def test_validate_headers_long_value(self):
        """Test rejecting overly long header value."""
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_headers({"Custom": "x" * 2000})
        assert "too long" in str(exc.value).lower()

    def test_validate_http_get_args(self):
        """Test validating HTTP GET arguments."""
        HttpValidator.validate_http_get_args(
            "https://api.example.com/data",
            headers={"Accept": "application/json"}
        )

    def test_validate_http_post_args_valid(self):
        """Test validating valid HTTP POST arguments."""
        HttpValidator.validate_http_post_args(
            "https://api.example.com/submit",
            body={"key": "value"},
            headers={"Content-Type": "application/json"}
        )

    def test_validate_http_post_args_body_not_dict(self):
        """Test rejecting non-dict body."""
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_http_post_args(
                "https://api.example.com",
                body="not a dict"
            )
        assert "dictionary" in str(exc.value).lower()

    def test_validate_http_post_args_body_too_large(self):
        """Test rejecting overly large body."""
        large_body = {f"key_{i}": "x" * 1000 for i in range(100)}
        with pytest.raises(ValueError) as exc:
            HttpValidator.validate_http_post_args(
                "https://api.example.com",
                body=large_body
            )
        assert "too large" in str(exc.value).lower()


class TestPythonValidator:
    """Test Python validator."""

    def test_validate_code_safe(self):
        """Test validating safe code."""
        PythonValidator.validate_code("x = 2 + 2")
        PythonValidator.validate_code("result = [1, 2, 3]")
        PythonValidator.validate_code("print('hello')")

    def test_validate_code_import_blocked(self):
        """Test blocking import statements."""
        with pytest.raises(ValueError) as exc:
            PythonValidator.validate_code("import os")
        assert "forbidden" in str(exc.value).lower()

    def test_validate_code_from_import_blocked(self):
        """Test blocking from import."""
        with pytest.raises(ValueError) as exc:
            PythonValidator.validate_code("from os import system")
        assert "forbidden" in str(exc.value).lower()

    def test_validate_code_subprocess_blocked(self):
        """Test blocking subprocess."""
        with pytest.raises(ValueError) as exc:
            PythonValidator.validate_code("import subprocess")
        assert "forbidden" in str(exc.value).lower()

    def test_validate_code_double_underscore_blocked(self):
        """Test blocking double underscore."""
        with pytest.raises(ValueError) as exc:
            PythonValidator.validate_code("x.__dict__")
        assert "dangerous" in str(exc.value).lower()

    def test_validate_code_eval_blocked(self):
        """Test blocking eval."""
        with pytest.raises(ValueError) as exc:
            PythonValidator.validate_code("eval('code')")
        assert "forbidden" in str(exc.value).lower()

    def test_validate_code_exec_blocked(self):
        """Test blocking exec."""
        with pytest.raises(ValueError) as exc:
            PythonValidator.validate_code("exec('code')")
        assert "forbidden" in str(exc.value).lower()

    def test_validate_code_open_blocked(self):
        """Test blocking file open."""
        with pytest.raises(ValueError) as exc:
            PythonValidator.validate_code("open('/etc/passwd')")
        assert "dangerous" in str(exc.value).lower()

    def test_validate_code_socket_blocked(self):
        """Test blocking socket operations."""
        with pytest.raises(ValueError) as exc:
            PythonValidator.validate_code("socket.connect()")
        assert "dangerous" in str(exc.value).lower()

    def test_validate_code_too_long(self):
        """Test rejecting overly long code."""
        long_code = "x = 1\n" * 500
        with pytest.raises(ValueError) as exc:
            PythonValidator.validate_code(long_code)
        assert "too long" in str(exc.value).lower()

    def test_validate_code_empty(self):
        """Test rejecting empty code."""
        with pytest.raises(ValueError):
            PythonValidator.validate_code("")

    def test_validate_code_safe_mode_off(self):
        """Test unsafe code with safe mode off."""
        # Should raise because patterns match
        with pytest.raises(ValueError):
            PythonValidator.validate_code("import sys", safe_mode=True)

    def test_validate_python_eval_args(self):
        """Test validating python_eval arguments."""
        PythonValidator.validate_python_eval_args("2 + 2")
        PythonValidator.validate_python_eval_args("[1, 2, 3]")


class TestSearchValidator:
    """Test search validator."""

    def test_validate_search_args_valid(self):
        """Test valid search arguments."""
        SearchValidator.validate_search_args("test query", limit=10)
        SearchValidator.validate_search_args("python programming")

    def test_validate_search_args_no_limit(self):
        """Test search without limit."""
        SearchValidator.validate_search_args("query")

    def test_validate_search_args_empty_query(self):
        """Test rejecting empty query."""
        with pytest.raises(ValueError):
            SearchValidator.validate_search_args("")

    def test_validate_search_args_query_too_long(self):
        """Test rejecting overly long query."""
        long_query = "x" * 1000
        with pytest.raises(ValueError) as exc:
            SearchValidator.validate_search_args(long_query)
        assert "too long" in str(exc.value).lower()

    def test_validate_search_args_limit_not_int(self):
        """Test rejecting non-int limit."""
        with pytest.raises(ValueError) as exc:
            SearchValidator.validate_search_args("query", limit="10")
        assert "integer" in str(exc.value).lower()

    def test_validate_search_args_limit_too_low(self):
        """Test rejecting limit < 1."""
        with pytest.raises(ValueError) as exc:
            SearchValidator.validate_search_args("query", limit=0)
        assert "between" in str(exc.value).lower()

    def test_validate_search_args_limit_too_high(self):
        """Test rejecting limit > 100."""
        with pytest.raises(ValueError) as exc:
            SearchValidator.validate_search_args("query", limit=200)
        assert "between" in str(exc.value).lower()


class TestSqlValidator:
    """Test SQL validator."""

    def test_validate_query_select(self):
        """Test validating SELECT query."""
        SqlValidator.validate_query("SELECT * FROM users")
        SqlValidator.validate_query("SELECT id, name FROM products WHERE price > 100")

    def test_validate_query_drop_blocked(self):
        """Test blocking DROP queries."""
        with pytest.raises(ValueError) as exc:
            SqlValidator.validate_query("DROP TABLE users")
        assert "dangerous" in str(exc.value).lower()

    def test_validate_query_delete_blocked(self):
        """Test blocking DELETE queries."""
        with pytest.raises(ValueError) as exc:
            SqlValidator.validate_query("DELETE FROM users")
        assert "dangerous" in str(exc.value).lower()

    def test_validate_query_truncate_blocked(self):
        """Test blocking TRUNCATE queries."""
        with pytest.raises(ValueError) as exc:
            SqlValidator.validate_query("TRUNCATE TABLE users")
        assert "dangerous" in str(exc.value).lower()

    def test_validate_query_alter_blocked(self):
        """Test blocking ALTER queries."""
        with pytest.raises(ValueError) as exc:
            SqlValidator.validate_query("ALTER TABLE users ADD COLUMN")
        assert "dangerous" in str(exc.value).lower()

    def test_validate_query_update_blocked(self):
        """Test blocking UPDATE queries."""
        with pytest.raises(ValueError) as exc:
            SqlValidator.validate_query("UPDATE users SET admin=1")
        assert "dangerous" in str(exc.value).lower()

    def test_validate_query_whitelist(self):
        """Test query whitelist."""
        # Allowed operation
        SqlValidator.validate_query(
            "SELECT * FROM data",
            allowed_operations=["SELECT"]
        )

        # Not allowed
        with pytest.raises(ValueError) as exc:
            SqlValidator.validate_query(
                "DELETE FROM data",
                allowed_operations=["SELECT"]
            )
        assert "not in whitelist" in str(exc.value).lower()

    def test_validate_query_too_long(self):
        """Test rejecting overly long query."""
        long_query = "SELECT * FROM table WHERE x=" + "y" * 10000
        with pytest.raises(ValueError):
            SqlValidator.validate_query(long_query)

    def test_validate_query_empty(self):
        """Test rejecting empty query."""
        with pytest.raises(ValueError):
            SqlValidator.validate_query("")

    def test_validate_sql_query_args(self):
        """Test validating SQL query execution arguments."""
        SqlValidator.validate_sql_query_args(
            "SELECT * FROM users",
            "analytics",
            allowed_operations=["SELECT"]
        )
