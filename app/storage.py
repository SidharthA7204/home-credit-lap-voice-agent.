"""Persist the structured post-call record + transcript as JSON (swap for a DB / CRM webhook in production)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def save_call(data_dir: str, call_id: str, record: dict, transcript: list[tuple[str, str]]) -> Path:
    path = Path(data_dir)
    path.mkdir(parents=True, exist_ok=True)
    out = path / f"{call_id}.json"
    payload = {
        "call_id": call_id,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "record": record,
        "transcript": [{"role": r, "text": t} for r, t in transcript],
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
