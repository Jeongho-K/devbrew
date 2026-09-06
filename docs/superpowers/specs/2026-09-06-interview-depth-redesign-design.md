---
name: interview-depth-redesign
type: design
created_at: 2026-09-06
source_interview: docs/superpowers/interview/2026-09-06-interview-depth-redesign-interview.md
next_phase: superpowers:writing-plans
---

# 인터뷰 깊이 재설계 — 설계

> **인터뷰어의 다음 행동은 사용자의 직전 답에서 나와야 한다.**

spec-distill 의 Phase 1 인터뷰(`conducting-interview`)는 첫 사이클(2026-07-20)이 «무엇을 열 것인가»
를 원장으로 만들었지만, 열린 차원 «안에서» 답을 파는 행동은 어떤 장치에도 걸리지 않았다. 이 설계는
그 행동을 **라운드 형식 자체**에 박고(«직전 답에서» 블록), 차원의 닫힘을 **사용자 발화**에 묶으며,
깊이를 **사후에 세 층으로 재고** 사람이 표본을 검증하게 한다. 새 판정 구조(닫힘 거부권 에이전트)는
들이지 않되, 들여야 할 조건을 숫자로 적어 둔다. Phase 0(`framing-requests`)에는 경량 절 셋만 붙는다
— seed 의 «다시 검증할 것» 문단, 첫 라운드 워크트리, handoff 직전 커밋.

## 목차

- [Goal](#goal)
- [Handoff Context](#handoff-context)
- [Context / Why](#context--why)
- [Goals](#goals)
- [Non-goals](#non-goals)
- [Constraints](#constraints)
- [1. 라운드 규약](#1-라운드-규약)
  - [1.1 라운드 기록 형식](#11-라운드-기록-형식)
  - [1.2 질문 — AskUserQuestion 한 번, 질문 둘](#12-질문--askuserquestion-한-번-질문-둘)
  - [1.3 되묻기로 바뀌는 조건](#13-되묻기로-바뀌는-조건)
  - [1.4 규칙 셋과 제거하는 것](#14-규칙-셋과-제거하는-것)
- [2. 원장 · 닫힘 · 재개방 · dispatch](#2-원장--닫힘--재개방--dispatch)
  - [2.1 닫힘 근거 — S앵커 (기계 검사)](#21-닫힘-근거--s앵커-기계-검사)
  - [2.2 재개방](#22-재개방)
  - [2.3 coverage-mapper dispatch 규칙 교체](#23-coverage-mapper-dispatch-규칙-교체)
  - [2.4 state 스키마](#24-state-스키마)
- [3. 사후 측정](#3-사후-측정)
  - [3.1 세 층](#31-세-층)
  - [3.2 시점과 흐름](#32-시점과-흐름)
  - [3.3 기록 — audit §2 와 인터뷰별 측정 파일](#33-기록--audit-2-와-인터뷰별-측정-파일)
  - [3.4 판정자를 넣는 조건](#34-판정자를-넣는-조건)
- [4. Phase 0 경량 절](#4-phase-0-경량-절)
  - [4.1 seed 의 «다시 검증할 것» 규약](#41-seed-의-다시-검증할-것-규약)
  - [4.2 워크트리](#42-워크트리)
  - [4.3 premortem 함정의 처분](#43-premortem-함정의-처분)
- [5. 컴포넌트와 격리](#5-컴포넌트와-격리)
- [Acceptance Criteria](#acceptance-criteria)
- [Files to Modify](#files-to-modify)
- [Verification Plan](#verification-plan)
- [Rejected Alternatives](#rejected-alternatives)
- [Open Questions](#open-questions)
- [Concrete Next Action](#concrete-next-action)

## Goal

`conducting-interview` 의 매 라운드가 직전 사용자 답에서 도출한 «직전 답에서» 블록으로 시작하고, 차원은
사용자 발화 앵커를 인용해야만 닫히며, 종료 시 «답 직후 파고들었는가»가 스크립트·에이전트·사람 세 층으로
audit 과 누적 원장에 기록된다 — 구조 게이트와 mutation 락으로 검증되고, 실제 인터뷰 1회로 관측된다.

## Handoff Context

> 이 spec 을 처음 보는 사람(또는 /compact 후 자기 자신)이 30초에 핵심을 잡을 수 있게. 대화 컨텍스트를
> 가정하지 않는다 — 모든 사실은 이 문서 안에 있다.

**TL;DR** — Phase 1 인터뷰가 얕게 끝나는 원인은 «인터뷰어의 다음 행동이 직전 답에서 나오지 않는다»
(brief 재구성 v3, 사용자 동의)이다. 처방은 (1) 라운드 형식에 «직전 답에서 — S<k>» 블록을 필수로 넣고
AskUserQuestion 질문 둘(되비추기 확인 + 새 결정)로 묻는 것, (2) 원장 행의 닫힘 evidence 에 사용자
발화 앵커 `S<N>` 을 요구하는 기계 검사, (3) 종료 직전 세 층 측정(스크립트 형식 · `depth-auditor`
내용 · 사람 ≤4개 라벨)과 인터뷰별 측정 파일, (4) Phase 0 의 seed «다시 검증할 것» 문단·첫 라운드 워크트리·
handoff 직전 커밋. 독립 판정자(닫힘 거부권)는 들이지 않고, 들일 조건(누적 5건 · 사람 라벨 «안
팠다» 30% · 일치 70%)만 적는다.

**표기 규약** — 이 문서에서 «brief C<n>» 은 brief §2 의 확정 항목(C1~C38)이고, 접두 없는 «C<n>» 은 이
문서의 Constraints(C1~C13)다. SKILL 내부의 C43·C51 은 «SKILL C43» 처럼 쓴다.

**Implicit context** (Constraints 에 안 박힌, 작업에 필요한 외부 사실):
- 이 브랜치(`feature/interview-depth-redesign`, 워크트리 `.claude/worktrees/interview-depth-redesign`)의
  base 는 main `5a56e4c`(spec-distill 0.53.1)이고, main 은 그 뒤 `319ed43` 에서 0.54.0 이 됐다(agent
  frontmatter 의 `model: inherit` 줄 제거). 구현 착수 전에 main 을 **merge**(rebase 아님)하고 이 PR 의
  bump 는 그 merge 시점 main 보다 한 minor 위다(C12 — 이 브랜치에서 그 값은 `0.56.0`). 새 agent 파일에는
  `model:` 줄을 넣지 않는다.
- 세션 state(`state.local.md`)는 워크트리에서도 main repo 의 `.claude/spec-distill/<session-id>/` 로
  라우팅된다(`scripts/state_path.py`, `git rev-parse --git-common-dir`). 워크트리 세션에서 그 경로는
  Write/Edit 도구가 막히므로 state 갱신은 Bash 로만 한다(현행 PN1 계약).
- state 본문은 지금 자유 산문이다(«Round 1 — 4-block 요지» 같은 요약). 측정 스크립트가 읽으려면 본문
  형식이 계약이 돼야 한다(§1.1·§3). `user_statements` frontmatter 는 이미 `S<N>` + `round` 를 갖는다.
- 구조 게이트 `check_brief.py` 는 brief 파일(payload + audit)만 읽고 state 를 읽지 않는다(불변식).
  원장은 audit §1 에 `- floor:<dim> — <status> — <evidence>` 로 직렬화되고, 지금 검사는 «closed 토큰 +
  evidence 비어있지 않음»뿐이다. §6 앵커 집합(`payload_verbatim_anchors` ∪ `verbatim_anchors(audit)`)은
  이미 게이트 안에 있다.
- seed 게이트 `check_seed.py` 는 본문의 `[open:`·`[추론:`·`[외부:` 태그와 URL 을 금지하고 frontmatter 는
  보지 않는다. `tests/test_seed_one_sentence.sh` 가 «seed 본문에 슬롯 존재 검사를 추가하지 않는다»를
  동작으로 잠근다 — 재검증 표시를 기계로 요구할 수 없다.
- Stop 훅(`hooks/review-dispatch.py`)의 리뷰 대상은 `specs/` 의 `-design.md`·`-spec.md`·`locked_decisions`
  frontmatter 문서다(`scripts/resolve_mode.py`). `docs/superpowers/interview/` 의 seed·audit 은 어느 쪽에도
  안 걸리므로 선커밋은 훅과 무관하다. 반대로 **설계문서는 리뷰가 끝나기
  전에 커밋하면 훅이 arm 하지 않는다**(`arm_ledger.is_born`).
- project-init 의 PostToolUse 훅이 브랜치 생성 명령의 이름을 `docs/git-workflow/branch-strategy.md` 의
  패턴(`feature/*` 등)으로 검증하고 위반 시 `git branch -m <prefix>/<name>` 을 제안한다.
- 모든 subagent dispatch 자리는 `**처분** — consumer=… · fail-<open|closed> · disclosure=…` 한 줄을
  가져야 하고(`shared/tests/test_dispatch_disposition.sh`), `consumer=` 가 `.py` 경로면 그 파일이
  회계 모듈(`scripts/adjudication.py`, `shared/adjudication/` 의 배포 링크)을 import 해야 한다.
- 첫 사이클 원장 실측(brief §0·✎): 인터뷰 9건 전부 닫힘 근거가 이벤트형, coverage-mapper 정체
  트리거 0회 발화, 첫 전이 dispatch 4/9 미이행, teach-beat 열린 질문 8/8 소실.
- Phase 0 은 웹을 보지 않는다(양쪽 SKILL 에 같은 문장). 이 설계는 그 경계를 바꾸지 않는다.
- `AskUserQuestion` 은 호출당 질문 ≤4, 선택지 2~4 개다. 라운드는 질문 2개, 라벨링은 질문 ≤4개(표본 수)를 쓴다.

**Deferred to plan** (이 spec 이 의도적으로 lock 하지 않은 것):
- native 워크트리 도구(`EnterWorktree`)의 브랜치명·base ref·훅/플러그인 경로 해석·종료 시 keep/remove
  프롬프트·격리 세션 git 가드가 `git branch -m` 을 허용하는지 — **plan 의 첫 task 가 격리 리포에서
  실측**하고 그 결과에 맞춰 §4.2 산문을 확정한다. 설계는 이 사실들을 단정하지 않는다.
- `depth_pairs.py` 의 발췌 길이·표본 무작위 시드·측정 파일 필드명의 세부. 계약(§3)만 고정.
- SKILL.md 의 최종 줄 수. AC 는 «순감»만 요구한다.
- **task 묶음 분리**: §4(Phase 0 — 워크트리·재검증 문단·커밋)는 §1~§3(깊이)와 독립인 하위 시스템이고 미실측
  도구 사실에 걸려 있다. plan 은 §4.2 를 별 task 묶음으로 두어 V6 실측이 막혀도 §1~§3 가 독립 출하
  가능하게 한다(같은 브랜치·같은 PR 이되 순서상 뒤, 필요하면 별 PR 로 뗄 수 있게).

## Context / Why

**두 번째 사이클이다.** 2026-07-20 사이클이 같은 증상(«더 집요하게»)을 «집요함이 고정 라운드에 묶여
있다»로 진단하고 커버리지 원장(고정 floor 5 차원 + 주제-도출 derived 차원, 전부 `closed` 여야 종료)·
teach-beat·blind-spot-prober 를 넣었다. 그때 steelman 은 «더 무겁게 말고 더 가볍게»(응답자 피로)였고
«집요함 ≠ 길이»로 방어됐다. 결과물은 전부 «무엇을 열 것인가»였고, 열린 차원 안에서 답을 파는 행동은
«probe 는 CTA 툴킷에서 모델이 적응적으로 고른다» 한 문장으로 재량에 남았다.

**이번 인터뷰가 확인한 것** (brief `docs/superpowers/interview/2026-09-06-interview-depth-redesign-interview.md`):
첫 사이클 이후 인터뷰 9건의 원장을 전수로 읽었다. 닫힘 근거는 9/9 «steelman 1회·sweep n회» 식 이벤트
완료형이고 «무엇을 알게 되어 더 물을 것이 없다»는 내용 판단은 0건. coverage-mapper 의 «연속 3 probe
무진전» 트리거는 «진전 = evidence append» 정의 탓에 한 번도 발화하지 않았고, «첫 전이마다 dispatch»
규칙은 4/9 미이행. 사용자 증상은 «질문이 안 떠올라 끝난다»(S3). 08-22 기록에서 추천안을 두 번 연속
수락한 직후 사용자가 «나 아직 뭐를 한다는지 명확히 이해가 안가»라고 말했다.

**진짜 문제(재구성 v3, 사용자 동의 brief C13)** — 인터뷰어의 다음 행동이 사용자의 직전 답에서 나오지 않는다.
답은 기록 대상이지 파고들 대상이 아니라서 «닫아도 되는가»를 판정할 재료가 생기지 않는다. 귀속은
설계(모든 닫힘·dispatch·종료를 끝내고 싶은 턴의 재량에 둠)·미이행·미측정 셋이 맞물린 것이다.

**사용자가 이미 확정한 것(brief §2, 38항목)** 중 이 설계가 직접 받는 것: 파고드는 수단은 되묻기·
되비추기 둘 다 후보이고 기본값은 설계가 정한다(brief C23); 구조 추가는 정당화 필요한 후보(brief C10); 추천은 항상
먼저(brief C21); 묶어 묻기는 후보(brief C24); 답 단위 사용자 판정자는 채택 안 함(brief C25); 사후 측정은
게이트가 아닌 숫자(brief C11), 모델 계수는 사람 검증 전엔 근거 아님(brief C22); 쉽게 이해되게 — 무엇을
정하는지·용어·기술 사실·선택의 결과(brief C15); 질문은 AskUserQuestion(brief C5); seed 무표시=미확인
(brief C6)·재검증 지시(brief C29); Phase 0 첫 라운드 native 워크트리 + rename(brief C7·C8·C12); 한 브랜치
관통 + 자료 선커밋(brief C26); 형식·원장만 무거워지는 해법 금지(brief C20); 확정 사실 반증 층과 형제
워크트리 충돌은 범위 밖(brief C16·C9).

**brainstorming 에서 사용자가 추가로 정한 것(2026-09-06)**: 라운드 모양 = 되비추기 기본 + 새 질문 1개
(AskUserQuestion 질문 둘); 사람 검증 = 인터뷰당 4개 안팎 라벨; 접근 = 규약 + 측정 지금, 독립 판정자는
조건부; 다섯 설계 섹션 전부 «이대로».

## Goals

- **G1 — 파고들기가 라운드 형식에 산다.** 매 라운드는 직전 답마다 «직전 답에서 — S<k>» 블록(함의·상충·
  확인한 사실·위험)으로 시작하고, AskUserQuestion 의 Q1 이 그 되비추기의 확인이다. 블록 자체가 없는 라운드는
  성립하지 않는다. 네 줄이 전부 «없음»인 블록은 허용되되 그 라운드의 Q1 은 반드시 되묻기(§1.3)다 — «못
  끌어냈다»는 기록으로 남고 §3 이 그것을 센다.
- **G2 — 차원은 사용자 발화로만 닫힌다.** 원장 행의 닫힘 evidence 는 실재하는 `S<N>` 앵커를 최소 하나
  담아야 한다(게이트). 이벤트 횟수는 닫힘 근거가 아니다.
- **G3 — 깊이가 사후에 재진다.** 종료 시 «답→다음 행동» 짝을 스크립트가 뽑고, `depth-auditor` 가 내용을
  라벨하고, 사람이 ≤4개에 라벨해, 세 층이 audit §2 와 인터뷰별 측정 파일에 남는다. 게이트 아님.
- **G4 — 판정자 투입 조건이 기록된다.** 측정 파일 전체(`depth/*.json`)를 읽는 스크립트가 조건 도달 여부를 audit 에 한 줄로
  낸다. 막지 않는다.
- **G5 — 쉽게 이해되게.** 질문 본문이 무엇을 정하는지·용어·기술 사실을 풀고, 각 선택지 description 이
  «고르면 무엇이 달라지는가»를 담는다.
- **G6 — Phase 0 경량 셋.** seed 마지막 문단 «다시 검증할 것 —», 첫 라운드 워크트리(승낙 후) + `feature/
  <topic>` rename, proceed 게이트 ①/② 에서 handoff 직전 커밋.
- **G7 — 순감.** SKILL.md 는 teach-beat·정체 트리거·경로 (c) 를 잃고 줄 수가 준다. 새로 늘어나는 산문은
  라운드 형식·닫힘 규칙·재개방·측정 단계뿐이다.

## Non-goals

- **NG1**: 질문 수·라운드 수를 늘리는 것 자체. 상한을 복원하는 것도 아니다(사용자가 시계).
- **NG2**: 독립 판정 에이전트의 닫힘 거부권. 이번엔 조건만 적는다(§3.4).
- **NG3**: probe 목록형 도구상자(CDM/ACTA 식 6~8 항목). 되묻기 세 축 한 줄이 전부다.
- **NG4**: 인터뷰가 설계·계획·구현 결정을 미리 닫는 것. 접근법 비교는 brainstorming 몫(brief C17).
- **NG5**: 인터뷰가 확정한 사실이 나중에 코드로 반증되는 층(brief C16). 형제 워크트리 충돌 처분(brief C9).
- **NG6**: 하류(brainstorming)가 brief 를 읽고 다시 물은 횟수의 측정 채널(OQ2 유지).
- **NG7**: seed 게이트·원문 완전성 검사·reviewing-brief·reviewing-spec·훅 둘·steelman-builder·
  blind-spot-prober 본문의 변경. Phase 0 의 «웹 안 봄» 경계의 변경.
- **NG8**: 측정값의 게이트화. 어떤 층의 숫자도 brief 완결이나 proceed 를 막지 않는다.

## Constraints

- **C1 (되비추기 기본)**: 매 라운드 Q1 은 «직전 답에서» 블록의 확인이다. 되묻기(이유·사례·실패 조건)는
  §1.3 의 조건에서만 Q1 을 대체하고, 그때도 인터뷰어의 추측이 첫 선택지다(brief C21 추천 먼저).
- **C2 (닫힘 = S앵커)**: audit §1 의 닫힌 행(floor 전부, derived 전부, 사용자-승인 박제 포함)의 evidence
  는 `S\d+` 앵커를 최소 하나 담고 그 앵커는 payload §6 ∪ audit §6 에 실재해야 한다. 형식 검사만 —
  «그 S 가 닫힘을 정당화하는가»는 모델·사람 몫이고 게이트는 그 한계를 숨기지 않는다.
- **C3 (재개방 무상한)**: `closed → open` 을 허용하되 상한을 두지 않는다. 재개방은 그 라운드의 «직전
  답에서» 블록 «상충» 줄에 «→ <차원> 재개방»으로 보여야 하고, 원장 행에 사유가 쌓인다.
- **C4 (coverage-mapper 상한 2)**: 첫 라운드 첫 질문 전 필수 1회 + 재개방 시 최대 1회. 정체 트리거와
  그 state 필드 셋은 제거. 종료 시 audit §2 의 `coverage-mapper <k>` 가 k≥1 이어야 게이트 통과 —
  단 `coverage-mapper 0 (unavailable: <이유>)` 는 advisory 로 통과(에이전트 dispatch 불가 환경).
- **C5 (측정은 게이트 아님)**: `depth_pairs.py`·`depth-auditor`·사람 라벨·`depth_record.py` 의 어떤
  결과도 exit 코드로 종료를 막지 않는다. 실패는 «측정 불가/unavailable/미라벨»로 **기록**된다.
- **C6 (state 본문 형식 계약)**: 라운드 기록은 §1.1 의 헤딩·소제목 형식으로 state 본문에 남는다.
  `depth_pairs.py` 는 `## R<n>` 헤딩을 못 찾으면 0 이 아니라 «측정 불가»를 낸다.
- **C7 (사람 라벨 ≤4개)**: 종료 시 AskUserQuestion 1회, 질문 `min(4, 적격 짝 수)` 개(4 는 호출 상한),
  선택지 «파고들었다 / 안 팠다 / 판단불가». 건너뛰면 «미라벨», 적격 짝 0 이면 «표본 없음». 사용자 시간 2~3분.
- **C8 (Law 2 격리)**: `depth-auditor` 는 `tools: []`, 짝 목록을 inline 으로 받는다(brief-critic 과 같은
  모양). `model:` 줄 없음(main 0.54.0 규약). dispatch 자리에 처분 한 줄: `consumer=plugins/spec-distill/
  scripts/depth_record.py · fail-open` — 그 스크립트가 `adjudication.py` 를 import 해 파손 항목을
  held 로 센다.
- **C9 (Phase 0 산문 규약, 기계 검사 없음)**: seed 확정 표시는 «(사용자 확인)» 하나, 마지막 문단은
  «다시 검증할 것 —»로 시작, 그 밖은 미확인. `check_seed.py` 는 손대지 않는다.
- **C10 (워크트리는 승낙 후, 확산 1번 «전»)**: framing-requests 진입 직후·audit 첫 write **전**에
  AskUserQuestion 하나로 «`feature/<kebab-topic>` 워크트리를 만들고 거기서 시작할까요? (권장)» 를 묻는다
  (첫 라운드의 첫 행동 — brief C7). 거절·도구 부재·`DEVBREW_SPEC_DISTILL_DISABLE_WORKTREE=1` 이면 현재
  디렉토리에서 진행하고 audit §5 에 이유를 남긴다. 커밋은 proceed 게이트 ①/② 선택 뒤 handoff 직전 1회
  (`docs(interview): <topic> interview seed + audit`).
- **C11 (도구 사실 미단정)**: §4.2 의 native 도구 동작은 이 spec 이 단정하지 않는다. plan 첫 task 가 실측하고
  그 결과는 plan 산출물·CHANGELOG 에 남으며 framing-requests 산문이 그것을 따른다. spec 에 사후 절을 더하지
  않는다.
- **C12 (버전·CHANGELOG)**: 착수 전 `origin/main` 을 **merge**(rebase 아님)하고, `plugin.json` 을 **가장 최근
  merge 시점**의 main 보다 **한 minor 위**로 올린다(minor 인 이유: 새 surface — 스크립트 둘·에이전트 하나·
  측정 단계). 「가장 최근」이 필수다 — 이 브랜치는 merge 커밋이 둘이고 착수 전 그것으로 재면 틀린 수가 나온다.
  CHANGELOG 최상단 헤딩이 `plugin.json` 과 **같은 값**이어야 한다. README «Principles Instantiated» 갱신.
  **이 브랜치에서 그 값은 `0.56.0` 이다.** 착수 시 계획했던 minor 번호는 작업 도중 upstream 이 다른
  릴리스로 선점했다(원장 R22·R23) — 그래서 이 제약은 그때의 리터럴이 아니라 «한 minor 위 + 최상단 일치»
  라는 불변식을 잰다. 하류 AC·V 항목이 «CHANGELOG 최상단 절» 이라고만 쓰는 것도 같은 이유다.
- **C13 (락은 블록 스코프 + mutation)**: 산문 락은 헤더가 아니라 본문 고유 문구를 블록 스코프로 잡고,
  통째 삭제·부정문·값 변경 mutation 으로 이빨을 확인한다. 제거 어휘는 stale-term 락에 등재.

## 1. 라운드 규약

### 1.1 라운드 기록 형식

현행 4-block(현재 이해 / 막힌 결정 / 추천 답안 / 질문)을 아래로 대체한다. 사용자에게 보이는 출력과
state 본문 기록이 **같은 형식**이다 — 측정 스크립트가 state 본문을 읽기 때문이다.

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
<AskUserQuestion 결과 — user_statements 에 S<m>[, S<m+1>] 로 append 된 것의 id>
```

- `## R<n>` 은 1부터 순증. 직전 라운드가 발화를 둘 만들었으면(Q1·Q2) **`### 직전 답에서 — S<k>` 블록을
  발화마다 하나씩** 둔다 — 한 블록에 두 S 를 섞으면 어느 답에서 무엇이 나왔는지가 사라지고 §3 의 짝이
  성립하지 않는다. 각 블록의 네 줄은 **그 S 에서** 따라 나오는 것만 적는다(다른 답이나 무관한 정보는 «없음»).
- **S1 이 seed(최초 요청, `round: 0`)이면 R1 은 S1 을 되비춘다** — seed 의 «다시 검증할 것» 문단 항목이 R1 의
  함의·상충·위험 줄을 채운다. **인자 없이 `/interview` 를 부른 경로**(S1 이 없고 첫 사용자 답이 S1 이 되는
  현행 호환 경로)에서는 R1 이 «직전 답에서» 블록 없이 «지금 이해 + 다음 결정 + Q2(새 결정 하나)» 만으로
  성립하고, 규약은 R2 부터 적용된다. coverage-mapper 첫 dispatch 도 그 경로에서는 R1 답을 받은 뒤 R2 전에
  일어난다. `depth_pairs.py` 는 `round: 0` 인 S1 만 R1 과 짝짓는다.
- 네 줄 중 하나라도 «없음»이 아니어야 «형식 층에서 성립»(§3.1)이다. 넷 다 «없음»이면 그 라운드는
  «S<k> 에서 아무것도 못 끌어냈다»는 기록이 되고 — 그것이 «안 떠올라 끝난다»의 관측 가능한 모양이다 —
  **그 라운드의 Q1 은 되묻기여야 한다**(§1.3). 블록을 아예 쓰지 않는 것만이 라운드 불성립이다. 이행
  규칙은 이 한 문장이고 G1·§3.1 은 이것을 가리킨다.
- «상충» 줄이 외부 근거(landscape·steelman·premortem 출력)를 싣는다. 현행 teach-beat 의 역할이 여기로
  흡수된다 — 열린 질문으로 흘려보내지 않고 «맞나?»로 사용자 처분을 받는다.
- routing 표(경로 a/b/d)와 rhythm guard 는 유지하되, 경로 (a)(코드·문서에서 찾을 수 있는 것)는 «확인한
  사실» 줄로 들어간다 — 묻기 전에 찾을 수 있는 것을 먼저 찾는다는 brief §4 «clariti» 근거.

### 1.2 질문 — AskUserQuestion 한 번, 질문 둘

```javascript
AskUserQuestion({
  questions: [
    { header: "직전 답",  question: "<S<k> 에서 끌어낸 것을 한 절로 — 용어와 기술 사실을 풀어서>. 맞나요?",
      options: [
        {label: "맞다",           description: "이대로 <차원> 을 진행/닫는다 — <고르면 달라지는 것>"},
        {label: "모르겠다",       description: "판단불가로 기록하고 Open Question 후보로 둔다"}],
      // 틀린 부분은 사용자가 «기타»(자유 입력)에 적는다 — 그 텍스트가 verbatim S 가 되고 다음 라운드 Q1 이 그것을 되비춘다.
      multiSelect: false },
    { header: "<결정 이름>", question: "<무엇을 정하는지 한 줄> · <용어 풀이> · <관련 기술 사실> · 추천은 첫 선택지",
      options: [
        {label: "<추천> (권장)",  description: "고르면 <결과>"},
        {label: "<대안 1>",       description: "고르면 <결과>"},
        {label: "<대안 2>",       description: "고르면 <결과>"}],
      multiSelect: false }
  ]
})
```

- Q1 이 항상 먼저다. Q2 는 새 결정 하나 — 지금의 «막힌 결정 + 추천 답안»이 옮겨온 자리다.
- Q1 의 선택지는 둘뿐이다(«맞다» / «모르겠다»). 틀린 부분은 사용자가 «기타» 자유 입력에 적는다 — 선택지
  하나를 고르면서 동시에 자유 입력을 남기는 동작은 도구에 없으므로 «일부 틀리다» 선택지를 두지 않는다.
  «기타» 텍스트는 `verbatim` S 로 기록되고 규칙 3(§1.4)의 입력이 된다.
- **Q2 는 Q1 의 확인과 독립이어야 한다.** Q2 의 결정이 Q1 이 되비춘 해석에 기대면 그 라운드는 Q1 만 낸다.
  독립인데도 사용자가 Q1 에 «모르겠다»·«기타(수정)» 로 답했으면 Q2 의 답은 state 에 `provisional_on: S<k>`
  표시를 달고, 그 표시가 해소(다음 라운드 되비추기 «맞다»)되기 전에는 어느 차원의 닫힘 근거로도 쓰지 않는다.
- 각 선택지의 `description` 은 «고르면 무엇이 달라지는가»를 담는다. question 본문은 무엇을 정하는지·
  용어·기술 사실을 푼다. 이것이 brief C15 의 넷을 집행하는 유일한 자리이고 기계 검사는 없다(사람 e2e 로 본다).
- 두 답은 `user_statements` 에 각각 `S<m>`·`S<m+1>` 로 append 된다(`source: chosen`, «기타» 입력은
  `verbatim`). 라운드 번호 공식은 현행과 같다.

### 1.3 되묻기로 바뀌는 조건

되비추기가 **성립하지 않는 답**에서 Q1 은 되묻기가 된다. 성립하지 않는 답의 열거(휴리스틱, 기계화 안 함):
보류(«모르겠다/둘 다/아무거나»), 한 단어 답, 추천안 즉시 동의(이유 없이 «추천»), 근거 없는 단정.
이때 Q1 의 본문은 이유·사례·실패 조건 중 **하나**를 묻고, 인터뷰어의 추측을 첫 선택지로 둔다:

```
Q1 (되묻기): «<S<k>>»라고 답하셨는데, 왜 그렇게 봤는지가 <차원> 을 닫는 데 필요합니다.
  - «내 추측: <이유 A>» (권장)  — 고르면 <결과>
  - «<이유 B>»                 — 고르면 <결과>
  - «잘 모르겠다»              — 판단불가로 기록, OQ 후보
```

되묻기의 세 축(이유·사례·실패 조건)이 brief C4 가 허용한 도구상자의 전부다. 목록을 더 두지 않는다(NG3).

### 1.4 규칙 셋과 제거하는 것

규칙(산문, 기계 검사 없음 — §3 의 측정이 이행을 재는 대상):
1. Q1 은 생략할 수 없다. R1 도 S1 을 되비춘다.
2. 차원은 «그 차원의 되비추기에 사용자가 답한 S» 뒤에만 닫는다. sweep·steelman·prober 의 **횟수**는
   닫힘 근거가 아니다 — 그 출력은 «상충/위험» 줄로 돌아와 사용자 처분 S 를 받은 뒤 닫힌다.
3. Q1 에 «기타»(수정)가 오면 다음 라운드 Q1 이 그 수정 텍스트(새 S)를 다시 되비춘다. 같은 주제에 대해
   최대 2회 — 3회째는 §3 Open Questions 로 박제하고 넘어간다.

제거(순감):
- teach-beat 절 전체(teach-lite/heavy 어휘, 열거 신호 4종, 크기 한도). «상충» 줄이 역할을 흡수.
- SKILL C43 경로 (c) «ambiguity → general-purpose adversarial draft»(사용 기록 0, 되비추기와 같은 자리).
- 4-block 절, SKILL C51 5-type 라벨 요구(경로 (d) 는 남기되 라벨 강제는 제거).
- coverage-mapper 정체 트리거 절과 «바운드가 묶는 것은 밀도이지 총량이 아니다» 문단(§2.3).

## 2. 원장 · 닫힘 · 재개방 · dispatch

### 2.1 닫힘 근거 — S앵커 (기계 검사)

`check_brief.py` 에 검사 하나를 더한다: audit §1 의 **닫힌 행마다** evidence 세그먼트에 `S\d+` 앵커가
최소 하나 있고, 그 앵커가 payload §6 ∪ audit §6 의 앵커 집합에 실재한다. 적용 행: floor 5 전부,
derived 전부(`derived: N/A` sentinel 제외), 사용자-승인 박제 행도 포함(종료 요청 발화가 S 다).

- 검사는 `coverage_ledger_failures` 와 별도 함수 `coverage_anchor_failures(audit_text, anchors)` 로 두고
  `gate` 가 둘 다 부른다 — 기존 form 검사의 실패 메시지를 바꾸지 않기 위해서다.
- 앵커 정규식은 `(?<![A-Za-z])S\d+\b` — 단어 경계 없이 `S\d+` 를 쓰면 `OQS3`·`STS1` 같은 우연 토큰을 앵커로
  센다.
- 사용자-승인 박제 행은 `finishing.md` 가 «`사용자-승인 박제` 로 시작»을 전제로 §3 이월을 판정하므로, 앵커는
  접두 **뒤**에 온다: `사용자-승인 박제(@S12) — §Open Questions 참조`. 두 검사가 같은 행을 읽는다.
- 실패 메시지: `floor:<dim> evidence cites no S<N> anchor` / `floor:<dim> evidence anchor S7 not found in §6`.
- 다섯 floor 의 닫힘 발화가 무엇인지(규약): root_problem = 재구성 동의 S · landscape = 외부 근거 되비추기
  처분 S · skepticism = steelman 판정 S · blind_spot = 숨은 가정·실패 양식 처분 S · open_questions = OQ
  목록 확인 S. 산문으로 SKILL 에 적고, 게이트는 «S 가 있는가»만 본다.

이 검사가 잡는 것: 첫 사이클 원장 9건의 «steelman 1회·blind-spot 1회·web sweep n회» 식 근거 전부.
**잡지 못하는 것: 아무 S 나 인용해 닫는 것.** 이 판본에는 그것을 보는 자리가 **없다** — §3 의 측정은 «답→다음
행동» 짝만 받고 원장·닫힘 근거를 받지 않으며, brief 분리 리뷰의 충실도 critic 은 payload 와 audit §6 만
받고 audit §1 을 받지 않는다(NG7 — reviewing-brief 무변경). 알려진 갭으로 OQ6 에 둔다: 다음 사이클의 후보는
번들에 audit §1 을 넣어 critic 이 «인용된 S 가 그 차원을 닫을 만한 발화인가»를 보게 하는 것이다.

### 2.2 재개방

- 상태 전이에 `closed → open` 을 더한다(현행은 open → in-progress → closed 편도).
- 조건(산문): 새 답·외부 근거·코드 사실이 그 차원의 닫힘 근거 S 와 **충돌**할 때(brief C34). 판단은 orchestrator.
- 기록: state 의 해당 차원에 `reopened: <n>` 증가 + `reopen_log` 에 `{round, reason, conflicts_with: S<N>}`
  append. 그 라운드의 «상충» 줄에 «→ <차원> 재개방: <사유>». 종료 시 audit §1 행 끝에
  `(재개방 <n>회 — <마지막 사유>)`.
- 상한 없음(C3). 근거: 재개방은 라운드 안에서만 일어나고 라운드는 사용자 답으로만 돈다 — 사용자가
  시계다(현행 SKILL 의 «나가는 문은 floor 뒤에만 있지 않다» 절과 같은 논리). 거부권을 들이지 않으므로
  brief OQ6 의 «거부권 + 재개방 루프»는 생기지 않는다.
- 재개방된 차원은 다시 닫힐 때 **새 S** 를 인용해야 한다(C2 는 최신 닫힘의 evidence 를 본다).

### 2.3 coverage-mapper dispatch 규칙 교체

현행 두 트리거(«연속 3 probe 무진전» — 0회 발화 / «floor 첫 open→in-progress 전이마다» — 4/9 미이행)를
버리고 둘로 바꾼다:

1. **R1 첫 질문 전 필수 1회.** 입력: seed 전문(S1)과 그 «다시 검증할 것» 문단, 원장 초기 상태. 출력의
   derived 차원을 orchestrator 가 admit 한 뒤에야 R1 질문이 나간다. 이것이 «seed 에서 주제 차원을
   처음에 뽑을 의무가 없다»(brief 원인 후보)에 대한 답이다.
2. **재개방 시 최대 1회.** 재개방이 새 파생 차원을 함의할 수 있어서다. 두 번째 재개방부터는 dispatch 안 함.

상한 2, 카운터 `orchestration.coverage_mapper_dispatches` (state). 종료 시 audit §2 Budget 의 dispatch
줄에 `coverage-mapper <k>` 를 쓰고 게이트가 k≥1 을 검사한다(C4). dispatch 가 불가능한 환경(Agent 도구
부재)은 `coverage-mapper 0 (unavailable: <이유>)` 로 적어 advisory 통과 — 침묵과 0 을 구분한다.
**이 검사가 잡지 못하는 것**: 그 sentinel 은 피검자(orchestrator)가 쓰는 문구라, dispatch 를 건너뛴 턴이
같은 문구를 적으면 게이트는 «도구 부재»와 구분하지 못한다. 그래서 sentinel 은 조용히 통과하지 않고
 advisory 로 Step B proceed 게이트 텍스트에 실려 **사람이 본다** — 게이트가 관측할 수 있는 것은 «k≥1 을
적었는가»까지이고, 실제 dispatch 여부는 audit §5 프로세스 로그와 사용자의 눈이 잰다.

steelman-builder 와 blind-spot-prober 의 dispatch 규칙은 그대로다. 바뀌는 것은 소비: 출력이 «상충/
위험» 줄로 되비추어지고 사용자 처분 S 가 skepticism·blind_spot 의 닫힘 근거가 된다.

### 2.4 state 스키마

```yaml
coverage:
  floor:
    root_problem:   {status: open, evidence: "", reopened: 0, reopen_log: []}
    # landscape · skepticism · blind_spot · open_questions 동일
  derived: []   # {name, rationale, status, evidence, reopened, reopen_log}
orchestration:
  focused_dimension: null
  blind_spot_dispatched: false
  coverage_mapper_dispatches: 0      # 상한 2 (§2.3)
# 제거: no_progress_streak · stall_episode · coverage_mapper_dispatched_episode
```

구세션 마이그레이션은 현행 «non-mutating read promote + resume 직후 1회 full-write» 패턴 그대로 —
부재 키는 기본값으로 추가, 제거된 키는 그 write 에서 자연 소멸, 다른 필드는 손대지 않는다.
advisory 문구의 버전을 이 릴리스의 값(C12)으로.

## 3. 사후 측정

### 3.1 세 층

| 층 | 무엇을 세나 | 누가 | 신뢰 |
|---|---|---|---|
| 형식 | `user_statements` 의 각 S<k>(round r)에 대해 `## R<r+1>` 의 `### 직전 답에서 — …S<k>…` 블록이 있는가; 네 줄 중 «없음» 아닌 줄이 ≥1 인가 | `scripts/depth_pairs.py` | 결정론. «없음»만 아니면 통과하므로 하한 |
| 내용 | 그 블록이 **S<k> 에서 따라 나오는** 함의·상충·사실·위험 중 S<k> 에 없던 것을 하나라도 적었는가(무관한 내용·다른 답에서 나온 내용은 안 센다) → {파고들었다 / 안 팠다 / 판단불가} + 한 줄 이유 | `agents/depth-auditor.md` (`tools: []`, 짝 목록 inline) | 같은 계열 모델 — 단독으론 근거 아님(C22) |
| 사람 | 스크립트가 뽑은 `min(4, 적격 짝 수)` 개 짝에 같은 세 라벨 | 사용자, AskUserQuestion 1회 | 이것만 근거. 인터뷰가 쌓여야 결론 |

짝(pair)의 정의: `(S<k>, R<r+1> 의 «직전 답에서 — S<k>» 블록 텍스트 | None)` — 블록이 S 마다 하나이므로 짝도
S 마다 하나다. 마지막 라운드의 답은 다음 라운드가 없으므로 짝에서 제외하고 `terminal` 로 센다. `round: 0`
인 S1(seed)은 R1 과 짝을 이룬다. **적격 짝** = terminal 이 아니고 사용자 텍스트가 비어 있지 않은 짝.
표본은 적격 짝에서 비복원 무작위(시드 = session_id)로 `min(4, 적격 짝 수)` 개 — 적격 짝이 0 이면 사람 층은
«표본 없음»으로 기록하고 라벨 질문을 띄우지 않는다. 라벨 질문 수·audit §2·측정 파일·조건 B 의 분모는 전부
**실제 표본 수**를 쓴다(«4» 는 상한이지 상수가 아니다).

«새 정보를 얻었는가»(brief OQ11 둘째 질문)는 별도 계수를 만들지 않고 «파고들었다» 라벨의 정의에 흡수한다
— 행동 횟수가 아니라 **S<k> 에서 따라 나오되 S<k> 에 없던 내용의 유무**를 세므로 «evidence append = 진전»의
재현이 아니다. «따라 나온다»(관련성)를 정의에 넣는 이유: 그것이 없으면 무관한 정보를 적은 블록도
«파고들었다»가 된다. auditor 는 라벨마다 «S<k> 의 어느 부분에서 따라 나왔는가»를 이유 줄에 적어야 한다.

### 3.2 시점과 흐름

`finishing.md` 에 **Step A.7 «깊이 측정»** 을 더한다 — Step A.5(분리 리뷰) 뒤, Step B(proceed 게이트)
직전. 흐름:

```bash
PAIRS="$ROOT/$harness_sid/depth-pairs.json"
python3 "$PR/scripts/depth_pairs.py" "$STATE" --sample 4 > "$PAIRS"; pairs_rc=$?
# rc 0: 짝 목록 + 표본 min(4, 적격) (session_id 시드 무작위, 비복원) · rc 3: «측정 불가»(R 헤딩 부재·state 판독 불가)
```

- `pairs_rc == 3` 이면 auditor 도 사람 라벨도 돌리지 않고 audit §2 에 «깊이 측정: 측정 불가 — <이유>».
- auditor dispatch(아래) → raw 출력을 `depth-auditor-raw.txt` 로 저장(요약·전사 금지).
- 사람 라벨: `AskUserQuestion` 질문 = 표본 수(≤4). 각 question 본문 = S<k> 발췌(≤200자) + 블록 발췌(≤300자).
  선택지: «파고들었다 / 안 팠다 / 판단불가». 「기타」에 «나중에» 류가 오면 «미라벨». 표본 0 이면 호출 안 함.
- auditor raw 는 heredoc 이 아니라 **파일 리다이렉트**로 저장한다(raw 에 `'`·`)` 가 섞이면 heredoc-in-`$()`
  파싱이 깨진 전례) — 경로는 plan 이 고정한다.
- `python3 depth_record.py "$PAIRS" --auditor depth-auditor-raw.txt --human '<json>' --audit "$AUDIT"
  --out docs/superpowers/interview/depth/<brief-basename>.json` → audit §2 세 줄을 stdout 으로 내고
  (orchestrator 가 삽입), 인터뷰별 측정 파일 하나를 쓰고, 조건 판정 한 줄(§3.4)을 낸다. 어떤 실패도 exit 0 +
  «기록 불가: <이유>» 로 표면화(C5).

```javascript
Agent({
  description: "Depth audit of answer→next-action pairs",
  subagent_type: "spec-distill:depth-auditor",
  // **처분** — consumer=plugins/spec-distill/scripts/depth_record.py · fail-open
  prompt: `아래 짝마다 «직전 답에서» 블록이 S 에 없던 함의·상충·사실·위험을 하나라도 적었는지 판정하라.
라벨은 dug | not_dug | undecidable, 각각 한 줄 이유. 짝 목록 밖의 것은 보지 마라.
<pairs>${PAIRS_INLINE}</pairs>` })
```

auditor 출력 계약: `depth-audit` 센티널 YAML 블록 `{pairs: [{s: S<k>, label, reason}]}`. 블록 부재·파손·
빈 출력은 «unavailable»(있는 판정과 없는 판정을 구분). 항목 단위 파손은 `adjudication.py` 의 `Ledger`
로 held 계수.

### 3.3 기록 — audit §2 와 인터뷰별 측정 파일

audit §2 Budget 에 세 줄이 추가된다(템플릿 갱신):

```
- 깊이 측정(형식): 짝 <n> 중 되비추기 블록 있음 <m> · 내용 있는 줄 ≥1 <p> · terminal <t>
- 깊이 측정(auditor): dug <a> · not_dug <b> · undecidable <c> · held <h> · unavailable <0|1>
- 깊이 측정(사람): 표본 <s> — dug <x> · not_dug <y> · undecidable <z> · 미라벨 <w> · auditor 일치 <k>/<v> (v = 양쪽 라벨이 dug|not_dug 인 짝 수; auditor 판정 없는 표본 <u> 별도)
```

**인터뷰별 측정 파일** `docs/superpowers/interview/depth/<brief-basename>.json` 하나(누적 원장을 한 파일의
EOF append 로 두면 브랜치마다 같은 줄에서 병합 충돌이 나고 조건 판정이 브랜치 로컬 부분 원장으로 계산된다):

```json
{"date":"2026-09-06","brief":"docs/superpowers/interview/<file>.md","session_id":"<sid>",
 "pairs":{"total":n,"eligible":e,"with_block":m,"substantive_form":p,"terminal":t},
 "auditor":{"dug":a,"not_dug":b,"undecidable":c,"held":h,"unavailable":false},
 "human":{"sampled":s,"dug":x,"not_dug":y,"undecidable":z,"unlabeled":w,
          "auditor_missing":u,"agreement":[k,v]}}
```

일치율은 **양쪽 라벨이 모두 dug|not_dug 인 짝**(v)에서만 계산한다 — auditor 가 unavailable·held 이거나 어느
쪽이 undecidable 인 짝은 분모에서 빼고 `auditor_missing` 으로 따로 센다. 분모 0 은 «자료 부족»으로 기록한다.
디렉토리는 이 PR 에서 만들고(`.gitkeep`), 아카이브로 옮기지 않는다(인터뷰 문서는 `docs/archive/interview/`
로 가도 측정 파일은 남는다 — Law 3 «다음 세션이 실제로 찾는 자리»). 집계는 `depth/*.json` glob.

### 3.4 판정자를 넣는 조건

`depth_record.py` 가 `depth/*.json` 전체를 읽어 아래를 한 줄로 낸다(audit §2 넷째 줄). **적격 인터뷰** =
사람 라벨 중 dug|not_dug 가 1개 이상인 인터뷰(전부 undecidable·미라벨·표본 없음이면 5건 계수에 안 든다):

- **조건 A(판정자)**: 적격 인터뷰 **5건 이상** 누적에서, 사람 라벨의 `not_dug` 비율(분모 = dug + not_dug 합)이
  **30% 이상** → «판정자 투입 조건 도달 — 다음 사이클이 닫힘 거부권 에이전트를 설계한다».
- **조건 B(auditor 신뢰)**: 같은 누적에서 auditor 일치율(k 합 / v 합)이 **70% 미만** → «auditor 계수는
  근거에서 제외 — 사람 표본을 늘린다». v 합이 0 이면 «자료 부족».
- 어느 쪽도 아니면 «조건 미도달 (<적격 건수>/5)».

두 숫자는 출발값이다. 참고 기준선은 Wuttke 의 «후속 질문 미이행이 위반의 88%»뿐이라 근거가 얇고, 첫 5건이
쌓이면 이 spec 의 후속 사이클이 재조정한다(OQ4). 조건 판정은 기록일 뿐 아무것도 막지 않는다(C5 · brief C11).

## 4. Phase 0 경량 절

### 4.1 seed 의 «다시 검증할 것» 규약

태그를 쓰지 않는다(`check_seed.py` 가 본문 태그를 금지하고, 슬롯 존재 검사 추가는 테스트가 막는다).
산문 규약 셋:

- **확정 표시는 «(사용자 확인)» 하나.** 이 표시가 붙은 문장만 Phase 1 이 다시 묻지 않는다(brief C36). brief §2 로
  옮길 때 `source: verbatim`, ✎ 에 «Phase 0 확인».
- **마지막 문단은 «다시 검증할 것 —»로 시작**해 Phase 0 이 추론·외부·열린 것으로 아는 항목을 산문으로
  나열한다. 예: «다시 검증할 것 — 종료 술어가 이벤트 완료라는 것은 Phase 0 이 구현을 읽고 본 원인
  후보이지 확정이 아니다. …».
- **그 밖의 모든 문장은 미확인**(brief C6). Phase 1 이 필요하면 되비추기로 검증한다.

Phase 1 쪽 소비: R1 의 «직전 답에서 — S1» 블록과 coverage-mapper 첫 dispatch 입력이 «다시 검증할 것»
문단이다. 규약 위반 seed(문단 없음)는 지금과 같은 태그 없는 산문으로 떨어질 뿐 깨지지 않는다 —
seed-readback(냉독)이 그 부재를 사람에게 보인다. `templates/interview-seed-template.md` 의 예시와
`references/compression.md` 에 문단 규약을 적는다.

### 4.2 워크트리

framing-requests 는 «확산 1. 원문 보존»에서 첫 질문 **전에** audit 을 cwd 에 쓰기 시작한다. 그래서 워크트리
질문은 첫 라운드 질문 묶음이 아니라 **진입 직후, audit 첫 write 전**에 단독 AskUserQuestion 으로 묻는다 —
그래야 audit 이 처음부터 워크트리 안에 쓰이고 «main 에 쓴 audit 을 옮기는» 절차가 필요 없다. 이름 파일
(`interview-basename`)은 세션 디렉토리(main repo 의 state root)에 있어 cwd 이동과 무관하다.

> «`feature/<kebab-topic>` 워크트리를 만들고 거기서 시작할까요? (권장) — 이 브랜치 하나에서 인터뷰·설계·
> 계획·구현까지 갑니다. 거절하면 현재 디렉토리에서 진행합니다.»

승낙 시 절차(순서 고정, 각 단계는 단순 명령 하나 — 격리 세션의 git 가드가 복합 명령을 막는다):

1. `EnterWorktree(name=<kebab-topic>)` — native 도구 우선(superpowers `using-git-worktrees` 와 같은 원칙).
2. `git branch -m feature/<kebab-topic>` — project-init 검증기가 위반 시 제안하는 바로 그 형태.
3. audit·seed 를 그 워크트리 안의 `docs/superpowers/interview/` 에 쓴다(현행과 같은 경로).
4. proceed 게이트에서 ①/② 를 고르면 **handoff 직전** `git add <두 파일>` → `git commit -F <msg>` (메시지
   `docs(interview): <topic> interview seed + audit` — C10 과 같은 리터럴). ③(수정)·④(멈춤)에서는 커밋하지
   않는다.
5. 게이트 텍스트의 «다음 세션 첫 턴» 안내에 워크트리 절대경로를 함께 낸다 — 사람이 그 디렉토리에서 새
   세션을 열어 `/interview <seed 전문>` 을 친다.

거절·`EnterWorktree` 부재·`DEVBREW_SPEC_DISTILL_DISABLE_WORKTREE=1` → 항목을 묻지 않거나(스위치·부재)
현재 디렉토리에서 진행(거절), audit §5 에 «워크트리 없음 — <이유>» 한 줄. 어느 경우도 seed 작성을 막지
않는다.

**이 spec 은 native 도구의 동작을 단정하지 않는다(C11).** plan 첫 task 가 격리 리포에서 재는 것: (a) native
도구가 만드는 브랜치명(brief 는 `worktree-*` 접두어라고 적었다), (b) base ref(설정 `worktree.baseRef` 의
`fresh`=origin 기본 브랜치 / `head`=로컬 HEAD — 로컬에만 있는 main 커밋이 들어오는지), (c) 워크트리 안에서
플러그인 훅·`CLAUDE_PLUGIN_ROOT` 가 해석되는지, (d) 종료 시 keep/remove 프롬프트의 모양과 «remove» 가
브랜치까지 지우는지, (e) 격리 세션의 git 가드가 `git branch -m` 과 `git commit -F` 를 허용하는지. 결과는
**plan task 의 산출물과 CHANGELOG 최상단 절(C12)** 에 남기고 framing-requests 산문을 그 사실에 맞춘다 — 이 spec
에는 나중에 절을 더하지 않는다(리뷰 후 커밋된 설계문서는 Stop 훅이 다시 arm 하지 않아 그 절이 Law 2 리뷰를
영구히 비켜간다). 위 1~5 단계 중 (a)·(e) 에 걸린 것은 실측 결과에 따라 plan 이 명령을 바꾼다.

### 4.3 premortem 함정의 처분

brief §5 의 premortem(HA6·FM6 계열)이 든 함정과 확인 결과:

| 함정 | 확인 | 처분 |
|---|---|---|
| 선커밋이 리뷰 훅을 끈다 | Stop 훅의 대상은 `specs/` 의 `-design.md`·`-spec.md`·`locked_decisions` frontmatter 문서다(`resolve_mode.py`). seed·audit 은 어느 쪽에도 안 걸린다 | 해당 없음. 단 설계문서는 리뷰 후 커밋(이 spec 자신에게 적용) |
| native 세션 고정 ↔ state 경로 | state 는 워크트리에서도 main repo 로 라우팅. Phase 0·1 은 원래 별 세션이라 session-id 가 다른 것이 정상 | 해당 없음 |
| 브랜치명이 «해답=구현»을 선점 | 이름은 주제(kebab-topic)이지 해법이 아니다(이 브랜치가 예) | 해당 없음 |
| 미커밋 파일이 워크트리에서 안 보임 | audit 첫 write 전에 워크트리로 들어가므로 해당 없음. base 가 origin 이면 로컬 main 커밋이 빠질 수 있다 | (b) 실측 후 framing-requests 산문에 반영 |
| `worktree-*` 접두어 ↔ `feature/*` 규칙 | rename 으로 해소(brief C8) | 2단계 |
| 형제 워크트리 충돌 | 범위 밖(brief C9) | OQ1 |

두 단계의 경계(brief C38): Phase 0 이 새로 갖는 책임은 «워크트리·커밋·재검증 문단» 셋뿐이다. 파고들기·측정·
원장은 전부 Phase 1. Phase 0 은 여전히 웹을 보지 않는다. handoff 계약의 변경은 «seed 마지막 문단»과
«게이트 텍스트의 워크트리 경로» 둘이다.

## 5. 컴포넌트와 격리

| 단위 | 하는 일 | 쓰는 법 | 의존 |
|---|---|---|---|
| `conducting-interview/SKILL.md` | 라운드 규약(§1)·닫힘 규칙·재개방·dispatch 규칙(§2) | 현행 진입 그대로 | state_path · coverage-mapper · steelman-builder · blind-spot-prober |
| `references/finishing.md` | Step A.7 측정 단계 추가, 원장 직렬화에 재개방·S앵커 | floor 전부 closed 시 Read | check_brief · depth_pairs · depth-auditor · depth_record |
| `scripts/check_brief.py` | `coverage_anchor_failures` + §2 `coverage-mapper ≥1` 검사 | `gate <payload>` | section6 (기존) |
| `scripts/depth_pairs.py` | state 본문에서 짝 추출 + 표본 ≤4 | `depth_pairs.py <state> --sample 4` → JSON / rc 3 측정 불가 | 없음 (state 파일만) |
| `agents/depth-auditor.md` | 짝의 내용 라벨 | inline 짝, `tools: []`, `model:` 없음 | 없음 |
| `scripts/depth_record.py` | auditor·사람 라벨 병합 → audit §2 줄 · 인터뷰별 측정 파일 · 조건 판정 | 위 §3.2 | `adjudication.py` (held 계수) |
| `framing-requests/SKILL.md` | 워크트리 항목·절차, «다시 검증할 것» 규약, 게이트 텍스트 경로 | 현행 진입 그대로 | EnterWorktree (있으면) · project-init (검증만) |
| `agents/coverage-mapper.md` | 입력에 seed·재검증 문단, dispatch 규칙 문구 교체 | R1 필수 + 재개방 1회 | 없음 (본문 변경만) |

격리: `depth-auditor` 는 도구 0 — audit·state·리포 어디에도 닿을 수 없고 짝 목록만 본다. 판정을 쓰는
것은 orchestrator 가 아니라 `depth_record.py`(결정론) 이고, 사람 라벨은 스크립트가 병합한다. 어느
단위도 다른 단위의 내부를 읽지 않는다 — state 본문 형식(§1.1)과 auditor 출력 형식(§3.2)이 두 인터페이스다.

## Acceptance Criteria

- **AC1 (라운드 형식)**: SKILL.md 에 §1.1 의 기록 형식 블록(`### 직전 답에서 — S<k>` · 네 줄 · `### 질문`
  Q1/Q2)이 있고, «Q1 은 생략할 수 없다»·«R1 은 S1 을 되비춘다»·«차원은 사용자가 답한 S 뒤에만 닫는다»
  문장이 있다. 4-block 절·teach-beat 절·경로 (c)·정체 트리거 절은 없다. SKILL.md 줄 수는 408 미만.
- **AC2 (AskUserQuestion 둘)**: SKILL.md 의 질문 블록이 `AskUserQuestion(` 호출에 질문 2개(되비추기
  확인 + 새 결정)를 담고, 첫 선택지가 추천이며, «description 은 고르면 무엇이 달라지는가»를 요구한다.
- **AC3 (S앵커 게이트)**: `check_brief.py gate` 가 (a) 닫힌 행 evidence 에 앵커(`(?<![A-Za-z])S\d+\b`) 없음
  → exit 1, (b) §6 에 없는 S 인용 → exit 1, (c) 실재 S 인용 → 통과, (d) `OQS3` 류 우연 토큰은 앵커로 안 센다.
  floor·derived·박제(`사용자-승인 박제(@S12) — …`) 행 모두. fixture 4쌍 + mutation(앵커 문자 삭제·번호 변경·
  행 삭제)으로 판정 반전 확인. **검사는 무조건이다**(audit `source:` 버전으로 조건화하지 않는다 — 피검자가
  쓰는 값으로 게이트를 끄는 길이 된다). 그러므로 **기존 fixture 86개의 audit §1 닫힌 행 전부에 실재 S 앵커를,
  §2 에 `coverage-mapper 1` 을 스크립트로 일괄 주입**하고, 그 스윕 뒤 각 fixture 가 원래 목적의 판정(red 는
  red, green 은 green)을 그대로 내는지 `test_check_brief.sh` 전체로 확인한다. 아카이브의 옛 brief 는
  재게이트 대상이 아니다 — CHANGELOG 최상단 절(C12)에 «이 릴리스 이전 brief 는 새 게이트를 통과하지
  않는다»를 그 절의 버전 값으로 적는다.
- **AC4 (coverage-mapper ≥1)**: audit §2 에 `coverage-mapper <k>` k≥1 없으면 exit 1; `coverage-mapper 0
  (unavailable: …)` 는 advisory 통과이고 그 advisory 가 Step B 게이트 텍스트에 실린다(finishing.md 락).
  fixture 양·음·unavailable 셋. 기존 fixture 스윕은 AC3 과 같은 스크립트가 한다.
- **AC5 (재개방)**: state 스키마에 `reopened`·`reopen_log` 가 있고 `closed → open` 전이 문장과 «상충 줄에
  → 재개방»·«재개방 후 닫힘은 새 S» 규칙이 SKILL 에 있다. audit §1 행의 `(재개방 n회 — …)` 접미가
  `coverage_ledger_failures` 정규식을 깨지 않는다(fixture).
- **AC6 (depth_pairs)**: 합성 state 6종 — 정상(적격 짝 ≥4, 표본 4, rc 0) / 적격 짝 0·1·3 (표본 0·1·3, 표본 0 이면
  `human_sample: []`) / `## R` 헤딩 없음(rc 3, stdout `{"unmeasurable": "<이유>"}`) / 블록 전부 «없음»
  (`substantive_form` 0, rc 0). 한 라운드에 답 둘 → 블록 둘 → 짝 둘. `round: 0` 이 아닌 S1(비-seed 경로)은
  R1 과 짝짓지 않는다. 표본은 session_id 시드로 재현 가능·비복원. 마지막 라운드 답은 `terminal`.
- **AC7 (depth-auditor)**: agent 파일에 `tools: []`, `model:` 줄 없음, 출력 계약 `depth-audit` 센티널,
  «짝 목록 밖을 보지 마라», «dug 는 그 S 에서 따라 나온 내용에만 — 이유 줄에 S 의 어느 부분에서인지».
  fixture 짝 셋: 관련 내용 → dug / 다른 답에서 나온 내용만 → not_dug / 무관한 정보만 → not_dug (agent
  프롬프트의 예시로 싣고, `depth_record.py` 는 라벨을 그대로 받는다). `test_dispatch_disposition.sh` 가 finishing.md 의 dispatch 자리 처분 줄과
  `depth_record.py` 의 `adjudication` import 를 통과시킨다.
- **AC8 (depth_record)**: auditor raw + 사람 라벨 JSON → audit §2 세 줄 + `depth/<basename>.json` + 조건 줄.
  입력 파손(센티널 부재·항목 파손·라벨 부재)은 각각 unavailable/held/미라벨로 기록되고 exit 0. 일치율은
  양쪽 dug|not_dug 인 짝만 분모(auditor unavailable·held·undecidable 짝은 `auditor_missing`), 분모 0 →
  «자료 부족». `depth/*.json` fixture 로 조건 A·B 의 경계값(30%·70%) 양쪽, 적격 인터뷰 계수(전부
  undecidable 인 인터뷰는 5건에 안 듦), 자료 부족 판정.
- **AC9 (finishing Step A.7)**: `finishing.md` 에 Step A.5 뒤·Step B 앞에 «깊이 측정» 절이 있고, 측정
  불가·unavailable·미라벨 셋을 «기록한다, 막지 않는다»로 적는다. proceed 게이트 question 텍스트에 깊이
  측정 세 줄 요약이 실린다.
- **AC10 (audit 템플릿)**: §2 에 깊이 측정 세 줄 자리, §1 에 재개방 접미 예시.
- **AC11 (seed 규약)**: framing-requests SKILL 과 `compression.md`·seed 템플릿 예시에 «(사용자 확인)»
  하나·«다시 검증할 것 —» 마지막 문단·무표시=미확인 규약이 있다. `check_seed.py` 는 무변경(diff 0).
  conducting-interview 의 seed 입력 절이 그 문단을 R1 의 S1 되비추기와 coverage-mapper 입력으로 쓴다.
- **AC12 (워크트리)**: framing-requests 진입 직후·audit 첫 write 전의 단독 워크트리 질문, 5단계 절차, 거절·
  부재·`DEVBREW_SPEC_DISTILL_DISABLE_WORKTREE` 강등, ①/② 에서만 handoff 직전 커밋(C10 과 같은 메시지
  리터럴), 게이트 텍스트에 경로. kill switch 는 SKILL 의 `## kill switch` 목록에 등재.
- **AC13 (실측 반영)**: §4.2 의 (a)~(e) 실측 결과가 plan task 산출물과 CHANGELOG 최상단 절(C12)에 있고,
  framing-requests 산문의 명령 다섯 단계가 그 결과와 모순되지 않는다. 이 spec 은 편집하지 않는다.
- **AC14 (순감·stale-term)**: `no_progress_streak`·`stall_episode`·`coverage_mapper_dispatched_episode`·
  `teach-lite`·`teach-heavy`·`teach-beat` 가 production 표면(SKILL·references·agents·templates)에 없다
  (`test_stale_terms.sh` 등재). CHANGELOG 에 Removed 항목.
- **AC15 (버전)**: `origin/main` merge 커밋이 브랜치에 있고, `plugin.json` 이 **가장 최근 merge 시점**의
  main 보다 한 minor 위이며(C12 — 이 브랜치는 merge 커밋이 둘이라 「가장 최근」이 판정을 가른다),
  CHANGELOG 최상단 헤딩이 `plugin.json` 과 같은 값이고 그 절이 이 릴리스 전체(Added·
  Changed·Removed·Verification)를 담는다. README «Principles Instantiated» 에 Law 3(측정 원장)·
  P17(사용자가 시계) 한 줄씩. **이 브랜치의 그 값은 `0.56.0`**(C12 — 리터럴이 아니라 불변식으로 재는 이유).
- **AC16 (사람 e2e)**: 새 SKILL 로 실제 인터뷰 1회 — 매 라운드 «직전 답에서» 블록이 출력·state 에 남고,
  Q2 본문이 무엇을 정하는지·용어·기술 사실·선택의 결과를 풀었는지(G5)를 사용자가 보며, 종료 시 라벨 질문
  `min(4, 적격)` 개가 뜨고, `depth/<basename>.json` 이 생긴다. 사용자가 확인하고 결과를 CHANGELOG 에 한
  줄로 남긴다. 이것이 판정자 조건의 1건째다.

## Files to Modify

```
plugins/spec-distill/.claude-plugin/plugin.json                     main merge 후 한 minor 위로 (C12)
plugins/spec-distill/CHANGELOG.md                                   최상단에 그 버전 절 — Added/Changed/Removed
plugins/spec-distill/README.md                                      skill 설명·Principles Instantiated·측정 원장 안내
plugins/spec-distill/skills/conducting-interview/SKILL.md           §1·§2 (라운드 규약·닫힘·재개방·dispatch), 순감
plugins/spec-distill/skills/conducting-interview/references/finishing.md
                                                                    Step A.7 깊이 측정 · 원장 직렬화(재개방·S앵커) · 게이트 텍스트 요약
plugins/spec-distill/skills/framing-requests/SKILL.md               워크트리 항목·절차·kill switch · «다시 검증할 것» 규약 · 게이트 경로
plugins/spec-distill/scripts/check_brief.py                         coverage_anchor_failures · §2 coverage-mapper ≥1
plugins/spec-distill/scripts/depth_pairs.py                         (신규) 짝 추출·표본 ≤4·측정 불가 rc 3
plugins/spec-distill/scripts/depth_record.py                        (신규) 병합·audit §2 줄·depth/<basename>.json·조건 판정 (adjudication import)
plugins/spec-distill/agents/depth-auditor.md                        (신규) tools: [] · 센티널 depth-audit · model 줄 없음
plugins/spec-distill/agents/coverage-mapper.md                      입력(seed·재검증 문단)·dispatch 규칙 문구
plugins/spec-distill/templates/interview-audit-template.md          §1 재개방 접미 · §2 깊이 측정 세 줄
plugins/spec-distill/templates/interview-seed-template.md           예시 마지막 문단 «다시 검증할 것 —»
plugins/spec-distill/references/compression.md                      «(사용자 확인)»·마지막 문단 규약
docs/superpowers/interview/depth/.gitkeep                          (신규) 인터뷰별 측정 파일 디렉토리 — <brief-basename>.json 하나씩
plugins/spec-distill/tests/fixtures/interview-brief-anchor-*.{md,audit.md}   AC3 4쌍 · AC4 3 · AC5 1
plugins/spec-distill/tests/fixtures/*.audit.md (기존 86개)          AC3·AC4 스윕 — 닫힌 행에 실재 S 앵커·§2 에 coverage-mapper 1 일괄 주입
plugins/spec-distill/tests/fixtures/sweep_anchor_fixtures.py        (신규, 1회용) 위 스윕 스크립트 — 커밋에 남겨 재현 가능하게
plugins/spec-distill/tests/fixtures/depth-state-*.md                AC6 6종 · AC8 depth/*.json 5건
plugins/spec-distill/tests/test_check_brief.sh                      AC3·AC4·AC5 락 + mutation
plugins/spec-distill/tests/test_depth_pairs.py                      (신규) AC6
plugins/spec-distill/tests/test_depth_record.py                     (신규) AC8
plugins/spec-distill/tests/test_depth_auditor_frontmatter.sh        (신규) AC7
plugins/spec-distill/tests/test_conducting_interview_stage.sh       AC1·AC2·AC5 블록 스코프 락 (구 4-block/teach-beat 락 제거)
plugins/spec-distill/tests/test_conducting_interview_internal.sh    정체 트리거 락 제거 · dispatch 규칙 락
plugins/spec-distill/tests/test_request_framing_command.sh          AC11·AC12 블록 스코프 락
plugins/spec-distill/tests/test_stale_terms.sh                      AC14 어휘 등재
shared/tests/test_dispatch_disposition.sh                           (변경 없음 — 새 dispatch 자리가 통과해야 함)
docs/superpowers/plans/2026-09-06-interview-depth-redesign.md      (writing-plans 산출물) task 1 = V6 실측, 결과는 여기와 CHANGELOG 에 (AC13)
```

건드리지 않음: `check_seed.py` · `check_verbatim_coverage.py` · `section6.py` · reviewing-brief ·
reviewing-spec · `hooks/*` · steelman-builder · blind-spot-prober 본문 · brief 템플릿.

## Verification Plan

- **V1 (게이트 락 + mutation)**: 기존 fixture 스윕(AC3) 뒤 `bash plugins/spec-distill/tests/test_check_brief.sh`
  — 스윕 전과 같은 ok/no 집합(스윕이 기존 판정을 바꾸지 않았다는 증거) + AC3·AC4·AC5 fixture 전부 GREEN. 이어서 각 양성 fixture 를 흔든다(앵커 삭제 / 번호 +1 / 행 삭제 / `coverage-mapper 1` → `0`)
  — 판정이 반전되지 않으면 락에 이빨이 없는 것이다. `PYTHONDONTWRITEBYTECODE=1`.
- **V2 (스크립트 단위)**: `python3 -m unittest discover -s plugins/spec-distill/tests -p 'test_depth_*.py'`
  — AC6·AC8. 경계값(30%·70%) 양쪽, 파손 입력 셋, 표본 재현성.
- **V3 (문서 락, 블록 스코프)**: `bash plugins/spec-distill/tests/test_conducting_interview_stage.sh`
  `test_conducting_interview_internal.sh` `test_request_framing_command.sh` `test_stale_terms.sh`
  `test_depth_auditor_frontmatter.sh` — 각 락은 본문 고유 문구를 awk 블록 스코프로 잡는다. 통째 삭제
  mutation 으로 RED 확인 후 복원(변이 전 커밋).
- **V4 (처분 회계)**: `bash shared/tests/test_dispatch_disposition.sh` — depth-auditor dispatch 자리와
  `depth_record.py` 의 import 통과.
- **V5 (전체 스위트 baseline)**: 착수 전 `for t in plugins/spec-distill/tests/test_*.sh; do bash "$t"; done`
  과 `python3 -m unittest discover -s plugins/spec-distill/tests` 의 실패 **줄 수**를 기록하고, 완료 후 새
  실패 0 을 확인한다(rc 만 보면 이미 RED 인 파일 안의 회귀가 안 보인다).
- **V6 (도구 실측, plan task 1)**: 격리 리포(`CLAUDE_CONFIG_DIR=<tmp>` 격리 증명 후)에서 §4.2 (a)~(e) 를
  헤드리스로 재고 결과를 plan task 산출물과 CHANGELOG 에 적는다(spec 은 편집하지 않는다). 실측 전엔
  framing-requests 산문을 확정하지 않는다.
- **V7 (사람 e2e, AC16)**: 이 브랜치의 플러그인으로(`--plugin-dir` 또는 격리 설치) 실제 인터뷰 1회.
  관찰 항목: 라운드마다 «직전 답에서» 블록 / Q1·Q2 모양 / 종료 시 라벨 ≤4개 / audit §2 네 줄(깊이 측정 셋 + 판정자 조건) / depth/<basename>.json 1개.
  결과를 CHANGELOG 최상단 절(C12)의 Verification 줄에 남긴다.
- **V8 (리뷰)**: 설계문서 — Stop 훅의 `spec-distill:spec-reviewer`(Law 2 분리, codex 병렬). 구현 —
  subagent-driven + whole-branch 리뷰 + codex. 커밋은 리뷰 뒤.

## Rejected Alternatives

- **R1 — 독립 판정 에이전트의 닫힘 거부권(지금)**: 라운드당 dispatch 5~10 추가, 거부 상한 별도 필요, 그리고
  brief §4 의 반박 셋(판정자의 입력을 피판정자가 쓴다 · 같은 계열 모델은 친숙한 텍스트를 선호 · 판정
  에이전트를 넣은 시스템이 인간 대비 유의차 없음)이 미해소. 측정 전엔 정당화되지 않는다 → §3.4 조건부.
- **R2 — 답 단위 판정자 = 사용자(매 답에 «더 팔 축» 선택지)**: 사용자가 채택하지 않음(brief C25). 라운드당
  클릭 증가.
- **R3 — 되묻기를 매 라운드 강제**: 사용자 타이핑·피로 증가, 동적 probing 이 동의 편향을 올린다는 근거
  (brief §4 «wuttke-2025»). 되비추기가 안 서는 답에서만(§1.3).
- **R4 — framing 식 묶음(라운드당 질문 3~4)**: 한 화면에 결정이 여럿이라 하나를 얕게 넘기기 쉽고, 하류
  설계 도구가 깊이를 위해 «한 번에 하나»를 택했다(brief §4 «superpowers-brainstorming»). 사용자가 ①을
  골랐다(2026-09-06).
- **R5 — 질문·라운드 상한 복원**: 첫 사이클이 뗀 것이고 «질문 수가 목적이 되는 것»을 사용자가 걱정(brief C5).
  사용자가 시계.
- **R6 — probe 목록형 도구상자(CDM/ACTA 6~8 항목)**: 사용 횟수가 evidence 로 적히는 순간 체크리스트로
  퇴화(premortem HA4); 도메인 무관 질문이 요구 도출 실수 1위(brief §4 «followup-generation»).
- **R7 — teach-beat 유지**: 열린 질문 8/8 이 답 없이 소실됐고 산문이 줄지 않는다. «상충» 줄이 같은 정보를
  «맞나?»로 되비춰 처분을 받는다.
- **R8 — seed 태그 문법(`[재검증: …]`)**: `check_seed.py` 가 본문 태그를 금지하고 «링크·라벨은 권위로
  읽혀 하류를 끈다»가 그 조항의 이유. 산문 문단으로.
- **R9 — 워크트리 무질문 자동 생성**: native 도구의 «명시 지시 시에만» 계약과 긴장하고 작은 요청에도
  워크트리가 생긴다. 첫 라운드 질문 묶음의 한 항목이 비용 0 에 가깝다.
- **R10 — seed 작성 직후 커밋**: ③(수정)마다 커밋이 늘고 ④(멈춤)에도 커밋이 남는다. handoff 직전 1회.
- **R11 — 원장 폐지**: 차원을 «여는» 데는 작동했다는 실측(9/9 floor 채워짐). 문제가 아닌 것을 고치게 된다.
- **R12 — 하류 재질문 계수 채널**: brainstorming 은 외부 플러그인·별 세션이라 채널이 없고, 게이트가 되면
  인터뷰가 설계 결정을 brief 에 선기입하는 쪽으로 왜곡된다. OQ2 유지.
- **R13 — 측정 내용 층을 orchestrator 자신이**: 피판정자가 판정. 도구 0 에이전트로 격리.
- **R14 — 사후 측정을 게이트로**: Goodhart(brief §4). brief C11 이 «게이트 아님»을 확정.
- **R15 — 재개방 상한(차원당 2회 → 사용자에게 계속/박제 질문)**: 라운드가 사용자 답으로만 돌아 사용자가
  이미 시계다. 상한은 state 카운터와 산문 한 절을 더할 뿐 자율을 묶지 않는다.

## Open Questions

- **OQ1**: 형제 워크트리(같은 리포에서 다른 세션이 쓰는 것)와 파일이 겹칠 때의 처분 — 범위 밖(brief C9). merge
  시점에 부딪히면 그때 결정.
- **OQ2**: «하류가 brief 를 읽고 다시 물은 횟수»의 측정 채널 — brainstorming 이 외부 플러그인·별 세션이라
  지금은 셀 수 없다(NG6).
- **OQ3**: 인터뷰가 확정한 사실이 나중에 코드로 반증되는 층(brief C16) — 어느 사이클이 맡는지.
- **OQ4**: §3.4 의 두 숫자(30%·70%)와 누적 5건의 재조정 시점 — 첫 5건이 쌓인 뒤 이 spec 의 후속 사이클.
- **OQ5**: 라벨 표본 ≤4개가 인터뷰 길이(짝 6~20)에 비해 충분한지 — 누적이 쌓이면 OQ4 와 함께 본다.
- **OQ6**: «아무 S 나 인용해 닫는 것»을 보는 자리가 이 판본에 없다(§2.1). 후보는 brief 분리 리뷰 번들에
  audit §1 을 넣어 충실도 critic 이 인용의 정당성을 보게 하는 것 — reviewing-brief 변경이라 다음 사이클.

## Concrete Next Action

다음 단계: `superpowers:writing-plans` (단, Stop 훅이 먼저 `spec-distill:spec-reviewer` Law 2 분리 리뷰를
강제 — 리뷰 pass 후 진행. 이 문서는 리뷰가 끝난 뒤 커밋한다).
- Spec 경로: `docs/superpowers/specs/2026-09-06-interview-depth-redesign-design.md`
- Plan 산출물: `docs/superpowers/plans/2026-09-06-interview-depth-redesign.md`
- plan 의 첫 task 는 V6(도구 실측), 둘째는 main 0.54.0 merge + V5 baseline. §4.2 는 별 task 묶음(Deferred 참조).
- 명령: `Skill superpowers:writing-plans docs/superpowers/specs/2026-09-06-interview-depth-redesign-design.md`
