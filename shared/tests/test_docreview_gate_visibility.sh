#!/usr/bin/env bash
# guards: shared/docreview/scripts/docreview_state.py shared/tests/fixtures/docreview/**
#
# 「승인을 막는 상태는 반드시 게이트 본문에 보인다」— 그리고 그 반대인 「막지 않는다고
# 표에 적힌 상태는 정말로 막지 않는다」(양성 짝, Ruling 19).
#
# 코퍼스를 열거하지 않는다 — `gate-rows` 가 내는 표에서 두 코퍼스를 **도출**한다:
#   · 가시성 코퍼스 — `render` 가 null 이 아닌 모든 행(승인을 막든 안 막든, 표가 「이
#     상태는 게이트 본문에 보여야 한다」고 선언한 전부). 각 행마다 그 상태 하나만
#     살아 있는 state 를 만들어 `gate --render` 본문에 그 finding id 가 나오는지 본다.
#   · 차단 코퍼스 — `blocks` 가 true 인 모든 행. 그 상태 하나만 살아 있으면
#     `approval_ready` 가 False 인지 본다.
# 행 ↔ 픽스처 집합 등식은 **가시성** 코퍼스로 잰다 — 렌더러가 있는 행은 모두 도달
# 픽스처가 있어야 하고(차단 여부와 무관), 브리프 원안의 「차단 코퍼스로 등식」은 이
# 태스크가 고치려는 축(비차단이라 안 그려지는 다섯 — `held_decide`·`ask_open`·
# `held_fix`·`superseded_expired`·`blocking_ask_open`)을 스스로 못 본다(Ruling 18).
#
# 양성 짝(Ruling 19) — `blocks` 가 false 인 행마다 그 상태 하나만 살아 있을 때
# `approval_ready` 가 True 인지도 같이 본다. 이게 없으면 「안 막는다」는 부재 단언이라,
# 실제로는 막는 행이 표에 `blocks: false` 로 잘못 적혀도 위 차단 단언들이 전부
# 공허하게 통과한다 — 절반짜리 락이 이빨 있는 척한다.
#
# 새 차단 상태가 표에 추가되면 이 락이 그 행의 픽스처(`gv_reach_<이름>`)를 요구하므로
# (아래 «행 ↔ 픽스처 집합 등식») 렌더를 빠뜨린 채 상태를 늘릴 수 없다.
set -uo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
. "$REPO_ROOT/shared/tests/assert.sh"
SCRIPTS="$REPO_ROOT/plugins/spec-distill/scripts"   # 형제 import(adjudication.py)가 잡히는 호스트 경로
if [ "${1:-}" = "--emit-scanned" ]; then
  echo "shared/docreview/scripts/docreview_state.py"; bash "$(dirname "$0")/docreview_fixture_corpus.sh"; exit 0
fi
. "$REPO_ROOT/shared/tests/fixtures/docreview/cases.sh"
export PYTHONDONTWRITEBYTECODE=1

# ── 행별 도달 픽스처 ────────────────────────────────────────────────────────
# `gv_reach_<행이름>` 은 「호출자가 만든 state 디렉토리(인자 `$1`)에 그 상태 하나만
# 살아 있는 원장을 짓고, 그 finding id 를 stdout 에 낸다」는 계약의 함수다. cases.sh 의
# `r1`·`route_r1`·`mk_state` 는 **자기 mktemp 로 새 디렉토리를 만들어 돌려준다** — 이
# 락의 루프는 반대로 디렉토리를 먼저 만들어 **넘겨준다**(그래야 `gate --state-dir "$d"`
# 가 같은 디렉토리를 본다). 그래서 그 셋을 그대로 못 쓰고, `init`+`begin-round` 만 하는
# 얇은 변형(`gv_r1`)을 이 락 안에 따로 둔다 — cases.sh 를 오염시키지 않는다(브리프
# 원문의 이유와 같다). `seed_findings`·`next_round`·저수준 CLI(`decide`·`fix`·`ask`)는
# 이미 명시 `--state-dir` 를 받으므로 그대로 재사용한다.
gv_r1() {   # gv_r1 <state-dir> <profile> <doc>
  py docreview_state.py init --state-dir "$1" --doc "$3" --profile "$2" >/dev/null || return 1
  # 파일명은 반드시 s1.json — `next_round()`(cases.sh) 가 다음 라운드에서
  # `$d/s$((n-1)).json` 로 이 파일을 도로 찾는다(r1() 과 같은 이름 계약).
  local s="$1/s1.json"; snap "$3" "$s"
  py docreview_state.py begin-round --state-dir "$1" --snapshot "$s" >/dev/null || return 1
}

gv_reach_open_decide() {
  local d="$1"
  gv_r1 "$d" "$PROF_SD/design-doc.md" "$FX/design-sample.md" || return 1
  seed_findings "$d" "[$F_DEC]" || return 1
  echo 'aaaa0001#r1.1'
}

gv_reach_adopted() {
  local d="$1"
  gv_r1 "$d" "$PROF_SD/design-doc.md" "$FX/design-sample.md" || return 1
  seed_findings "$d" "[$F_DEC]" || return 1
  py docreview_state.py decide --state-dir "$d" --id 'aaaa0001#r1.1' --choice adopt --quote '채택' >/dev/null || return 1
  echo 'aaaa0001#r1.1'
}

gv_reach_blocked_expired() {
  local d="$1"
  gv_r1 "$d" "$PROF_SD/design-doc.md" "$FX/design-sample.md" || return 1
  seed_findings "$d" "[$F_DEC]" || return 1
  py docreview_state.py decide --state-dir "$d" --id 'aaaa0001#r1.1' --choice adopt --quote '채택' >/dev/null || return 1
  next_round "$d" "$FX/design-sample.md" >/dev/null || return 1   # 변경 없음 → expired (superseded_by 없음, finalize 안 지남)
  echo 'aaaa0001#r1.1'
}

# superseded_expired 는 production 경로로는 `docreview_route.py finalize` 의 재상승
# 루프에서만 나고, 그 루프는 항상 새 open decide(후속)를 같이 만든다 — 「그 행 하나만
# 살아 있는」 상태를 finalize 로는 못 짓는다(후속이 곧 open_decide 행도 함께 켠다).
# `st_set_stale_pointer.py`(cases.sh 의 case_AC20_stale_pointer_cleared_on_reobserve 가
# 쓰는 같은 픽스처)로 만료 레코드에 `superseded_by` 만 직접 심어 격리한다.
gv_reach_superseded_expired() {
  local d="$1"
  gv_r1 "$d" "$PROF_SD/design-doc.md" "$FX/design-sample.md" || return 1
  seed_findings "$d" "[$F_DEC]" || return 1
  py docreview_state.py decide --state-dir "$d" --id 'aaaa0001#r1.1' --choice adopt --quote '채택' >/dev/null || return 1
  next_round "$d" "$FX/design-sample.md" >/dev/null || return 1   # 변경 없음 → expired
  python3 "$FX/st_set_stale_pointer.py" "$d/docreview-state.md" 'aaaa0001#r1.1' 'zzzz9999#r9.9' '#12-files-to-modify' || return 1
  echo 'aaaa0001#r1.1'
}

gv_reach_held_decide() {
  local d="$1"
  gv_r1 "$d" "$PROF_SD/design-doc.md" "$FX/design-sample.md" || return 1
  seed_findings "$d" "[$F_DEC]" || return 1
  py docreview_state.py decide --state-dir "$d" --id 'aaaa0001#r1.1' --choice hold --quote '나중에' >/dev/null || return 1
  echo 'aaaa0001#r1.1'
}

gv_reach_unapplied_fix() {
  local d="$1"
  gv_r1 "$d" "$PROF_SD/design-doc.md" "$FX/design-sample.md" || return 1
  seed_findings "$d" "[$F_FIX]" || return 1
  echo 'bbbb0001#r1.1'
}

# check-intent 를 거치지 않고 저수준 CLI 로 바로 escalate 한다 — Task 2 의 escalated
# 케이스들과 같은 수법(브리프 인터페이스 노트가 명시한 이유: check-intent 경유는 상태
# 가드를 갖지만 이 저수준 CLI 는 안 가져 격리하기 쉽다).
gv_reach_escalated_fix() {
  local d="$1"
  gv_r1 "$d" "$PROF_SD/design-doc.md" "$FX/design-sample.md" || return 1
  seed_findings "$d" "[$F_FIX]" || return 1
  py docreview_state.py fix --state-dir "$d" --id 'bbbb0001#r1.1' --event escalate --reason 'check-intent 거부' >/dev/null || return 1
  echo 'bbbb0001#r1.1'
}

gv_reach_held_fix() {
  local d="$1"
  gv_r1 "$d" "$PROF_SD/design-doc.md" "$FX/design-sample.md" || return 1
  seed_findings "$d" "[$F_FIX,$F_ASK]" || return 1   # F_ASK 가 F_FIX 를 blocks 로 지목 → record_findings 가 fix 를 held 로
  echo 'bbbb0001#r1.1'
}

gv_reach_blocking_ask_open() {
  local d="$1"
  gv_r1 "$d" "$PROF_SD/design-doc.md" "$FX/design-sample.md" || return 1
  seed_findings "$d" "[$F_FIX,$F_ASK]" || return 1
  echo 'cccc0001#r1.1'
}

# ask_open 은 blocks 가 비고 from_decide 도 아닌 일반 ask 다 — F_ASK(cases.sh)는 blocks
# 가 있어(blocking_ask_open 전용) 못 쓰므로, 이 락 전용의 짧은 템플릿을 따로 둔다.
GV_F_ASK_PLAIN='{"id":"gggg0001#r1.1","lineage":"gggg0001#r1.1","bucket":"gggg0001","origin":"reviewer","layer":2,"category":"ambiguity","anchor":"#12-files-to-modify","edit_scope":"#12-files-to-modify","disposition":"ask","summary":"그냥 물어보기(비차단)","evidence":null,"blocks":[]}'
gv_reach_ask_open() {
  local d="$1"
  gv_r1 "$d" "$PROF_SD/design-doc.md" "$FX/design-sample.md" || return 1
  seed_findings "$d" "[$GV_F_ASK_PLAIN]" || return 1
  echo 'gggg0001#r1.1'
}

# ── 도출 ────────────────────────────────────────────────────────────────────
ROWS_JSON="$(py docreview_state.py gate-rows)"
RENDERED="$(printf '%s' "$ROWS_JSON" | jgets '" ".join(r["name"] for r in d if r["render"] is not None)')"
n_rendered="$(printf '%s\n' $RENDERED | grep -c . || true)"
# vacuity 하한 — 가시성 코퍼스가 8건에 못 미치면 아래 루프가 거의 아무것도 단언하지
# 않고 GREEN 이 될 수 있다(표가 통째로 비거나 렌더러가 대부분 지워진 상태).
[ "$n_rendered" -ge 8 ] \
  && ok "도출: 가시성 행 ${n_rendered}건 (하한 8)" \
  || no "도출: 가시성 행이 ${n_rendered}건이다 — 표 도출이 깨졌거나 렌더 대상 집합이 비었다. 아래 단언은 무의미하다"

BLOCKING="$(printf '%s' "$ROWS_JSON" | jgets '" ".join(r["name"] for r in d if r["blocks"])')"
n_block="$(printf '%s\n' $BLOCKING | grep -c . || true)"
[ "$n_block" -ge 4 ] \
  && ok "도출: 차단 행 ${n_block}건 (하한 4)" \
  || no "도출: 차단 행이 ${n_block}건이다 — 표 도출이 깨졌거나 차단 집합이 비었다. 아래 단언은 무의미하다"

# 행 ↔ 픽스처 집합 등식 — **가시성** 코퍼스로 잰다(Ruling 18). `blocks` 코퍼스로
# 재면 이 태스크가 고치려는 다섯 비차단 행(held_decide 등)이 등식 밖에 남아, 그
# 다섯의 렌더러를 전부 지워도 이 등식은 여전히 통과한다 — 이 락이 존재하는 이유
# 그 자체를 놓친다.
HAVE="$(declare -F | sed -n 's/^declare -f gv_reach_//p' | sort | tr '\n' ' ')"
assert_eq "$(printf '%s\n' $RENDERED | sort | tr '\n' ' ')" "$HAVE" \
  "등식: 표의 가시성 행 집합 = 이 락이 도달 픽스처를 가진 행 집합"

# ── 가시성 + 차단/양성 짝 ───────────────────────────────────────────────────
for row in $RENDERED; do
  d="$(mktemp -d -t gv-XXXXXX)"
  if [ -z "$d" ] || [ ! -d "$d" ]; then
    no "도달: $row — mktemp 실패로 임시 디렉토리를 못 만들었다(가드)"
    continue
  fi
  fid="$("gv_reach_$row" "$d")"
  if [ -z "$fid" ]; then
    no "도달: $row 픽스처가 실패했다(finding id 를 못 냈다)"
    rm -rf "$d"
    continue
  fi
  out="$(py docreview_state.py gate --state-dir "$d" --render)"
  case "$out" in
    *"$fid"*) ok "가시: 행 $row 의 항목 $fid 가 게이트 본문에 나온다" ;;
    *)        no "가시: 행 $row 의 항목 $fid 가 게이트 본문에 없다 — 표는 렌더 대상이라는데 실제로 안 보인다(fail-open)" ;;
  esac
  ar="$(py docreview_state.py gate --state-dir "$d" | jgets 'd["approval_ready"]')"
  case " $BLOCKING " in
    *" $row "*)
      # 차단 코퍼스 — 짝이 되는 양의 단언(이 상태가 실제로 막고 있는가)이 없으면
      # 「막는데 안 보인다」류 위 가시성 단언이 이 상태가 애초에 막지 않을 때도
      # 공허하게 무의미해질 수 있다.
      assert_eq "$ar" "False" "차단: 행 $row 하나만 살아 있으면 approval_ready 는 False" ;;
    *)
      # 양성 짝(Ruling 19) — 표가 `blocks: false` 라고 적은 행은 실제로도 안 막아야
      # 한다. 이게 없으면 실제로는 막는 행이 표에 거짓으로 `blocks: false` 라고
      # 적혀도 이 락은 못 잡는다(부재 단언에는 짝이 없으면 이빨이 없다).
      assert_eq "$ar" "True" "양성 짝: 행 $row(비차단) 하나만 살아 있으면 approval_ready 는 True" ;;
  esac
  rm -rf "$d"
done
finish
