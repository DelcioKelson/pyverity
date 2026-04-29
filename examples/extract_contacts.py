"""Structured entity extraction — pull contact details from messy free-form text.

Demonstrates:
- TypedDict return types for precise schema enforcement
- ``requires`` contracts to reject empty input early
- ``ensures`` contracts to guarantee the extracted name is non-empty
- ``retry`` with a repair hint for malformed JSON responses

Run:
    VERITY_API_KEY=sk-... python examples/extract_contacts.py
"""

import asyncio
from typing import TypedDict

from pyverity import Cost, Fallible, Latent, prompt, retry


class ContactInfo(TypedDict):
    name: str
    email: str
    phone: str
    company: str


@prompt(
    effects=[Latent(1.5), Fallible, Cost(0.001)],
    model="openai/gpt-4o-mini",
    retry=retry(
        3,
        with_hint=(
            "Return valid JSON with exactly these string fields: "
            "name, email, phone, company. "
            "Use an empty string for any field you cannot find."
        ),
    ),
    requires=["len(text.strip()) > 0"],
    ensures=["len(result['name']) > 0"],
)
def extract_contact(text: str) -> ContactInfo:
    """
    Extract contact information from the following text.

    Text:
    {{text}}

    Return JSON with exactly these fields (use "" for missing values):
    {
      "name":    "<full name>",
      "email":   "<email address>",
      "phone":   "<phone number>",
      "company": "<company or organisation>"
    }
    """


async def main() -> None:
    samples = [
        (
            "Hey, I'm Sarah Mitchell from Acme Corp. "
            "Reach me at sarah.mitchell@acme.io or call +1-555-0192."
        ),
        (
            "Please contact our sales rep John Okafor (jokafor@globex.com) "
            "for pricing. He can also be reached on 020 7946 0321."
        ),
        (
            "Dr. Priya Nair, priya@healthbridge.org — "
            "no phone on file, works at HealthBridge Solutions."
        ),
    ]

    for raw in samples:
        contact = await extract_contact(text=raw)
        print(f"Name:    {contact['name']}")
        print(f"Email:   {contact['email']}")
        print(f"Phone:   {contact['phone']}")
        print(f"Company: {contact['company']}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
