import os
from dataclasses import dataclass, field


@dataclass
class ProviderConfig:
    api_base: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"


@dataclass
class RuntimeConfig:
    provider: ProviderConfig = field(default_factory=ProviderConfig)
    default_retry: int = 2
    debug: bool = False
    timeout_s: float = 30.0


def default_config() -> RuntimeConfig:
    """Build a RuntimeConfig from environment variables.

    Variables:
        VERITY_API_KEY   — required for LLM calls
        VERITY_API_BASE  — defaults to https://api.openai.com/v1
        VERITY_MODEL     — defaults to gpt-4o-mini
        VERITY_DEBUG     — set to "1" to print prompts and responses
    """
    return RuntimeConfig(
        provider=ProviderConfig(
            api_key=os.environ.get("VERITY_API_KEY", ""),
            api_base=os.environ.get("VERITY_API_BASE", "https://api.openai.com/v1"),
            model=os.environ.get("VERITY_MODEL", "gpt-4o-mini"),
        ),
        debug=os.environ.get("VERITY_DEBUG", "") == "1",
    )
