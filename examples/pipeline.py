"""Pipeline composition example — pyverity equivalent of bad_pipeline.vrt
(but with matching types so the pipeline is valid).

Run:
    VERITY_API_KEY=sk-... python examples/pipeline.py
"""

import asyncio
from typing import TypedDict

from pyverity import Fallible, prompt, retry


class ExtractOutput(TypedDict):
    title: str
    score: int


class SummarizeOutput(TypedDict):
    summary: str


@prompt(effects=[Fallible], retry=retry(2))
def extract(text: str) -> ExtractOutput:
    """
    Extract the title and a relevance score (0-100) from the following text.

    Text:
    {{text}}

    Return JSON: {"title": "<title>", "score": <int>}
    """


@prompt(effects=[Fallible], retry=retry(2))
def summarize(title: str, score: int) -> SummarizeOutput:
    """
    Write a one-sentence summary for an article titled "{{title}}"
    with a relevance score of {{score}}.

    Return JSON: {"summary": "<one sentence>"}
    """


# Pipeline: extract >> summarize
# extract's output  { title: str, score: int }
# is unpacked as keyword args into summarize(title=..., score=...)
pipeline = extract >> summarize


async def main() -> None:
    result = await pipeline(text=(
        "OpenAI releases GPT-5 with unprecedented reasoning capabilities, "
        "scoring 95% on the MMLU benchmark."
    ))
    print(result["summary"])


if __name__ == "__main__":
    asyncio.run(main())
