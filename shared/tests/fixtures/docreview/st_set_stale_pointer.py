#!/usr/bin/env python3
"""decides 레코드에 «낡은» superseded_by 를 심고 같은 id 를 겨눈 새 미소비 permit 을
연다(픽스처 전용, st_set_reraise.py 와 같은 종류의 상태 강제 도구).

**Task 3 시점 한정** — CLI 로는 이 조합에 도달할 수 없다: `cmd_decide` 는
`state == "open"` 인 decide 만 받고(§`docreview_state.cmd_decide`), `record-findings`
로 같은 id 를 다시 심으면 `record_findings` 가 decides 레코드를 통째로 새 dict 로
덮어써 기존 `superseded_by` 를 지운다(§`docreview_state.record_findings`). 하지만
Task 4 의 만료 재결정 탈출구(`cmd_decide` 가 `state in ("open", "expired")` 를 받게
넓어짐)는 이 조합을 실경로로 만든다 — 그 탈출구는 `st["reraise"]` 의 미소비 예약만
폐기하고 `superseded_by` 는 안 지우므로, 재결정이 낡은 포인터를 그대로 들고 새
permit 을 연다. 그래서 이 픽스처는 영원히 도달 불가한 상태를 증명하는 게 아니라
다음 태스크가 열 창을 미리 격리해 재는 것이다 — `cmd_observe_diff` 의
`d.pop("superseded_by", None)` 가 그 상태에서 작동하는지를 지금 잰다.

경로 계산은 st_set_reraise.py 와 같다: `parents[3]` 이 이미 `shared/` 이므로 "shared"
세그먼트를 다시 붙이지 않는다.
"""
import sys, pathlib
SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[3] / "docreview" / "scripts"
assert SCRIPTS_DIR.is_dir(), "resolved scripts dir missing: %s" % SCRIPTS_DIR
sys.path.insert(0, str(SCRIPTS_DIR))
from docreview_state import load_state, save_state  # noqa: E402
state_file, fid, stale_ptr, anchor = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
d = str(pathlib.Path(state_file).parent)
st = load_state(d)
st["decides"][fid]["superseded_by"] = stale_ptr
n = int(st["round"])
st["permits"]["FIXTURE.%s" % fid] = {"kind": "apply", "apply_anchors": [anchor], "round": n + 1,
                                      "finding_id": fid, "consumed": False}
save_state(d, st, "fixture: stale superseded_by + fresh permit on %s" % fid)
