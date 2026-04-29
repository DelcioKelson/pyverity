"""Quiz generator — produce multiple-choice questions from any topic text.

Demonstrates:
- Returning a list of TypedDicts via a wrapper TypedDict
- Numeric ``ensures`` contracts (e.g. correct number of questions generated)
- ``requires`` contracts to validate caller-supplied arguments
- ``Cost`` and ``Latent`` effects for budgeting awareness
- Standalone prompts (no pipeline) used in a simple async loop

Run:
    VERITY_API_KEY=sk-... python examples/quiz_generator.py
"""

import asyncio
from typing import TypedDict

from pyverity import Cost, Fallible, Latent, prompt, retry


class QuizQuestion(TypedDict):
    question: str
    options: list[str]   # exactly 4 items
    answer: str          # must be one of the options


class QuizOutput(TypedDict):
    questions: list[QuizQuestion]


@prompt(
    effects=[Latent(3.0), Fallible, Cost(0.003)],
    model="openai/gpt-4o-mini",
    retry=retry(
        3,
        with_hint=(
            "Return valid JSON. Each question must have exactly 4 options "
            "and an answer that is one of those options."
        ),
    ),
    requires=[
        "len(topic.strip()) > 0",
        "1 <= num_questions <= 10",
    ],
    ensures=[
        "len(result['questions']) == num_questions",
        "all(len(q['options']) == 4 for q in result['questions'])",
        "all(q['answer'] in q['options'] for q in result['questions'])",
    ],
)
def generate_quiz(topic: str, num_questions: int) -> QuizOutput:
    """
    Generate {{num_questions}} multiple-choice quiz questions about: {{topic}}.

    Rules:
    - Each question must have exactly 4 answer options (A, B, C, D as plain strings).
    - The "answer" field must be the full text of the correct option (not just a letter).
    - Questions should test understanding, not just recall.

    Return JSON:
    {
      "questions": [
        {
          "question": "<question text>",
          "options":  ["<A>", "<B>", "<C>", "<D>"],
          "answer":   "<correct option text>"
        }
      ]
    }
    """


def _print_quiz(topic: str, quiz: QuizOutput) -> None:
    print(f"=== Quiz: {topic} ===\n")
    for i, q in enumerate(quiz["questions"], 1):
        print(f"Q{i}. {q['question']}")
        for letter, opt in zip("ABCD", q["options"]):
            marker = " ✓" if opt == q["answer"] else ""
            print(f"    {letter}) {opt}{marker}")
        print()


async def main() -> None:
    topics = [
        ("Python type hints", 3),
        ("The water cycle", 2),
    ]

    for topic, n in topics:
        quiz = await generate_quiz(topic=topic, num_questions=n)
        _print_quiz(topic, quiz)


if __name__ == "__main__":
    asyncio.run(main())
