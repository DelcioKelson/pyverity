import json
import re
from typing import Any, Literal, Union, get_args, get_origin, get_type_hints

from .exceptions import ParseError, ValidationFailed

# ---------------------------------------------------------------------------
#  JSON extraction
# ---------------------------------------------------------------------------

_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.MULTILINE)


def _extract_json(text: str) -> str:
    """Pull a JSON block out of raw LLM text (handles markdown fences)."""
    fence = _FENCE_RE.search(text)
    if fence:
        return fence.group(1).strip()

    for open_ch, close_ch in [('{', '}'), ('[', ']')]:
        start = text.find(open_ch)
        end = text.rfind(close_ch)
        if start != -1 and end > start:
            return text[start:end + 1]

    return text


# ---------------------------------------------------------------------------
#  Type validation
# ---------------------------------------------------------------------------

def _is_literal_type(tp: Any) -> bool:
    return get_origin(tp) is Literal


def _validate(value: Any, tp: Any, path: str) -> list[str]:
    """Recursively validate *value* against Python type annotation *tp*.

    Returns a (possibly empty) list of human-readable error strings.
    """
    # Any / unknown — always valid
    if tp is Any:
        return []

    origin = get_origin(tp)
    args = get_args(tp)

    # Union (includes Optional[X] == Union[X, None])
    if origin is Union:
        non_none = [a for a in args if a is not type(None)]
        # None value is allowed if NoneType is in the union
        if value is None and type(None) in args:
            return []
        branch_errors = [_validate(value, a, path) for a in non_none]
        if any(len(errs) == 0 for errs in branch_errors):
            return []
        # Report errors from the first branch
        return branch_errors[0] if branch_errors else []

    # Literal — enum-like check
    if _is_literal_type(tp):
        if value not in args:
            return [f"At '{path}': expected one of {list(args)}, got {value!r}"]
        return []

    # dict / TypedDict
    if tp is dict or origin is dict or (
        isinstance(tp, type) and issubclass(tp, dict)
    ):
        if not isinstance(value, dict):
            return [f"At '{path}': expected dict, got {type(value).__name__}"]

        # For TypedDict and generic dict[K, V] — validate fields/values
        try:
            hints = get_type_hints(tp)
        except Exception:
            hints = getattr(tp, "__annotations__", {})

        errors: list[str] = []
        if hints:
            for field_name, field_tp in hints.items():
                child = f"{path}.{field_name}" if path else field_name
                if field_name not in value:
                    errors.append(f"Missing field '{field_name}' at '{path or 'root'}'")
                else:
                    errors.extend(_validate(value[field_name], field_tp, child))
        elif origin is dict and len(args) == 2:
            # dict[K, V] — validate all values
            _val_tp = args[1]
            for k, v in value.items():
                errors.extend(_validate(v, _val_tp, f"{path}[{k!r}]"))
        return errors

    # list
    if origin is list:
        if not isinstance(value, list):
            return [f"At '{path}': expected list, got {type(value).__name__}"]
        item_tp = args[0] if args else Any
        errors = []
        for i, item in enumerate(value):
            errors.extend(_validate(item, item_tp, f"{path}[{i}]"))
        return errors

    # Primitive types
    if tp is str:
        return [] if isinstance(value, str) else [
            f"At '{path}': expected str, got {type(value).__name__}"
        ]
    if tp is int:
        # Accept int but not bool (bool is a subclass of int in Python)
        if isinstance(value, bool) or not isinstance(value, int):
            return [f"At '{path}': expected int, got {type(value).__name__}"]
        return []
    if tp is float:
        return [] if isinstance(value, (int, float)) and not isinstance(value, bool) else [
            f"At '{path}': expected float, got {type(value).__name__}"
        ]
    if tp is bool:
        return [] if isinstance(value, bool) else [
            f"At '{path}': expected bool, got {type(value).__name__}"
        ]

    return []


# ---------------------------------------------------------------------------
#  Public entry point
# ---------------------------------------------------------------------------

def validate_output(raw: str, return_type: Any) -> Any:
    """Parse and validate LLM *raw* output against a Python type annotation.

    Args:
        raw:         Raw text from the LLM.
        return_type: The Python type annotation declared on the prompt function.

    Returns:
        The parsed (and validated) Python value.

    Raises:
        ParseError:       The text could not be parsed as JSON when required.
        ValidationFailed: The parsed value does not match *return_type*.
    """
    text = raw.strip()

    # Plain string output — no JSON parsing needed
    if return_type is str:
        return text

    # Literal types — LLM may return the value as plain text
    if _is_literal_type(return_type):
        json_candidate = _extract_json(text)
        try:
            value = json.loads(json_candidate)
        except json.JSONDecodeError:
            # Try the stripped text directly (e.g. "positive\n")
            value = text.strip().strip('"').strip("'")

        errors = _validate(value, return_type, "")
        if errors:
            raise ValidationFailed(errors)
        return value

    # All other types — expect JSON
    json_text = _extract_json(text)
    try:
        value = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ParseError(
            f"Could not parse LLM output as JSON: {text[:300]}"
        ) from exc

    errors = _validate(value, return_type, "")
    if errors:
        raise ValidationFailed(errors)

    return value
