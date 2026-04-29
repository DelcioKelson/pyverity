# pyverity

[![CI](https://github.com/DelcioKelson/pyverity/actions/workflows/ci.yml/badge.svg)](https://github.com/DelcioKelson/pyverity/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pyverity)](https://pypi.org/project/pyverity/)
[![Python](https://img.shields.io/pypi/pyversions/pyverity)](https://pypi.org/project/pyverity/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Python SDK for the Verity LLM prompt DSL.

Define, type-check, and run prompts against any OpenAI-compatible API using Python decorators and type hints — no `.vrt` files needed.

## Installation

```bash
pip install pyverity
```

## Quick start

```python
import asyncio
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
    """
    Summarize the following text in one concise sentence.
    Count the total words in the original text.

    Text:
    {{text}}

    Return JSON: {"summary": "<sentence>", "word_count": <int>}
    """

async def main():
    result = await summarize(text="The quick brown fox jumps over the lazy dog.")
    print(result["summary"])

asyncio.run(main())
```

## Environment variables

| Variable          | Default                          | Description                      |
|-------------------|----------------------------------|----------------------------------|
| `VERITY_API_KEY`  | _(required)_                     | API key for your LLM provider    |
| `VERITY_API_BASE` | `https://api.openai.com/v1`      | OpenAI-compatible base URL       |
| `VERITY_MODEL`    | `gpt-4o-mini`                    | Default model                    |
| `VERITY_DEBUG`    | _(unset)_                        | Set to `1` to log prompts/responses |

## Feature map (Verity → pyverity)

| Verity DSL                          | pyverity                                      |
|-------------------------------------|-----------------------------------------------|
| `prompt name(x: string) -> T`       | `@prompt` decorator + type hints              |
| `{{var}}` template interpolation    | Same syntax in the docstring                  |
| `[effects: Latent(n), Fallible]`    | `effects=[Latent(n), Fallible]`               |
| `[model: "openai/gpt-4o"]`          | `model="openai/gpt-4o"`                       |
| `retry(n) with: "hint"`             | `retry=retry(n, with_hint="hint")`            |
| `requires: "expr"` / `ensures: "expr"` | `requires=["expr"]` / `ensures=["expr"]`  |
| `enum("a" \| "b")`                  | `Literal["a", "b"]`                           |
| `{ field: type }`                   | `TypedDict` or `dict`                         |
| `A \| B` union output               | `Union[A, B]`                                 |
| `pipeline_a >> pipeline_b`          | `prompt_a >> prompt_b` → `Pipeline`           |

## Pipeline composition

```python
from pyverity import prompt, Fallible

@prompt(effects=[Fallible])
def extract(text: str) -> dict:
    """Extract key facts from: {{text}}  →  {"title": "...", "score": 42}"""

@prompt(effects=[Fallible])
def rewrite(title: str, score: int) -> dict:
    """Rewrite "{{title}}" (score {{score}}) in simpler terms.  →  {"result": "..."}"""

pipeline = extract >> rewrite          # Pipeline object
result = await pipeline(text="...")    # extract output unpacked into rewrite
```

Dict outputs are automatically unpacked as keyword arguments into the next step.

## Output validation

Return types are validated against the parsed JSON from the LLM:

- `str` — returned as-is (no JSON parsing)
- `TypedDict` / `dict` — fields checked recursively
- `Literal["a", "b"]` — enum membership check
- `list[T]` — each element checked
- `Union[A, B]` / `Optional[X]` — first matching branch wins

A `ValidationFailed` exception (with a list of error messages) is raised on mismatch — and if `retry` is configured, the repair hint is automatically appended on the next attempt.

## Runtime config

Override the defaults programmatically:

```python
from pyverity import RuntimeConfig, ProviderConfig, prompt

cfg = RuntimeConfig(
    provider=ProviderConfig(
        api_key="sk-...",
        api_base="https://my-proxy.example.com/v1",
        model="claude-3-5-sonnet",
    ),
    debug=True,
    timeout_s=60.0,
)

@prompt(model="gpt-4o", config=cfg)
def my_prompt(x: str) -> str:
    """Answer: {{x}}"""
```
