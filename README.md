# Home Credit — LAP Voice Agent

An AI voice agent that calls existing customers about a **pre-approved Loan Against Property (up to ₹75 lakh)**, verifies identity, runs an 8-field eligibility check (out-of-order answers supported), handles disqualification / loan-transfer / callback / do-not-call paths, and hands qualified leads to a senior loan expert.

**Design principle: the LLM only *understands* speech; deterministic code *decides*.** Eligibility, rule priority and the handoff gate are plain, unit-tested Python, so behaviour is auditable and regression-tested in CI.

![CI](https://img.shields.io/badge/tests-40%20passing-brightgreen) ![python](https://img.shields.io/badge/python-3.10%2B-blue)

## Features
- 8-field state tracking, "ask the first missing question", latest-answer-wins corrections
- Rules: agricultural ✗, cash income ✗, no original docs ✗, amount > ₹75L → offer max, tenure 3–15 yrs → correction round
- Rule priority: privacy/DNC → busy → human → **existing-loan transfer** → disqualify → corrections → questions → handoff
- English + Hindi, strict agent-gender grammar
- Groq (free) LLM extraction with automatic rule-based fallback (works with **no API key**)
- Retell AI custom-LLM WebSocket, REST API, browser voice demo, CLI simulator
- Structured post-call JSON record (CRM-ready), 26 scripted scenarios, GitHub Actions CI, Docker

## Repository layout
```
app/        dialog.py (engine) · rules.py · extractor.py (Groq+rules) · responses.py (EN/HI) · main.py (API+Retell WS) · models.py
prompts/    system_prompt_final.md   <- paste into Retell/Bolna for the assignment submission
tests/      scenarios.py (26 cases) · test_*.py
scripts/    run_scenarios.py -> docs/test_results.md
docs/       architecture.md · test_results.md (generated)
evidence/   your real call links / recordings
```

## Step-by-step setup

### 1. Run locally (5 min, no keys needed)
```bash
git clone https://github.com/<you>/home-credit-lap-voice-agent.git && cd home-credit-lap-voice-agent
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env
pytest -q                     # 40 tests should pass
python -m app.cli             # chat with the agent in your terminal (try --lang hi --gender male)
uvicorn app.main:app --reload # open http://localhost:8000 for the browser voice demo (use Chrome)
```

### 2. Add the free Groq LLM
1. Create a free key at https://console.groq.com/keys
2. Put it in `.env`: `GROQ_API_KEY=gsk_...` and restart. `GET /health` now shows `"llm": "groq"`.
3. Any Groq failure automatically falls back to the rule extractor.

### 3. Voice calls with Retell AI (free trial credits)
**Option A — single prompt (matches the assignment text):**
1. retellai.com → Create Agent → *Single Prompt*. Paste `prompts/system_prompt_final.md`.
2. Choose an Indian-English voice matching `agent_gender`; set language; enable *End Call* function.
3. Define dynamic variables: `company_name, customer_name, agent_name, agent_gender, current_date, current_day, current_time, additional_context_from_rag, language_to_speak`. (`conversation_history`/`customer_utterance` are supplied by Retell's transcript; verify in your test call how your agent version handles them.)
4. Run test calls for every scenario in `docs/test_results.md`, then copy each public call link into `evidence/README.md`.

**Option B — custom LLM (this repo's engine drives the call):**
1. Start the server and expose it: `uvicorn app.main:app --port 8000` then `ngrok http 8000` (or deploy to Render/Fly.io with the Dockerfile).
2. Retell → Create Agent → *Custom LLM* → WebSocket URL `wss://<your-host>/llm-websocket` (Retell appends `/{call_id}`).
3. Pass dynamic variables when creating the web/phone call. The server reads them from Retell's `call_details` event.
4. Check Retell's current Custom-LLM docs if field names change; protocol handling is in `app/main.py::retell_ws`.

### 4. Push to GitHub (professional workflow)
```bash
git init && git add . && git commit -m "feat: LAP voice agent engine, rules, tests"
git branch -M main
git remote add origin https://github.com/<you>/home-credit-lap-voice-agent.git
git push -u origin main
```
Then work through branches + PRs (`feat/hindi-tuning`, `fix/tenure-regex`); CI (`.github/workflows/ci.yml`) runs ruff + pytest on each PR. Keep `.env` out of git (already ignored). Use Conventional Commit messages (`feat:`, `fix:`, `test:`, `docs:`).

### 5. Deploy (free tier)
Render/Railway/Fly.io → deploy from the Dockerfile; set env vars from `.env.example`; use the public URL for Retell.

## API
| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | status + active LLM |
| POST | `/api/sessions` | start a call `{customer_name, language, agent_gender}` → opening line |
| POST | `/api/sessions/{id}/turn` | `{utterance}` → reply, outcome, structured state |
| GET | `/api/sessions/{id}` | state + transcript |
| WS | `/llm-websocket/{call_id}` | Retell custom-LLM protocol |

Example record: `{"call_outcome":"handoff","property_type":"residential","ownership":"sole","original_documents":true,"loan_amount_lakh":50,"occupation":"salaried","income_mode":"bank","market_value_lakh":100,"tenure_years":10,"all_fields_complete":true}`

## Testing
`make test` (pytest) · `make report` (regenerates `docs/test_results.md` from real runs). The 26 scenarios cover happy path, every disqualifier, transfer + priority conflicts, amount/tenure correction, out-of-order and vague answers, busy, wrong person, DNC, unclear audio, Hindi gender grammar.
**Honesty note:** these are simulated text conversations on the engine. Live-voice results belong in `evidence/` from your real Retell calls.

## Roadmap
Redis sessions · CRM webhook on call end · Groq Whisper STT path · eval harness scoring live transcripts · Hindi number-word parsing.
