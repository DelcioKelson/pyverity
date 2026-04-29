"""pyverity equivalent of examples/summarize.vrt

Run:
    VERITY_API_KEY=sk-... python examples/summarize.py
"""

import asyncio
from typing import Literal, TypedDict

from pyverity import Cost, Fallible, Latent, prompt, retry


# ---------------------------------------------------------------------------
#  Output types (TypedDict → TRecord, Literal → TEnum)
# ---------------------------------------------------------------------------


class SummarizeOutput(TypedDict):
    summary: str
    word_count: int


# ---------------------------------------------------------------------------
#  Prompts
# ---------------------------------------------------------------------------


@prompt(
    effects=[Latent(2.0), Fallible, Cost(0.002)],
    model="openai/gpt-4o-mini",
    retry=retry(3, with_hint=(
        "Ensure the response is valid JSON with 'summary' (string)"
        " and 'word_count' (int) fields."
    )),
    requires=["len(text) > 0"],
    ensures=["result['word_count'] > 0"],
)
def summarize(text: str) -> SummarizeOutput:
    """
    Summarize the following text in one concise sentence.
    Also count the total words in the original text.

    Text:
    {{text}}

    Return JSON with exactly these fields:
    {
      "summary": "<one sentence summary>",
      "word_count": <integer number of words>
    }
    """


@prompt(
    effects=[Fallible],
    retry=retry(2),
    ensures=["result in ['positive', 'negative', 'neutral']"],
)
def classify(text: str) -> Literal["positive", "negative", "neutral"]:
    """
    Classify the sentiment of the following text as one of:
    positive, negative, or neutral.

    Text:
    {{text}}

    Reply with only the single word: positive, negative, or neutral.
    """


@prompt(
    effects=[Latent(1.5), Fallible],
)
def translate(text: str, target_lang: str) -> dict:
    """
    Translate the following text to {{target_lang}}.

    Text:
    {{text}}

    Return JSON: {"translated": "<translation>"}
    """


# ---------------------------------------------------------------------------
#  Demo
# ---------------------------------------------------------------------------


async def main() -> None:
    sample = "The quick brown fox jumps over the lazy dog."

    result = await summarize(text=sample)
    print(f"Summary:    {result['summary']}")
    print(f"Word count: {result['word_count']}")
    print()

    sentiment = await classify(text="I absolutely love this product!")
    print(f"Sentiment:  {sentiment}")
    print()

    translation = await translate(text=sample, target_lang="French")
    print(f"French:     {translation['translated']}")


if __name__ == "__main__":
    asyncio.run(main())
