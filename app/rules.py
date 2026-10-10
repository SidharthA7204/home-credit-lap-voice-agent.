"""Deterministic business rules. No LLM involvement: these decisions must be auditable."""
from __future__ import annotations

from .models import MAX_LOAN_LAKH, TENURE_MAX, TENURE_MIN, CallState, IncomeMode, PropertyType


def tenure_ok(years: float) -> bool:
    return TENURE_MIN <= years <= TENURE_MAX


def amount_ok(lakh: float) -> bool:
    return 0 < lakh <= MAX_LOAN_LAKH


def disqualification_reason(s: CallState) -> str | None:
    """Hard disqualifiers (evaluated as soon as the data is known)."""
    if s.property_type == PropertyType.agricultural:
        return "agricultural_property"
    if s.documents_available is False:
        return "original_documents_unavailable"
    if s.income_mode == IncomeMode.cash:
        return "cash_income"
    return None
