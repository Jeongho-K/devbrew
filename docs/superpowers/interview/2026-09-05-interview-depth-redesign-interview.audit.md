---
type: interview-seed-audit
topic: interview-depth-redesign
created: 2026-09-05
---

# Phase 0 audit — interview-depth-redesign

## 1. 원문

### 라운드 0 — 최초 요청 (2026-09-05)

Phase 1 interview를 보강해줘.

* 인터뷰가 지는 책임
조사 방향 pm 등, 다음단계는 구현입니다 brainstorming은  설계가 주가되는 자리라, 여기서 내부 외부 조사를 최대한 해내 양질의 정보를 넘겨야 함
그리고 현재 interview는 커버리지 원장을 갖고 있지만 실제 사용감은 여전히 라운드 단위로 질문을 소진한 뒤, 문제를 충분히 파고들기 전에 끝나는 경우가 있다. 단순히 질문 수나 고정
체크리스트를 늘리는 방식이 아니라, 왜 기존 interview가 얕게 종료되는지 현재 구현을 먼저 분석하고 더 집요한 문제공간 탐색으로 재설계해라.
Phase 0와 Phase 1의 경계는 다음과 같다.
   * request-framing: 다음 에이전트에게 무엇을 맡길지 정렬하고 interview-seed를 만든다.
   * interview: 그 요청 뒤에서 실제로 해결해야 할 문제, 원인, 제약, 이해관계, 대안과 방향을 탐색해 interview-brief를 만든다.
Phase 1은 seed의 confirmed 항목을 불필요하게 다시 묻지 않되, inferred·external·open 항목과 새로운 근거로 흔들린 항목은 다시 검증할 수 있어야 한다. Phase 0에서 정리된
실행 계약을 반복하는 대신, 왜 이 문제가 존재하는지, 누구에게 어떤 영향을 주는지, 사용자의 답변이 어떤 가정에 기대는지, 다른 선택지가 무엇인지까지 파고들어라.
인터뷰는 고정 라운드나 질문 수가 아니라 문제공간의 충족도를 기준으로 진행되어야 한다. 모호하거나 피상적인 답, 추천안에 대한 빠른 동의, 근거 없는 확신 하나만으로 차원을
닫지 말고 필요하면 이유·사례·우선순위·상충 관계·실패 조건을 후속 질문으로 확인한다. 새 답이나 외부 근거가 이전 답과 충돌하면 이미 닫힌 주제도 자연스럽게 다시 열 수 있어야 한다.
외부 탐색은 실제 도메인의 대안과 prior art, 그리고 현재 결정에 영향을 주는 사실 검증에 사용한다. 모델의 오래된 지식이 인터뷰 방향을 고정하지 않도록 하되, 외부 사례나 에이전트 추론을 사용자 요구사항으로 승격하지 않는다.
기존 4-block 형식, floor·derived coverage, 상태 전이, probe/round 개념, 종료 조건, steelman·blind-spot 결과의 후속 질문 반영 방식을 함께 점검해라. 어떤 구조를 유지하거나 바꿀지는 미리 단정하지 말고 여러 접근을 비교하되, 형식과 원장만 무거워지고 실제 대화 깊이는 늘지 않는 해결책은 피한다.
성공한 interview는 질문을 많이 한 인터뷰가 아니라 다음 조건을 만족하는 인터뷰다.
   * 핵심 방향이 사용자 표현과 근거를 통해 충분히 드러난다.
   * 중요한 가정과 상충 관계가 검토된다.
   * topic-specific한 미탐색 영역이 남지 않았는지 확인된다.
   * 불확실한 내용은 억지로 닫지 않고 Open Question으로 보존된다.
   * 사용자가 중단하거나 handoff를 선택할 권리는 유지된다.

• • 최종 interview-brief만 읽어도 후속 brainstorming이 문제를 다시 추측하거나 같은 질문을 반복하지 않아도 된다.
먼저 현재 구현과 변경 이력을 조사해 얕은 종료의 실제 원인을 설명하고, 가능한 재설계 방향을 비교한 뒤 구현을 진행해줘. Phase 0 추가와 interview 보강이 하나의 거대한 책
임으로 섞이지 않도록 두 단계의 경계와 handoff 계약도 함께 검증해라.

### 라운드 0 — 세션 중 추가 지시

새로운 워크트리 만들고 거기에서 진행 시작해줘


### 라운드 0 — 세션 중 추가 지시 (2)

추가로 전체 그림을 봤을 때 더 개선사항이 있거나 내가 말한게 좋은 방향이 아니라면 이야기해줘

### 라운드 1 — 사용자 답변 (원문)

더 찾을 수 있다면 찾아봐 git에도 자료가 있을거야 다만 잘 찾아 너무 비용 많이 들지 않게, 2 그런데 우리가 볼 핵심은 interview 쪽이야, 후자, 늘어도 돼, a 필요하면 고쳐도 돼 그리고 대부분 a와 같을거라 phase0면 워크트리 만들어서 거기서 시작하는거로 하면 어떨까 다만 세션에 워크트리가 고정되지는 않게 그리고 인터뷰 자료부터 커밋하고 브랜치명 적절히 선정해주고 superpowers같이, 풀고 너가 보기에 가장 적절한 방식으로 가자 그리고 framing-requests 이쪽이 더 좋은거 같아

### 라운드 2 — 사용자 답변 (원문)

첫번째는 맞는데 두번째는 권장방식이 뭔지 나에게 알려줘 모든 선택지를 바로 결정말고 트레이드오프를, 전부 재검토 대상 다만 지금까지 고민한걸 이해해야겠지

### 라운드 3 — 사용자 답변 (원문; 워크트리 선택지 A/B/C/D 제시에 대한 답, A 권장이었음)

b 가능하면 native 우선

## 2. 라운드 기록

(라운드마다 아래에 append)

### 라운드 1 — 레포 읽기 결과와 질문 (2026-09-05)

읽은 것: `conducting-interview/SKILL.md`(408줄) · `references/finishing.md` · `check_brief.py`
(coverage_ledger_failures 는 form-only) · brief 템플릿 · coverage-mapper/blind-spot/steelman agent ·
CHANGELOG v0.22.0/v0.38.0 · request-framing 설계 §5.1(seed 는 태그 없음) · check_seed.py(TAG_RE 가
`[open:|추론:|외부:` 를 거부) · 실제 인터뷰 audit 3건(08-30 brief-restructure 11라운드, 09-02
seam-channel 9라운드, 09-02 adjudication 9라운드).

얕은 종료의 구현상 원인 후보 (Phase 0 관찰 — 인터뷰가 검증할 것):
- O1 종료 술어가 «이벤트 완료»다: landscape=sweep≥1, skepticism=steelman verdict 1건,
  blind_spot=prober 1회 dispatch. 차원마다 한 번의 dispatch 로 closed 가 될 수 있다.
- O2 «진전» 정의 = status 전이 또는 evidence append. 피상적 답도 evidence 가 되므로
  no_progress_streak 가 안 오르고 coverage-mapper 가 안 불린다.
- O3 4-block 이 «질문 하나 + 추천 답안» 강제 → 라운드당 결정 1개, 추천안 동의 유도.
  framing-requests 는 반대로 «질문을 한꺼번에».
- O4 상태 전이에 closed→open 이 없다. 재개방은 seed 뒤집기(P23)에만 있고 floor/derived 엔 없다.
- O5 derived 차원 공급원이 coverage-mapper 뿐이고 dispatch 조건이 정체·첫 전이다 —
  round 0 에서 seed 로부터 주제 차원을 도출할 의무가 orchestrator 에 없다.
- O6 v0.22.0 이 이미 «집요함»을 목표로 원장을 넣었는데 여전히 얕다 — 원장을 더 넣는 방식이
  깊이를 못 산다는 가장 강한 증거.
- O7 seed 계약 충돌: 요청은 seed 에 confirmed/inferred/external/open 항목이 있다고 전제하지만
  현행 seed 는 «태그 없는 메시지»이고 게이트가 태그를 거부한다.

질문 (아래 보고의 «질문» 블록과 동일) — 답변은 라운드 2 에 append.



### 라운드 2 — git 추가 조사 결과 (2026-09-05)

비용 제한: git log 300건 grep + docs 전수 grep 2회 + 파일 3개 읽기. 웹 없음(Phase 0 경계).

- ★ **같은 문제의 첫 사이클이 이미 있었다** — `docs/archive/interview/2026-07-20-spec-distill-interview-strengthening-interview.md`
  (v0.21.0). 요청 원문 «인터뷰가 더 집요해지고, 미지·모호를 드러내 가르치고, 외부 탐색을 더
  적극적으로, 라운드 기반을 유연한 아키텍처로». 재구성 = «집요함·깊이·차원이 고정 라운드
  체크리스트에 묶여 있다» → LD1~LD5(커버리지 하이브리드·teach-beat·floor 5·범위 중간) → v0.22.0.
  그 인터뷰의 steelman 은 «더 집요하게 만들지 말고 더 가볍게» 였고 verdict=defended
  (집요함≠길이로 재정의해 흡수). 이번 요청은 그 결과물이 여전히 얕다는 것 — 두 번째 사이클.
- 07-26 qg 인터뷰 audit: open_questions floor 가 «사용자 미응답 → 보류 처리, OQ 박제»로 닫힘.
  침묵이 차원을 닫는 경로가 실재.
- 07-25 brief audit: «OQ1(권위 다이얼)은 인터뷰에서 묻지 못했음을 명시» — 못 물은 채 종료.
- 09-02 seam-channel 설계 §9.3: brief §6 S1 의 사실 하나가 코드에 의해 반증됨(«빌더가 스스로
  구한다» → 실제로는 위치 인자 요구). 확정 사실이 틀린 채 넘어간 사례.
- 07-25 archive 설계 §Rejected: «사용자가 명시한 것만 confirmed → 거의 전부 provisional →
  하류 재질문 harassment» — 재질문 문제가 brief 형식 쪽에서도 한 번 다뤄짐.
- superpowers `using-git-worktrees` SKILL(6.3.0) 실재 — Phase 0 워크트리 제안의 참조 대상.

라운드 1 답변 해석(확인 대상):
- Q1 사례: 지목 없음 → git 조사로 대체(위).
- Q2 seed 계약: «2» = ② seed 에 가벼운 구조, 단 핵심은 interview 쪽 (해석 확인 필요).
- Q3 분업: 후자 — brainstorming 유지, 인터뷰 조사가 설계 입력으로 충분해지면 됨.
- Q4 비용: 늘어도 됨.
- Q5 범위: (a) 한 브랜치 연속. Phase 0 도 필요하면 고침. **신규 요구**: 구현으로 갈 요청이면
  Phase 0 이 워크트리를 만들어 거기서 시작 · 세션에 워크트리 고정 안 함 · 인터뷰 자료(audit/seed)
  부터 커밋 · 브랜치명 자동 선정 · superpowers(using-git-worktrees) 같이.
- Q6: 질문-하나 원칙 해제, 추천 답안은 내 판단, framing-requests 의 «질문 한꺼번에» 방식 선호.


### 라운드 2 — 사용자 답변 (원문)

첫번째는 맞는데 두번째는 권장방식이 뭔지 나에게 알려줘 모든 선택지를 바로 결정말고 트레이드오프를, 전부 재검토 대상 다만 지금까지 고민한걸 이해해야겠지

### 라운드 3 — 워크트리 선택지 제시 → 사용자 답변 (원문)

(제시한 선택지: A `git worktree add` + 세션 유지 / B `EnterWorktree` native / C Phase 1 에서 생성 / D 워크트리 없이 브랜치만. 권장 A. C 는 미커밋 audit 을 워크트리가 못 봐 깨짐.)

b 가능하면 native 우선

해석: B 확정. 「세션에 워크트리가 고정되지 않게」는 native 우선에 양보됨(대가를 알고 수용). 브랜치 접두어 `worktree-` 교정, 격리 세션 git 가드는 인터뷰가 다룰 세부.

## 3. 긴 초안


### A. 발단과 정체

spec-distill 의 Phase 1 interview(`conducting-interview`) 가 문제를 충분히 파기 전에 끝난다. 커버리지 원장(floor 5 + derived) 이 있음에도 사용자 체감은 «라운드 단위로 질문을 소진하고 끝». 사용자는 질문 수·체크리스트 증설이 아니라 원인 분석 → 재설계 → 구현을 요구했고, Phase 0/1 경계와 handoff 계약 검증을 함께 요구했다.

### B. 두 번째 사이클이라는 사실

- 2026-07-20 `spec-distill-interview-strengthening` 인터뷰(v0.21.0, archive) 가 같은 요청을 받았다. 재구성 = «집요함·깊이·차원이 고정 라운드 체크리스트에 묶여 있다». LD1 커버리지-구동 하이브리드 · LD2 teach-beat + blind-spot 슬롯 · LD3 집요함 = 신호 기반 깊이 + 커버리지 계약(길이 아님) · LD4 floor 5 + 주제-도출 · LD5 범위 중간(SKILL 산문 + check_brief + 상태 스키마). 그 steelman: «더 집요하게 말고 더 가볍게(respondent fatigue·YAGNI)» → defended(집요함≠길이로 흡수).
- 그 결과 v0.22.0(2026-07-21): 원장·probe_budget(cap 12)·blind-spot-prober·coverage-mapper·teach-beat. v0.38.0(08-28): probe 상한 제거(사용자가 시계라 묶을 자율이 없다), 탈출구를 카운터에서 사용자 발화로.
- 이번 요청은 그 결과가 여전히 얕다는 것. 사용자: 전부 재검토 대상, 단 그때의 고민을 이해한 뒤.

### C. 현재 구현에서 본 원인 후보 (Phase 0 관찰, 확정 아님)

- O1 종료 술어가 이벤트 완료: landscape=web sweep ≥1, skepticism=steelman verdict 1건, blind_spot=prober 1회. `check_brief.py coverage_ledger_failures` 는 status 토큰 + evidence 비어있지 않음만(주석이 form-only 자인).
- O2 진전 = status 전이 또는 evidence append. 피상적 답도 진전. `no_progress_streak` 가 안 올라 coverage-mapper 조건 1 이 거의 안 발화.
- O3 4-block «한 번에 하나의 질문 + 추천 답안» (devbrother2024 deep-interview 흡수). 라운드당 결정 1개, 추천안 동의 유도. framing-requests 는 «질문을 한꺼번에» — 사용자는 이쪽이 낫다고 판단.
- O4 상태 전이 open→in-progress→closed 만. closed→open 없음. 재개방은 seed 뒤집기 P23 뿐.
- O5 derived 공급원 = coverage-mapper 뿐, dispatch 조건 = 정체 3 또는 floor 첫 전이. round 0 에 seed 로부터 주제 차원을 도출할 의무 없음.
- O6 v0.22.0 이 이미 «집요함» 목표로 원장을 넣었는데 여전히 얕다 → 원장 증설이 깊이를 못 산다는 가장 강한 증거.
- O7 seed 계약: 태그 없는 산문(설계 §5.1, `check_seed.py` TAG_RE). 요청의 «confirmed/inferred/external/open 재검증» 구분이 파일에 없다.
- O8 규칙 대부분이 SKILL 산문. orchestrator 이행률 미측정(08-27 이음매 진단 동일 지적). 재설계도 산문이면 같은 미측정 재생산.
- git 실증: 07-26 qg 인터뷰 open_questions 를 «사용자 미응답 → 보류» 로 닫음 · 07-25 «OQ1 은 묻지 못했음» 명시 후 종료 · 09-02 seam 설계 §9.3 brief S1 사실이 코드로 반증 · 07-25 설계 Rejected «명시만 confirmed → 전부 provisional → 하류 재질문 harassment».
- 실측: 최근 인터뷰 3건 9·9·11 라운드, brief 286~575줄 — 라운드가 적은 게 아니라 라운드가 깊이로 안 쌓임.

### D. 사용자가 정한 것 (라운드 1~3)

- Q2 seed 계약: ② seed 에 가벼운 구조 — 단 이번 무게중심은 interview.
- Q3 brainstorming 은 그대로. 인터뷰 조사가 설계 입력으로 충분해지면 됨.
- Q4 비용(라운드·dispatch·web·codex) 늘어도 됨.
- Q5 (a) 한 브랜치 연속(분석→설계→구현). Phase 0 파일 필요하면 고침.
- Q5 신규: 구현 갈 요청이면 Phase 0 이 워크트리 생성·인터뷰 자료 선커밋·브랜치명 선정·superpowers 같이. 라운드 3: **B native(`EnterWorktree`) 우선** — 세션 고정 대가 수용.
- Q6 질문-하나 원칙 해제. 추천 답안 유지 여부는 내 판단. Phase 0 의 «한꺼번에» 방식 선호.
- 첫 사이클: 전부 재검토, 단 이해 후.

### E. 워크트리 선택지 비교 (라운드 3 제시분)

A git worktree add + 세션 유지(권장했음) / B native 세션 이동(브랜치 `worktree-` 접두어, 격리 세션 git 가드, 종료 프롬프트) / C Phase 1 생성(깨짐: 미커밋 audit 을 워크트리가 못 봄 → `audit_file` 결속 단절) / D 브랜치만(동시 세션 충돌 — `feature+steelman-goal-fit` 워크트리가 잠긴 채 실재). 사용자 선택 B. 남는 세부: 생성 시점(첫 라운드 vs 압축 직후).

### F. 성공 기준 (원문 + 정련)

핵심 방향이 사용자 표현·근거로 드러남 · 가정·상충 검토 · topic-specific 미탐색 영역 확인(«남지 않았다» 는 검증 불가 → «어떤 방법으로 찾았는데 못 찾았다» 로) · 불확실은 OQ 로 보존 · 중단/handoff 권리 유지 · brief 만 읽은 brainstorming 이 재추측·재질문 안 함.

### G. 경계·handoff

request-framing = 무엇을 맡길지 정렬 + seed. interview = 진짜 문제·원인·제약·이해관계·대안 탐색 + brief. Phase 1 은 confirmed 재질문 금지, inferred/external/open·흔들린 항목 재검증. Phase 0 추가와 interview 보강이 한 책임으로 섞이지 않게.

### H. 압축에서 깎은 것 (seed 에 없음, 여기만)

파일 경로·줄번호·버전 번호 · 상태 스키마 필드명 · 테스트 러너 · 워크트리 선택지 표 전문 · 기억 파일 목록 · 라운드 수·brief 줄 수 실측치 · 사용자 답변의 축약 표기 · CLAUDE.md 상시 규칙(Law 1~3, 버전 bump, 워크트리 git 규칙) · 하류가 정할 것(어떤 구조를 바꿀지, 생성 시점, 추천 답안 유지).

## 4. 검증 라운드 (억제 리뷰 · codex · 냉독)

### 4.0 degrade 원장

- 원장 없음 — Phase 0 은 인터뷰 이전이라 state.local.md 가 없다(`no-state-in-phase-0`). 아래 기록이 유일한 채널.
- readback · readback · **degraded(model)** — `seed-readback`(model: inherit=Fable) 이 2회 연속 API safeguard 오류(`[reasoning_extraction]`, req_011Cejw4AVBjMCwUB6WVD9Cn · req_011CejwEe4ADHEtvr8MGqVNR)로 종료. 축 소실을 막기 위해 dispatch-time `model: opus` 로 대체 실행. frontmatter 는 손대지 않음. 두 냉독(r1·r2) 모두 opus.
- pipeline · suppression · **fixed** — 첫 번들이 라운드 2·3 사용자 답변을 `## 1. 원문` 에 싣지 않았다(라운드 기록 절에만 있었음). codex r1 이 그 부재를 적발 → §1 에 이관 후 번들 재조립. codex r1 결과는 그 결함 상태의 산출물.
- codex · suppression · ok ×3 (r1 결함 번들 · r2 초안 v1 · r3 초안 v2). 실호출 3회, 성공 3회.
- seed-critic · suppression · ok ×2 (초안 v1 · v2).

### 4.1 codex r1 (결함 번들 — 라운드 2·3 원문 부재 상태)

- agent_inference_as_user_decision: «대가는 알고 받아들였다: native 로 들어가면 세션이 워크트리에 고정되고…»는 사용자 원문 «세션에 워크트리가 고정되지는 않게»와 반대. → 수락 문장을 빼고 원래 요구 유지.

### 4.2 codex r2 (초안 v1)

1. premature_closure — «같은 재구성으로 되돌아가면 실패다» 는 이전 접근 재선택을 미리 배제. → 삭제, 대안과 함께 비교.
2. unsupported_constraint — «남지 않았다»가 아니라 «어떤 방법으로 찾아봤는데 못 찾았다» 는 입증 방식 추가. → 원문 조건으로 되돌림.
3. agent_inference_as_user_decision — «seed 에 가벼운 구조를 넣는 쪽으로 정했으나» 결정 단정. → 삭제 또는 비교 대안으로.
4. agent_inference_as_user_decision — «대가는 알고 받아들였다…» 세 대가 수락 단정. → 삭제, 미결 트레이드오프로.
5. unsupported_constraint — origin/main 이동량·형제 워크트리 사전 점검을 필수 절차로. → 삭제.

### 4.3 seed-critic r1 (초안 v1)

1. 축1 «같은 재구성으로 되돌아가면 실패다» — 원문 대응 부재. → 삭제 또는 «같은 결론이면 첫 사이클이 왜 얕았는지 설명» 조건으로.
2. 축3/4 «Phase 0 처럼 모아 묻는 쪽이 낫다» — 에이전트 선호가 대체안을 못 박음. → «—» 이후 삭제.
3. 축1/4 «어떤 방법으로 찾아봤는데 못 찾았다» — 증명 형식 강화. → 원문 표현으로.
4. 축1 origin/main·형제 워크트리 점검 — 원문 부재. → 삭제 또는 «Phase 0 관찰:» 접두.
5. 축3 «audit 라운드 기록과 SKILL 규칙 대조를 원인 분석의 일부로 하라» — 방법 처방. → 명령 삭제, 관찰만.
6. 축4 «미커밋 파일이 안 보이므로 … 그것이 이유다» — 사용자 근거(«대부분 a와 같을거라»)를 에이전트 근거로 치환. → 주체 분리.
7. 축4(경미) «superpowers skill 이 native 우선을 말한다» / «대가는 알고 받아들였다» — «가능하면»의 fallback 미명시. → «가능하면 native, 불가 시 A».
- 범위 밖: 라운드 1 «framing-requests 이쪽이 더 좋은거 같아» 가 초안에 없음.

### 4.4 냉독 r1 (초안 v1, opus)

이해: 원인 규명→재설계→구현 한 브랜치; 두 번째 사이클이라 선행 사이클 사고 경로 복원 후 다른 곳에 도착; 핵심 축 = 종료 술어의 교체(이벤트→충족도). 모르겠는 곳: Phase 0 의 정체(기존인지 신설인지) · 워크트리 요구가 절차인지 구현물인지 · 형제 워크트리 확인의 후속 · seed 구조화의 범위 포함 여부 · «floor 다섯 차원» 파싱과 나머지 두 이름 · «질문 많이 한 인터뷰가 아니다»와 첫 사이클 방어 논리의 거리 · 충족도 판정 주체 · handoff 지시 대상 · 개선 대상 skill 이 이번 인터뷰를 수행하는 자기참조.

### 4.5 초안 v1 → v2 반영

critic r1 1·3·4·5·6·7 + codex r2 1·2·4·5 반영(«같은 결론이면 설명» 조건화 · 원문 조건 복원 + Phase 0 관찰로 이동 · 사전 점검을 관찰로 강등 · 대조 명령 삭제 · 근거 주체 분리 · 긴장을 미해결로 명시). codex r2 3 은 부분 반영(사용자 선택+확인 사실을 출처 표기로). 냉독 r1 의 사실 공백 넷 반영(Phase 0=request-framing · floor 다섯 이름 · handoff 대상 · 자기참조).

### 4.6 codex r3 (초안 v2)

1. agent_inference_as_user_decision — «seed 에 가벼운 구조를 넣는다는 선택지를 골랐고 그 해석을 확인했다» — 원문엔 «2», «첫번째는 맞는데»뿐이라 확인 불가. → 삭제.
2. unsupported_constraint — «라운드·dispatch·web·codex 비용은 늘어도 된다» — 원문은 대상 없는 «늘어도 돼»와 «너무 비용 많이 들지 않게»가 함께. → 포괄 허용 문장 삭제.
3. premature_closure — «한 브랜치에서 원인 분석, 설계, 구현까지 간다» — 원문은 워크트리 시작·자료 커밋만. → 삭제.

### 4.7 seed-critic r2 (초안 v2)

1. 축1 «구현으로 이어질 요청이면» — «대부분 a와 같을거라»는 무조건 생성의 근거이지 판별 조건이 아님. → 조건절 삭제.
2. 축1 «같은 결론이면 첫 사이클이 왜 얕았는지 설명» — 원문 부재. → 삭제 또는 «Phase 0 제안:».
3. 축2 «생성 시점(첫 라운드인지 압축 직후인지)» — 괄호가 선택지를 둘로 고정. → 괄호 삭제 또는 예시 표시.
4. 축2 «인터뷰 자료(audit 과 seed)» — 괄호는 해석; 라운드 기록이 빠짐. → 예시 표시.
5. 축3 «brainstorming 으로의 handoff» — 원문은 목적지 없음. → 복원.
6. 축3 «brainstorming 은 그대로 둔다» — «후자»는 분업 결정이지 파일 불가침 아님. → «접근법 비교는 brainstorming 몫으로 유지».
7. 축3 «방향은 이렇다» 문단이 확정문 — 사용자는 «내가 말한게 좋은 방향이 아니라면 이야기해줘»로 반박을 초청. → 방향을 검증 대상으로 표시.
8. 축3 «비용은 늘어도 된다» — 같은 답변의 «너무 비용 많이 들지 않게»(사례 탐색)가 사라짐. → 둘 다 싣기.
9. 축4 «대부분의 요청이 구현으로 이어진다» 겹낫표 — 의역을 인용처럼. → 원문 «대부분 a와 같을거라» + a 정의 병기.
10. 축4 «긴장은 풀리지 않은 채» — B 는 대가 명시 후 선택된 후행 결정; 미확인은 라운드 2 둘째 확인(«세션 고정 안 함»의 의미)에 답이 없었다는 것뿐. → 그렇게 적기. **(codex r1·r2 와 반대 방향의 판정)**
11. 축4 «측정된 적이 없다» — 부재 단정. → «측정 기록을 Phase 0 은 찾지 못했다».
12. 축4 «그 자기참조는 자료다» — 착안이 선언문. → «Phase 0 착안:» 또는 허용형만.
13. 축4 과거 audit 세 사례 — 위치 없이 «실재한다». → 파일 경로 병기, «Phase 0 이 찾은 것» 표시.

### 4.8 냉독 r2 (초안 v2, opus)

이해: 순서(원인 설명→1차 사이클 이해→비교→재설계→구현)가 요구; 딸린 둘 = seed 가벼운 구조(범위 안, 무게중심 interview)·Phase 0 워크트리 책임; 자기참조는 자료; 핵심 = 종료 술어 교체; 외부는 «모델을 흔드는 데 쓰고 사용자를 대변하는 데 쓰지 않는다»; «양은 늘려도 되지만 양으로 푸는 것은 안 된다». 신경 쓰는 것: 재발 경계 · 형식주의 불신 · 미측정 불안 · 사용자 자율 · 단계 경계. 모르겠는 곳: 얕음의 판정자 · 후속 확인 다섯 항목이 체크리스트가 아니라면 무엇인지 · «구현까지»의 세션 경계 · 워크트리 요구가 범위인지 인터뷰 주제인지 · 워크트리 긴장의 처분 · Phase 0 질문 방식이 seed 안에 없음 · 추천 답안 위임이 진짜인지 · 대리 조건 후보 부재 · 원인 후보 검증 기준 · «전부 재검토»에 제거가 포함되는지 · 비용 상한 부재와 정지 조건 · 자기참조 자료 범위.
