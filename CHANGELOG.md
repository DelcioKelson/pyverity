# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-29

### Added
- `@prompt` decorator — turns a typed Python function into a Verity prompt
- `{{var}}` template interpolation via the function docstring
- Structured output validation against Python type annotations (`TypedDict`, `Literal`, `list[T]`, primitives, `Optional`)
- JSON extraction from raw LLM responses (handles markdown fences)
- `effects=[Latent(n), Fallible, Cost(n)]` annotations
- `retry(n, with_hint="...")` — configurable retry with repair hints
- `requires` / `ensures` contract expressions evaluated before and after LLM calls
- `Pipeline` via `>>` operator — automatic dict-unpacking between steps
- `RuntimeConfig` / `ProviderConfig` for programmatic configuration
- `default_config()` — reads `VERITY_API_KEY`, `VERITY_API_BASE`, `VERITY_MODEL`, `VERITY_DEBUG` from environment
- `httpx`-based async HTTP client for OpenAI-compatible APIs
- Full exception hierarchy: `VerityError`, `HttpError`, `NetworkError`, `RequestTimeout`, `ParseError`, `ValidationFailed`, `MaxRetriesExceeded`, `ConfigError`, `ContractViolation`
- PEP 561 `py.typed` marker for inline type checking support

[0.1.0]: https://github.com/DelcioKelson/pyverity/releases/tag/v0.1.0
