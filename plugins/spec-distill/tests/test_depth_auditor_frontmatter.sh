#!/usr/bin/env bash
# guards: plugins/spec-distill/agents/depth-auditor.md
# AC7 — depth-auditor 도구 표면 0 · model 키 부재 · 출력 계약 · 입력 격리 문장.
set -u -o pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
AGENT="$REPO_ROOT/plugins/spec-distill/agents/depth-auditor.md"
. "$REPO_ROOT/shared/tests/assert.sh"
if [ "${1:-}" = "--emit-scanned" ]; then echo "plugins/spec-distill/agents/depth-auditor.md"; exit 0; fi
[ -f "$AGENT" ] || { no "agent 파일 부재: $AGENT"; finish; exit $?; }
FM="$(awk 'NR==1&&$0=="---"{f=1;next} f&&$0=="---"{exit} f' "$AGENT")"
grep -qE '^name: depth-auditor$' <<<"$FM" && ok "name: depth-auditor" || no "name 불일치"
tl="$(printf '%s\n' "$FM" | sed -n 's/^tools:[[:space:]]*//p' | head -1)"; tl="${tl%"${tl##*[![:space:]]}"}"
case "$tl" in "[]"|"[ ]") ok "tools: [] (도구 표면 0 — Law 2)";; *) no "tools 가 빈 리스트가 아니다: '$tl'";; esac
MODEL_KEY="^[\"']?model[\"']?[[:space:]]*:"
grep -qE "$MODEL_KEY" <<<"$FM" && no "frontmatter 에 model 키가 있다 (0.54.0 규약 위반)" || ok "model 키 없음 (tier-unpinned)"
grep -qE '^cost_class: (low|medium|high|variable)$' <<<"$FM" && ok "cost_class 선언" || no "cost_class 없음"
grep -qE '^\s+- tag: pairs$' <<<"$FM" && grep -qE '^\s+var: PAIRS_INLINE$' <<<"$FM" \
  && ok "input_slots: pairs/PAIRS_INLINE" || no "input_slots 에 pairs 슬롯이 없다"
# 본문 계약 — frontmatter 제외 본문에서
BODY="$(awk 'c>=2{print} /^---$/{c++}' "$AGENT")"
grep -qF '```depth-audit' <<<"$BODY" && ok "출력 계약: depth-audit 센티널" || no "depth-audit 센티널 부재"
grep -qE 'dug \| not_dug \| undecidable|dug.*not_dug.*undecidable' <<<"$BODY" && ok "라벨 어휘 셋" || no "라벨 어휘 부재"
grep -qF '짝 목록 밖' <<<"$BODY" && ok "입력 격리 문장(짝 목록 밖을 보지 마라)" || no "입력 격리 문장 부재"
grep -qE 'S<k> 의 어느 부분|어느 부분에서' <<<"$BODY" && ok "이유 줄에 출처 부분 요구" || no "출처 부분 요구 부재"
# 예시 짝 셋(관련 → dug / 다른 답에서 → not_dug / 무관 → not_dug) 이 본문에 있다
[ "$(grep -cE '^\s+label: (dug|not_dug)' <<<"$BODY")" -ge 3 ] && ok "예시 짝 ≥3" || no "예시 짝이 3개 미만"
finish
