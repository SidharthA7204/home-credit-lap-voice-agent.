"""Interactive text simulator:  python -m app.cli [--lang hi] [--gender male]"""
import argparse
import asyncio

from .config import get_settings
from .dialog import CallContext, DialogEngine
from .main import build_extractor


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--lang", default="en")
    p.add_argument("--gender", default=None)
    p.add_argument("--name", default="Rahul Sharma")
    a = p.parse_args()
    st = get_settings()
    ctx = CallContext(a.name, st.company_name, st.agent_name, a.gender or st.agent_gender, a.lang, "10:00")
    eng = DialogEngine(build_extractor(st), ctx, st.max_unclear_retries)
    print("AGENT:", eng.opening().reply)
    while not eng.state.stage.value == "ended":
        res = await eng.handle(input("YOU:   "))
        print("AGENT:", res.reply)
    print("\n--- structured record ---")
    import json
    print(json.dumps(eng.state.to_record(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
