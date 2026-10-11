"""20+ scripted customer scenarios shared by the pytest suite and scripts/run_scenarios.py."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Scenario:
    id: str
    name: str
    turns: list[str]
    outcome: str  # expected final outcome ("in_progress" = call still running)
    state: dict = field(default_factory=dict)  # expected subset of the structured record
    reply_contains: list[str] = field(default_factory=list)  # substrings expected in the LAST agent reply
    reply_absent: list[str] = field(default_factory=list)
    lang: str = "en"
    gender: str = "female"
    no_repeat: bool = False  # no eligibility question may be asked twice


V = ["Yes, speaking", "Yes sure, go ahead"]  # verify + availability

SCENARIOS = [
    Scenario("T01", "Happy path - eligible customer", V + [
        "It's a residential flat", "Yes",
        "It's in my name only", "Yes",
        "The original documents are available", "Yes",
        "I need fifty lakh", "Yes",
        "I'm salaried", "Yes",
        "It comes into my bank account", "Yes",
        "The property is worth one crore", "Yes",
        "Ten years", "Yes"],
        "handoff", {"property_type": "residential", "ownership": "sole",
                    "documents_available": True, "loan_amount_lakh": 50,
                    "occupation": "salaried", "income_mode": "bank",
                    "market_value_lakh": 100, "tenure_years": 10,
                    "all_fields_complete": True},
        ["senior loan expert"], no_repeat=True),
    Scenario("T02", "Agricultural property", V + [
        "It's agricultural land", "Yes"],
        "disqualified", {"outcome_reason": "agricultural_property"},
        ["don't meet the criteria"]),
    Scenario("T03", "Cash income (self-employed)", V + [
        "It's a commercial shop", "Yes",
        "It's in my name only", "Yes",
        "The original documents are available", "Yes",
        "I need forty lakh", "Yes",
        "I run a business", "Yes",
        "I receive all my income in cash", "Yes"],
        "disqualified", {"outcome_reason": "cash_income",
                         "property_type": "commercial",
                         "ownership": "sole",
                         "documents_available": True,
                         "loan_amount_lakh": 40,
                         "occupation": "self_employed",
                         "income_mode": "cash"}),
    Scenario("T04", "Original documents missing", V + [
        "Residential", "Yes",
        "Sole owner", "Yes",
        "I only have photocopies", "Yes"],
        "disqualified", {"outcome_reason": "original_documents_unavailable"}),
    Scenario("T05", "Existing property loan -> transfer", V + ["I already have a loan on this property"],
             "transfer", {"existing_loan_mentioned": True}, ["transfer specialist"]),
    Scenario("T06", "Amount above 75L accepted at 75L, then qualifies", V + [
        "Residential", "Yes",
        "Joint with my brother", "Yes",
        "Yes, the original documents are available", "Yes",
        "I need ninety lakh", "Yes",
        "Yes, that's fine",
        "Salaried", "Yes",
        "Bank account", "Yes",
        "The property is worth 80 lakh", "Yes",
        "Twelve years", "Yes"],
        "handoff", {"loan_amount_lakh": 75, "ownership": "joint", "tenure_years": 12}),
    Scenario("T07", "Tenure too short -> correction accepted", V + [
        "Residential", "Yes",
        "Sole", "Yes",
        "Yes the original documents are available", "Yes",
        "I need 30 lakh", "Yes",
        "Salaried", "Yes",
        "Bank", "Yes",
        "The property is worth one crore", "Yes",
        "I want to repay in two years", "Yes",
        "Ten years", "Yes"],
        "handoff", {"tenure_years": 10}),
    Scenario("T08", "Tenure correction refused", V + [
        "Residential", "Yes",
        "Sole", "Yes",
        "Yes the original documents are available", "Yes",
        "I need 30 lakh", "Yes",
        "Salaried", "Yes",
        "Bank", "Yes",
        "The property is worth one crore", "Yes",
        "I want to repay in two years", "Yes",
        "No, I want two years only"],
        "disqualified", {"outcome_reason": "tenure_outside_range_refused"}),
    Scenario("T09", "Amount above limit, maximum rejected", V + [
        "Residential", "Yes",
        "Sole", "Yes",
        "Yes, the original documents are available", "Yes",
        "I need one crore", "Yes",
        "No, I need the full one crore"],
        "disqualified", {"outcome_reason": "declined_max_amount"}),
    Scenario("T10", "Sequential confirmation of all qualification answers", V + [
    "Commercial",
    "Yes",
    "Sole ownership",
    "Yes",
    "The original property documents are available",
    "Yes",
    "I need forty lakh",
    "Yes",
    "I'm self-employed",
    "Yes",
    "My income comes into my bank account",
    "Yes",
    "The property is worth around one crore",
    "Yes",
    "Eight years",
    "Yes"],
    "handoff", {"property_type": "commercial", "occupation": "self_employed",
                "loan_amount_lakh": 40, "tenure_years": 8, "market_value_lakh": 100},
    no_repeat=True),
Scenario("T11", "Out-of-order: joint ownership + documents", V + [
        "It's my residential property, jointly owned with my brother, and the original documents are available",
        "Yes",
        "Yes",
        "Yes"],
        "in_progress", {"property_type": "residential", "ownership": "joint", "original_documents": True},
        ["borrow"], no_repeat=True),
    Scenario("T12", "Customer changes the amount", V + [
        "Residential", "Yes",
        "Sole", "Yes",
        "Original documents are available", "Yes",
        "I need forty lakh. Actually, make that fifty lakh.",
        "Yes"],
        "in_progress", {"loan_amount_lakh": 50}, ["salaried"]),
    Scenario("T13", "Vague market value accepted", V + [
        "Residential", "Yes",
        "Only mine", "Yes",
        "Original documents are available", "Yes",
        "I need 30 lakh", "Yes",
        "I'm salaried", "Yes",
        "Yes, it's credited to my bank", "Yes",
        "The property is worth around one crore", "Yes",
        "Ten years", "Yes"],
        "handoff", {"market_value_lakh": 100, "loan_amount_lakh": 30}),
    Scenario("T14", "Interest-rate question mid-flow", V + ["Before I answer, what interest rate will you charge?"],
             "in_progress", {"property_type": None}, ["senior loan expert", "residential, commercial"],
             ["% "]),
    Scenario("T15a", "Busy, gives callback time immediately", ["Yes this is Rahul, but I'm driving. Call me tomorrow evening."],
             "callback", {"callback_time": "tomorrow evening"}, ["tomorrow evening"]),
    Scenario("T15b", "Busy, agent asks for time", ["Yes speaking", "I'm in a meeting right now", "Call me at 6 pm"],
             "callback", {"callback_time": "at 6 pm"}),
    Scenario("T16", "Wrong person - no loan details disclosed", ["I'm his wife"],
             "wrong_person", {}, [], ["loan", "75 lakh", "offer"]),
    Scenario("T17", "Do-not-call request", V + ["Please stop calling me"], "do_not_call"),
    Scenario("T18", "Priority: agricultural + existing loan -> transfer", V + [
        "I have agricultural land, and I already have a loan against it"],
        "transfer", {"existing_loan_mentioned": True}),
    Scenario("T19", "EMI reduction request -> transfer", V + ["I want to reduce my current EMI"], "transfer"),
    Scenario("T20", "Repeated unclear answers -> callback", V + ["Hmm... umm", "uh", "hmm"], "unclear_callback"),
    Scenario("T21", "Customer asks what LAP is, agent resumes", V + ["Wait, what exactly is a loan against property?"],
             "in_progress", {}, ["security", "residential, commercial"]),
    Scenario("T22", "Hindi + female agent uses feminine grammar", ["Haan ji, bol raha hoon", "Haan ji bataiye"],
             "in_progress", {}, ["चाहूँगी", "रिहायशी"], ["चाहूँगा", "रहा हूँ"], lang="hi", gender="female"),
    Scenario("T23", "Hindi + male agent uses masculine grammar", ["Haan ji, bol raha hoon", "Haan ji bataiye"],
             "in_progress", {}, ["चाहूँगा", "रिहायशी"], ["चाहूँगी", "रही हूँ"], lang="hi", gender="male"),
    Scenario("T24", "Contradiction: residential then agricultural (latest wins)", V + [
        "It's residential... actually no, it's agricultural land", "Yes"],
        "disqualified", {"outcome_reason": "agricultural_property"}),
    Scenario("T25", "Customer asks for a human", V + ["I'd rather speak to a human please"], "human_callback"),
]
