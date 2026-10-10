"""FastAPI service: REST API, browser demo, and Retell AI custom-LLM WebSocket."""
from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .config import Settings, get_settings
from .dialog import CallContext, DialogEngine
from .extractor import BaseExtractor, GroqExtractor, RuleExtractor
from .storage import save_call

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("lap-agent")

DEFAULT_RAG = (
    "Loan Against Property (LAP): a secured loan where the customer's property is the collateral. "
    "Pre-approved offer up to INR 75 lakh for existing Home Credit customers. Eligible property: residential, commercial, industrial. "
    "Tenure 3 to 15 years. Exact interest rates are provided by the senior loan expert."
)


def build_extractor(st: Settings) -> BaseExtractor:
    if st.groq_api_key:
        log.info("Using Groq extractor (%s)", st.groq_model)
        return GroqExtractor(st.groq_api_key, st.groq_model, RuleExtractor())
    log.info("GROQ_API_KEY not set: using offline rule-based extractor")
    return RuleExtractor()


settings = get_settings()
extractor = build_extractor(settings)
app = FastAPI(title="Home Credit LAP Voice Agent", version="1.0.0")
SESSIONS: dict[str, DialogEngine] = {}


def make_engine(**over) -> DialogEngine:
    lang = str(over.get("language") or settings.default_language).lower()
    lang = "hi" if lang.startswith("hi") else "en"
    ctx = CallContext(
        customer_name=over.get("customer_name") or "Customer",
        company_name=over.get("company_name") or settings.company_name,
        agent_name=over.get("agent_name") or settings.agent_name,
        agent_gender=over.get("agent_gender") or settings.agent_gender,
        language=lang,
        current_time=over.get("current_time") or "",
        rag=over.get("rag") or DEFAULT_RAG,
    )
    return DialogEngine(extractor, ctx, settings.max_unclear_retries)


def _persist(call_id: str, eng: DialogEngine) -> None:
    try:
        save_call(settings.data_dir, call_id, eng.state.to_record(), eng.transcript)
    except OSError as exc:
        log.error("could not persist call %s: %s", call_id, exc)


# ----------------------------------------------------------------------------- REST
class SessionCreate(BaseModel):
    customer_name: str = "Rahul Sharma"
    language: str = "en"
    agent_name: str | None = None
    agent_gender: str | None = None
    current_time: str | None = None


class TurnRequest(BaseModel):
    utterance: str


@app.get("/health")
def health():
    return {"status": "ok", "llm": "groq" if settings.groq_api_key else "rule-based"}


@app.get("/", include_in_schema=False)
def demo():
    return FileResponse(Path(__file__).parent / "static" / "demo.html")


@app.post("/api/sessions")
def create_session(body: SessionCreate):
    eng = make_engine(**body.model_dump())
    sid = uuid.uuid4().hex[:12]
    SESSIONS[sid] = eng
    return {"session_id": sid, "reply": eng.opening().reply}


@app.post("/api/sessions/{sid}/turn")
async def turn(sid: str, body: TurnRequest):
    eng = SESSIONS.get(sid)
    if not eng:
        raise HTTPException(404, "unknown session")
    res = await eng.handle(body.utterance)
    if res.ended:
        _persist(sid, eng)
    return {"reply": res.reply, "ended": res.ended, "outcome": res.outcome.value, "state": res.state}


@app.get("/api/sessions/{sid}")
def get_session(sid: str):
    eng = SESSIONS.get(sid)
    if not eng:
        raise HTTPException(404, "unknown session")
    return {"state": eng.state.to_record(), "transcript": [{"role": r, "text": t} for r, t in eng.transcript]}


# ----------------------------------------------------------------------------- Retell custom LLM
def _vars_from_call_details(msg: dict) -> dict:
    call = msg.get("call", {}) or {}
    v = call.get("retell_llm_dynamic_variables", {}) or {}
    return {
        "customer_name": v.get("customer_name"),
        "company_name": v.get("company_name"),
        "agent_name": v.get("agent_name"),
        "agent_gender": v.get("agent_gender"),
        "language": v.get("language_to_speak"),
        "current_time": v.get("current_time"),
        "rag": v.get("additional_context_from_rag"),
    }


@app.websocket("/llm-websocket/{call_id}")
async def retell_ws(ws: WebSocket, call_id: str):
    """Retell AI 'Custom LLM' protocol. Retell does STT/TTS; this server owns the brain."""
    await ws.accept()
    engine: DialogEngine | None = None
    opened, latest = False, {"id": -1}

    async def send(response_id: int, text: str, end: bool = False):
        await ws.send_json({"response_type": "response", "response_id": response_id, "content": text,
                            "content_complete": True, "end_call": end})

    try:
        await ws.send_json({"response_type": "config", "config": {"auto_reconnect": True, "call_details": True}})
        while True:
            msg = await ws.receive_json()
            kind = msg.get("interaction_type")

            if kind == "ping_pong":
                await ws.send_json({"response_type": "ping_pong", "timestamp": msg.get("timestamp")})
            elif kind == "call_details":
                engine = make_engine(**_vars_from_call_details(msg))
                await send(0, engine.opening().reply)
                opened = True
            elif kind in ("response_required", "reminder_required"):
                rid = msg.get("response_id", 0)
                latest["id"] = rid
                if engine is None:
                    engine = make_engine()
                if not opened:
                    opened = True
                    await send(rid, engine.opening().reply)
                    continue
                if kind == "reminder_required":
                    await send(rid, engine.reprompt().reply)
                    continue
                transcript = msg.get("transcript", [])
                last_user = next((t["content"] for t in reversed(transcript) if t.get("role") == "user"), "")
                res = await engine.handle(last_user, is_current=lambda r=rid: latest["id"] == r)
                if res is None:
                    continue  # superseded by a newer utterance
                await send(rid, res.reply, end=res.ended)
                if res.ended:
                    _persist(call_id, engine)
    except WebSocketDisconnect:
        log.info("retell call %s disconnected", call_id)
    except (asyncio.CancelledError, RuntimeError):
        pass
    except Exception:
        log.exception("retell websocket error")
        await ws.close()
