#!/usr/bin/env bash
# PN2/V8/AC10 — reviewing-spec is design-mode only; spec-mode/re-consensus/Mode B removed;
# drafting-spec absent from skills/hooks/commands.
#
# ── 앵커 재조준 (문서 리뷰 엔진 전환) ────────────────────────────────────────
# 이 파일의 두 **양의** 단언은 옛 라우팅 표의 두 행(`design | approved | … Human Gate`,
# `design | needs_revise | … author 회귀`)을 잡고 있었다. 그 표는 verdict 어휘 위에
# 서 있었는데, 껍데기화로 verdict 자체가 사라졌다 — 라우팅은 이제 `docreview_route.py
# finalize` 의 처분 회계가 하고 표는 없다. 없어진 문자열을 계속 요구하면 이 락은
# **거짓 인용을 강제**하는 장치가 된다(삭제된 규칙이 남기는 거짓 인용).
#
# 그래서 파일을 지우지 않고 두 양의 단언만 재조준한다. 이 파일의 주제 — *"이 skill 은
# design 자리 전용인가"* — 는 껍데기에서도 그대로 참이고, 그 주제를 오늘 지탱하는 것은
# 표가 아니라 **프로필 선택**이다: 이 skill 은 `design-doc.md` 하나만 고르고, 훅이 내는
# `mode:` 두 값(`design`·`spec`)이 그 하나로 모인다. 그 매핑이 갈라지는 순간 이 skill 은
# design 전용이 아니게 된다.
#
# 아래 **부재** 단언 넷(re-consensus · mode_b_violation · spec-mode 표 행 · drafting-spec)
# 은 손대지 않는다 — 그것들이 잠그는 개념은 껍데기에서도 여전히 되살아나면 안 된다.
set -u -o pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PLUGIN="$REPO_ROOT/plugins/spec-distill"
SKILL="$PLUGIN/skills/reviewing-spec/SKILL.md"

. "$(cd "$(dirname "$0")/../../.." && pwd)/shared/tests/assert.sh"

# (1) 이 skill 이 고르는 프로필은 design-doc 하나다.
grep -qF 'references/docreview-profiles/design-doc.md' "$SKILL" \
  && ok "design-doc 프로필을 이름으로 고른다" \
  || no "design-doc 프로필 선택이 사라졌다 — 이 skill 이 어느 자리인지 문서가 말하지 않는다"

# (2) 훅이 내는 `mode:` 두 값이 **그 하나로** 모인다고 적혀 있다. 값 둘을 함께 요구하는
#     이유: 한쪽만 적으면 다른 값이 왔을 때 무엇을 할지가 껍데기 밖으로 새고, 그것이
#     이 skill 을 design 전용이 아니게 만드는 정확한 경로다.
if grep -qE 'design.*spec.*design-doc\.md|`design`.*`spec`' "$SKILL" \
   && grep -qF 'design-doc.md' "$SKILL"; then
  ok "mode 매핑: design·spec 두 값이 같은 design-doc 프로필로 모인다"
else
  no "mode 매핑 문장이 없다 — 훅의 두 값 중 하나가 다른 프로필로 갈 여지가 생긴다"
fi

grep -qiE 'reconsensus|re-consensus|\[3\.5\]' "$SKILL" \
  && no "re-consensus gate still present (should be removed)" \
  || ok "re-consensus [3.5] removed"
grep -qE 'mode_b_violation' "$SKILL" \
  && no "mode_b_violation still present" || ok "mode_b_violation removed"
grep -qE '^\|[[:space:]]*\**[[:space:]]*spec\b' "$SKILL" \
  && no "spec-mode routing rows still present" || ok "spec-mode routing rows removed"
grep -q 'drafting-spec' "$SKILL" \
  && no "drafting-spec still referenced in reviewing-spec" || ok "drafting-spec ref removed from reviewing-spec"

# F9-D: scan agents/ + templates/ too — the exact dirs this PR cleaned of
# drafting-spec/Mode-B refs (spec-reviewer persona, spec-template comment).
# Task 33: `$PLUGIN/references` (플러그인 레벨 공유 계약, skills/ 밖) 도 스캔 루트다.
#
# 〔fix round 1 / F4〕 루트를 덧붙이기만 하면 오타·개명 시 `grep -r` 의 *No such file* 이
# `2>/dev/null` 에 삼켜지고, 이 **부재** 단언은 좁아진 코퍼스 위에서 통과한다(조용한 축소).
# 열거한 루트가 전부 실재하는지 먼저 잰다.
F9D_ROOTS=("$PLUGIN/skills" "$PLUGIN/hooks" "$PLUGIN/commands" \
  "$PLUGIN/agents" "$PLUGIN/templates" "$PLUGIN/references")
for _r in "${F9D_ROOTS[@]}"; do
  [[ -d "$_r" ]] \
    && ok "AC10/F9-D: 스캔 루트 실재 — ${_r#"$PLUGIN/"}" \
    || no "AC10/F9-D: 스캔 루트 '${_r#"$PLUGIN/"}' 부재 — grep -r 이 그 코퍼스를 조용히 건너뛴다"
done
COUNT=$(grep -rl 'drafting-spec' "${F9D_ROOTS[@]}" 2>/dev/null | wc -l | tr -d ' ')
[[ "$COUNT" == "0" ]] && ok "AC10/F9-D: 0 drafting-spec refs in skills/hooks/commands/agents/templates" \
  || no "AC10/F9-D: $COUNT drafting-spec refs remain"
[[ ! -d "$PLUGIN/skills/drafting-spec" ]] && ok "drafting-spec/ directory removed" \
  || no "drafting-spec/ directory still exists"
finish
