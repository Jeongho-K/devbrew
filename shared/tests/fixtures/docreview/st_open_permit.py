#!/usr/bin/env python3
"""이미 만료(expired)한 decides 레코드에 같은 id 를 겨눈 미소비 permit 을 하나 더
연다(픽스처 전용, st_set_reraise.py·st_set_stale_pointer.py 와 같은 종류의 상태
강제 도구) — `cmd_decide` 를 거치지 않는다.

**Task 4 시점 정정** — 원안(`shared/tests/fixtures/docreview/cases.sh` 의
`case_AC21_reraise_dedup` R1 실행 노트)은 `seed_findings` 로 같은 id 를 다시
disposition=decide 로 심어 `record_findings` 가 그 decides 레코드를 "open" 으로
되돌리는 것을 이용해 두 번째 permit 을 열려 했다. 그 재심기 자체는 `cmd_decide` 를
거치지 않지만, 바로 다음 줄이 그 (지금은 "open" 인) 항목을 실제 `cmd_decide` 로
다시 채택한다 — Task 4 의 재결정 탈출구는 **모든** `cmd_decide` 호출에서 새 permit
을 여는 것과 그 id 의 미소비 예약을 폐기하는 것을 **같은 호출 안에서 함께** 하므로
(§`docreview_state.cmd_decide`, 설계 §6.4 상호배제의 절반), 이 원안은 첫 예약을
스스로 지워버려 dedup 이 막아야
할 「같은 id 의 예약 둘」 조합 자체를 만들지 못한다(실측: `reraise_no_dedup` 변이가
no_teeth — 변이 있든 없든 결과가 똑같이 `(1, 1)`). 그래서 이 픽스처로 `cmd_decide`
를 완전히 우회해 두 번째 permit 을 직접 연다 — 이미 있는 미소비 예약을 그대로 둔
채로.

경로 계산은 st_set_reraise.py 와 같다: `parents[3]` 이 이미 `shared/` 이므로 "shared"
세그먼트를 다시 붙이지 않는다.
"""
import sys, pathlib
SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[3] / "docreview" / "scripts"
assert SCRIPTS_DIR.is_dir(), "resolved scripts dir missing: %s" % SCRIPTS_DIR
sys.path.insert(0, str(SCRIPTS_DIR))
from docreview_state import load_state, save_state  # noqa: E402
state_file, fid, anchor = sys.argv[1], sys.argv[2], sys.argv[3]
d = str(pathlib.Path(state_file).parent)
st = load_state(d)
n = int(st["round"])
st["permits"]["FIXTURE2.%s" % fid] = {"kind": "apply", "apply_anchors": [anchor], "round": n + 1,
                                       "finding_id": fid, "consumed": False}
save_state(d, st, "fixture: extra unconsumed permit on %s" % fid)
