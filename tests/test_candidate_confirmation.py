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

    result = await engine.handle("Yes")

    assert engine.pending_confirmation is None
    assert engine.state.property_type == "residential"


@pytest.mark.asyncio
async def test_no_discards_candidate_and_reasks_original_question():
    """A negative response discards the candidate."""

    engine = make_engine([
        Extraction.model_validate({"confirm": False})
    ])

    result = await engine.handle("No")

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