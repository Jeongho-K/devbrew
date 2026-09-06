## In-flight state migration

state.local.md 로드 시 **구세션 스키마**(`interview_round` 존재 / `coverage` 부재)를 감지하면
*non-mutating read*로 fresh 초기화(승격):

- `coverage.floor`의 5개 차원(root_problem/landscape/skepticism/blind_spot/open_questions) 전부
  `{status: open, evidence: "", reopened: 0, reopen_log: []}`로 seed.
- `coverage.derived`: `[]`.
- `orchestration`: `{focused_dimension: null, blind_spot_dispatched: false, coverage_mapper_dispatches: 0}`.

기존 필드(`non_user_streak`·`web_*`·`issue_history` 등)는 유지. 구세션의 라운드별 잠금 레코드
리스트(v0.22.0까지의 잠금 필드)는 승계하지 않고 `user_statements: []`로 fresh seed합니다 — 잠금
레코드를 발화 레코드로 승격하면 판정이 없던 척하는 잠금이 그대로 넘어옵니다.

**영속화 시점**: 승격된 스키마는 재개된 세션의 첫 액션으로, 첫 probe보다 먼저 Bash 전체-frontmatter
write로 즉시 디스크에 반영합니다(PN1) — coverage-mapper 상한 카운터(`coverage_mapper_dispatches`)와
재개방 원장(`reopen_log`)이 그 디스크 값을 직접 읽기 때문입니다. 신규 필드(coverage/orchestration)만
추가하는 forward promotion이지 backward-rewrite가 아닙니다(`interview_round`는 자연 소멸, 다른
기존 필드는 불변) — "다음 명시적 write"를 기다리는 연기가 아니라 resume 직후 1회입니다.

사용자에게 advisory 한 줄 출력:
```
[spec-distill v0.56.0] state schema migration: reopen ledger + coverage_mapper_dispatches added (stall trigger retired).
```

자동 promote 실패 시(파일 corruption 등) → "구세션 in-flight state 호환 실패 — 세션 재시작 권장"
알림 + state.local.md 보존 (P14).
