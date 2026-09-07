#!/usr/bin/env python3
"""state 파일의 st["reraise"] 에 지정 finding_id 예약 하나를 심는다(픽스처 전용).

경로 계산 노트(task-2-brief 의 st_set_reraise.py 초안 수정) — 이 파일은
`shared/tests/fixtures/docreview/st_set_reraise.py` 에 있다. `Path(__file__).resolve().parents`
는 [0]=…/docreview, [1]=…/fixtures, [2]=…/tests, [3]=…/shared 순으로 오르므로
`parents[3]` 은 이미 리포의 `shared/` 디렉토리다 — 거기에 다시 "shared" 를 붙이면
`shared/shared/docreview/scripts` 가 되어 import 가 죽는다(초안의 버그). "shared" 세그먼트
없이 `parents[3] / "docreview" / "scripts"` 로 바로 내려간다.
"""
import sys, pathlib
SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[3] / "docreview" / "scripts"
assert SCRIPTS_DIR.is_dir(), "resolved scripts dir missing: %s" % SCRIPTS_DIR
print("st_set_reraise: scripts dir = %s" % SCRIPTS_DIR, file=sys.stderr)
sys.path.insert(0, str(SCRIPTS_DIR))
from docreview_state import load_state, save_state  # noqa: E402
d = str(pathlib.Path(sys.argv[1]).parent)
st = load_state(d)
st["reraise"] = [{"finding_id": sys.argv[2], "kind": "apply", "reason": "픽스처가 심은 미소비 예약"}]
save_state(d, st, "fixture: seed unconsumed reraise")
