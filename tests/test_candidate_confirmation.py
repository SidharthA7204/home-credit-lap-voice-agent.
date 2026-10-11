import pytest

from app.dialog import CallContext, DialogEngine
from app.extractor import Extraction
from app.models import Stage


class FakeExtractor:
    """Returns predefined extraction results without making API calls."""

    def __init__(self, results):
        self.results = list(results)

    async def extract(self, utterance, context):
        if not self.results:
            return Extraction()
        return self.results.pop(0)

    async def answer(self, question, rag, language):
        return None


def make_engine(results):
    """Create a dialog engine with a pending candidate."""

    engine = DialogEngine(
        extractor=FakeExtractor(results),
        ctx=CallContext(customer_name="Test Customer"),
    )

    # Place the engine in the candidate-confirmation state.
    engine.state.stage = Stage.QUALIFY
    engine.asked_field = "confirm_candidate"

    engine.pending_confirmation = {
        "field": "property_type",
        "value": "residential",
        "display": "Residential",
    }

    return engine


@pytest.mark.asyncio
async def test_yes_accepts_candidate():
    """An affirmative response accepts the proposed answer."""

    engine = make_engine([
        Extraction.model_validate({"confirm": True})
    ])

    await engine.handle("Yes")

    assert engine.pending_confirmation is None
    assert engine.state.property_type == "residential"


@pytest.mark.asyncio
async def test_no_discards_candidate_and_reasks_original_question():
    """A negative response discards the candidate."""

    engine = make_engine([
        Extraction.model_validate({"confirm": False})
    ])

    await engine.handle("No")

    assert engine.pending_confirmation is None
    assert engine.state.property_type is None
    assert engine.asked_field == "property_type"


@pytest.mark.asyncio
async def test_unclear_confirmation_keeps_candidate_pending():
    """An unclear response must not accept the candidate."""

    engine = make_engine([
        Extraction()
    ])

    result = await engine.handle("Maybe")

    assert engine.pending_confirmation is not None
    assert engine.state.property_type is None
    assert engine.asked_field == "confirm_candidate"
    assert "yes or no" in result.reply.lower()


@pytest.mark.asyncio
async def test_do_not_call_overrides_pending_confirmation():
    """A do-not-call request takes priority over candidate confirmation."""

    engine = make_engine([
        Extraction.model_validate({"do_not_call": True})
    ])

    result = await engine.handle("Don't call me again")

    assert result.ended is True
    assert result.outcome.value == "do_not_call"
    assert engine.pending_confirmation is None


@pytest.mark.asyncio
async def test_human_request_overrides_pending_confirmation():
    """A human request takes priority over candidate confirmation."""

    engine = make_engine([
        Extraction.model_validate({"human_requested": True})
    ])

    result = await engine.handle("I want to speak to a human")

    assert result.ended is True
    assert result.outcome.value == "human_callback"
    assert engine.pending_confirmation is None

@pytest.mark.asyncio
async def test_clear_qualification_answer_requires_confirmation():
    """A clear answer must not be saved before explicit confirmation."""

    engine = DialogEngine(
        extractor=FakeExtractor([
            Extraction.model_validate({
                "property_type": "residential",
            }),
        ]),
        ctx=CallContext(customer_name="Test Customer"),
    )

    engine.state.stage = Stage.QUALIFY
    engine.asked_field = "property_type"

    result = await engine.handle("Residential")

    assert engine.state.property_type is None
    assert engine.pending_confirmation is not None
    assert engine.pending_confirmation["field"] == "property_type"
    assert engine.pending_confirmation["value"] == "residential"
    assert engine.asked_field == "confirm_candidate"
    assert "correct" in result.reply.lower()


@pytest.mark.asyncio
async def test_confirming_candidate_prompts_next_queued_answer_once():
    """Confirm the current value, then ask once to confirm a queued value."""
    engine = make_engine([
        Extraction.model_validate({
            "confirm": True,
            "ownership": "sole",
        }),
    ])

    previous_agent_replies = sum(
        role == "agent" for role, _ in engine.transcript
    )

    result = await engine.handle("Yes, and the property is solely mine")

    assert engine.state.property_type == "residential"
    assert engine.state.ownership is None
    assert engine.pending_confirmation is not None
    assert engine.pending_confirmation["field"] == "ownership"
    assert engine.asked_field == "confirm_candidate"
    assert "solely in your name" in result.reply.lower()

    current_agent_replies = sum(
        role == "agent" for role, _ in engine.transcript
    )
    assert current_agent_replies - previous_agent_replies == 1


@pytest.mark.asyncio
async def test_new_answer_is_queued_without_saving_before_confirmation():
    """A new answer during confirmation must remain queued and unsaved."""
    engine = make_engine([
        Extraction.model_validate({
            "loan_amount_lakh": 40,
        }),
    ])

    result = await engine.handle("I need forty lakh")

    assert engine.state.property_type is None
    assert engine.state.loan_amount_lakh is None
    assert engine.pending_confirmation is not None
    assert engine.pending_confirmation["field"] == "property_type"
    assert any(
        answer["field"] == "loan_amount_lakh"
        and answer["value"] == 40
        for answer in engine.pending_answers
    )
    assert engine.asked_field == "confirm_candidate"
    assert "yes or no" in result.reply.lower()


@pytest.mark.asyncio
async def test_queued_answer_is_updated_when_customer_corrects_it():
    """A newer explicit value replaces an older queued value for the same field."""
    engine = make_engine([
        Extraction.model_validate({
            "loan_amount_lakh": 40,
        }),
        Extraction.model_validate({
            "loan_amount_lakh": 50,
        }),
    ])

    await engine.handle("I need forty lakh")

    assert engine.pending_confirmation is not None
    assert engine.pending_confirmation["field"] == "property_type"
    assert engine.state.loan_amount_lakh is None

    await engine.handle("Actually, I need fifty lakh")

    queued_amounts = [
        answer["value"]
        for answer in engine.pending_answers
        if answer["field"] == "loan_amount_lakh"
    ]

    assert queued_amounts == [50]
    assert engine.state.loan_amount_lakh is None
