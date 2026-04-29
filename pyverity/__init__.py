"""pyverity — Python SDK for the Verity LLM prompt DSL."""

from .config import ProviderConfig, RuntimeConfig, default_config
from .effects import Cost, Fallible, Latent
from .exceptions import (
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
from .pipeline import Pipeline
from .prompt import RetrySpec, VerityPrompt, prompt, retry

__version__ = "0.1.0"

__all__ = [
    # Decorator
    "prompt",
    "retry",
    # Effects
    "Latent",
    "Fallible",
    "Cost",
    # Config
    "ProviderConfig",
    "RuntimeConfig",
    "default_config",
    # Types
    "VerityPrompt",
    "RetrySpec",
    "Pipeline",
    # Exceptions
    "VerityError",
    "HttpError",
    "NetworkError",
    "RequestTimeout",
    "ParseError",
    "ValidationFailed",
    "MaxRetriesExceeded",
    "ConfigError",
    "ContractViolation",
]
