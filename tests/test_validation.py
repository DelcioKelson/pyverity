"""Tests for pyverity.validation."""

from typing import TypedDict

import pytest

from pyverity.exceptions import ParseError, ValidationFailed
from pyverity.validation import validate_output


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class Point(TypedDict):
    x: float
    y: float


class Named(TypedDict):
    name: str
    value: int


# ---------------------------------------------------------------------------
# str return type
# ---------------------------------------------------------------------------

class TestStringOutput:
    def test_returns_raw_text(self):
        result = validate_output("hello world", str)
        assert result == "hello world"

    def test_does_not_parse_json(self):
        result = validate_output('{"key": "val"}', str)
        assert result == '{"key": "val"}'


# ---------------------------------------------------------------------------
# dict / TypedDict
# ---------------------------------------------------------------------------

class TestDictOutput:
    def test_valid_typed_dict(self):
        result = validate_output('{"name": "Alice", "value": 42}', Named)
        assert result == {"name": "Alice", "value": 42}

    def test_json_in_markdown_fence(self):
        raw = '```json\n{"name": "Bob", "value": 7}\n```'
        result = validate_output(raw, Named)
        assert result["name"] == "Bob"

    def test_missing_field_raises_validation_failed(self):
        with pytest.raises(ValidationFailed) as exc_info:
            validate_output('{"name": "Alice"}', Named)
        assert "value" in str(exc_info.value).lower() or "Missing" in str(exc_info.value)

    def test_wrong_type_raises_validation_failed(self):
        with pytest.raises(ValidationFailed):
            validate_output('{"name": 123, "value": 42}', Named)

    def test_invalid_json_raises_parse_error(self):
        with pytest.raises(ParseError):
            validate_output("not json at all", Named)


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

class TestListOutput:
    def test_valid_list_of_strings(self):
        result = validate_output('["a", "b", "c"]', list[str])
        assert result == ["a", "b", "c"]

    def test_invalid_item_type_raises_validation_failed(self):
        with pytest.raises(ValidationFailed):
            validate_output('[1, 2, 3]', list[str])


# ---------------------------------------------------------------------------
# Literal
# ---------------------------------------------------------------------------

class TestLiteralOutput:
    def test_valid_literal(self):
        from typing import Literal
        result = validate_output('"yes"', Literal["yes", "no"])
        assert result == "yes"

    def test_invalid_literal_raises_validation_failed(self):
        from typing import Literal
        with pytest.raises(ValidationFailed):
            validate_output('"maybe"', Literal["yes", "no"])


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------

class TestPrimitiveOutput:
    def test_int(self):
        result = validate_output("42", int)
        assert result == 42

    def test_bool_not_accepted_as_int(self):
        with pytest.raises(ValidationFailed):
            validate_output("true", int)

    def test_float_accepts_int_value(self):
        result = validate_output("3", float)
        assert result == 3.0

    def test_bool(self):
        result = validate_output("true", bool)
        assert result is True

    def test_none(self):
        result = validate_output("null", type(None))
        assert result is None
