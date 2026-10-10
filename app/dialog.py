"""Deterministic dialog engine.

Per turn:  extract -> (priority checks) -> update state -> validate -> ask FIRST missing field -> handoff gate.

Rule priority (highest first):
  1 privacy (wrong person) / do-not-call / declined
  2 busy -> callback          3 human requested
  4 existing loan / EMI reduction -> transfer specialist
  5 hard disqualification     6 loan-amount cap & tenure correction
  7 normal eligibility questions      8 handoff (only when all 8 fields captured)
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from . import rules
from .extractor import BaseExtractor, Extraction, ExtractionContext
from .models import MAX_LOAN_LAKH, CallState, Outcome, Stage
from .responses import ack, fmt_amount, say, time_greeting

log = logging.getLogger(__name__)


@dataclass
class CallContext:
    customer_name: str = "Customer"
    company_name: str = "Home Credit"
    agent_name: str = "Riya"
    agent_gender: str = "female"
    language: str = "en"
    current_time: str = ""  # "HH:MM" or free text
    rag: str = ""


@dataclass
class TurnResult:
    reply: str
    ended: bool
    outcome: Outcome
    state: dict


class DialogEngine:
    def __init__(self, extractor: BaseExtractor, ctx: CallContext, max_unclear: int = 3):
        self.extractor = extractor
        self.ctx = ctx
        self.max_unclear = max_unclear
        self.state = CallState()
        self.transcript: list[tuple[str, str]] = []
        self.asked_log: list[str] = []
        self.asked_field = "verify"
        self.last_reply = ""
        self._ack_n = 0
        self.pending_confirmation: dict[str, str | float | bool] | None = None

    # ------------------------------------------------------------------ helpers
    def _say(self, key: str, **kw) -> str:
        c = self.ctx
        return say(key, c.language, c.agent_gender, customer=c.customer_name, agent=c.agent_name, company=c.company_name, **kw)

    def _finish(self, text: str) -> TurnResult:
        self.last_reply = text
        self.transcript.append(("agent", text))
        return TurnResult(text, self.state.stage == Stage.ENDED, self.state.outcome, self.state.to_record())

    def _ask(self, parts: list[str], field_key: str) -> TurnResult:
        self.asked_field = field_key
        self.asked_log.append(field_key)
        return self._finish(" ".join(p for p in parts if p))

    def _end(self, outcome: Outcome, reason: str | None, key: str, **kw) -> TurnResult:
        s = self.state
        s.stage, s.outcome, s.reason = Stage.ENDED, outcome, reason
        log.info("call ended outcome=%s reason=%s", outcome.value, reason)
        return self._finish(self._say(key, **kw))

    def _greeting(self) -> str:
        try:
            hour = int(self.ctx.current_time.strip()[:2])
        except ValueError:
            hour = None
        return time_greeting(self.ctx.language, hour)

    # ------------------------------------------------------------------ public API
    def opening(self) -> TurnResult:
        return self._ask([self._say("greet", greeting=self._greeting())], "verify")

    def reprompt(self) -> TurnResult:
        """Customer was silent: repeat the pending question."""
        return self._finish(self.last_reply)

    async def handle(self, utterance: str, is_current: Callable[[], bool] | None = None) -> TurnResult | None:
        s = self.state
        if s.stage == Stage.ENDED:
            return TurnResult("", True, s.outcome, s.to_record())
        ctx = ExtractionContext(self.asked_field, s.stage, self.ctx.customer_name, self.ctx.language)
        ex = await self.extractor.extract(utterance, ctx)
        if is_current is not None and not is_current():
            return None  # customer interrupted; a newer request supersedes this one
        self.transcript.append(("user", utterance))

        # Process high-priority requests before candidate confirmation.
        if ex.do_not_call:
            self.pending_confirmation = None
            return self._end(
                Outcome.DO_NOT_CALL,
                "do_not_call",
                "dnc",
            )

        if ex.human_requested:
            self.pending_confirmation = None
            return self._end(
                Outcome.HUMAN_CALLBACK,
                "human_requested",
                "human",
            )

        # A pending interpretation must be confirmed before it changes qualification state.
        if self.pending_confirmation is not None:
            if ex.confirm is True:
                pending = self.pending_confirmation
                self.pending_confirmation = None
                field = str(pending["field"])
                value = pending["value"]
                try:
                    ex = Extraction.model_validate({**ex.model_dump(), field: value,
                        "candidate_field": None, "candidate_value": None, "candidate_display": None})
                except Exception:
                    log.exception("Could not apply confirmed candidate field=%s", field)
                    return self._ask([self._say("sorry"), self._question_for(field)], field)
                side = await self._side_answer(ex)
                return self._step(ex, side, utterance)
            if ex.confirm is False:
                field = str(self.pending_confirmation["field"])
                self.pending_confirmation = None
                return self._ask(["No problem.", self._question_for(field)], field)
            # If the answer is neither a clear yes nor no, do not lose the candidate.
            return self._ask(["I may have misunderstood. Please say yes or no: did you mean "
                              + str(self.pending_confirmation["display"]) + "?"], "confirm_candidate")

        # The extractor can propose a best interpretation of noisy speech. Never save it
        # until the customer confirms it. Do not start confirmation for clear facts.
        if ex.candidate_field and ex.candidate_value is not None:
            field = ex.candidate_field
            value = ex.candidate_value
            display = ex.candidate_display or str(value)
            if field in {"property_type", "ownership", "documents_available", "loan_amount_lakh",
                         "occupation", "income_mode", "market_value_lakh", "tenure_years"}:
                self.pending_confirmation = {"field": field, "value": value, "display": display}
                return self._ask([f"I heard {display}. Is that correct?"], "confirm_candidate")

        side = await self._side_answer(ex)
        return self._step(ex, side, utterance)

    def _question_for(self, field: str) -> str:
        """Return the original field question after a rejected prediction."""
        if field in {"property_type", "ownership", "documents_available", "loan_amount_lakh",
                     "occupation", "income_mode", "market_value_lakh", "tenure_years"}:
            return self._say("q_" + field)
        return self._say("sorry")

    async def _side_answer(self, ex: Extraction) -> str | None:
        if ex.asks_rate:
            return self._say("rate_defer")
        if ex.asks_what_is_lap:
            return self._say("what_is_lap")
        if ex.asks_docs:
            return self._say("docs_needed")
        if ex.side_question:
            return await self.extractor.answer(ex.side_question, self.ctx.rag, self.ctx.language) or self._say("expert_defer")
        return None

    # ------------------------------------------------------------------ core step
    def _step(self, ex: Extraction, side: str | None, utterance: str) -> TurnResult:
        s = self.state

        # 1. privacy, do-not-call, decline
        if s.stage == Stage.VERIFY and (ex.wrong_person or (ex.confirm is False and not ex.busy)):
            return self._end(Outcome.WRONG_PERSON, "wrong_person", "wrong_person")
        if ex.do_not_call:
            return self._end(Outcome.DO_NOT_CALL, "do_not_call", "dnc")
        if ex.declined:
            return self._end(Outcome.DECLINED, "not_interested", "declined")

        # identity verification gate
        if s.stage == Stage.VERIFY:
            if ex.identity_confirmed or ex.busy:
                s.identity_verified, s.stage, s.unclear_count = True, Stage.AVAILABILITY, 0
                if not ex.busy:
                    return self._ask([self._say("availability")], "availability")
            else:
                s.unclear_count += 1
                if s.unclear_count >= self.max_unclear:
                    return self._end(Outcome.UNCLEAR_CALLBACK, "identity_unclear", "unclear_end")
                return self._ask([self._say("who_are_you" if ex.asks_who else "verify_retry")], "verify")

        # callback time collection
        if s.stage == Stage.CALLBACK_TIME:
            if ex.callback_time or s.unclear_count >= 1:
                s.callback_time = ex.callback_time or utterance.strip()
                return self._end(Outcome.CALLBACK, "customer_busy", "callback_done", when=s.callback_time)
            s.unclear_count += 1
            return self._ask([self._say("callback_ask_again")], "callback_time")

        # 2. busy -> callback
        if ex.busy or (s.stage == Stage.AVAILABILITY and ex.confirm is False):
            if ex.callback_time:
                s.callback_time = ex.callback_time
                return self._end(Outcome.CALLBACK, "customer_busy", "callback_done", when=s.callback_time)
            s.stage, s.unclear_count = Stage.CALLBACK_TIME, 0
            return self._ask([self._say("callback_ask")], "callback_time")

        # 3. wants a human
        if ex.human_requested:
            return self._end(Outcome.HUMAN_CALLBACK, "human_requested", "human")

        # 4. existing loan / EMI reduction -> transfer specialist (beats ordinary disqualification)
        if ex.existing_loan is True:
            s.existing_loan_mentioned = True
            return self._end(Outcome.TRANSFER, "existing_loan", "transfer")

        offer_now = False
        if s.stage == Stage.AVAILABILITY:
            s.stage, offer_now = Stage.QUALIFY, True

        # 5/6. stage-specific handling
        if s.stage == Stage.CONFIRM_MAX:
            amt = ex.loan_amount_lakh
            if amt is not None and rules.amount_ok(amt):
                s.loan_amount_lakh, s.pending_amount_lakh = amt, None
            elif ex.confirm is True and amt is None:
                s.loan_amount_lakh, s.pending_amount_lakh = MAX_LOAN_LAKH, None
            elif ex.confirm is False or amt is not None:
                return self._end(Outcome.DISQUALIFIED, "declined_max_amount", "max_declined")
            else:
                return self._ask([self._say("confirm_retry")], "confirm_max")
            s.stage = Stage.QUALIFY
            self._capture(ex, skip_loan=True)
            return self._advance([ack(self.ctx.language, self.ctx.agent_gender, self._bump())], False)

        if s.stage == Stage.FIX_TENURE:
            tv = ex.tenure_years
            if tv is not None and rules.tenure_ok(tv):
                s.tenure_years, s.pending_tenure_years, s.stage = tv, None, Stage.QUALIFY
                self._capture(ex, skip_tenure=True)
                return self._advance([ack(self.ctx.language, self.ctx.agent_gender, self._bump())], False)
            if tv is not None or ex.confirm is False:
                return self._end(Outcome.DISQUALIFIED, "tenure_outside_range_refused", "disqualified")
            return self._ask([self._say("sorry"), self._say("tenure_range")], "fix_tenure")

        # 7. normal qualification
        progress = self._capture(ex) or offer_now
        if progress or side:
            s.unclear_count = 0
            parts = [side] if side else ([] if offer_now else [ack(self.ctx.language, self.ctx.agent_gender, self._bump())])
        else:
            s.unclear_count += 1
            if s.unclear_count >= self.max_unclear:
                return self._end(Outcome.UNCLEAR_CALLBACK, "unclear_responses", "unclear_end")
            parts = [self._say("sorry")]
        return self._advance(parts, offer_now)

    def _bump(self) -> int:
        self._ack_n += 1
        return self._ack_n

    def _capture(self, ex: Extraction, skip_loan: bool = False, skip_tenure: bool = False) -> bool:
        """Update state with everything the customer said (latest value wins). Returns True if anything captured."""
        s, got = self.state, False
        for name in ("property_type", "ownership", "documents_available", "occupation", "income_mode", "market_value_lakh"):
            val = getattr(ex, name)
            if val is not None:
                setattr(s, name, val)
                got = True
        if ex.loan_amount_lakh is not None and not skip_loan:
            got = True
            if rules.amount_ok(ex.loan_amount_lakh):
                s.loan_amount_lakh, s.pending_amount_lakh = ex.loan_amount_lakh, None
            else:
                s.loan_amount_lakh, s.pending_amount_lakh = None, ex.loan_amount_lakh
        if ex.tenure_years is not None and not skip_tenure:
            got = True
            if rules.tenure_ok(ex.tenure_years):
                s.tenure_years, s.pending_tenure_years = ex.tenure_years, None
            else:
                s.tenure_years, s.pending_tenure_years = None, ex.tenure_years
        return got

    def _advance(self, parts: list[str], offer_now: bool) -> TurnResult:
        s = self.state
        reason = rules.disqualification_reason(s)
        if reason:
            return self._end(Outcome.DISQUALIFIED, reason, "disqualified")

        if offer_now and not s.offer_made:
            s.offer_made = True
            parts = [self._say("offer")] + [p for p in parts if p]

        if s.pending_amount_lakh is not None:
            s.stage = Stage.CONFIRM_MAX
            cap = fmt_amount(MAX_LOAN_LAKH, self.ctx.language)
            return self._ask(parts + [self._say("amount_cap", cap=cap)], "confirm_max")
        if s.pending_tenure_years is not None:
            s.stage = Stage.FIX_TENURE
            return self._ask(parts + [self._say("tenure_range")], "fix_tenure")

        nxt = s.next_missing()
        if nxt is None:  # handoff gate: every field captured, no disqualifier, no transfer
            return self._end(Outcome.HANDOFF, None, "handoff")
        s.stage = Stage.QUALIFY
        return self._ask(parts + [self._say("q_" + nxt)], nxt)
