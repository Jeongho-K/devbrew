---
type: interview-seed
next_phase: spec-distill:interview
audit_file: 2026-09-05-interview-depth-redesign-interview.audit.md
---

spec-distill 의 Phase 1 interview 가 문제를 충분히 파기 전에 끝난다. 커버리지 원장이 있는데도 실제 사용감은 라운드마다 질문을 소진하고 나면 끝나는 쪽이다. 질문 수나 고정 체크리스트를 늘리는 방식이 아니라, 왜 얕게 끝나는지 현재 구현과 변경 이력에서 먼저 원인을 찾아 설명하고, 가능한 재설계 방향을 비교한 뒤, 더 집요한 문제공간 탐색으로 재설계해 구현까지 가라. 사용자는 이 방향 자체가 좋은 방향이 아니라면 그렇게 말하라고 했다 — 아래의 방향 서술도 검증 대상이다.

Phase 0 은 이미 있는 request-framing skill 이고 Phase 1 은 conducting-interview skill 이다 — 이 seed 자체가 request-framing 이 만든 것이고, 다음 세션의 인터뷰는 바로 그 개선 대상 skill 로 돈다. Phase 0 착안: 그 자기참조는 쓸 수 있는 자료이고, 이번 인터뷰의 라운드 기록도 대조 코퍼스에 넣을 수 있다.

이 문제는 두 번째 사이클이다. 2026-07-20 인터뷰(지금은 archive 에 있다)가 같은 요청 — 더 집요하게, 미지를 드러내 가르치고, 외부 탐색을 더 — 을 받아 «집요함이 고정 라운드에 묶여 있다»로 재구성했고, 그 결과가 커버리지 원장·teach-beat·blind-spot-prober·floor 다섯 차원(root_problem·landscape·skepticism·blind_spot·open_questions)이다. 그때 steelman 은 «더 무겁게 하지 말고 더 가볍게»였고 집요함은 길이가 아니라고 재정의해 방어됐다. 그 결과가 여전히 얕다는 것이 이번 발단이다. 전부 재검토 대상이다. 다만 그때 무엇을 고민했고 왜 그렇게 정했는지를 그 brief·설계·CHANGELOG 에서 먼저 이해한 뒤 재구성하라. Phase 0 제안: 같은 결론으로 돌아온다면 첫 사이클이 왜 얕았는지를 설명할 수 있어야 한다.

Phase 0 이 구현을 읽고 본 원인 후보다. 검증 대상이지 확정이 아니다. 종료 술어가 이벤트 완료다 — landscape 는 sweep 한 번, skepticism 은 verdict 한 건, blind_spot 은 dispatch 한 번이면 닫힐 수 있고 게이트는 상태 토큰과 evidence 비어있지 않음만 본다. 진전의 정의가 evidence append 라 피상적 답도 진전으로 센다. 4-block 이 질문 하나와 추천 답안을 강제해 라운드당 결정 하나, 추천안 동의를 유도한다. closed 에서 open 으로 돌아가는 전이가 없다. derived 차원의 공급원이 coverage-mapper 뿐이고 seed 에서 주제 차원을 처음에 뽑을 의무가 없다. Phase 0 이 찾은 과거 사례 셋: 사용자 침묵으로 open_questions 를 닫은 것(docs/archive/interview/2026-07-26-qg-impact-driven-qa-runtime-interview.md 의 원장), 묻지 못한 채 끝낸 것(docs/archive/interview/2026-07-25-spec-distill-brief-handoff-redesign-interview.audit.md 의 원장), 확정 사실이 코드로 반증된 것(docs/superpowers/specs/2026-09-02-seam-channel-verification-design.md 의 «brief 의 사실 하나가 코드에 의해 반증됐다» 절). 규칙 대부분이 SKILL 산문인데 orchestrator 가 그것을 얼마나 이행하는지의 측정 기록을 Phase 0 은 찾지 못했다.

방향은 이렇다. 인터뷰는 고정 라운드나 질문 수가 아니라 문제공간의 충족도로 진행한다. 모호하거나 피상적인 답, 추천안에 대한 빠른 동의, 근거 없는 확신 하나로 차원을 닫지 말고 필요하면 이유·사례·우선순위·상충 관계·실패 조건을 후속으로 확인한다. 새 답이나 외부 근거가 이전 답과 충돌하면 이미 닫힌 주제도 다시 연다. 외부 탐색은 실제 도메인의 대안과 prior art, 현재 결정에 영향을 주는 사실 검증에 쓴다 — 모델의 낡은 지식이 방향을 고정하지 않게 하되, 외부 사례나 에이전트 추론을 사용자 요구로 승격하지 않는다. 기존 4-block 형식, floor 와 derived 커버리지, 상태 전이, probe 와 round 개념, 종료 조건, steelman 과 blind-spot 결과의 후속 질문 반영을 전부 점검하되 무엇을 유지하고 바꿀지 미리 단정하지 말고 여러 접근을 비교하라. 형식과 원장만 무거워지고 실제 대화 깊이는 늘지 않는 해법은 피한다. 라운드·dispatch·web·codex 비용은 늘어도 된다(사용자 확인) — 다만 과거 사례를 찾는 탐색은 «너무 비용 많이 들지 않게». 질문을 한 번에 하나만 하는 원칙은 푼다 — 대체 방식은 네가 정하되, 사용자는 Phase 0(framing-requests) 쪽이 더 좋아 보인다고 했다. 추천 답안을 유지할지도 네 판단이다.

성공한 인터뷰는 질문을 많이 한 인터뷰가 아니다. 핵심 방향이 사용자 표현과 근거로 충분히 드러나고, 중요한 가정과 상충 관계가 검토되고, topic-specific 미탐색 영역이 남지 않았는지 확인되고, 불확실한 것은 억지로 닫지 않고 Open Question 으로 남기고, 사용자가 중단하거나 handoff 를 고를 권리가 유지되며, 최종 brief 만 읽은 brainstorming 이 문제를 다시 추측하거나 같은 질문을 반복하지 않는다. 역할 분담은 유지한다(사용자 확인): 인터뷰는 조사와 문제공간, brainstorming 은 설계, writing-plans 는 계획, 그 다음이 구현이다 — 인터뷰의 조사가 설계 입력으로 충분해지면 되고, 접근법 비교는 brainstorming 의 몫으로 남는다. Phase 0 관찰 하나: «미탐색 영역이 남지 않았다»는 그 자체로는 증명할 수 없어 대리 조건이 필요할 수 있다.

경계는 이렇다. request-framing 은 다음 에이전트에게 무엇을 맡길지 정렬해 interview-seed 를 만들고, interview 는 그 요청 뒤에서 실제로 해결해야 할 문제·원인·제약·이해관계·대안과 방향을 탐색해 interview-brief 를 만든다. Phase 1 은 seed 가 확정한 것을 불필요하게 다시 묻지 않되, 추론·외부·열린 항목과 새 근거로 흔들린 항목은 재검증한다. 지금 seed 계약은 태그 없는 산문이라 그 구분이 파일에 없다. 사용자는 seed 에 가벼운 구조를 넣는 쪽을 골랐고 확인했다 — 이번 사이클 범위 안이되 무게중심은 interview 다. Phase 0 추가와 interview 보강이 하나의 거대한 책임으로 섞이지 않게 두 단계의 경계와 handoff 계약도 검증하라. Phase 0 파일은 필요하면 고쳐도 된다.

Phase 0 에 붙는 새 요구가 하나 있고, 이것도 이번 사이클 범위 안이다. Phase 0 이 워크트리를 만들어 거기서 시작하고, 인터뷰 자료(예: audit, seed)부터 그 브랜치에 커밋하고, 브랜치명을 적절히 정한다 — 사용자 근거는 «대부분 a와 같을거라»(a = 한 브랜치에서 분석→설계→구현)이고, «superpowers 같이»라고 했다. 가능하면 하니스 native 워크트리 도구를 우선한다 — 사용자는 native 가 세션을 워크트리에 고정한다는 대가를 알고 그쪽을 골랐다(확인됨). 다만 사용자가 앞서 말한 «세션에 워크트리가 고정되지는 않게»가 정확히 무엇을 뜻했는지는 확인되지 않았다. Phase 0 관찰: 미커밋 파일은 워크트리에서 보이지 않으므로 Phase 1 이 워크트리에서 시작하려면 audit 이 먼저 그 브랜치에 커밋돼 있어야 하고, native 로 들어가면 브랜치가 worktree 접두어로 나오며 격리 세션의 git 가드가 복합 명령을 막는다. 생성 시점은 열려 있다(예: 첫 라운드, 압축 직후).

한 브랜치에서 원인 분석, 설계, 계획, 구현까지 간다(사용자 확인). Phase 0 관찰: 같은 리포에 steelman 관련 이름의 형제 워크트리가 함께 돌고 있다(다른 세션이 쓰는 중). 겹치면 어떻게 할지는 정해진 바 없다.
