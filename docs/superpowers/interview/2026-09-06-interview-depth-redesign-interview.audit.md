---
type: interview-audit
payload: 2026-09-06-interview-depth-redesign-interview.md
created_at: 2026-09-06
session_id: 445f0aa1-6fbd-44c2-b0d6-be8d3a05e447
source: spec-distill conducting-interview v0.53.1
---

# 인터뷰 깊이 재설계 — Interview Audit

> 순수 텔레메트리 — 다음 stage가 읽는 핸드오프 산출물은 payload이고, 여기에는 이 인터뷰가 어떻게 진행됐는지의 프로세스 기록만 남는다(D1).
> payload frontmatter의 `audit_file`이 이 파일을 가리키며, 게이트는 두 파일을 함께 검사한다.
> Phase 0 의 기록은 `2026-09-05-interview-depth-redesign-interview.audit.md`(seed audit)에 따로 있다.

## 1. Coverage Ledger

- floor:root_problem — closed — R1 S3(질문 소진=안 떠올라 끝남) → R2 재구성 v2 동의(S10) → 아카이브 원장 실측(닫힘 근거 전부 이벤트형·정체 트리거 무발화·mapper 미이행)과 S3 위에서 v3 «인터뷰어의 다음 행동이 직전 답에서 나오지 않는다» 도출, S21 동의, 리뷰 후 S31 로 재확인. v2 는 결과로 강등. (d) ROOT_CAUSE + HIDDEN_ASSUMPTIONS
- floor:landscape — closed — orchestrator web sweep 2콜 + coverage-mapper 9편 + steelman 11건 + blind-spot-prober 13건. 핵심 취함: Wuttke(후속질문 미이행 88%) · Anthropic context-engineering(고고도 지시+예시). 피함: judge 동계열 독립성 · AInterviewer. payload §4 에 14항목 판정과 함께
- floor:skepticism — closed — ST1 steelman-builder 1회 dispatch → R4 verbatim 제시 → 사용자 보류(S15) → R5 재게이트 verdict=switched(부분, S20). 원안 함의 방향은 payload §5 기각
- floor:blind_spot — closed — blind-spot-prober 1회(C8): 숨은 가정 6 + 실패 양식 7(conf 0.72). R4 에서 HA2·HA3·HA4·HA6·FM2·FM6 표면화, 인용 2건 orchestrator 코드 확인(finishing.md:225 · framing-requests SKILL git 언급 0건). 사용자 처분: HA3→지표 폐기(S16→S19), HA6→유지·기록(S17). payload §5 위험 항목 10건
- floor:open_questions — closed — OQ 11건 사용자 확인 박제(S25) + FM6 범위 밖(S24), 리뷰 후 OQ 재편. R1 보류 2건(S2·S6)은 아카이브 실측으로 해소돼 OQ 아님. 유추 금지
- derived:depth-measurement — closed — 충족도의 조작적 정의·판정자(check_brief 는 form-only, 계측 부재); S4 독립 판정 → HA2 반박, 지표(나) → HA3 폐기, S16 육안 → 되물음 → S18 «빠른 답» → S19 «측정만·게이트 아님». 측정 형태 = Wuttke 식 사후 계수(사람 표본 검증 필수 — S27·S31). 판정자 형태는 OQ3
- derived:rule-adherence — closed — 산문 규칙 이행률·집행 층위; 실측: coverage-mapper 첫 전이 dispatch 4/9 미이행, teach-beat open-ended 8/8 답 없이 소실, 옵션에 적은 위험 재론 0건. 어느 규칙을 기계로 옮길지는 OQ8
- derived:fatigue-vs-depth — closed — 첫 사이클 LD3 fatigue 방어의 산물이 얕음 후보; S9 허용치(3~5×10~15) + 우려 2(질문 수 목적화·하류 결정 선점) + S22(추천은 답을 짧게 만들지만 모를 때 필요, 트레이드오프 가시화, 쉽게 이해). «되묻기 부재»가 fatigue 방어의 그늘
- derived:prior-cycle-attribution — closed — 첫 해법 실패의 귀속(설계/미이행/미측정); 아카이브 원장 9건 실측으로 셋 다 실재하며 맞물림. 07-26 audit 원문 «stall 조건이 한 번도 발화 안 함(매 probe evidence append)» = 설계, mapper 4/9 미이행 = 미이행, 깊이 지표 부재 = 미측정
- derived:seed-handoff — closed — Phase 0 seed 계약·워크트리 선커밋의 인터뷰 결합점(경량); 결합점 = seed 의 «재검증 지시» 표시(S11). 워크트리 첫 라운드(S12), 세션 고정 발언 철회(S13), 형제 충돌 OQ(S14), premortem HA6 반박 후 유지(S17)

## 2. Budget

- 질문 라운드: 7 (R1~R6 + R4b 되물음) · agent dispatch: 5 (coverage-mapper 1 · steelman-builder 1 · blind-spot-prober 1 · 계수 general-purpose 2) · codex 실호출: 0 (성공 0) — brief 리뷰 파이프라인 전
- orchestrator web 호출: 2 (kill switch 매 호출 직전 확인, 미설정)

## 3. Steelman 원문

#### ST1 — 구조를 더하지 말고 측정 먼저 + 단일 고고도 지시 + 닫힘 근거 노출

> **alternative_statement:** "구조를 하나도 더하지 말라 — 새 닫힘-판정 에이전트·probe 도구상자·closed→open 상태기계 대신, (1) 기존 audit 9건의 트랜스크립트를 Wuttke 식으로 «후속 질문을 했어야 했는데 안 한 자리»로 세어 얕음의 실제 모양을 먼저 확정하고, (2) SKILL.md 의 규칙 더미(C43/C44/C11/C8/R1–R5/teach-beat)를 걷어내 «모호·놀라운·빠른-동의 답에는 이유·사례·실패조건을 되묻고 그 전엔 닫지 않는다»는 단일 고고도 지시 + canonical 예시 2–3개로 바꾸고, (3) 닫힘 판정은 옮기지 않되 orchestrator 가 «이 차원을 닫는 근거 한 줄»을 사용자에게 보이게 해 재량을 없애는 대신 드러내며, (4) «하류가 다시 물은 횟수»는 측정만 하고 게이트로 만들지 않는다. 이것이 사이클 1 이 시도하지 않은 유일한 축이며, 사이클 2 가 구조를 더하면 사이클 1 의 재생산이다."
>
> **strongest_case:** 사이클 1(v0.22.0)이 실증한 것은 «구조(원장·카운터·dispatch 조건)를 더해도 얕음이 그대로»(audit O6)라는 사실이고, 사이클 1 이 시도하지 않은 것은 «규칙을 줄이고 핵심 지시 하나를 세게 + 측정»이다 — 그때의 steelman «가볍게»는 «길이 줄이기»로 읽혀 defended 됐을 뿐 «구조 대신 지시»는 검증된 적이 없다. 이번 재구성 v2 가 제안하는 셋(독립 judge·도구상자·상태 전이)은 전부 사이클 1 과 같은 종류(형식·원장)이고, seed 가 명시적으로 피하라 한 실패의 후보다.
> 같은 문제를 실제로 측정한 Wuttke et al.(2410.01824)은 단일-프롬프트 GPT-4 인터뷰어의 결정적 결함이 정확히 «놀랍거나 모호한 답에 후속 질문을 하라»는 지시 미이행(해당 위반의 88%)임을 **판정 에이전트 없이 트랜스크립트를 읽고 위반을 세어서**(인터뷰당 AI 72 vs 인간 64) 찾아냈다. 우리의 «얕음»도 이미 알려진, 한 문장으로 적히고, 세어서 잡히는 failure mode다 — Hamel 의 «error analysis 가 evals 의 가장 중요한 활동»이 말하는 그것이며, 이 리포는 audit 9건을 갖고도 «어느 라운드에서 되묻지 않았는가»를 한 번도 센 적이 없다(O8). 측정 없이 judge 를 넣으면 judge 는 무엇을 거부해야 하는지도 모른다.
> 독립 judge 의 «독립»은 이름뿐이다 — 같은 모델 계열 judge 는 orchestrator 가 «닫아도 된다»고 적은 저-perplexity 근거를 그대로 선호한다(self-preference bias 는 자기 인식이 아니라 친숙한 텍스트 선호에서 온다). 도구를 나눠도 전제는 안 나뉜다. AInterviewer 는 «충분히 후속했는가»를 판정하는 분류 에이전트를 실제로 넣었는데 결과는 인간 대비 차이 없음(specificity·relevance 동일)이었다 — 구조가 우월성을 샀다는 증거가 아니다. CDM 자체도 probe 표를 lock-step 으로 돌리는 방법이 아니라 «순간에 맞는 것을 고르는 유연성 + 인터뷰어 숙련»이며, 그 유연성은 프롬프트 속 예시 몇 줄이지 상태기계가 아니다. 그리고 Anthropic 의 «smallest possible set of high-signal tokens / brittle hardcoded logic 이 실패 모드» 와 «complexity only when it demonstrably improves outcomes», 그리고 «scaffolding 의 10–20% 이득은 다음 모델 세대에 소거된다(Manus 4회 재구축)»는 전부 같은 방향을 가리킨다: 408줄 SKILL 에 규칙을 더 얹을수록 «되물어라»는 핵심 지시가 묻히고, 오늘 짠 judge 와 도구상자는 내년 모델에 대한 역베팅이다.
>
> **weakness_of_current:** "재구성 v2 는 «미측정」을 스스로 인정하면서 측정 없이 구조 셋을 제안한다 — 「재량 → 4/9 미이행」을 인과로 단정하지만, 규칙이 너무 많아 우선순위가 안 보여서 건너뛴 것인지(지시 문제)와 재량 자체가 문제인지(판정자 문제)를 가른 적이 없다. 닫힘 판정을 독립 에이전트로 «옮기는」 것은 재량을 없애는 게 아니라 같은 산문 규칙을 읽는 같은 계열 모델에게 재량을 한 번 더 주는 것이고, 그 에이전트의 이행률도 똑같이 미측정으로 남는다(O8 재생산). 도구상자와 closed→open 전이는 «형식과 원장만 무거워지는» 실패의 정의에 그대로 들어맞으며 사이클 1 이 이미 그 길을 걸었다."
>
> **confidence:** 0.62
>
> **builder 의 caveat:** 대안이 가장 세게 치는 것은 원안의 (1) 독립 judge 와 (3) 상태 전이이고, (4) 하류 재질문 계수는 대안도 원하는 것(단 게이트 아닌 측정으로)이라 양립한다. (2) probe 는 «프롬프트 속 예시」로 축소하면 대안 안에 흡수된다. 반대로 대안의 «단일 강한 지시」 부분은 Wuttke 결과 자체가 «단일 지시가 안 지켜졌다」이므로 약하다 — 그 논문은 더 센 지시나 예시를 시험하지 않았을 뿐, 지시만으로 충분하다는 증거는 아니다. 따라서 대안의 핵심은 «지시로 충분하다」가 아니라 **«측정 전엔 어느 구조도 정당화되지 않는다」** 이고, 그 측정(audit 9건에서 되묻지 않은 자리 계수)은 하니스 없이 이번 사이클 안에서 바로 할 수 있다.
>
> **evidence (URL 은 §7):** «wuttke» · «hamel-error-analysis» · «anthropic-context-eng» · «anthropic-effective-agents» · «bitter-lesson-harness» · «judge-self-preference» · «judge-survey» · «ainterviewer» · «cdm-globalcognition» · «chopra-haaland» · «goodhart»

## 4. 게이트 실행 기록

- check_brief.py gate — pass (2026-09-06) — web: enabled (1차 실행 fail: §4 산문 속 «» 5건이 출처키로 파싱됨 → 「」로 교체 후 pass)
- check_verbatim_coverage.py — exit 0 (2026-09-06) (1차 exit 3: state user_statements 가 flow-style YAML 이라 파서 거부 → block-style 로 변환; 2차 exit 1: state 의 chosen 텍스트에 orchestrator 주석이 섞여 audit 원문과 불일치 → 사용자 pick 원문으로 정정)

## 5. 프로세스 로그

- round 0: seed 입력(S1). state 초기화(floor 5 open). 첫 사이클 자료 읽음(07-20 brief LD1~LD5 · 07-20 설계 G1~G5/C1~C12/R1~R11 · CHANGELOG v0.36~0.38). 웹 kill switch 미설정 확인
- round 1: (d) ROOT_CAUSE + (b) — 묶음 질문 5개(seed 가 위임한 형식 결정 공시). coverage-mapper dispatch(root_problem 첫 전이, episode 0) → derived 5 제안, 전부 admit. teach-heavy(CDM 반복 pass vs 우리 원장). 답 S2~S6: 사례 모름 / 안 떠올라 끝남 / 판정자=추천 / 묶음 방식 / 귀속 모름
- round 2: (a) 아카이브 audit 9건 원장 행 스윕(steelman 1회 8/9, prober 1회 9/9, mapper 5/9, derived N/A 5/9, «stall 한 번도 안 발화» 원문) + web sweep 2콜. (b) 재구성 v2 제시. 답 S7~S10: 도구상자 허용 / 지표 (나)+(다) / 3~5×10~15 ok + 우려 2 + AskUserQuestion 요청 / v2 동의
- round 3: (b) AskUserQuestion — seed 구조 목적 / 워크트리 시점 / 세션 고정 원뜻 / 형제 충돌. 답 S11~S14. 병렬 dispatch: steelman-builder(ST1) + blind-spot-prober
- round 4: (b) ST1 verbatim 제시 + premortem 표면화(HA2·HA3·HA4·HA6·FM2·FM6). 인용 2건 코드 확인. 답 S15~S17: 보류 / 육안만 / 워크트리 유지
- round 4b: (b) «육안만» 되물음(이 인터뷰의 원칙 자체 적용). 답 S18~S19: 빠른 답 / 측정만·게이트 아님
- round 4c: (a) 세션 기록 8건에서 되묻음 누락을 모델 2회로 계수 시도. 리뷰 1단계에서 «같은 계열 모델·저자 루브릭·사람 미검증»이 지적돼 사용자 결정(S27·S31)으로 결과를 brief·audit 에서 제거
- round 5: (b) 재구성 v3 + steelman 재게이트. 답 S20~S22: 부분 전환 / v3 동의 / 추천·트레이드오프·쉽게 이해
- round 6: (b) S22 의 «쉽게 이해» 되물음 + FM6 범위 + OQ 11 확인. 답 S23~S25. floor 5/5 · derived 5/5 closed → finishing
- 형식 결정(공시): seed 가 «한 번에 하나» 원칙을 풀고 대체 방식을 위임했으므로 라운드마다 질문을 묶어 묻고 추천은 트레이드오프와 함께 냈다. R3 부터 AskUserQuestion(S9 요청)
- degrade: 없음 (web 가용, dispatch 5/5 정상 반환). seed-readback 이 Phase 0 에서 opus 로 강등된 것은 seed audit 에 기록

### brief 리뷰 라운드 (reviewing-brief, v0.24.0)

- 방향성: Claude 6건 / codex 3건 (겹침 1) → 7항목 사용자 결정 S26~S34 — 재결정 5건(계수 제거 · seed 무표시=미확인 · native+rename · 묶음→후보 · 되묻기/되비추기 둘 다 후보), 방어 2건(추천 항상 먼저 · 답 단위 사용자 판정자 미채택)
- 충실도 기록(게이트 아님, 마지막 관측 verdict): needs_revise — critic 6건 / codex 3건(medium, codex 단독 verdict approved) — 재라운드 2/2 (상한 도달). 라운드별: r1 critic 11·codex 7 → 수정 → r2 critic 7·codex 3 → 수정 → r3 critic 6·codex 3 → 저자 수정 반영(C1·C2·C6·C7·C8·C12·C24·C29 축소, C26~C38 추가, §1 Non-goal·§5·✎ 정정) 후 fresh 재리뷰 없음 — Step B 에 미재리뷰 사실로 상신
- 냉독: gap 0건 (G1~G6 전부 해당 없음 — 전부 잠정으로 읽음·OQ 11건·§7 다음 행동 정확). 가독성 메모: C10·C13·C2 는 statement 만으로는 뜻이 안 보이고 ✎ 절을 읽어야 함; OQ3 의 S8 참조는 payload 에 S8 이 없어 역추적 필요; 첫 사이클 장치 용어(teach-beat·4-block·coverage-mapper·floor)는 설명 짧음. blob rc=3 이라 신뢰도 하향
- degrade: critic:fidelity:degraded(번들 payload 에 S1 seed 의 audit 파일명 잔존) · critic:fidelity:degraded(재리뷰 상한 2 도달, 마지막 findings critic 6·codex 3 medium 잔존 — 저자 수정 반영, fresh 재리뷰 없음) · readback:readback:degraded(blob 에 같은 잔존, 신뢰도 하향). fallback 채널 0건

## 6. 사용자 원문

> **출처 표기** — 🗣 사용자 발화 · ☑ 사용자 선택 · ✎ 모델 추론

- **S2** 🗣 발화 (R1 Q1 — 얕음의 구체 사례):
  > 1. 잘 모르겠네

- **S3** 🗣 발화 (R1 Q2 — 질문 소진의 뜻):
  > 2. 안 떠올라 끝남

- **S4** 🗣 발화 (R1 Q3 — 충족 판정자; «추천»=②독립 에이전트 주판정 + ①사용자 종료 시 일괄):
  > 3. 추천으로

- **S5** 🗣 발화 (R1 Q4 — «framing-requests 쪽이 더 좋다»의 지시 대상):
  > 4. 질문을 한라운드에 하나씩만 하는데 묶이지 않는걸 말한거야 framing-requests과 interview는 역할이 다르니까 그건 명확히 해야지

- **S6** 🗣 발화 (R1 Q5 — 첫 사이클 귀속):
  > 5. 모름

- **S7** ☑ 선택 (R2 Q1 — probe 묶음):
  > 1. 2  (= ② 허용하되 «완료해야 할 목록»이 아니라 «꺼내 쓰는 도구상자»로)

- **S8** ☑ 선택 (R2 Q2 — «얕다»의 측정; «추천»=(나) 하류가 다시 물은 횟수를 최종 지표, (다) 독립 에이전트 판정 기록을 인터뷰 중 지표):
  > 2. 추천

- **S9** 🗣 발화 (R2 Q3 — 피로 허용치):
  > 3. ok 다만 질문 개수를 늘리는게 목적이 되지 않을지 걱정되고 그게 하류의 결정(설계와 그 이후)을 섣불리 닫아버릴지 걱정돼, 가능하면 ask question 사용해주고

- **S10** 🗣 발화 (R2 Q4 — 재구성 v2):
  > 4. 동의

- **S11** ☑ 선택 (R3 — seed 구조의 목적):
  > 재검증 지시 (권장)

- **S12** ☑ 선택 (R3 — 워크트리 생성 시점):
  > 첫 라운드 (권장)

- **S13** ☑ 선택 (R3 — «세션에 워크트리가 고정되지는 않게»의 원뜻):
  > 철회됨 — native 선택으로 대체

- **S14** ☑ 선택 (R3 — 형제 워크트리 충돌):
  > 이번 범위 밖 — OQ 로 (권장)

- **S15** ☑ 선택 (R4 — steelman 게이트):
  > 보류 — 계수 먼저 하고 재판정 (권장)

- **S16** ☑ 선택 (R4 — 지표(나) 측정 채널 부재 후 처분):
  > 사용자 육안만

- **S17** ☑ 선택 (R4 — premortem HA6 후 워크트리 첫 라운드 생성):
  > 유지 — 반박은 기록하고 설계가 다룬다

- **S18** ☑ 선택 (R4b — «육안만»의 이유):
  > 빠른 답이었다 — 재고 가능

- **S19** ☑ 선택 (R4b — 사후 측정을 게이트 아닌 숫자로 남기는 것):
  > 받아들인다 — 측정만, 게이트 아님 (권장)

- **S20** ☑ 선택 (R5 — steelman 재게이트):
  > 부분 전환 (권장)

- **S21** ☑ 선택 (R5 — 재구성 v3):
  > 동의

- **S22** 🗣 발화 + ☑ 선택 (R5 — 추천 답안이 답을 어떻게 만드나; 자유 서술 + 복수 선택):
  > 추천도 필요하고 트레이드오프를 잘보이는곳에 제시해주는거도 필요하다, 그리고 쉽게 이해되게 전달도 필요함,짧게 만든다 — 이유를 안 쓰게 된다,유용하다 — 모를 때 기대다,추천보다 트레이드오프가 낫다

- **S23** ☑ 선택 (R6 — «쉽게 이해되게 전달»의 부족분; 복수 선택):
  > 무엇을 결정하는지가 안 보인다, 용어·내부 식별자가 많다, 기술 사실의 설명이 없다, 선택의 결과가 안 보인다

- **S24** ☑ 선택 (R6 — FM6 확정 사실 검증 층의 범위):
  > 범위 밖 — OQ 로 (권장)

- **S25** ☑ 선택 (R6 — OQ 11개 초안):
  > 그대로 박제

- **S26** 🗣 발화 (방향성 ① 추천 지연 — 첫 응답(설명 요청)):
  > 둘다 뭐야? 

- **S27** ☑ 선택 (방향성 ② 계수의 지위):
  > 계수를 방향 근거에서 떼다

- **S28** ☑ 선택 (방향성 ③ 되묻기 vs 되비추기):
  > 둘 다 후보 — 어느 쪽이 기본인지는 설계가 (권장)

- **S29** ☑ 선택 (방향성 ④ 워크트리 브랜치명·base 충돌):
  > native 유지 — 브랜치 rename 으로

- **S30** ☑ 선택 (방향성 ① 추천 지연 — 재질문 후):
  > 추천은 항상 먼저

- **S31** ☑ 선택 (방향성 ② v3 와 계수):
  > v3 유지, 계수는 brief·audit 에서 전부 제거

- **S32** ☑ 선택 (방향성 ⑤ 답 단위 판정자 = 사용자):
  > 추가하지 않는다

- **S33** ☑ 선택 (방향성 ⑥ 묶어 묻기):
  > 후보로 내린다 (권장)

- **S34** ☑ 선택 (방향성 ⑦ seed 무표시 기본값):
  > 미확인이 기본 (권장)

## 7. 확산 원자료

- «wuttke» — https://arxiv.org/abs/2410.01824 — AI Conversational Interviewing (Wuttke et al.): GPT-4 인터뷰어의 후속질문 지시 미이행 88%, 트랜스크립트 계수 AI 72 vs 인간 64 위반/인터뷰
- «llmrei» — https://arxiv.org/html/2507.02564v1 — LLMREI: 암묵 요구 <50% 도출, 유효 질문은 후반 턴
- «reqelicitgym» — https://arxiv.org/html/2602.18306 — ReqElicitGym: LLM 인터뷰어의 종료 기준 결여, 턴 예산 소진
- «cdm» — https://journals.sagepub.com/doi/10.1518/001872098779480442 — Hoffman/Crandall/Shadbolt 1998, Critical Decision Method
- «cdm-globalcognition» — https://www.globalcognition.org/cognitive-task-analysis/ — CDM 은 lock-step 이 아니라 순간에 맞는 probe 선택
- «acta» — https://www.academia.edu/1008791/Applied_Cognitive_Task_Analysis_ACTA_A_practitioners_toolkit_for_understanding_cognitive_task_demands — ACTA knowledge audit probes
- «anthropic-context-eng» — https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents — 최소 고신호 토큰 + canonical 예시, brittle hardcoded logic 이 실패 모드
- «anthropic-effective-agents» — https://www.anthropic.com/engineering/building-effective-agents — 복잡성은 결과가 입증될 때만
- «bitter-lesson-harness» — https://agent-hypervisor.ai/posts/bitter-lesson-of-agentic-coding/ — scaffolding 이득은 다음 모델 세대에 소거
- «judge-self-preference» — https://arxiv.org/abs/2410.21819 — LLM judge self-preference 는 친숙 텍스트(저-perplexity) 선호에서 온다
- «judge-survey» — https://arxiv.org/html/2411.15594v1 — LLM-as-a-Judge 서베이, 동일 모델 평가자 회피 권고
- «ainterviewer» — https://arxiv.org/html/2606.20588 — AInterviewer: 후속 충분성 판정 에이전트를 넣어도 인간 대비 유의차 없음
- «chopra-haaland» — https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4583756 — 프롬프트 한 장 GPT-4 인터뷰어의 깊이 실증
- «hamel-error-analysis» — https://hamel.dev/blog/posts/evals-faq/why-is-error-analysis-so-important-in-llm-evals-and-how-is-it-performed.html — error analysis 가 evals 의 가장 중요한 활동
- «instruction-stacking» — https://arxiv.org/html/2608.02639 — Instruction Stacking Collapse; 관련: https://arxiv.org/pdf/2605.12922 (multi-turn attention), https://arxiv.org/html/2603.23530 (prospective memory), https://arxiv.org/html/2505.19030 (RECAST)
- «saturation» — https://link.springer.com/article/10.1007/s11135-017-0574-8 — Saunders et al. 2018 saturation; https://www.tandfonline.com/doi/full/10.1080/23311886.2020.1838706 — saturation controversy
- «goodhart» — https://www.holistics.io/blog/four-types-goodharts-law/ — Goodhart 4유형; https://jellyfish.co/blog/goodharts-law-in-software-engineering-and-how-to-avoid-gaming-your-metrics/ ; https://codepulsehq.com/guides/goodharts-law-engineering-metrics
- «cc-subagents» — https://code.claude.com/docs/en/sub-agents — subagent 는 부모 대화를 보지 못하고 호출 프롬프트만 받는다
- «followup-generation» — https://arxiv.org/html/2507.02858v1 — Requirements Elicitation Follow-Up Question Generation: 실수 14종, 제약 동시 부과 시 1/30
- «laddering» — https://ixdf.org/literature/article/laddering-questions-drilling-down-deep-and-moving-sideways-in-ux-research — laddering / 5 whys
- «self-correct» — https://arxiv.org/abs/2310.01798 — LLMs cannot self-correct reasoning yet; https://arxiv.org/pdf/2510.20653 (reflection sweet spot); https://arxiv.org/pdf/2601.11578 (multi-agent limitations)
- «clarifycodebench» — https://arxiv.org/pdf/2607.00711 — LLM 은 과제가 요구하는 것보다 적게 묻는다; https://arxiv.org/abs/2510.12015 (preference elicitation); https://arxiv.org/pdf/2603.01775 (rubric-aware interview); https://arxiv.org/html/2608.01640v1 (script management)
- «anchoring-delay» — https://arxiv.org/abs/2505.15392 — LLM 앵커링: 제안을 초기 응답 뒤에 두면 영향 감소; https://www.sciencedirect.com/science/article/pii/S2451958826001600 — Q-Survey 의 지연 제안
- «clariti» — https://arxiv.org/abs/2604.14624 — 과제 관련성·답변가능성 기반 질문 선택으로 질문 41% 감소; https://arxiv.org/html/2606.03135v1 — 묻기 전에 찾기
- «wuttke-2025» — https://arxiv.org/abs/2504.13908 — 동적 probing 은 상세도↑ 대신 응답 경험↓·동의 편향↑ (n=1,800)
- «bmad-elicitation» — https://docs.bmad-method.org/explanation/advanced-elicitation/ — 사용자가 메뉴에서 고르는 심화 도구상자
- «cc-worktrees» — https://code.claude.com/docs/en/worktrees — native 워크트리: worktree-<name> 브랜치, base=origin/HEAD 기본, 훅 경로는 워크트리를 따라오지 않음
- «superpowers-brainstorming» — https://raw.githubusercontent.com/obra/superpowers/main/skills/brainstorming/SKILL.md — 한 메시지 한 질문
- «madr-status» — https://adr.github.io/madr/decisions/0008-add-status-field.html — 명시적 상태 필드
- «dod-checklist» — https://plane.so/blog/definition-of-done-dod-checklist-examples-for-agile-teams — 목록은 구조상 소진 대상이 된다


## 8. Premortem 원문 (blind-spot-prober, confidence 0.72)

- HA1 독립 판정자 거부 → 깊이: 거부는 «다시 물어라»만 만들지 «무엇을 물어라»는 못 만듦. 동계열 자기교정은 1회 후 수확체감(«self-correct»). 07-25 audit: 동계열 정적 리뷰 둘이 통과시킨 문서에서 codex 12건·게이트 실행 1건 적발.
- HA2 판정 분리가 allowlist 로 성립: subagent 는 부모 대화를 못 보고 orchestrator 가 쓴 프롬프트만 받음(«cc-subagents») — 판정자 입력을 피판정자가 작성. fork 는 같은 컨텍스트=같은 전제. 둘 다 «판정 위치 이동».
- HA3 «하류 재질문 수» 지표: 측정 채널 없음 — brainstorming 은 외부 플러그인·별 세션(finishing.md:225, orchestrator 확인). Goodhart 양방향.
- HA4 두 번째 사이클이 다른 층: 해법 넷 전부 orchestration 상태기계 층. 포화 문헌(«saturation»): «충분히 파였다»는 판정자의 주장이라 투명한 기록으로만.
- HA5 CDM/ACTA 툴박스가 해결: CDM 은 사건 회고용. 요구도출 실수 #1 = generic question(«followup-generation»). 사용 횟수가 evidence 로 적히면 체크리스트로 퇴화. (프로버 자평: 근거가 일반론이라 확신 낮음)
- HA6 Phase 0 워크트리가 무해: 브랜치명·«구현으로 갈 요청» 판정을 인터뷰 전에 → «해답=구현» 확정. 선커밋은 «턴 끝 전 커밋이 리뷰 훅을 끈다» 위. native 고정 + state main-repo → sid 갈림. framing-requests SKILL git 언급 0건(orchestrator 확인).
- FM1 거부권 루프 · FM2 override 가 default(07-26 침묵 닫힘) · FM3 지표 공백/외부 결합 · FM4 재개방 발산(SKILL «총량 바운드 이월») · FM5 툴박스 체크리스트화 · FM6 확정 사실이 틀린 채 «깊게» 파임(09-02 §9.3) · FM7 Phase 0 선커밋·워크트리가 훅·state 를 조용히 끊음.
