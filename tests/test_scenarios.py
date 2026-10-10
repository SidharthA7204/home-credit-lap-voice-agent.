import pytest

from .runner import check, run
from .scenarios import SCENARIOS


@pytest.mark.parametrize("sc", SCENARIOS, ids=[s.id for s in SCENARIOS])
async def test_scenario(sc):
    eng, last = await run(sc)
    errs = check(sc, eng, last)
    assert not errs, f"{sc.id} {sc.name}: {errs}\nTRANSCRIPT: {eng.transcript}"
