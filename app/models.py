"""Domain model: the conversation state the agent tracks on every call."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

MAX_LOAN_LAKH = 75.0
TENURE_MIN = 3.0
TENURE_MAX = 15.0


class PropertyType(str, Enum):
    residential = "residential"
    commercial = "commercial"
    industrial = "industrial"
    agricultural = "agricultural"


class Ownership(str, Enum):
    sole = "sole"
    joint = "joint"


class Occupation(str, Enum):
    salaried = "salaried"
    self_employed = "self_employed"


class IncomeMode(str, Enum):
    bank = "bank"
    cash = "cash"


class Stage(str, Enum):
    VERIFY = "verify"
    AVAILABILITY = "availability"
    CALLBACK_TIME = "callback_time"
    QUALIFY = "qualify"
    CONFIRM_MAX = "confirm_max"
    FIX_TENURE = "fix_tenure"
    ENDED = "ended"


class Outcome(str, Enum):
    IN_PROGRESS = "in_progress"
    HANDOFF = "handoff"
    DISQUALIFIED = "disqualified"
    TRANSFER = "transfer"
    CALLBACK = "callback"
    HUMAN_CALLBACK = "human_callback"
    WRONG_PERSON = "wrong_person"
    DO_NOT_CALL = "do_not_call"
    DECLINED = "declined"
    UNCLEAR_CALLBACK = "unclear_callback"


# The order in which missing fields are asked (the "first missing question" algorithm).
QUESTION_ORDER = [
    "property_type",
    "ownership",
    "documents_available",
    "loan_amount_lakh",
    "occupation",
    "income_mode",
    "market_value_lakh",
    "tenure_years",
]


class CallState(BaseModel):
    stage: Stage = Stage.VERIFY
    identity_verified: bool = False

    property_type: PropertyType | None = None
    ownership: Ownership | None = None
    documents_available: bool | None = None
    loan_amount_lakh: float | None = None
    occupation: Occupation | None = None
    income_mode: IncomeMode | None = None
    market_value_lakh: float | None = None
    tenure_years: float | None = None

    # Values the customer gave that need a correction round before they become valid.
    pending_amount_lakh: float | None = None
    pending_tenure_years: float | None = None

    existing_loan_mentioned: bool = False
    callback_time: str | None = None
    offer_made: bool = False
    unclear_count: int = 0

    outcome: Outcome = Outcome.IN_PROGRESS
    reason: str | None = None

    def next_missing(self) -> str | None:
        for name in QUESTION_ORDER:
            if getattr(self, name) is None:
                return name
        return None

    @property
    def all_fields_complete(self) -> bool:
        return self.next_missing() is None

    def to_record(self) -> dict:
        """Structured post-call record (CRM / LOS friendly)."""

        def v(x):
            return x.value if isinstance(x, Enum) else x

        return {
            "call_outcome": self.outcome.value,
            "outcome_reason": self.reason,
            "identity_verified": self.identity_verified,
            "property_type": v(self.property_type),
            "ownership": v(self.ownership),
            "original_documents": self.documents_available,
            "loan_amount_lakh": self.loan_amount_lakh,
            "occupation": v(self.occupation),
            "income_mode": v(self.income_mode),
            "market_value_lakh": self.market_value_lakh,
            "tenure_years": self.tenure_years,
            "existing_loan_mentioned": self.existing_loan_mentioned,
            "callback_time": self.callback_time,
            "all_fields_complete": self.all_fields_complete,
        }
