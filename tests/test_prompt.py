"""Tests for pyverity.prompt — decorator, RetrySpec, and VerityPrompt."""

from typing import TypedDict

import pytest
import respx
import httpx

from pyverity import prompt, retry
from pyverity.config import ProviderConfig, RuntimeConfig
from pyverity.exceptions import (
    ConfigError,
    ContractViolation,
    MaxRetriesExceeded,
)
from pyverity.pipeline import Pipeline
from pyverity.prompt import RetrySpec


# ---------------------------------------------------------------------------
# Test config (avoids touching real env vars)
# ---------------------------------------------------------------------------

_CFG = RuntimeConfig(
    provider=ProviderConfig(api_key="sk-test", api_base="https://api.openai.com/v1"),
)


def _mock_response(content: str) -> dict:
    return {
        "choices": [{"message": {"content": content}}]
    }


# ---------------------------------------------------------------------------
# RetrySpec
# ---------------------------------------------------------------------------

class TestRetrySpec:
    def test_valid(self):
        spec = RetrySpec(3, with_hint="Try again")
        assert spec.max_attempts == 3
        assert spec.with_hint == "Try again"

    def test_max_attempts_must_be_positive(self):
        with pytest.raises(ValueError):
            RetrySpec(0)

    def test_repr_without_hint(self):
        assert repr(RetrySpec(2)) == "RetrySpec(2)"

    def test_repr_with_hint(self):
        assert "with_hint" in repr(RetrySpec(2, with_hint="fix it"))


def test_retry_helper():
    spec = retry(3, with_hint="be precise")
    assert isinstance(spec, RetrySpec)
    assert spec.max_attempts == 3
    assert spec.with_hint == "be precise"


# ---------------------------------------------------------------------------
# @prompt decorator — metadata preservation
# ---------------------------------------------------------------------------

class TestPromptDecorator:
    def test_preserves_name(self):
        @prompt(config=_CFG)
        def my_func(text: str) -> str:
            """Return the text: {{text}}"""

        assert my_func.__name__ == "my_func"

    def test_preserves_docstring(self):
        @prompt(config=_CFG)
        def greet(name: str) -> str:
            """Hello, {{name}}!"""

        assert "{{name}}" in greet.__doc__

    def test_rshift_returns_pipeline(self):
        @prompt(config=_CFG)
        def step_a(x: str) -> str:
            """Process: {{x}}"""

        @prompt(config=_CFG)
        def step_b(x: str) -> str:
            """Continue: {{x}}"""

        result = step_a >> step_b
        assert isinstance(result, Pipeline)

    def test_repr(self):
        @prompt(config=_CFG)
        def my_prompt(x: str) -> str:
            """Do something: {{x}}"""

        assert "my_prompt" in repr(my_prompt)


# ---------------------------------------------------------------------------
# Requires / ensures contract violations
# ---------------------------------------------------------------------------

class TestContracts:
    async def test_requires_violation_raises(self):
        @prompt(requires=["len(text) > 10"], config=_CFG)
        def check(text: str) -> str:
            """Say: {{text}}"""

        with pytest.raises(ContractViolation, match="requires"):
            await check(text="hi")

    async def test_requires_bad_expression_raises(self):
        @prompt(requires=["undefined_var > 0"], config=_CFG)
        def check(text: str) -> str:
            """Say: {{text}}"""

        with pytest.raises(ContractViolation, match="raised an error"):
            await check(text="hello")

    @respx.mock
    async def test_ensures_violation_raises(self):
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=_mock_response("5"))
        )

        @prompt(ensures=["result > 10"], retry=retry(1), config=_CFG)
        def check(x: int) -> int:
            """Return a number: {{x}}"""

        with pytest.raises(ContractViolation, match="ensures"):
            await check(x=1)


# ---------------------------------------------------------------------------
# ConfigError when no API key
# ---------------------------------------------------------------------------

class TestConfigError:
    async def test_raises_when_no_api_key(self, monkeypatch):
        monkeypatch.delenv("VERITY_API_KEY", raising=False)

        @prompt()
        def no_key(x: str) -> str:
            """Say: {{x}}"""

        with pytest.raises(ConfigError, match="VERITY_API_KEY"):
            await no_key(x="test")


# ---------------------------------------------------------------------------
# Successful LLM call (mocked)
# ---------------------------------------------------------------------------

class TestSuccessfulCall:
    @respx.mock
    async def test_returns_string(self):
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=_mock_response("hello world"))
        )

        @prompt(config=_CFG)
        def greet(name: str) -> str:
            """Say hello to {{name}}."""

        result = await greet(name="Alice")
        assert result == "hello world"

    @respx.mock
    async def test_returns_parsed_json(self):
        class Out(TypedDict):
            msg: str

        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=_mock_response('{"msg": "hi"}'))
        )

        @prompt(config=_CFG)
        def greet(name: str) -> Out:
            """Greet {{name}}. Return JSON: {"msg": "<text>"}"""

        result = await greet(name="Bob")
        assert result == {"msg": "hi"}

    @respx.mock
    async def test_strips_provider_prefix_from_model(self):
        captured = {}

        async def capture_request(request):
            import json
            body = json.loads(request.content)
            captured["model"] = body["model"]
            return httpx.Response(200, json=_mock_response("ok"))

        respx.post("https://api.openai.com/v1/chat/completions").mock(
            side_effect=capture_request
        )

        @prompt(model="openai/gpt-4o", config=_CFG)
        def my_fn(x: str) -> str:
            """Do: {{x}}"""

        await my_fn(x="test")
        assert captured["model"] == "gpt-4o"


# ---------------------------------------------------------------------------
# Retry behaviour (mocked)
# ---------------------------------------------------------------------------

class TestRetry:
    @respx.mock
    async def test_retries_on_parse_error(self):
        route = respx.post("https://api.openai.com/v1/chat/completions")
        route.side_effect = [
            httpx.Response(200, json=_mock_response("not json")),
            httpx.Response(200, json=_mock_response('{"val": 1}')),
        ]

        @prompt(retry=retry(2), config=_CFG)
        def fn(x: str) -> dict:
            """Return JSON: {{x}}"""

        result = await fn(x="test")
        assert result == {"val": 1}

    @respx.mock
    async def test_raises_max_retries_exceeded(self):
        respx.post("https://api.openai.com/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=_mock_response("not json"))
        )

        @prompt(retry=retry(2), config=_CFG)
        def fn(x: str) -> dict:
            """Return JSON: {{x}}"""

        with pytest.raises(MaxRetriesExceeded):
            await fn(x="test")
