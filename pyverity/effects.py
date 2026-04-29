from dataclasses import dataclass


@dataclass
class Latent:
    """Annotates a prompt as having an expected latency (in seconds)."""

    seconds: float | None = None

    def __repr__(self) -> str:
        return f"Latent({self.seconds})" if self.seconds is not None else "Latent"


class _FallibleSingleton:
    """Singleton sentinel — marks a prompt as fallible (may fail and need retry)."""

    _instance: "_FallibleSingleton | None" = None

    def __new__(cls) -> "_FallibleSingleton":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "Fallible"


Fallible = _FallibleSingleton()


@dataclass
class Cost:
    """Annotates a prompt with an estimated cost per call (in USD)."""

    max_usd: float | None = None

    def __repr__(self) -> str:
        return f"Cost({self.max_usd})" if self.max_usd is not None else "Cost"
