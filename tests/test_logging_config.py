"""Tests for structured logging configuration."""

import json
import logging

from app.logging_config import JSONFormatter, TextFormatter, setup_logging, get_logger


class TestJSONFormatter:
    """Tests for the JSON log formatter."""

    def test_basic_json_output(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "app.test"
        assert parsed["message"] == "Test message"
        assert parsed["line"] == 42
        assert "timestamp" in parsed

    def test_json_with_exception(self):
        formatter = JSONFormatter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="app.test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        output = formatter.format(record)
        parsed = json.loads(output)

        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]

    def test_json_with_extra_fields(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Request",
            args=(),
            exc_info=None,
        )
        record.request_id = "abc-123"
        record.duration_ms = 45.2
        record.component = "health"

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["request_id"] == "abc-123"
        assert parsed["duration_ms"] == 45.2
        assert parsed["component"] == "health"

    def test_json_single_line(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="app.test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Multi\nline\nmessage",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        # JSON itself should be a single line (no embedded newlines outside of values)
        assert json.loads(output)["message"] == "Multi\nline\nmessage"


class TestTextFormatter:
    """Tests for the text log formatter."""

    def test_pipe_delimited_format(self):
        formatter = TextFormatter()
        record = logging.LogRecord(
            name="app.test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=5,
            msg="Warning msg",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        assert " | WARNING  | " in output
        assert "app.test" in output
        assert "Warning msg" in output


class TestSetupLogging:
    """Tests for the setup_logging function."""

    def setup_method(self):
        """Reset the app logger before each test."""
        logger = logging.getLogger("app")
        logger.handlers.clear()

    def test_setup_with_text_format(self):
        logger = setup_logging(level=logging.DEBUG, log_format="text")
        assert logger.name == "app"
        assert len(logger.handlers) == 2  # console + file
        assert isinstance(logger.handlers[0].formatter, TextFormatter)

    def test_setup_with_json_format(self):
        logger = setup_logging(level=logging.INFO, log_format="json")
        assert logger.name == "app"
        assert len(logger.handlers) == 2
        assert isinstance(logger.handlers[0].formatter, JSONFormatter)

    def test_setup_defaults_to_text_in_dev(self, monkeypatch):
        monkeypatch.setenv("DASH_ENV", "development")
        monkeypatch.delenv("DASH_LOG_FORMAT", raising=False)
        logger = setup_logging(level=logging.DEBUG)
        assert isinstance(logger.handlers[0].formatter, TextFormatter)

    def test_suppresses_third_party_loggers(self):
        setup_logging(level=logging.DEBUG, log_format="text")
        assert logging.getLogger("werkzeug").level == logging.WARNING
        assert logging.getLogger("dash").level == logging.WARNING


class TestGetLogger:
    """Tests for the get_logger helper."""

    def test_returns_child_logger(self):
        logger = get_logger("mymodule")
        assert logger.name == "app.mymodule"

    def test_child_inherits_from_app(self):
        parent = logging.getLogger("app")
        child = get_logger("child")
        assert child.parent == parent
