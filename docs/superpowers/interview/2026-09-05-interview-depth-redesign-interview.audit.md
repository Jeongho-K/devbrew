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

## 3. 긴 초안

(압축 직전에 작성)
