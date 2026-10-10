"""Run every scripted scenario and write docs/test_results.md (honest, regenerated from real runs)."""
import asyncio
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.runner import check, run  # noqa: E402
from tests.scenarios import SCENARIOS  # noqa: E402


async def main() -> int:
    rows, details, failed = [], [], 0
    for sc in SCENARIOS:
        eng, last = await run(sc)
        errs = check(sc, eng, last)
        failed += bool(errs)
        status = "PASS" if not errs else "FAIL"
        rows.append(f"| {sc.id} | {sc.name} | {sc.outcome} | {eng.state.outcome.value} | {status} |")
        convo = "\n".join(f"- **{r.title()}:** {t}" for r, t in eng.transcript)
        details.append(f"### {sc.id} - {sc.name} ({status})\n{convo}\n\n```json\n{__import__('json').dumps(eng.state.to_record(), ensure_ascii=False, indent=2)}\n```\n"
                       + ("" if not errs else f"**Failures:** {errs}\n"))
    out = [f"# Test Results (deterministic engine, rule-based extractor)\n\nGenerated {date.today()} by `scripts/run_scenarios.py`. "
           f"{len(SCENARIOS) - failed}/{len(SCENARIOS)} passed.\n\n"
           "> These are simulated text conversations against the dialog engine. Live voice-call results (recordings/links) are listed separately in `evidence/`.\n\n"
           "| ID | Scenario | Expected | Actual | Status |\n|---|---|---|---|---|", *rows, "\n## Transcripts\n", *details]
    (ROOT / "docs" / "test_results.md").write_text("\n".join(out), encoding="utf-8")
    print(f"{len(SCENARIOS) - failed}/{len(SCENARIOS)} passed -> docs/test_results.md")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
