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
# 존재 검사(∃)가 아니라 지배 관계다. `grep -qF '```depth-audit'` 한 줄이면 본문 «어디든»
# 하나만 있으면 통과하고, 그래서 런타임에 실제로 소비되는 유일한 것(출력 계약 펜스)만
# 깨뜨려도 15줄 위의 «예시» 펜스가 대신 만족시킨다 — 결과는 모든 인터뷰에서 영구
# `unavailable` 인데 락은 GREEN 이다(수정 라운드 1 F2, 리뷰어 실측). 그래서 ①본문 전체에
# 둘 이상 있고 ②그중 하나가 «출력» 절 안에 있을 것을 함께 건다. 대상은 문면이 아니라
# 구조에서 도출한다 — 절 경계(`^## 출력`)로 자른다.
OUT_SEC="$(awk '/^## 출력/{f=1;next} /^## /{f=0} f' <<<"$BODY")"
n_fence="$(grep -cF '```depth-audit' <<<"$BODY")"
n_out_fence="$(grep -cF '```depth-audit' <<<"$OUT_SEC")"
{ [ "${n_fence:-0}" -ge 2 ] && [ "${n_out_fence:-0}" -ge 1 ]; } \
  && ok "출력 계약: depth-audit 센티널 (본문 ${n_fence}개 · 출력 절 안 ${n_out_fence}개)" \
  || no "depth-audit 센티널: 본문 ${n_fence}개 · 출력 절 안 ${n_out_fence}개 — 출력 절 «안»에 계약 펜스가 있어야 한다(예시 절의 펜스로 대체되지 않는다)"
grep -qE 'dug \| not_dug \| undecidable|dug.*not_dug.*undecidable' <<<"$BODY" && ok "라벨 어휘 셋" || no "라벨 어휘 부재"
grep -qF '짝 목록 밖' <<<"$BODY" && ok "입력 격리 문장(짝 목록 밖을 보지 마라)" || no "입력 격리 문장 부재"
grep -qE 'S<k> 의 어느 부분|어느 부분에서' <<<"$BODY" && ok "이유 줄에 출처 부분 요구" || no "출처 부분 요구 부재"
# 예시 짝 셋(관련 → dug / 다른 답에서 → not_dug / 무관 → not_dug) 이 본문에 있다
[ "$(grep -cE '^\s+label: (dug|not_dug)' <<<"$BODY")" -ge 3 ] && ok "예시 짝 ≥3" || no "예시 짝이 3개 미만"
finish
