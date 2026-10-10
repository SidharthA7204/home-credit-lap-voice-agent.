"""AI-assisted interpretation of unclear voice transcripts.

This module does not silently save or normalize customer answers. It proposes a
candidate only; the dialog layer must ask the customer to confirm it first.
It deliberately contains no pronunciation/typo dictionary.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)

# These are the valid business concepts, not lists of accepted misspellings.
# Keep these values aligned with app/models.py and the LAP business rules.
FIELD_OPTIONS: dict[str, dict[str, str]] = {
    "property_type": {
        "residential": "A home, flat, apartment, villa, or other residential property",
        "commercial": "A shop, office, showroom, or other commercial property",
        "industrial": "A factory, warehouse, or other industrial property",
        "agricultural": "Agricultural or farmland property (not eligible)",
    },
    "ownership": {
        "sole": "Owned by the customer alone",
        "joint": "Owned jointly with another person",
    },
    "occupation": {
        "salaried": "Employed and receiving a salary",
        "self_employed": "Self-employed or running a business",
    },
    "income_mode": {
        "bank": "Income received through a bank account",
        "cash": "Income received in cash",
    },
    "documents_available": {
        "true": "Original property documents are available",
        "false": "Original property documents are not available",
    },
    "existing_loan": {
        "true": "The customer already has an existing loan against the property",
        "false": "The customer does not have an existing loan against the property",
    },
}

SYSTEM_PROMPT = """You interpret a speech-to-text transcript in a loan qualification call.
The transcript may contain Indian-English pronunciation, broken English, partial
words, or speech-recognition mistakes. Infer meaning from the current question
and conversation context, but do not invent information.

Return JSON only with this schema:
{
  "status": "clear" | "candidate" | "unclear",
  "candidate_value": string | null,
  "candidate_display": string | null,
  "alternatives": [string],
  "reason": string
}

Rules:
- If the transcript clearly and directly expresses one valid answer, use status
  clear and return that canonical candidate_value.
- If the transcript plausibly points to one valid answer but is incomplete,
  phonetically rendered, or ASR-corrupted, use status candidate and propose the
  best candidate plus at most two genuinely plausible alternatives.
- If two or more meanings remain similarly plausible, or evidence is insufficient,
  use status unclear. Do not force a guess.
- Only choose values from the supplied allowed values. Do not treat an unclear
  transcript as a confirmed fact. The application must ask the customer to confirm
  every candidate before saving it.
- Do not infer an answer merely because it would be convenient for eligibility.
- Treat yes/no according to the question being asked; a bare yes/no is not enough
  to infer a different field.
- The reason is short and for internal logs; never expose it to the customer.
"""


@dataclass
class InterpretationResult:
    status: str
    candidate_value: str | None = None
    candidate_display: str | None = None
    alternatives: list[str] | None = None
    reason: str = ""

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "InterpretationResult":
        status = payload.get("status")
        if status not in {"clear", "candidate", "unclear"}:
            status = "unclear"
        value = payload.get("candidate_value")
        display = payload.get("candidate_display")
        alternatives = payload.get("alternatives", [])
        if not isinstance(alternatives, list):
            alternatives = []
        return cls(
            status=status,
            candidate_value=value if isinstance(value, str) else None,
            candidate_display=display if isinstance(display, str) else None,
            alternatives=[x for x in alternatives if isinstance(x, str)][:2],
            reason=str(payload.get("reason", ""))[:300],
        )


class AIInterpreter:
    """Groq-backed interpreter. It proposes meaning; it never confirms/saves it."""

    def __init__(self, api_key: str, model: str, timeout: float = 8.0):
        from groq import AsyncGroq
        self.client = AsyncGroq(api_key=api_key, timeout=timeout, max_retries=1)
        self.model = model

    async def interpret(
        self,
        transcript: str,
        *,
        asked_field: str,
        question: str = "",
        conversation_context: str = "",
        language: str = "en",
    ) -> InterpretationResult:
        transcript = (transcript or "").strip()
        options = FIELD_OPTIONS.get(asked_field)
        if not transcript or not options:
            return InterpretationResult(status="unclear", reason="empty transcript or unsupported field")

        payload = {
            "transcript": transcript,
            "asked_field": asked_field,
            "current_question": question,
            "recent_conversation_context": conversation_context[-1800:],
            "language": language,
            "allowed_values_and_meanings": options,
        }
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
            )
            raw = (response.choices[0].message.content or "{}").strip()
            result = InterpretationResult.from_payload(json.loads(raw))

            # Validate the model's output against the business vocabulary.
            allowed = options
            if result.candidate_value is not None and result.candidate_value not in allowed:
                return InterpretationResult(status="unclear", reason="model returned unsupported value")
            if result.status in {"clear", "candidate"} and result.candidate_value is None:
                return InterpretationResult(status="unclear", reason="model omitted candidate value")
            if result.status == "candidate" and not result.candidate_display:
                result.candidate_display = allowed[result.candidate_value]
            result.alternatives = [v for v in (result.alternatives or []) if v in allowed and v != result.candidate_value][:2]
            return result
        except Exception as exc:
            log.warning("AI interpretation failed: %s", exc)
            return InterpretationResult(status="unclear", reason="interpreter unavailable")
