"""Tests for pyverity.exceptions."""

import pytest

from pyverity.exceptions import (
    ConfigError,
    ContractViolation,
    HttpError,
    MaxRetriesExceeded,
    NetworkError,
    ParseError,
    RequestTimeout,
    ValidationFailed,
    VerityError,
)


class TestVerityError:
    def test_is_exception(self):
        err = VerityError("base")
        assert isinstance(err, Exception)
        assert str(err) == "base"


class TestHttpError:
    def test_message_includes_status_and_body(self):
        err = HttpError(429, "Rate limit exceeded")
        assert "429" in str(err)
        assert "Rate limit exceeded" in str(err)
        assert err.status_code == 429
        assert err.body == "Rate limit exceeded"

    def test_body_truncated_to_200_chars(self):
        long_body = "x" * 300
        err = HttpError(500, long_body)
        assert len(str(err)) < 300

    def test_is_verity_error(self):
        assert isinstance(HttpError(400, "bad"), VerityError)


class TestValidationFailed:
    def test_stores_errors_list(self):
        errors = ["field 'name' missing", "field 'age' wrong type"]
        err = ValidationFailed(errors)
        assert err.errors == errors
        assert "field 'name' missing" in str(err)
        assert "field 'age' wrong type" in str(err)

    def test_is_verity_error(self):
        assert isinstance(ValidationFailed([]), VerityError)


class TestSubclasses:
    @pytest.mark.parametrize("cls", [
        NetworkError,
        RequestTimeout,
        ParseError,
        MaxRetriesExceeded,
        ConfigError,
        ContractViolation,
    ])
    def test_subclass_of_verity_error(self, cls):
        err = cls("test")
        assert isinstance(err, VerityError)
        assert str(err) == "test"
