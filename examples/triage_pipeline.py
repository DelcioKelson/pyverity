"""Three-step support-ticket triage pipeline.

Demonstrates:
- Pipeline composition across three prompts with ``>>``
- Passing structured output from one step as keyword args to the next
- ``Literal`` types for controlled-vocabulary fields
- ``ensures`` contracts at each stage

Pipeline:
    classify_ticket        →  { category, priority }
         ↓
    draft_response         →  { response, estimated_minutes }
         ↓
    translate_response     →  { translated }

Run:
    VERITY_API_KEY=sk-... python examples/triage_pipeline.py
"""

import asyncio
from typing import Literal, TypedDict

from pyverity import Fallible, Latent, prompt, retry


# ---------------------------------------------------------------------------
#  Step 1 — classify the incoming ticket
# ---------------------------------------------------------------------------


class TicketClassification(TypedDict):
    category: str
    priority: str


@prompt(
    effects=[Fallible],
    retry=retry(2, with_hint='Return JSON: {"category": "...", "priority": "..."}'),
    ensures=[
        "result['priority'] in ('low', 'medium', 'high', 'critical')",
        "len(result['category']) > 0",
    ],
)
def classify_ticket(ticket: str) -> TicketClassification:
    """
    Classify the following customer support ticket.

    Ticket:
    {{ticket}}

    Choose a category (e.g. "billing", "technical", "account", "general") and
    a priority from: low, medium, high, critical.

    Return JSON:
    {
      "category": "<category>",
      "priority": "<low|medium|high|critical>"
    }
    """


# ---------------------------------------------------------------------------
#  Step 2 — draft a first-response using the classification
# ---------------------------------------------------------------------------


class DraftedResponse(TypedDict):
    response: str
    estimated_minutes: int


@prompt(
    effects=[Latent(2.0), Fallible],
    retry=retry(2),
    requires=["len(category) > 0", "priority in ('low', 'medium', 'high', 'critical')"],
    ensures=["len(result['response']) > 20", "result['estimated_minutes'] > 0"],
)
def draft_response(category: str, priority: str) -> DraftedResponse:
    """
    You are a customer support agent. Draft a polite, professional first
    response for a {{priority}}-priority {{category}} ticket.

    The response should:
    - Acknowledge the issue category
    - Give a realistic resolution time estimate in minutes
    - Be concise (2-3 sentences)

    Return JSON:
    {
      "response":           "<draft reply text>",
      "estimated_minutes":  <integer>
    }
    """


# ---------------------------------------------------------------------------
#  Step 3 — translate the draft into the customer's language
# ---------------------------------------------------------------------------


class TranslatedResponse(TypedDict):
    translated: str


@prompt(
    effects=[Fallible],
    retry=retry(2),
    ensures=["len(result['translated']) > 0"],
)
def translate_response(response: str, estimated_minutes: int) -> TranslatedResponse:
    """
    Translate the following support response to Spanish.
    Keep the estimated resolution time ({{estimated_minutes}} minutes) in the text.

    Response to translate:
    {{response}}

    Return JSON: {"translated": "<Spanish translation>"}
    """


# ---------------------------------------------------------------------------
#  Three-step pipeline
# ---------------------------------------------------------------------------

triage_pipeline = classify_ticket >> draft_response >> translate_response


async def main() -> None:
    tickets = [
        "I was charged twice for my subscription this month. Please refund ASAP.",
        "The app crashes every time I try to upload a file larger than 10 MB.",
        "How do I change the email address on my account?",
    ]

    for ticket in tickets:
        print(f"Ticket:  {ticket}")
        result = await triage_pipeline(ticket=ticket)
        print(f"Spanish: {result['translated']}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
