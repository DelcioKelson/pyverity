"""Core prompt decorator and supporting types."""

from __future__ import annotations

import inspect
import re
from collections.abc import Callable
from typing import Any, get_type_hints

from .config import RuntimeConfig, default_config
from .exceptions import (
    ConfigError,
    ContractViolation,
    MaxRetriesExceeded,
)
from .pipeline import Pipeline
from .runtime import call_llm
from .validation import validate_output

_TEMPLATE_VAR = re.compile(r"\{\{(\w+)\}\}")


def _render(template: str, kwargs: dict[str, Any]) -> str:
    """Substitute ``{{var}}`` placeholders in *template* with values from *kwargs*."""

    def _sub(m: re.Match) -> str:
        key = m.group(1)
        if key not in kwargs:
            raise KeyError(
                f"Template variable '{{{{{key}}}}}' not provided. "
                f"Available: {list(kwargs.keys())}"
            )
        return str(kwargs[key])

    return _TEMPLATE_VAR.sub(_sub, template)


# ---------------------------------------------------------------------------
#  Retry specification
# ---------------------------------------------------------------------------


class RetrySpec:
    """Retry configuration attached to a prompt."""

    def __init__(self, max_attempts: int, *, with_hint: str = "") -> None:
        if max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        self.max_attempts = max_attempts
        self.with_hint = with_hint

    def __repr__(self) -> str:
        hint = f", with_hint={self.with_hint!r}" if self.with_hint else ""
        return f"RetrySpec({self.max_attempts}{hint})"


def retry(max_attempts: int, *, with_hint: str = "") -> RetrySpec:
    """Create a :class:`RetrySpec`.

    Args:
        max_attempts: Total number of LLM calls before raising
                      :class:`~pyverity.MaxRetriesExceeded`.
        with_hint:    Repair hint appended to the prompt on every retry
                      (equivalent to Verity's ``retry(n) with: "..."``)
    """
    return RetrySpec(max_attempts, with_hint=with_hint)


# ---------------------------------------------------------------------------
#  VerityPrompt
# ---------------------------------------------------------------------------


class VerityPrompt:
    """A callable, composable Verity prompt.

    Created by the :func:`prompt` decorator. Supports ``>>`` for pipeline
    composition with other :class:`VerityPrompt` instances or
    :class:`~pyverity.Pipeline` objects.
    """

    def __init__(
        self,
        fn: Callable,
        *,
        template: str,
        return_type: Any,
        effects: list,
        model: str | None,
        retry_spec: RetrySpec | None,
        requires: list[str],
        ensures: list[str],
        config: RuntimeConfig | None,
    ) -> None:
        self._fn = fn
        self._template = template
        self._return_type = return_type
        self._effects = effects
        self._model = model
        self._retry_spec = retry_spec
        self._requires = requires
        self._ensures = ensures
        self._config = config

        # Preserve function metadata
        self.__name__ = fn.__name__
        self.__qualname__ = fn.__qualname__
        self.__doc__ = fn.__doc__
        self.__wrapped__ = fn

    # ------------------------------------------------------------------

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        sig = inspect.signature(self._fn)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        kw = dict(bound.arguments)

        # ---- requires contracts ----
        # NOTE: expressions are developer-supplied source code, not external input.
        for expr in self._requires:
            try:
                ok = eval(expr, {}, kw)  # noqa: S307
            except Exception as exc:
                raise ContractViolation(
                    f"requires expression raised an error — {expr!r}: {exc}"
                ) from exc
            if not ok:
                raise ContractViolation(f"requires: {expr}")

        rendered = _render(self._template, kw)

        cfg = self._config or default_config()
        if not cfg.provider.api_key:
            raise ConfigError(
                "VERITY_API_KEY is not set. "
                "Set the environment variable or pass a RuntimeConfig with api_key."
            )

        # Resolve model: "provider/model" → strip provider prefix
        if self._model:
            effective_model = (
                self._model.split("/", 1)[1] if "/" in self._model else self._model
            )
        else:
            effective_model = cfg.provider.model

        max_attempts = (
            self._retry_spec.max_attempts if self._retry_spec else cfg.default_retry
        )
        repair_hint = self._retry_spec.with_hint if self._retry_spec else ""

        last_error: Exception | None = None
        for attempt in range(max_attempts):
            prompt_text = rendered
            if attempt > 0 and repair_hint:
                prompt_text = f"{rendered}\n\nRepair hint: {repair_hint}"

            try:
                raw = await call_llm(prompt_text, model=effective_model, cfg=cfg)
                result = validate_output(raw, self._return_type)

                # ---- ensures contracts ----
                for expr in self._ensures:
                    check_ns = {**kw, "result": result}
                    try:
                        ok = eval(expr, {}, check_ns)  # noqa: S307
                    except Exception as exc:
                        raise ContractViolation(
                            f"ensures expression raised an error — {expr!r}: {exc}"
                        ) from exc
                    if not ok:
                        raise ContractViolation(f"ensures: {expr}")

                return result

            except ContractViolation:
                raise
            except Exception as exc:
                last_error = exc
                if cfg.debug:
                    print(
                        f"[verity] attempt {attempt + 1}/{max_attempts} failed: {exc}"
                    )

        raise MaxRetriesExceeded(
            f"All {max_attempts} attempt(s) failed. Last error: {last_error}"
        )

    def __rshift__(self, other: Any) -> Pipeline:
        return Pipeline(self, other)

    def __repr__(self) -> str:
        return f"<VerityPrompt '{self.__name__}'>"


# ---------------------------------------------------------------------------
#  @prompt decorator
# ---------------------------------------------------------------------------


def prompt(
    *,
    effects: list | None = None,
    model: str | None = None,
    retry: RetrySpec | None = None,
    requires: list[str] | None = None,
    ensures: list[str] | None = None,
    config: RuntimeConfig | None = None,
) -> Callable[[Callable], VerityPrompt]:
    """Decorator that turns a Python function into a Verity prompt.

    The function body is unused at runtime — its **docstring** is the prompt
    template. Use ``{{var}}`` to interpolate input parameters by name.

    Args:
        effects:  List of effect annotations (:class:`~pyverity.Latent`,
                  :data:`~pyverity.Fallible`, :class:`~pyverity.Cost`).
                  Informational only — not enforced at runtime.
        model:    Model identifier, e.g. ``"gpt-4o"`` or
                  ``"openai/gpt-4o-mini"``. Overrides ``VERITY_MODEL``.
        retry:    A :class:`RetrySpec` created with :func:`retry`.
        requires: List of Python expressions (as strings) evaluated before
                  calling the LLM. Raise :class:`~pyverity.ContractViolation`
                  on failure. Input parameters are available by name.
        ensures:  List of Python expressions evaluated after a successful LLM
                  call. ``result`` holds the parsed output.
        config:   Explicit :class:`~pyverity.RuntimeConfig`. Defaults to
                  reading from environment variables.

    Example::

        from typing import TypedDict
        from pyverity import prompt, retry, Latent, Fallible

        class Summary(TypedDict):
            summary: str
            word_count: int

        @prompt(
            effects=[Latent(2.0), Fallible],
            model="openai/gpt-4o-mini",
            retry=retry(3, with_hint="Return valid JSON only."),
            requires=["len(text) > 0"],
            ensures=["result['word_count'] > 0"],
        )
        def summarize(text: str) -> Summary:
            '''
            Summarize the following text in one sentence.
            Count the total words in the original text.

            Text:
            {{text}}

            Return JSON: {"summary": "<sentence>", "word_count": <int>}
            '''
    """

    def decorator(fn: Callable) -> VerityPrompt:
        template = inspect.getdoc(fn) or ""
        hints = get_type_hints(fn)
        return_type = hints.get("return", Any)

        return VerityPrompt(
            fn,
            template=template,
            return_type=return_type,
            effects=effects or [],
            model=model,
            retry_spec=retry,
            requires=requires or [],
            ensures=ensures or [],
            config=config,
        )

    return decorator
