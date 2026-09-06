---
name: conducting-interview
description: >
  Runs the spec-distill problem-space interview stage and produces a terminal
  interview-brief at docs/superpowers/interview/. 종료는 커버리지 원장의 floor
  5차원(root-problem/landscape/skepticism/blind-spot/open-questions)이 모두
  closed일 때이며, check_brief.py의 구조적 게이트로 기계적 검증합니다(Law 1).
  Optionally hands the brief to superpowers:brainstorming.
cost_class: variable
user-invocable: false
---

# Conducting Interview — 문제공간 Stage (Phase 1)

당신은 spec-distill의 인터뷰 stage를 진행 중입니다. 이 stage는 *받아적는* 인터뷰가
아니라 **강한 문제공간 stage**입니다(Double Diamond 1st diamond — brainstorming 해답공간
앞단, 상보적·비중복). 매 라운드를 «직전 답에서» 블록으로 시작하고 AskUserQuestion 질문
둘로 묻되, 종료는
**커버리지 원장의 floor 5차원**(root-problem/landscape/skepticism/blind-spot/open-questions)이
**모두 `closed`**일 때만 허용됩니다 — landscape·skepticism 등 통과 의례 메커니즘이 각 차원을
채우는 수단이며, `check_brief.py`가 이를 기계적으로 검증합니다(Law 1 구조 게이트).

산출물은 `spec.md`가 아니라 **interview brief**(brainstorming용 meta-prompt)이며, 이
brief는 **단독 완결 terminal 산출물**입니다 — superpowers가 있으면 brainstorming으로
넘기고(optional), 없으면 brief 자체로 완료합니다.

## State location

`.claude/spec-distill/<session-id>/state.local.md` (per-session 격리, devbrew §4.8 준수)

State frontmatter schema:

```yaml
---
session_id: <uuid>
phase: 1
coverage:                            # G1 커버리지 원장 (floor 5 + derived[]). 종료 driver.
  floor:
    root_problem:   {status: open, evidence: ""}
    landscape:      {status: open, evidence: ""}
    skepticism:     {status: open, evidence: ""}
    blind_spot:     {status: open, evidence: ""}
    open_questions: {status: open, evidence: ""}
  derived: []                        # 주제-도출 차원 (coverage-mapper 제안 → orchestrator admit; {name, rationale, status, evidence})
orchestration:                       # C11/C8 across-resumption 상태 (orchestrator 소유, agent read-only)
  focused_dimension: null            # 현재 probe 대상 차원 이름 또는 null
  no_progress_streak: 0              # C11 연속 무진전 probe 수; focused 변경·진전 시 0 reset
  blind_spot_dispatched: false       # C8 인터뷰당 1회 보장; 첫 dispatch 시 true
  stall_episode: 0                   # streak 이 0 으로 reset 될 때마다 +1. 정체 «구간»의 id
  coverage_mapper_dispatched_episode: null   # 마지막 dispatch 가 일어난 에피소드 id
non_user_streak: <int>
rereview_count: 0
trivia_escape_armed: false
issue_history: []                    # 각 항목: {id, raised_count, dismissed_by_user, accepted_by_user, reconsensus_count, resolved, escalated}
user_statements: []                  # 매 round 끝 append. 판정 없음 — 확정은 종료 게이트가 결정.
confirm_repost_count: 0              # 종료 확정 확인 재제시 횟수 (상한 2, Unbounded-autonomy 가드)
---
```

State body: 각 라운드의 §1.1 기록(`## R<n>` 형식 그대로 — `depth_pairs.py` 가 읽는 계약) + coverage-mapper 출력 transcript.

**Secret 기록 금지** (P21): 사용자 답변에 token/key/credential 패턴 감지 시 placeholder로 치환 후
기록합니다. **치환 토큰은 `<REDACTED>` 또는 `<REDACTED:라벨>` 형태**로 씁니다(다른 허용 형태:
`<SECRET:...>` · `<TOKEN:...>` · `<KEY:...>` · `<CREDENTIAL:...>` · `<PLACEHOLDER:...>`).
`check_verbatim_coverage.py`가 payload §6 ∪ audit §6 원문 대조에서 **이 토큰 집합**을 보고 L2를 advisory로 강등하므로,
다른 형태로 치환하면 정당한 치환이 red로 잡혀 사용자가 Step B에서 판정해야 합니다(fail-closed 방향).

### State write contract (PN1 — worktree-safe)

`state.local.md`는 `state_path.py`가 **main repo** `.claude/spec-distill/<sid>/`로 라우팅합니다
(`git rev-parse --git-common-dir`). 워크트리 세션에서 이 경로는 워크트리 *밖*이라 `Write`/`Edit`
tool이 차단됩니다 — state 갱신은 **반드시 Bash**로 하십시오:

```bash
ROOT="$(python3 "${CLAUDE_PLUGIN_ROOT}/scripts/state_path.py" state-root)"
STATE="$ROOT/<session-id>/state.local.md"
# read-modify-write via python3 -c / heredoc (Edit tool 사용 금지 — main-repo 경로)
```

**brief는 예외**: `docs/superpowers/interview/`는 워크트리 *안*이라 `Write` tool로 정상 작성.

## 라운드 규약 — «직전 답에서» 블록 + 질문 둘

인터뷰어의 다음 행동은 사용자의 직전 답에서 나온다. 사용자에게 보이는 출력과 state 본문 기록이
**같은 형식**이다 — 측정 스크립트(`depth_pairs.py`)가 state 본문을 읽기 때문이다.

```markdown
## R<n>

### 직전 답에서 — S<k>
- 함의: <이 답이 사실이면 따라오는 것>
- 상충: <이전 답 S<j> / 외부 근거 / 코드 사실과 부딪히는 점 — 재개방이면 «→ <차원> 재개방: <사유>»> (없으면 «없음»)
- 확인한 사실: <답을 받고 코드·문서에서 찾아본 것> (없으면 «없음»)
- 위험: <이 답대로 가면 무너질 수 있는 것> (없으면 «없음»)

### 지금 이해
<문제의 현재 재구성 — 바뀐 부분만 한두 문장>

### 다음 결정
<무엇을 정하는지 한 줄> · 추천: <첫 선택지> · 트레이드오프: <선택지별 한 줄>

### 질문
Q1 (되비추기 확인 | 되묻기): <본문>
Q2: <본문>

### 답
→ S<m>[, S<m+1>]
```

- `## R<n>` 은 1부터 순증. 직전 라운드가 발화를 둘 만들었으면(Q1·Q2) **`### 직전 답에서 — S<k>`
  블록을 발화마다 하나씩** 둔다 — 한 블록에 두 S 를 섞으면 어느 답에서 무엇이 나왔는지가 사라진다.
  각 블록의 네 줄은 **그 S 에서** 따라 나오는 것만 적는다(다른 답·무관한 정보는 «없음»).
- **R1 은 S1 을 되비춘다** — S1 이 seed(`round: 0`)이면 seed 의 «다시 검증할 것» 문단 항목이 R1 의
  함의·상충·위험 줄을 채운다. **인자 없이 `/interview` 를 부른 경로**(S1 이 없고 첫 사용자 답이 S1 이
  되는 호환 경로)에서는 R1 이 «직전 답에서» 블록 없이 «지금 이해 + 다음 결정 + Q2» 만으로 성립하고
  규약은 R2 부터 적용된다; coverage-mapper 첫 dispatch 도 R1 답을 받은 뒤 R2 전에 일어난다.
- 네 줄 중 하나라도 «없음»이 아니어야 «형식 층에서 성립»이다. **넷 다 «없음»이면** 그 라운드는
  «S<k> 에서 아무것도 못 끌어냈다»는 기록이 되고 **그 라운드의 Q1 은 되묻기여야 한다**(아래 절).
  블록을 아예 쓰지 않는 것만이 라운드 불성립이다.
- «상충» 줄이 외부 근거(landscape·steelman·premortem 출력)를 싣는다 — 열린 질문으로 흘려보내지 않고
  «맞나?»로 사용자 처분을 받는다. 경로 (a)(코드·문서에서 찾을 수 있는 것)는 «확인한 사실» 줄로
  들어간다 — 묻기 전에 찾을 수 있는 것을 먼저 찾는다.

### 질문 — AskUserQuestion 한 번, 질문 둘

```javascript
AskUserQuestion({
  questions: [
    { header: "직전 답",  question: "<S<k> 에서 끌어낸 것을 한 절로 — 용어와 기술 사실을 풀어서>. 맞나요?",
      options: [
        {label: "맞다",     description: "이대로 <차원> 을 진행/닫는다 — <고르면 달라지는 것>"},
        {label: "모르겠다", description: "판단불가로 기록하고 Open Question 후보로 둔다"}],
      multiSelect: false },
    { header: "<결정 이름>", question: "<무엇을 정하는지 한 줄> · <용어 풀이> · <관련 기술 사실> · 추천은 첫 선택지",
      options: [
        {label: "<추천> (권장)", description: "고르면 <결과>"},
        {label: "<대안 1>",      description: "고르면 <결과>"},
        {label: "<대안 2>",      description: "고르면 <결과>"}],
      multiSelect: false }
  ]
})
```

- **Q1 은 생략할 수 없다.** Q1 이 항상 먼저고 Q2 는 새 결정 하나다.
- **Q1 의 선택지는 둘뿐이다**(«맞다» / «모르겠다»). 틀린 부분은 사용자가 «기타» 자유 입력에 적는다 —
  선택지를 고르면서 동시에 자유 입력을 남기는 동작은 도구에 없다. «기타» 텍스트는 `verbatim` S 로
  기록되고 다음 라운드 Q1 이 그것을 다시 되비춘다(같은 주제 최대 2회 — 3회째는 §3 Open Questions 로
  박제하고 넘어간다).
- **Q2 는 Q1 의 확인과 독립이어야 한다.** Q2 가 Q1 이 되비춘 해석에 기대면 그 라운드는 Q1 만 낸다.
  독립인데도 Q1 이 «모르겠다»·«기타(수정)» 이면 Q2 의 답은 state 에 `provisional_on: S<k>` 를 달고,
  그 표시가 해소(다음 라운드 되비추기 «맞다»)되기 전에는 어느 차원의 닫힘 근거로도 쓰지 않는다.
- 각 선택지의 `description` 은 «고르면 무엇이 달라지는가»를 담고, question 본문은 무엇을 정하는지·
  용어·기술 사실을 푼다. 기계 검사는 없다 — 사람 e2e 가 본다.
- 두 답은 `user_statements` 에 `S<m>`·`S<m+1>` 로 append 된다(`source: chosen`, «기타» 입력은
  `verbatim`). 번호 공식은 «사용자 발화 기록» 절 그대로.

## 되묻기로 바뀌는 조건

되비추기가 **성립하지 않는 답**에서 Q1 은 되묻기가 된다 — 보류(«모르겠다/둘 다/아무거나»), 한 단어 답,
추천안 즉시 동의(이유 없이 «추천»), 근거 없는 단정(휴리스틱, 기계화 안 함). Q1 본문은 **이유·사례·
실패 조건** 중 하나를 묻고 인터뷰어의 추측을 첫 선택지로 둔다:

```
Q1 (되묻기): «<S<k>>»라고 답하셨는데, 왜 그렇게 봤는지가 <차원> 을 닫는 데 필요합니다.
  - «내 추측: <이유 A>» (권장)  — 고르면 <결과>
  - «<이유 B>»                 — 고르면 <결과>
  - «잘 모르겠다»              — 판단불가로 기록, OQ 후보
```

세 축이 도구상자의 전부다. 목록을 더 두지 않는다.

## C43 4-path routing

질문을 만들 때 다음 4 경로 중 하나로 분류해서 routing 하십시오:

| Path | When | Action |
|---|---|---|
| (a) **factual / landscape** | 답이 codebase/git history *또는 외부 prior-art*에 있는 경우 | codebase는 grep/Read *auto-confirm*; 외부는 web sweep(아래 R2). 마커 `[from-code][auto-confirmed]` 또는 `[from-web]`. streak +1. |
| (b) **judgment** | 사용자 선호/우선순위/제약 | 사용자에게 묻기 (default path). |
| (d) **ontological** | "이게 무엇인가" 종류 (essence/root cause 등) | essence/root cause 류 — 라벨 강제 없음. 사용자에게 묻기. |

매 라운드의 «확인한 사실»·«질문» 에 어떤 path 인지 transcript에 명시하십시오.

## 사용자 발화 기록 (G1, AC1)

매 round 끝에 사용자가 실제로 답한 것을 `user_statements`에 append합니다. **여기서 무엇도
판정하지 않습니다** — 이 stage는 문제공간이고, 무엇이 확정인지는 종료 직전 사용자 일괄
확인(Step B-0)이 결정합니다.

| 사용자 응답 유형 | path | 기록? | `source` |
|---|---|---|---|
| 자유 텍스트 응답 (수락·거절·요구 무관) | b, d | ✅ | `verbatim` |
| 선택지 선택 | b, d | ✅ | `chosen` |
| 보류 ("잘 모르겠음", "둘 다 괜찮음") | b, d | ✅ — §3 Open Questions로도 이월 | `verbatim` |
| factual auto-confirm | a | ❌ (사용자 발화 아님) | — |

```yaml
- id: S<N>                 # N = user_statements.length + 1 + (최초 요청 원문 있으면 1, 없으면 0 — finishing.md S1 예약과 합의)
  source: verbatim         # verbatim(발화 그대로) | chosen(고른 선택지 라벨 + 요지)
  round: <int>
  text: "<사용자가 실제로 한 말>"    # P21 secret placeholder 치환 적용
```

`status` 필드는 없습니다. `section:` 해답공간 앵커도 없습니다 — 문제공간의 답변을 답이
들어갈 슬롯에 미리 바인딩하면 다음 stage의 탐색이 그 슬롯 모양대로 갇힙니다.

거절도 수락과 똑같이 **발화 그대로** 기록합니다. 반대 명제로 뒤집어 "잠긴 방향"으로
승격시키지 않습니다 — 그 승격이 라운드마다 결정을 박제하던 경로였습니다.

## C44 Dialectic Rhythm Guard

`non_user_streak` 카운터 — 직전 N probe 동안 *사용자 답변이 없었던* 횟수.

- (a) factual auto-confirm: streak +1
- (b) 사용자 답변 받음: streak = 0
- (d) ontological 사용자 답변 받음: streak = 0
- (a) web auto-research: streak +1 (과도하면 강제 (b)로 사용자를 loop에 유지 — AP16).

`non_user_streak >= DEVBREW_SPEC_DISTILL_RHYTHM_GUARD_THRESHOLD` (default 3) 도달 시:

→ 다음 probe의 질문은 **반드시 (b) judgment path** (사용자에게 직접 질문)로 라우팅. 강제.

## coverage-mapper dispatch (C11)

`coverage-mapper`는 고정 floor 위 **주제-도출 차원**을 *제안*하는 advisory 에이전트다(원장 admit
판정은 orchestrator, G2). 다음 조건 중 하나에서 dispatch:

1. 한 focused 차원이 **연속 3 probe** 동안 status·evidence 무변경(진전 없음), OR
2. floor 차원의 **첫 open→in-progress 전이**.

진전 = status 전이(open→in-progress→closed) 또는 evidence append. `orchestration.no_progress_streak`는
focused 차원이 바뀌거나 진전 발생 시 0으로 reset.

**redispatch 바운드(Unbounded-autonomy 가드)**: 재dispatch 조건은
`no_progress_streak >= 3 AND coverage_mapper_dispatched_episode != stall_episode` 다. dispatch
시 `orchestration.coverage_mapper_dispatched_episode = stall_episode` 를 기록하고,
`no_progress_streak` 가 0 으로 reset 될 때마다 `stall_episode` 를 +1 한다. 한 정체 구간당
정확히 1회다.

판정은 **디스크 두 값의 비교**이므로 어느 턴에서든 무상태로 재계산된다 — 그 성질을 잃으면
판정이 모델의 턴-간 기억에 의존하는 *프로즈 self-tracking*이 되어, 이 문단이 세운 기계적
bound 자체가 무너진다. **streak 값 자체를 저장하지 않는 이유**: streak 3 에서 dispatch(저장
3) → streak 4 → `3 != 4` → 재dispatch → streak 5 → 재dispatch … 로 레벨-트리거 무한
재dispatch 가 그대로 살아난다.

**dispatch 조건 2 는 이 바운드의 대상이 아니라 «바운드가 불필요»하다.** floor 차원의 첫
`open→in-progress` 전이는 대상이 **floor 다섯 차원으로 고정**이므로(derived 차원은 그 조건의
대상이 아니다) 상한이 5 다. 유한성이 구조에서 나오므로 추가 바운드를 두지 않는다.

**이 바운드가 묶는 것은 «밀도»이지 «총량»이 아니다.** 정체 구간 수에는 상한이 없고,
coverage-mapper 가 제안한 derived 차원이 원장에 admit 되면 새 focused 대상이 생겨 새 정체
구간을 낳는 되먹임도 있다. 총량 바운드는 이 판본에 없다(설계 §11 이월).

**Web kill switch (dispatch 직전 확인 — 이 블록에 종속)**: `coverage-mapper`는
`WebSearch`/`WebFetch`를 보유한다. kill switch `DEVBREW_SPEC_DISTILL_DISABLE_WEB=1`이면
dispatch 프롬프트에 `web_disabled: true`를 실어 **codebase 근거만으로 차원을 제안**하게 하고,
loud advisory를 남긴다: `[spec-distill] web 비활성 — coverage-mapper가 codebase 근거만 사용`.
이 확인은 R2의 landscape 확인과 **별개로** 여기 있어야 한다 — kill switch는 보안 컨트롤이고,
egress를 가진 dispatch가 하나라도 게이트 밖에 있으면 스위치는 꺼졌다고 *믿게만* 만든다.
`coverage-mapper`는 `tools:`에 `Bash`가 없어 스스로 확인할 수 없다(Law 2) — orchestrator가
유일한 집행 지점이다.

```bash
if [[ "${DEVBREW_SPEC_DISTILL_DISABLE_WEB:-0}" == "1" ]]; then
  web_disabled=true
  echo "[spec-distill] web 비활성 — coverage-mapper가 codebase 근거만 사용" >&2
else
  web_disabled=false
fi
```

```
Agent({ description: "Map coverage dimensions", subagent_type: "spec-distill:coverage-mapper",
        prompt: "coverage 원장 상태(열린/닫힌 차원 요약 · focused_dimension · no_progress_streak): <ledger_state>${LEDGER_STATE}</ledger_state>. web_disabled(true면 WebSearch/WebFetch 사용 금지, codebase 근거만): <web_disabled>${WEB_DISABLED}</web_disabled>. 이 주제가 요구하는 derived 차원과 neglect를 제안." })
// **처분** — consumer=orchestrator · fail-open · disclosure=advisory
```

출력(`derived_dimensions[] + neglect_flag`)은 **advisory** — orchestrator가 원장에 admit할지 판정한다.
`neglect_flag: true`면 다음 probe에서 neglected 차원 하나를 추천 답안으로 제시. 복수 dispatch 시
name 기준 union·dedup.

## blind-spot-prober dispatch (C8 — blind_spot floor 차원)

`blind_spot` floor 차원의 **첫 open→in-progress 전이**(그 차원에 첫 probe 착수) 시 `blind-spot-prober`를
**인터뷰당 1회** dispatch한다(fan-out 1, C8). `orchestration.blind_spot_dispatched`가 false일 때만
dispatch하고, dispatch 후 true로 세팅(재dispatch 금지).

```
Agent({ description: "Adversarial premortem", subagent_type: "spec-distill:blind-spot-prober",
        prompt: "지금까지의 framing(재구성된 문제정의 + 사용자 제약 요지): <framing>${FRAMING}</framing>. 이 framing의 hidden assumption과 failure mode를 웹근거와 함께." })
// **처분** — consumer=orchestrator · fail-open · disclosure=loud advisory
```

출력(`hidden_assumptions[] + failure_modes[]`)을 orchestrator가 payload §5 `## 5. 기각 · Blind Spots`의
**`위험` 항목**(`- 위험 — <숨은 가정 | 실패 양식>: <내용> — <근거>`)으로 기록하고, `blind_spot` floor
차원을 in-progress→closed로 전이(사용자에게 표면화된 blind-spot 확인 후).

**Web 부재 시 graceful degradation (C5)**: kill switch `DEVBREW_SPEC_DISTILL_DISABLE_WEB=1` 또는 web
도구 부재로 blind-spot-prober를 돌릴 수 없으면 — R2/R3 web-absent 강등과 대칭으로 — opaque gate-fail로
떨어뜨리지 말고 **loud advisory** 후 **inline premortem**으로 전환:
`[spec-distill] web 비활성 — blind-spot-prober 자동 생략, inline premortem으로 전환`. 이 경우 §5의
`위험` 항목은 codebase 근거 또는 사용자 판단으로 기록(URL 부재 사유 명시).

## 5 통과 의례 (Law 1 구조 게이트, R1–R5)

brief 작성(+ optional brainstorming invoke)은 다음 5 의례를 **모두 통과**해야 허용됩니다.
하나라도 미충족이면 종료 차단. 종료 직전 `check_brief.py gate`로 **기계적 검증**:

| # | 의례 | 통과 기준 | 메커니즘 |
|---|---|---|---|
| R1 | **Problem Reframe** | seed 가 가리키는 **작업 뒤의 진짜 문제**를 재구성한 한 문장 문제정의 + 진짜 goal. seed 의 문장을 되풀이하는 것은 통과가 아니다. | (d) ontological 5-type → payload §0 · §1 |
| R2 | **Landscape 수집** | web sweep ≥1회, prior-art/대안이 **인용과 함께** 표면화. | path(a) 확장 → payload §4 External Landscape |
| R3 | **Skepticism 통과** | 의심 triggered 방향이 모두 steelman 후 *방어 또는 전환*. un-challenged 의심 방향은 확정 후보가 될 수 없다. | steelman-builder dispatch → payload §5의 **`verdict:` 항목** |
| R4 | **시행착오 기록** | steelman switch된 방향 **또는** 사용자가 명시적으로 폐기한 방향이 *이유와 함께* 기록. 0건이면 `- 기각 — N/A — 전부 first-time defend+lock` 한 줄 명시(빈 섹션 금지). | payload §5의 **`기각` 항목** |
| R5 | **Open Questions 박제** | 미해결 명시("유추 금지"). | payload §3 Open Questions |

### R2 — 웹 Landscape

**탐색 경계** — `request-framing` 은 **레포는 읽되 웹은 보지 않는다.** framing 의 공백은
사용자에게 물어서 메운다. 바깥에서 찾는 것은 이 단계(interview)의 R&R 이다 — landscape ·
steelman · blind-spot premortem · coverage-mapper 넷이 전부 그 장치다.

**질문 라우팅** — 답을 사용자만 알 수 있으면 framing, 사용자 밖에서 찾아야 하면 interview.
같은 주제도 이 기준으로 갈린다.

토픽이 잡히면(round 1–2) landscape sweep을 수행합니다. 각 web 검색 *직전에* kill switch를
확인합니다(세션 시작 시 캐시하지 않고 매 호출 직전 재평가):

```bash
if [[ "${DEVBREW_SPEC_DISTILL_DISABLE_WEB:-0}" == "1" ]]; then
  echo "[spec-distill] web 비활성 — landscape 생략, codebase 근거만 사용"
else
  # <web 검색 수행>
  :
fi
```

- 모든 외부 주장은 **출처 URL 필수** — payload §4 External Landscape에 `[취함|피함|중립]` + 이유와 함께.
- **kill switch `DEVBREW_SPEC_DISTILL_DISABLE_WEB=1`** 또는 web 도구 부재 → landscape를 **loud하게
  생략**하고 계속(crash 금지, graceful degradation): `[spec-distill] web 비활성 — landscape 생략, codebase 근거만 사용`.

### R3 — Steelman 의심 게이트 (P17)

의심 trigger = landscape 모순 / 알려진 anti-pattern / 기존 사용자 제약과의 충돌 / coverage-mapper neglect.

1. `steelman-builder` 에이전트를 dispatch:
   ```
   Agent({ description: "Steelman alternative", subagent_type: "spec-distill:steelman-builder",
           prompt: "의심 방향: <direction>${SUSPECT_DIRECTION}</direction>. trigger: <trigger>${TRIGGER}</trigger>. 대안의 강한 케이스를 웹근거와 함께." })
   // **처분** — consumer=orchestrator · fail-open · disclosure=loud advisory
   ```
2. builder 출력(`alternative_statement` + `evidence[].url`)을 **verbatim**으로 다음 라운드의
   «상충» 줄에 반대 케이스로 제시 — conducting-interview는 이를 **약화·편집하지 않습니다**.
3. **게이트**(P17): 사용자가 (방어 → 원안 유지 / 전환 → 대안 채택, 원안은 R4로 / 보류 → §3 OQ) 중 하나를 선택한다.
4. 판정을 payload §5의 **`verdict:` 항목**으로 기록 — 각 항목은 (대안 statement + 웹근거 URL + `verdict ∈ {defended | switched | deferred}` + audit §3의 `ST<N>` 참조). 게이트 매핑: 방어→`defended`, 전환→`switched`, 보류→`deferred`(§3 OQ에도 박제). builder 출력 verbatim은 audit §3에 `#### ST<N>` 헤딩으로 남고, payload §5와 audit §3은 이 `ST<N>` id로 맞물린다(bijection A) — frontmatter에는 별도 필드를 두지 않는다.
5. 한 방향당 steelman 1회(새 근거 없으면 재steelman 금지 — AP16 harassment 방지).

**Web 부재 시 graceful degradation (R2 대칭)**: `steelman-builder`는 WebSearch/WebFetch를 요구합니다.
kill switch `DEVBREW_SPEC_DISTILL_DISABLE_WEB=1` 또는 web 도구 부재로 steelman을 돌릴 수 없으면 —
R2 landscape와 대칭으로 — opaque한 "malformed skepticism (no-url)" 게이트 실패로 떨어뜨리지 말고
**loud advisory**를 내고 **수동 의심 게이트**로 전환합니다:
`[spec-distill] web 비활성 — steelman 자동 생략, 사용자에게 의심 방향 수동 확인 요청`. 이 경우 §5의
`verdict:` 항목은 사용자 판단(방어/전환/보류)을 근거로 기록하되 URL 부재 사유를 명시합니다(`check_brief.py`의
skepticism 형식 검사는 web-disabled 시 수동 판단으로 위임).

**Law 2 경계**: steelman 게이트는 Law 2 분리 메커니즘이 *아닙니다* — Law 2 분리 reviewer는
오직 design doc(brainstorming `-design.md`)에만 적용됩니다. steelman은 문제공간 품질을 끌어올리는
Law 1급 skepticism 의례입니다(verbatim pass-through로 무력화 방지).

## seed 를 입력으로 받았을 때

`$ARGUMENTS` 가 `type: interview-seed` frontmatter 를 가진 문서면, 그것은 **Phase 0 에서
사용자가 확정한 메시지**다. Phase 0 은 그 파일을 **전문으로** 이 command 의 인자에
붙여넣게 하고(그 호출 모양의 정본은 `framing-requests` 의 「호출 모양」 절이다), 그
frontmatter 줄이 seed 를 알아보는 유일한 표지다 — 본문만 오면 seed 로 인식되지 않아 아래
규약이 발동하지 않는다.

- **§6 `S1` 은 `$ARGUMENTS` 원문 그대로다**(frontmatter 포함) — `finishing.md` 의 S1
  규약과 같은 값이다. 그것이 이 세션의 최초 사용자 발화다.
- **seed 에는 태그가 없다.** seed 게이트가 막는 `[open:`/`[추론:`/`[외부:` 구분을 seed
  에서 읽으려 하지 말 것 — Phase 0 이 전문을 사용자 확정으로 만들었으므로 전부 사용자
  **출처**(provenance)다. 이것은 출처일 뿐 **상태**(status)가 아니다 — `status` 는
  하류 규약대로 전부 `provisional` 로 시작하고, `confirmed` 로의 전이는 오직 Step B-0
  사용자 확인에서만 일어난다.
- **seed 를 뒤집을 수 있다**(P23). 인터뷰 중 사용자가 seed 의 확정을 뒤집으면 **새 발화가
  이긴다** — 그리고 그 뒤집음을 **audit §6** 에 새 `S<N>` 으로 추가하고(payload §6은 `S1`
  으로 불변이므로 새 앵커는 audit에만 붙는다) §5 `기각` 에 *원래 / 재결정 / 근거* 로 남긴다.
  조용히 덮어쓰지 않는다.
- **seed 가 아닌 입력도 그대로 받는다.** `/interview` 는 호환을 유지한다 — 조언 한 줄을
  내되 **차단하지 않는다**.

## 종료 — brief 작성 + optional handoff

**종료 절차 전문은 `references/finishing.md` 에 있다.** floor 5차원이 전부 `closed` 가 되어
brief 작성으로 넘어갈 때 그 파일을 Read 로 읽어 그대로 따른다. 인터뷰가 아직 진행 중일 때는
읽지 않는다 — 이 분리의 목적이 그것이다(조건부 로드).

### 나가는 문은 floor 뒤에만 있지 않다

floor 다섯이 전부 `closed` 여야 종료가 열리지만, **사용자는 언제든 종료를 요청할 수 있다.**
그때 미충족 floor 는 **사용자-승인 박제**로 닫는다 — 그 차원의 `evidence` 에
`사용자-승인 박제(@사용자 종료 요청) — §Open Questions 참조` 를 적고, 그 내용을 payload
§3 Open Questions 로 이월한다. 박제 표식이 원장에 남으므로 silent bypass 가 아니다.

발동 조건이 카운터가 아니라 **사용자 발화**라는 점만 예전 escalation 과 다르다. 상한을
없애는 것과 탈출구를 없애는 것은 다르다 — 없애는 것은 사용자 질문의 상한이지 나가는 문이
아니다.

읽어야 하는 조건: `coverage.floor` 의 다섯 차원이 모두 `status: closed`.

```
Read references/finishing.md
```

경로는 이 SKILL.md 파일 기준 상대경로다 — 레포·설치본 두 레이아웃 모두 이 SKILL.md와
같은 위치에 `references/finishing.md` 가 있으므로 그대로 resolve 된다.

## In-flight state migration

state.local.md 로드 시 **구세션 스키마**(`interview_round` 존재 / `coverage` 부재)를 감지하면
*non-mutating read*로 fresh 초기화(승격):

- `coverage.floor`의 5개 차원(root_problem/landscape/skepticism/blind_spot/open_questions) 전부
  `{status: open, evidence: ""}`로 seed.
- `coverage.derived`: `[]`.
- `orchestration`: `{focused_dimension: null, no_progress_streak: 0, blind_spot_dispatched: false, stall_episode: 0, coverage_mapper_dispatched_episode: null}`.

기존 필드(`non_user_streak`·`web_*`·`issue_history` 등)는 유지. 구세션의 라운드별 잠금
레코드 리스트(v0.22.0까지의 잠금 필드)는 승계하지 않고 `user_statements: []`로 fresh
seed합니다 — 잠금 레코드를 발화 레코드로 승격하면 판정이 없던 척하는 잠금이 그대로
넘어옵니다.

**영속화 시점**: 승격된 스키마는 재개된 세션의 첫 액션으로, 첫 probe보다 먼저 Bash
전체-frontmatter write로 즉시 디스크에 반영한다(PN1 state write contract). 이 write는
"다음 명시적 state write"를 기다리지 않는다 — 연기가 아니라 resume 직후 1회다.

근거: coverage-mapper 재dispatch 바운드(`## coverage-mapper dispatch`)는 `orchestration`의
두 에피소드 필드(`stall_episode`·`coverage_mapper_dispatched_episode`)를 디스크에서 직접
비교한다 — 이 write 없이는 그 필드들이 디스크에 없는 채로 첫 probe가 발생해 판정이 무상태
재계산 전제를 잃는다.

이 write는 신규 필드(coverage/orchestration)만 추가하는 forward promotion이며
backward-rewrite가 아니다 — `interview_round`는 이 write에서 자연 소멸하되 다른 기존
필드는 고치지 않는다. backward-rewrite 금지·P14 실패-상태 보존과 무충돌: 이것은 성공적
resume의 promotion write이지 실패-상태 mutation이 아니다.

사용자에게 advisory 한 줄 출력:
```
[spec-distill v0.38.0] state schema migration: coverage/orchestration added (probe counters retired).
```

자동 promote 실패 시(파일 corruption 등) → "구세션 in-flight state 호환 실패 — 세션 재시작 권장"
알림 + state.local.md 보존 (P14).

## kill switch

- `DEVBREW_SPEC_DISTILL_DISABLE=1`: 즉시 abort, state.local.md 보존 (실패 분석용).
- `DEVBREW_SPEC_DISTILL_RHYTHM_GUARD_THRESHOLD=N`: rhythm guard threshold override.
- `DEVBREW_SPEC_DISTILL_DISABLE_WEB=1`: web landscape(R2) 비활성 — loud advisory 후 codebase 근거만 사용.
