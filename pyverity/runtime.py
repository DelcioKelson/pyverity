import httpx

from .config import RuntimeConfig
from .exceptions import HttpError, NetworkError, ParseError, RequestTimeout


async def call_llm(prompt: str, *, model: str, cfg: RuntimeConfig) -> str:
    """Call an OpenAI-compatible chat completion endpoint.

    Args:
        prompt:  The fully rendered prompt text.
        model:   The model identifier (bare name, no provider prefix).
        cfg:     Runtime configuration (API key, base URL, timeout).

    Returns:
        The raw text content from the model's first choice.

    Raises:
        RequestTimeout: The HTTP request timed out.
        NetworkError:   A network-level error occurred.
        HttpError:      The API returned a non-200 status code.
        ParseError:     The response JSON was not in the expected shape.
    """
    if cfg.debug:
        print(f"[verity] >>> prompt:\n{prompt}\n")

    headers = {
        "Authorization": f"Bearer {cfg.provider.api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        async with httpx.AsyncClient(timeout=cfg.timeout_s) as client:
            resp = await client.post(
                f"{cfg.provider.api_base}/chat/completions",
                headers=headers,
                json=body,
            )
    except httpx.TimeoutException as exc:
        raise RequestTimeout("LLM request timed out") from exc
    except httpx.NetworkError as exc:
        raise NetworkError(str(exc)) from exc

    if resp.status_code != 200:
        raise HttpError(resp.status_code, resp.text)

    try:
        data = resp.json()
        content: str = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise ParseError(f"Unexpected response structure: {exc}") from exc

    if cfg.debug:
        print(f"[verity] <<< response:\n{content}\n")

    return content
