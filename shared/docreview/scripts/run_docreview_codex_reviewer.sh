#!/usr/bin/env bash
# run_docreview_codex_reviewer.sh — 문서 리뷰 엔진(shared/docreview)의 codex co-reviewer. 정본.
#
# **처분** — consumer=orchestrator · fail-open · disclosure=advisory
#
# 실제 소비자는 같은 엔진의 docreview_route.py(§6.3 라우팅의 codex 입력)다. 이 파일은
# spec-distill·quality-gates 두 플러그인에 같은 파일 단위 심볼릭 링크로 배포되므로(설계
# §12 「신규(호스트)」) consumer= 경로가 어느 한 플러그인과도 같을 수 없다(처분 락 축 A⑤
# — 이 파일 자체가 애초에 어느 플러그인 서브트리에도 없다). 그래서 orchestrator 로 적고
# 실제 소비자는 이 주석이 밝힌다. fail-open 인 이유는 형제 run_spec_codex_reviewer.sh 와
# 같다 — codex 는 모델 다양성 보조지 주 판정자가 아니다(설계 §9 「codex 부재·실패」행:
# 공시하되 막지 않는다).
#
# Usage: run_docreview_codex_reviewer.sh <profile.md> <doc-or-bundle> <project_dir> <out_yaml>
# 성공·실패 모두 <out_yaml> 에 codex_findings_to_yaml.py --emit-keys docreview 스키마의
# 중첩 YAML 을 쓴다. <out_yaml> 자체를 못 쓰면(디렉토리 부재·권한·RO 마운트) YAML 이
# 애초에 불가능하므로 rc 3 으로 죽는다 — 호출자는 rc==3 을 보면 <out_yaml> 을 지워야
# 한다(형제 run_spec_codex_reviewer.sh·run_brief_codex_reviewer.sh 와 같은 계약. 이 fail-
# closed 가 핵심이다 — 조용히 죽으면 직전 라운드의 stale YAML 이 이번 라운드 판정으로
# 읽힌다).
#
# 프롬프트 빌더는 자리별 파일(build_*_codex_prompt.py)로 안 뽑는다 — 문서 리뷰 엔진은
# 프로필 넷을 전부 이 러너 하나로 흡수하므로(설계 §5.2), 빌더는 아래 인라인 python 함수
# 하나다.
set -euo pipefail

PROFILE="${1:-}"
DOC="${2:-}"
PROJECT_DIR="${3:-}"
OUTPUT_PATH="${4:-}"

# CLAUDE_PLUGIN_ROOT는 훅 실행에만 주입된다 — 스킬의 bash 블록에는 오지 않는다.
# fallback 없이 참조하면 `set -u` 아래서 codex에 도달하기 전에 즉사한다. 형제
# 러너들과 같은 철자를 쓴다(세 번째 철자를 발명하지 않는다).
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

if [[ -z "$OUTPUT_PATH" ]]; then
  echo "usage: run_docreview_codex_reviewer.sh <profile> <doc-or-bundle> <project_dir> <out_yaml>" >&2
  exit 2
fi

# 절대화는 `cd "$PROJECT_DIR"` **이전**이다 — 아니면 상대 경로가 project_dir 기준으로
# 조용히 잘못 풀린다(형제 run_spec_codex_reviewer.sh B3 의 교훈과 같은 자리).
[[ "$OUTPUT_PATH" = /* ]] || OUTPUT_PATH="$PWD/$OUTPUT_PATH"
[[ "$DOC" = /* ]] || DOC="$PWD/$DOC"
[[ "$PROFILE" = /* ]] || PROFILE="$PWD/$PROFILE"

# stale 제거 + 쓰기 가능성 확인을 자원을 처음 만지는 지점에서 한다. 여기서 실패하면
# YAML 자체가 불가능하므로 rc 3 — 호출자가 <out_yaml> 을 지워야 한다는 계약의 근거다.
: > "$OUTPUT_PATH" 2>/dev/null || {
  echo "[docreview] 산출물 경로에 쓸 수 없다: $OUTPUT_PATH" >&2
  exit 3
}

# `write_failclosed` · `_degrade_if_empty` 는 shared/codex/runner_common.sh 정본을
# 그대로 쓴다(설계 §5.2 표 「reviewing-document.md」 행의 의존). source 를 가드한다 —
# 위 guarded truncate 가 이미 OUTPUT_PATH 를 0바이트로 만들어 놨고 트랩은 아직
# 안 떴다. source 실패가 `set -e` 아래서 즉사하면 0바이트 산출물이 "성공, 발견 0건"
# 으로 읽힌다.
# shellcheck source=/dev/null
_RUNNER_COMMON="$(dirname -- "${BASH_SOURCE[0]}")/runner_common.sh"
if [ -r "$_RUNNER_COMMON" ] && bash -n "$_RUNNER_COMMON" 2>/dev/null \
   && . "$_RUNNER_COMMON"; then
  :
else
  printf 'findings: []\nmeta:\n  codex_failed: true\n  reason: runner_common_unloadable\n  exit_code: 0\n' \
    > "$OUTPUT_PATH" 2>/dev/null || {
      echo "[docreview] runner_common.sh 로드 실패 + 산출물 기록 실패 — 호출자는 stale 을 지워야 한다" >&2
      exit 3
    }
  echo "[docreview] runner_common.sh 를 로드할 수 없다 — degrade 기록 후 종료(공유 정본 미배포)" >&2
  exit 0
fi
emit_fallback() { write_failclosed "$OUTPUT_PATH" "$1" || exit 3; exit 0; }

[[ -n "$PROJECT_DIR" ]] || emit_fallback missing_project_dir
[[ -f "$PROFILE" ]] || emit_fallback profile_missing
[[ -f "$DOC" ]] || emit_fallback doc_missing
cd "$PROJECT_DIR" || emit_fallback project_dir_unreachable

# 스크래치 디렉토리 대입은 트랩 무장 **이전**이다(`cd ""` repo-delete footgun 회피).
SCRATCH="$(mktemp -d -t docreview-codex-XXXXXX)" || emit_fallback scratch_dir_uncreatable
# 트랩 한 줄 — 여러 줄로 펼치면 순서 락이 이 줄을 못 보고 무력화된다(형제 러너 계약과 같다).
trap 'rm -rf "$SCRATCH"; _degrade_if_empty "$OUTPUT_PATH" aborted_before_completion' EXIT
PROMPT_FILE="$SCRATCH/prompt.md"
WEB_META_FILE="$SCRATCH/web.meta"
STDOUT_FILE="$SCRATCH/codex.jsonl"
STDERR_FILE="$SCRATCH/codex.stderr"

# 프롬프트 조립(러너 안 인라인 빌더) — 프로필의 frontmatter(`layer_rubric` ·
# `allowed_dispositions` · `web`) 와 shared/codex/prompt-preamble.md(P21) 로 프롬프트
# 하나를 낸다. `web` 판정을 **같은 호출에서** WEB_META_FILE 에 함께 써서, frontmatter
# 파싱을 두 번(프롬프트용 · 웹 스위치용) 하지 않는다 — 파싱이 한 곳이면 그 결과를 두
# 갈래로 읽는 자리가 하나이므로 웹 인자를 만드는 지점도 하나로 유지하기 쉽다(P11).
if ! python3 - "$PROFILE" "$DOC" "$PLUGIN_ROOT/scripts/prompt-preamble.md" "$WEB_META_FILE" \
       > "$PROMPT_FILE" <<'PY'
import pathlib, re, sys

prof_path, doc_path, preamble_path, meta_path = sys.argv[1:5]

t = pathlib.Path(prof_path).read_text(encoding="utf-8")
m = re.match(r"^---\n(.*?)\n---\n", t, re.DOTALL)
fm_text = m.group(1) if m else ""

# PyYAML 없이 stdlib 만으로 — 형제 러너 셋(build_brief_codex_prompt.py ·
# build_seed_codex_prompt.py · build_spec_codex_prompt.py)이 third-party 모듈을
# 안 쓰는 것과 같은 이유다: 이 러너는 `HOME` 이 격리되는 하니스(예: codex 인증
# 격리)에서 site-packages 의 PyYAML 에 닿지 못해 죽는다(실측 — 이 파일이 그
# 하니스에서 유일하게 third-party import 를 했다). 필요한 것은 프로필
# frontmatter 의 셋뿐이고 넷 다 한 줄짜리 flow-list/불리언이므로(design-doc·
# brief·seed·generic 프로필 실측 — 참고: `docreview_state.py:load_profile()` 은
# 이 넷을 훨씬 엄격하게 검증하지만 그건 정본 스키마 게이트이지 이 러너가
# 다시 구현할 대상이 아니다) 새 YAML 파서를 발명하지 않고 그 모양만 좁게 뽑는다.
def _unquote(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        v = v[1:-1]
    return v


def _flow_list(key, text):
    # `layer1`·`layer2` 는 `layer_rubric:` 아래 2칸 들여쓰기다 — `allowed_
    # dispositions` 는 최상위(들여쓰기 없음). 둘 다 받으려면 줄 시작의 임의
    # 공백을 허용해야 한다(`^\s*`) — 앵커를 열 칸 고정으로 두면 한쪽이 깨진다.
    #
    # 형식은 **둘 다** 받는다 — flow(`key: [a, b, c]`)와 block(`key:\n  - a\n
    # - b`). `load_profile()`(docreview_state.py, 실 PyYAML)은 이 상위 스키마
    # 게이트라 둘 다 통과시키는데, 이 러너가 flow만 읽으면 그 게이트가 아무것도
    # 보호하지 못한다 — design-doc.md 의 `protected_headings` 가 이미 block
    # 이고(리뷰 F-1), layer1/layer2/allowed_dispositions 가 나중에 길어져 block
    # 으로 옮겨가면 flow 전용 파서는 **조용히 빈 리스트**를 내고(그 프로필 자체는
    # 여전히 유효하므로 게이트가 안 잡는다) 프롬프트는 "assign a disposition
    # from: " 뒤가 빈 채로 나간다. 트레일링 `# comment` 도 두 형식 모두에서
    # 허용한다(비교 지점: `web:` 아래에도 같은 요구가 있다).
    mm = re.search(r"(?m)^\s*" + re.escape(key) + r":[ \t]*\[(.*?)\][ \t]*(?:#.*)?$", text)
    if mm:
        inner = mm.group(1).strip()
        if not inner:
            return []
        return [_unquote(x) for x in inner.split(",") if x.strip()]
    # 헤더 뒤 개행을 **정규식 안에서** 소비한다(`$` 대신 리터럴 `\n`) — `$` 로
    # 끊으면 `mm.end()` 가 개행 문자 바로 앞에 멈춰, 그 뒤 `splitlines()` 의 첫
    # 원소가 빈 문자열이 된다("\n  - a".splitlines() == ['', '  - a']) — 그
    # 빈 줄이 `- ` 패턴에 안 맞아 첫 항목을 보기도 전에 루프가 끊긴다(실측
    # 회귀 — 고치기 전엔 block 세 프로필 모두 빈 리스트를 냈다).
    mm = re.search(r"(?m)^\s*" + re.escape(key) + r":[ \t]*(?:#.*)?\n", text)
    if not mm:
        return []
    items = []
    for line in text[mm.end():].splitlines():
        im = re.match(r"^\s*-\s*(.*?)[ \t]*(?:#.*)?$", line)
        if not im:
            break
        val = im.group(1)
        if val:
            items.append(_unquote(val))
    return items

lr_layer1 = _flow_list("layer1", fm_text)
lr_layer2 = _flow_list("layer2", fm_text)
ad = _flow_list("allowed_dispositions", fm_text)
# YAML(그리고 PyYAML 의 `load_profile()`)은 불리언 대소문자를 가린다 — `True`·
# `TRUE`·`true` 전부 파이썬 `True` 다(리뷰 F-1: `isinstance(True, bool)` 이라
# 상위 게이트가 그대로 통과시킨다). `(?i)` 로 대소문자 무시 + 트레일링 코멘트
# 허용.
web = re.search(r"(?im)^web:[ \t]*true[ \t]*(?:#.*)?$", fm_text) is not None
pathlib.Path(meta_path).write_text("web: %s\n" % ("true" if web else "false"), encoding="utf-8")

pre = ""
pre_p = pathlib.Path(preamble_path)
if pre_p.is_file():
    # P21 preamble 은 HTML 주석 줄을 제거한 뒤 프롬프트에 넣는다 — 그 마커가 본문으로
    # 새면 모델이 그것을 지시로 읽는다(shared/codex/prompt-preamble.md 자체 주석).
    pre = "\n".join(line for line in pre_p.read_text(encoding="utf-8").splitlines()
                    if not re.match(r"^\s*<!--.*-->\s*$", line))

doc = pathlib.Path(doc_path).read_text(encoding="utf-8")

print("You are an independent document reviewer in a read-only sandbox. Do NOT modify files.")
print("\nReview the document in two layers.")
print("Layer 1 (big-picture coherence) — categories: "
      + ", ".join(str(x) for x in lr_layer1))
l2 = lr_layer2 or ["(none — skip layer 2)"]
print("Layer 2 (detail completeness) — categories: " + ", ".join(str(x) for x in l2))
print("For each finding assign a disposition from: " + ", ".join(str(x) for x in ad))
print("  decide = user must decide · ask = ask the user · fix = author edits · drop = not worth raising"
      + (" · defer = hand to the implementation plan" if "defer" in ad else ""))
print("Zero findings is a valid honest answer.")
print("\n" + pre)
print('\nEmit ONE fenced JSON block. `disposition` is required unless you cannot judge it.')
print('```json\n{"findings":[{"ref":"x1","layer":1,"category":"...","anchor":"#slug",'
      '"disposition":"...","summary":"...","edit_scope":"#slug","blocks":[],"evidence":"..."}]}\n```')
print("\n<document>\n" + doc + "\n</document>")
PY
then emit_fallback prompt_build_failed; fi

# 웹 스위치 — 이 if/else 가 WEB_ARGS 를 만드는 **유일한 자리**다(P11). 기본값은 꺼짐:
# 프로필 web:false 면 두 kill switch 와 무관하게 꺼져 있고(WEB_META_FILE 이 "web: false"),
# `web: true` 여도 두 호스트 kill switch(DEVBREW_SPEC_DISTILL_DISABLE_WEB ·
# DEVBREW_QUALITY_GATES_DISABLE_WEB) 중 하나라도 켜져 있으면 끈다 — 공유 러너는 자기
# 호스트를 모르므로 과잉 적용(둘 다 검사)이 안전한 방향이다.
WEB_ARGS=(-c 'tools.web_search=false' -c 'web_search="disabled"')
WEB_META_VAL="$(cat "$WEB_META_FILE" 2>/dev/null || true)"
if [[ "$WEB_META_VAL" == "web: true" \
      && "${DEVBREW_SPEC_DISTILL_DISABLE_WEB:-0}" != "1" \
      && "${DEVBREW_QUALITY_GATES_DISABLE_WEB:-0}" != "1" ]]; then
  WEB_ARGS=(-c 'tools.web_search=true' -c 'web_search="live"')
elif [[ "$WEB_META_VAL" == "web: true" ]]; then
  echo "[docreview] web 비활성(kill switch) — codex 리포 근거만" >&2
fi

EXIT_CODE=0
codex exec - \
    -C "$PROJECT_DIR" \
    -s read-only \
    "${WEB_ARGS[@]}" \
    --json \
    < "$PROMPT_FILE" \
    > "$STDOUT_FILE" \
    2>"$STDERR_FILE" || EXIT_CODE=$?

OVERRIDE_REASON=""
[[ $EXIT_CODE -ne 0 ]] && OVERRIDE_REASON=exit_nonzero

if ! python3 "$PLUGIN_ROOT/scripts/codex_findings_to_yaml.py" \
       --stderr-file "$STDERR_FILE" \
       --meta-override-exit-code "$EXIT_CODE" \
       --meta-override-reason "$OVERRIDE_REASON" \
       --emit-keys docreview \
       < "$STDOUT_FILE" > "$OUTPUT_PATH"; then
  echo 'findings: []' > "$OUTPUT_PATH"
  echo 'meta:' >> "$OUTPUT_PATH"; echo '  codex_failed: true' >> "$OUTPUT_PATH"
  echo '  reason: yaml_conversion_failed' >> "$OUTPUT_PATH"
  exit 0
fi
