---
name: reviewing-spec
description: >
  Use this skill to review a brainstorming design doc (docs/superpowers/specs/...-design.md)
  with the shared document-review engine. It selects the design-doc profile, runs one engine
  round (snapshot → kill switch → detection → codex → anonymize → re-critique → freeze-check
  and routing → gate) inside a single turn, and closes with the shared proceed gate.
  Design-mode only — the interview brief has its own reviewers (reviewing-brief).
cost_class: medium
---

# reviewing-spec — 문서 리뷰 엔진의 design doc 자리

이 skill 은 진입 껍데기다. 한 라운드의 절차는 공유 엔진이 갖고 있고, 여기 남는 것은 이 자리의
것 — 입력 · 프로필 · dispatch 둘 · 원장 · 게이트 · degrade 채널 — 뿐이다.

## 입력

Stop 훅(`hooks/review-dispatch.py`)의 dispatch mandate 가 세 슬롯을 싣는다. 훅은 무변경이므로 이
셋이 계약의 전부다.

- `spec path: <절대경로>` → `$spec_path`. 리뷰 대상 문서. 어느 체크아웃인지도 이 절대경로가 말한다.
- `mode: design|spec` → `$mode`. 프로필 선택에만 쓴다(아래 `## 프로필`).
- 수명 문장 — 이 mandate 는 이번 dispatch 1회에만 유효하다(상한에 닿았으면 자동 dispatch 중단
  사실). 이것은 **범위**이지 면제가 아니다 — 리뷰를 건너뛸 근거로 읽지 않는다.

mandate 없이 수동 호출됐으면 그 사실을 loud advisory 로 알리고 `$spec_path` 를 사용자에게 확인한다.

훅이 읽는 파일과 *정의상 동일한* harness session id + state root 로 상태를 연다. 훅은 raw sid 가
아니라 `resolve_session_id`(env-first: `DEVBREW_SPEC_DISTILL_SESSION_ID` → `CLAUDE_CODE_SESSION_ID`
→ payload)를 쓰므로, 스킬도 같은 리졸버를 CLI 로 재사용한다(DRY):

```bash
harness_sid="$(python3 "${CLAUDE_PLUGIN_ROOT:-./plugins/spec-distill}/scripts/state_path.py" session-id)"
ROOT="$(python3 "${CLAUDE_PLUGIN_ROOT:-./plugins/spec-distill}/scripts/state_path.py" state-root)"
STATE="$ROOT/$harness_sid/state.local.md"   # 훅이 읽는 바로 그 파일
STATE_DIR="$ROOT/$harness_sid"              # 엔진 상태(docreview-state.md)도 같은 디렉토리
```

`$STATE` 를 여는 이유는 arm 원장(`armed_paths`·`dispatch_attempts`·`inflight_paths`)이 훅이 읽는
바로 그 파일에 있어야 하기 때문이다 — **read==write 디렉토리 불변식**(이 READ 와 아래 `## 원장`
의 WRITE **전부** 가 같은 `$STATE` 를 가리킴)이 깨지면 arm-once 게이트가 훅과 다른 파일을 키잉해
통째로 무의미해진다.

## 프로필

```bash
PROFILE="${CLAUDE_PLUGIN_ROOT:-./plugins/spec-distill}/references/docreview-profiles/design-doc.md"
```

훅이 내는 `mode:` 의 값역은 `design`·`spec` 인데 프로필 파일 이름은 `design-doc.md` 다 — 이름이
다르다. **매핑은 이 한 곳에만 있다: `design` 도 `spec` 도 같은 `design-doc.md` 로 간다.** 이 skill
은 v0.12.0 부터 design 전용이라 `spec` 값이 와도 프로필이 갈리지 않는다.

## 절차

```
Read ${CLAUDE_PLUGIN_ROOT:-./plugins/spec-distill}/references/reviewing-document.md
```

그 파일의 여덟 단계를 **한 턴 안에서** 돈다. 절차를 여기 복사하지 않는다 — 네 자리가 같은 절차를
쓰기 때문에 공유 정본에 두는 것이다. `--state-dir` 는 위 `$STATE_DIR` 이고, 상한은 그 문서가 정하는
**재리뷰 상한 2** 다(라운드 4 이상은 사용자가 승인 게이트에서 열어야만 돈다).

4단계 codex 는 이 자리의 리터럴 게이트다. 조건을 산문으로 적지 않는다 — 산문 조건은 집행되지 않고,
kill switch 는 P21 보안 컨트롤이라 그 공백은 "껐다고 믿게만" 만든다.

<!-- codex-gate:begin runner=run_docreview_codex_reviewer.sh -->
```bash
SD="${CLAUDE_PLUGIN_ROOT:-./plugins/spec-distill}"
# `## 프로필` 과 **같은 한 줄**이다. Bash 도구는 호출마다 새 셸이라 앞 펜스의 대입이 여기로
# 오지 않는다 — `SD=` 를 펜스마다 다시 세우는 것과 같은 이유다. 어느 모드가 어느 프로필로
# 가는가(매핑)는 그 절 하나에만 있고, 여기 있는 것은 그 결과값의 재도출뿐이다.
PROFILE="${CLAUDE_PLUGIN_ROOT:-./plugins/spec-distill}/references/docreview-profiles/design-doc.md"
DETECT_OUT="$(bash "$SD/scripts/detect_codex.sh")"
codex_avail="$(printf '%s\n' "$DETECT_OUT" | sed -n 's/^codex_available: //p')"
skip_reason="$(printf '%s\n' "$DETECT_OUT" | sed -n 's/^skip_reason: //p')"
# "감지기를 못 돌렸다"와 "codex가 없다"를 구별한다: 정상 실행된 감지기는 항상 exit 0 이고
# codex_available: 줄을 낸다(false 여도). 그 줄이 없으면 감지기 자체가 안 돈 것이다 —
# skip_reason: unknown 으로 뭉개지 않는다.
if [[ -z "$codex_avail" ]]; then skip_reason="detector_not_runnable"; fi
if [[ "$codex_avail" == "true" ]]; then
  bash "$SD/scripts/run_docreview_codex_reviewer.sh" "$PROFILE" "$spec_path" "$(pwd)" "$CODEX_YAML"; runner_rc=$?
  # 러너는 산출물을 **쓰지 못하면** exit 3 으로 죽는다. 그 경우 직전 라운드 YAML 이 그대로
  # 남아 이번 라운드 판정으로 읽히므로 잔존물을 제거한다.
  if [[ "$runner_rc" -eq 3 ]]; then rm -f "$CODEX_YAML"; fi
else
  echo "[spec-distill] codex co-review SKIPPED (reason: ${skip_reason:-unknown}) — Claude-only, 이 리뷰에는 모델 다양성이 없었다 (degraded)." >&2
fi
```
<!-- codex-gate:end -->

`DEVBREW_SPEC_DISTILL_DISABLE=1` 은 훅이 dispatch 이전에 이미 걸러낸다(이 skill 에 진입하지 않는다).
`DEVBREW_SPEC_DISTILL_DISABLE_CODEX=1` 은 codex 만 끄고 탐지 리뷰는 그대로 돈다.
`DEVBREW_SPEC_DISTILL_DISABLE_RECRITIC=1` 은 재비판만 끈다. 셋 다 dispatch 직전에 확인하고
캐시하지 않으며, 발화한 스위치는 아래 degrade 채널로 공시한다.

## dispatch 블록 둘

3단계 탐지 — 한 번 dispatch 하고 출력을 요약·전사 없이 verbatim 파일(`critic.txt`)로 저장한다.
파싱은 `docreview_route.py` 가 그 파일에서 한다.

```
Agent({
  description: "Document review detection (layer 1 then layer 2)",
  subagent_type: "spec-distill:doc-critic",
  // **처분** — consumer=plugins/spec-distill/scripts/docreview_route.py · fail-closed
  prompt: "<document>${DOCUMENT}</document>
    <profile>${PROFILE}</profile>
    <prior_finding_ids>${PRIOR_FINDING_IDS}</prior_finding_ids>"
})
```

6단계 재비판 — 입력 슬롯은 **정확히 셋**이다: 문서 · `prep.json` 의 `items`(출처 라벨 없음) ·
프로필. dispatch 사유도, 이전 대화도, 어느 리뷰어가 냈는지도 넣지 않는다 — 그것을 알면 판단이 그
프레이밍을 흡수한다. 출력은 verbatim 파일(`recritic.txt`)로.

```
Agent({
  description: "Framing-blind re-critique of the finding list",
  subagent_type: "spec-distill:doc-recritic",
  // **처분** — consumer=plugins/spec-distill/scripts/docreview_route.py · fail-open
  prompt: "<document>${DOCUMENT}</document>
    <findings>${FINDINGS}</findings>
    <profile>${PROFILE}</profile>"
})
```

## 원장

arm-once 원장(`armed_paths`·`inflight_paths`·`dispatch_attempts`)을 지우는 손은 리포 전체에서 이
파일 하나뿐이다. 아래 네 호출이 빠지면 arm-once 게이트가 통째로 죽고, G6 상한 3 이 이 문서의 자동
dispatch 를 영구 중단시킨다.

### mark-reviewed — 승인 게이트에서 사용자가 진행(①/②)을 고른 뒤

리뷰의 종결 사건이다. 이 기록 이후의 같은-세션 편집은 재arm 되지 않는다. **판정이 났을 때가 아니라
사용자가 진행을 고른 뒤**에 찍는다 — 라운드 게이트에서 멈춘 문서는 아직 리뷰가 끝난 것이 아니다.

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-./plugins/spec-distill}/scripts/arm_ledger.py" mark-reviewed "$harness_sid" "$spec_path"
```

이 한 호출이 **in-flight 표시도 함께 지운다** — 그래서 정상 경로에서는 아래 두 종료 자리의
`clear-inflight` 를 부를 일이 없다. **예외** — `fin.json` 의 `blocks` 에 critic 사망이 실린 라운드,
즉 아무도 리뷰하지 않은 라운드에서는 찍지 않는다. 그 라운드를 기록하면 "리뷰가 실제로 일어났을
때만 표시된다"는 기록 시점의 근거가 무너진다. 배제된 라운드는 원장이 비어 다음 편집이 재시도하고,
`dispatch_attempts` 는 계속 올라 G6 상한이 결국 멈춘다.

`$harness_sid` 가 빈 값이면 상태 파일을 특정할 수 없으므로 호출하지 않고, 조용히 넘어가는 대신
advisory 를 낸다:

> `[spec-distill] harness_sid 미해석 — 이 세션의 상태 파일을 특정할 수 없어 리뷰 완료 기록(mark-reviewed)을 남기지 못했다. 같은 문서가 다시 dispatch될 수 있다. 해소: DEVBREW_SPEC_DISTILL_SESSION_ID로 sid를 명시하라.`

### check-born — 진행 직전

approve(①/②) 시점에 남은 유일한 할 일은 **문서가 아직 git 에 없으면 알리는 것**이다.

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-./plugins/spec-distill}/scripts/arm_ledger.py" check-born "$spec_path"
```

exit 0 = git-tracked(할 말 없음). exit 1 = 미커밋 — 스크립트가 stderr 로 낸 advisory 를 **그대로**
사용자에게 노출한다. arm-once 의 세션-바깥 조건이 `is_born`(git 추적 여부)이라, 커밋하지 않은 채
세션을 넘기면 이 문서의 리뷰가 한 번 더 발동한다. out-of-scope 경로면 exit 2 + advisory(비-fatal)
이고, 이 호출은 판정만 하며 상태를 쓰지 않으므로 실패해도 잃을 상태가 없다(P14).

### clear-inflight A — 문서 부재로 끝나는 경로

`$spec_path` 가 working-tree 에 없으면(삭제된 worktree 경로 등) 게이트를 띄우지 않고 끝난다. 이
문면 그대로 advisory 를 내고, **in-flight 표시를 걷어낸다** — 남겨 두면 `INFLIGHT_TTL_SEC` 만료
까지 그 키가 발견 제외로 살아 있다.

> `[spec-distill] current_spec '<path>' 부재 (working-tree에 없음) — stale state. current_spec 재선택 또는 세션 리셋 필요. handoff 진행 안 함.`

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-./plugins/spec-distill}/scripts/arm_ledger.py" clear-inflight "$harness_sid" "$spec_path"
```

**이 호출의 rc 를 성공 증거로 읽지 말 것** — CLI 는 지웠든 못 지웠든 항상 exit 0 이고, 「지울 표시가
없었다」와 「스코프 밖 경로·상태 파일 부재로 아무것도 못 했다」가 스킬 입장에서 구별되지 않는다.
소리를 내는 것은 원장 판독 실패와 write 실패 둘뿐이니 stderr 에 뜬 것만 사용자에게 노출한다.
`$harness_sid` 가 빈 값이면 호출하지 않고 위와 같은 사유의 advisory 를 낸다.

### clear-inflight B — ④ 멈춤으로 끝나는 경로

상태를 보존하고 종료한다. 새 판정은 남기지 않고, 남은 일은 in-flight 표시를 걷어내는 것 하나다.

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-./plugins/spec-distill}/scripts/arm_ledger.py" clear-inflight "$harness_sid" "$spec_path"
```

여기도 A 와 같은 이유로 **rc 를 성공 증거로 읽지 않는다**.
`$harness_sid` 가 빈 값이면 호출하지 않고 같은 사유의 advisory 를 낸다 — 형제 자리 둘
(mark-reviewed · A)이 그 문구를 요구하므로 여기만 침묵하면 그 비대칭이 다음 복사본으로
옮겨간다. 자동 재발동 여부를 이 호출이 정하지는 않는다 —
`armed_paths` 가 정한다. 재개는 사용자 요청 시 이 skill 의 수동 호출로 한다.

## 게이트

골격 · 두 가드 · 예외 경로의 정본은 아래 파일이다 — `conducting-interview` 종료 Step B 와 같은
계약이라 어느 skill 밑도 아닌 플러그인 루트에 산다. 게이트 진입 시 읽고 따르며, 여기에는 이 skill
의 어휘만 남는다.

```
Read ${CLAUDE_PLUGIN_ROOT:-./plugins/spec-distill}/references/proceed-gate.md
```

엔진 8단계의 `docreview_state.py gate --state-dir "$STATE_DIR" --render` 가 어느 게이트인지 정한다.
`round_gate_needed` 면 라운드 게이트(결정 묶음 + 차단 `ask`)를 `AskUserQuestion` **하나**로 띄우고
응답을 `decide`·`fix`·`ask` 서브커맨드로 반영한다. `approval_gate_open` 이면 승인 게이트이고, 열린
것이 남아 있으면 두 단계다.

승인 게이트의 옵션 넷 — 정본 Step B 표를 이 skill 어휘로 채운 것이다:

| # | 이 skill 에서 |
|---|---|
| ① | `/compact` 후 `superpowers:writing-plans` (권장) — verbatim `/compact` 명령을 노출하고 **턴 종료** |
| ② | 바로 `Skill superpowers:writing-plans <path>` |
| ③ | 수정 필요 — 후속 질문으로 revise per findings / `conducting-interview` 재진입 / 사용자 직접 편집 분기 |
| ④ | 멈춤 — 상태 보존하고 종료(`clear-inflight B`) |

- **① 의 정지 요건** — verbatim `/compact` 명령을 노출한 자리에서 **턴 종료(STOP)** 한다. 같은 턴
  에서 `writing-plans` 를 호출하지 않는다(compact 전 진입은 옵션 ① 을 무력화한다). 진입은 사용자가
  `/compact` 를 실제로 실행한 **다음 턴**에 사용자 트리거로만 일어나고, 사용자가 redirect 하면
  미진입한다(P17). **이 문단이 이 skill 의 AC19 기계적 검증 앵커다** — 정본에도 같은 어휘가 있지만
  그것은 계약 서술이지 이 skill 의 앵커가 아니다.
- **polite stop 금지 (AP2)** — ①/② 를 골랐는데 narrate 만 하고 `## 원장` 의 두 호출과 다음 단계
  진입을 skip 하면 polite stop 이다. 이 skill 을 종료하는 모든 경로는 이 게이트를 거치거나, 게이트를
  거치지 않는 예외 경로(문서 부재 · kill switch)면 명시적 advisory 단락을 동반한다 — 게이트-less
  silent 종료는 금지다.
- **재결정 규약 (P23)** — `decide` 처분이 인터뷰가 이미 확정한 항목을 겨냥하면 조용히 덮어쓰지
  않는다. design.md 의 재결정 기록에 *원래 / 재결정 후보 / 근거* 를 적어 다음 라운드로 들고 가고,
  확정이 실제로 뒤집히는 자리는 이 승인 게이트 하나다 — 사용자가 판정한다. 하류의 반증은 보고의
  근거이지 임의 변경의 근거가 아니다. 정본은 `proceed-gate.md` 의 「재결정 규약」 절.

## degrade 채널

이 skill 의 degrade 채널은 엔진의 것이고 별도 원장을 만들지 않는다. 이름은 셋이다:

- `fin.json` 의 `advisory[]` — codex 부재 · critic 층 2 부재 · recritic 부재 · 처분 회계의 degrade
  사유가 전부 이 한 채널로 온다.
- `fin.json` 의 `blocks` — **막는 것**만 여기 온다: critic 사망(주 판정자) · 항목 소실 · 셀 수 없음.
- `docreview_state.py gate --render` 의 **첫 줄** — 라운드 번호 · 재리뷰 카운트 · 그 라운드의 degrade
  요약.

게이트를 띄우기 **직전에** 이 셋을 읽어 하나도 빠뜨리지 않고 프로즈로 내고, 승인 게이트 질문
텍스트의 `degrade:` 슬롯에도 싣는다. 셋 다 비었을 때만 `degrade 없음` 이다 — 그 문구는 **채널을
실제로 읽었다는 주장**이므로, 읽지 않은 채 쓰지 않는다.
