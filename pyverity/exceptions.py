class VerityError(Exception):
    """Base class for all Verity errors."""


class HttpError(VerityError):
    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"HTTP {status_code}: {body[:200]}")


class NetworkError(VerityError):
    pass


class RequestTimeout(VerityError):
    pass


class ParseError(VerityError):
    pass


class ValidationFailed(VerityError):
    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("Validation failed:\n" + "\n".join(f"  {e}" for e in errors))


class MaxRetriesExceeded(VerityError):
    pass


class ConfigError(VerityError):
    pass


class ContractViolation(VerityError):
    pass
