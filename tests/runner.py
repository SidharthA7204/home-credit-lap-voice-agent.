from __future__ import annotations

from app.dialog import CallContext, DialogEngine
from app.extractor import RuleExtractor
from app.models import QUESTION_ORDER

from .scenarios import Scenario


async def run(sc: Scenario):
    ctx = CallContext("Rahul Sharma", "Home Credit", "Riya", sc.gender, sc.lang, "10:00")
    eng = DialogEngine(RuleExtractor(), ctx, max_unclear=3)
    eng.opening()
    last = None
    for utt in sc.turns:
        last = await eng.handle(utt)
        if last.ended:
            break
    return eng, last


def check(sc: Scenario, eng, last) -> list[str]:
    errs: list[str] = []
    rec = eng.state.to_record()
    if rec["call_outcome"] != sc.outcome:
        errs.append(f"outcome {rec['call_outcome']!r} != {sc.outcome!r}")
    state_key_aliases = {
        "documents_available": "original_documents",
    }
    for k, v in sc.state.items():
        record_key = state_key_aliases.get(k, k)
        actual = rec.get(record_key)
        if actual != v:
            errs.append(f"{k}: {actual!r} != {v!r}")
    reply = last.reply if last else ""
    for s in sc.reply_contains:
        if s.lower() not in reply.lower():
            errs.append(f"reply missing {s!r}")
    for s in sc.reply_absent:
        if s.lower() in reply.lower():
            errs.append(f"reply must not contain {s!r}")
    if sc.no_repeat:
        asked = [a for a in eng.asked_log if a in QUESTION_ORDER]
        if len(asked) != len(set(asked)):
            errs.append(f"question repeated: {asked}")
    return errs
