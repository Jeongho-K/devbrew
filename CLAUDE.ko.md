# CLAUDE.md (한국어)

> **Specify before you code. Review before you ship. Compound before you forget.**
> *코드보다 명세 먼저. 배포보다 리뷰 먼저. 잊기 전에 축적.*
>
> *병목은 모델이 아니다. 스펙, 리뷰, 메모리다. devbrew의 역할은 사용자가 의식적으로 기억하지 않아도 이 세 가지가 자동으로 지켜지도록 만드는 것이다.*

devbrew는 Claude Code를 위한 플러그인 마켓플레이스입니다. `plugins/*` 하위의 모든 플러그인은 아래 원칙을 상속합니다. 출처·anti-pattern 라이브러리·네 소스 하니스(oh-my-claudecode, gstack, ouroboros, compound-engineering)와 Anthropic 엔지니어링 문서의 원문 인용까지 담긴 전체 철학은 [`docs/philosophy/devbrew-harness-philosophy.md`](docs/philosophy/devbrew-harness-philosophy.md)에 있습니다 (한국어: [`docs/philosophy/devbrew-harness-philosophy.ko.md`](docs/philosophy/devbrew-harness-philosophy.ko.md)). 이 파일은 사전 로드 컨텍스트 앵커 — 자기 자리를 벌 만큼 타이트하고, 모든 플러그인 결정을 guide할 만큼 dense해야 합니다.

## 세 법칙 (Three Laws)

**Law 1 — Clarity Before Code (코드보다 명확성 먼저).** 명세가 모호한 상태에서는 구현이 진행되지 않습니다. 코드를 shipping하는 모든 플러그인은 실제 거절 메커니즘을 가져야 합니다 — 최소한 **구조적 게이트** (필수 섹션: Context/Why, Goals, Non-goals, Constraints, Acceptance Criteria, Files to Modify, Verification Plan, Rejected Alternatives, Metadata)를 silent하게 skip할 수 없어야 합니다. Adversarial self-review는 구조적 baseline 위에 강력 권장, 수치 스코어링은 허용되지만 권장하지 않음 (철학 문서 §5.3 참조). *Trivia escape:* **diff가 한 문장으로 설명 가능한** 변경 (Anthropic, *Claude Code Best Practices*)은 게이트 우회 — 오타, 리네임, 주석-only 편집, 단일 파일 포맷팅. 여러 파일이나 동작 변경은 반드시 통과.

**Law 2 — Writer and Reviewer Must Never Share a Pass (작성자와 리뷰어는 같은 턴에 공존 불가).** 코드를 쓴 턴은 그 코드를 승인할 수 없음. 분리는 프롬프트가 아니라 물리적: `allowed-tools` / `disallowed-tools` frontmatter로 리뷰어가 `Write`/`Edit`을 literally 할 수 없게 만들기. 쓰기 권한이 있는 리뷰어는 리뷰어가 아님. 검증은 load-bearing 인프라, 나중 생각이 아님 — rock-solid하게 만드는 데 투자.

**Law 3 — Every Cycle Must Leave the System Smarter (매 사이클마다 시스템이 더 똑똑해져야 함).** Compounding은 선택적 wrap-up이 아니라 discoverability check가 붙은 이름 붙은 단계. 사이클이 learning을 생산하면 하니스는 그것을 파일로 capture하고 다음 세션이 실제로 찾을 것임을 확인 — discoverability가 위험하면 인덱스 (`AGENTS.md`/`CLAUDE.md`)를 자동 편집. 어떤 미래 agent도 읽지 않는 파일에 기록하는 것은 theater.

*계층:* 법칙 N은 충돌 시 법칙 N+1을 override. 명확성 먼저, 독립성 둘째, compounding 셋째.

## 플러그인 형태 (Plugin Shape)

`plugins/*`의 모든 플러그인은 [`docs/philosophy/devbrew-harness-philosophy.md §4.0`](docs/philosophy/devbrew-harness-philosophy.md)의 canonical 디렉토리 구조를 따르고 다음을 모두 만족해야 함:

- **`.claude-plugin/plugin.json`**에 필수 `name`, `description`, `version` (optional: `author`, `license`, `repository`, `integrity`). **플러그인을 건드리는 모든 PR마다 `version` bump** — SemVer 따름: major = 공개 표면 제거/이름 변경 또는 agent 계약 breaking; minor = 새 command/skill/agent/hook 또는 추가 capability; patch = fix, 오타, prompt 조임, persona checklist 확장. Bump 누락은 cache key를 silent stale.
- **v1.0.0부터 `CHANGELOG.md`.** entry는 `## [version] — YYYY-MM-DD`에 Added/Changed/Deprecated/Removed/Fixed/Security 서브섹션. Breaking change는 migration note. 제거 전 one-minor deprecation window.
- **`README.md`에 "Principles Instantiated" 리스트** — 이 플러그인이 embody하는 20+ 원칙 중 어떤 것을, 한 줄 설명과 함께. 필수. 이것이 compounding substrate (Law 3) — 미래의 플러그인 README 전체 검색이 모든 원칙의 instantiation을 찾음.
- **Scoped agents.** 모든 agent는 명시적 `allowedTools`/`disallowedTools`를 가짐. default-everything으로 도는 agent 없음. 역할 프롬프트는 *"You are X. You are responsible for Y. You are NOT responsible for Z."*로 시작. 쓰기 권한이 있는 리뷰어는 버그 (Law 2).
- **최소 버전이 선언된 의존성.** `other-plugin:agent-name`을 dispatch하는 플러그인은 README prerequisites에 `other-plugin`을 최소 버전과 함께 리스트. Silent coupling은 버그. 보안-critical 의존성은 `plugin.json`의 optional `integrity` field로 git SHA 또는 tag에 pin.
- **Loud logging을 동반한 graceful degradation.** 누락된 optional 의존성은 capability를 downgrade, crash하지 않음. 사용자는 출력으로 fallback이 돌았는지 알 수 있어야 함.
- **모든 스킬에 `cost_class` 선언.** worst-case 동작 기반으로 `low` | `medium` | `high` | `variable`. `high` 스킬은 지출 전 명시적 `AskUserQuestion` 승인 게이트를 invoke해야 함. sub-agent를 dispatch할 때 fan-out factor N을 `<Use_When>`에 선언. N ≥ 5는 hard review 게이트.
- **JSON이 아니라 마크다운 state.** 플러그인 state는 `.claude/<plugin>.local.md`에 YAML frontmatter + 내러티브 body로 살음. **`.claude/*.local.md`는 리포 루트에서 git-ignore됨** — state 파일은 경로, branch 이름, PR URL을 담을 수 있고 commit되어선 안 됨. **State 파일에 secret (토큰, API key, 풀 PII) 기록 금지**; placeholder 참조 사용. State 파일은 성공 시 auto-delete, 실패 시 디버깅을 위해 보존.
- **Kill switch.** 플러그인이 설치하는 모든 훅은 opt-out을 가짐: `DEVBREW_DISABLE_<PLUGIN>=1` 또는 `DEVBREW_SKIP_HOOKS=<plugin>:<hook-name>`. 중요한 하니스 동작은 override 가능해야 함. Kill switch는 보안 컨트롤이기도 함 — 어떤 훅도 자신의 kill switch 존중을 거부할 수 없음.
- **훅 공존.** 같은 event 내 훅은 교환 가능해야 함 — 다른 플러그인이 같은 event를 훅해도 망가지지 않음. Signal tag는 `<{plugin}-signal>` 네임스페이스 사용. `SessionStart` 훅은 read-only 조언자, 절대 mutate 안 함. 설치된 모든 훅은 README의 "Hooks Installed" 섹션에 "왜 이것이 skill이 될 수 없는가"의 한 줄 justification과 함께 문서화.
- **스킬에 progressive disclosure.** 스킬 이름은 동명사 (`running-quality-gates`, `authoring-specs`). command 이름은 짧은 명령형 (`qg`, `review`). 선언적 trigger, `<Good>`/`<Bad>` anti-example이 있는 완전한 계약으로서의 skill body. 모호한 이름 (`helper`, `utils`, `"I can help you..."`) 없음.
- **Persona 파일은 보안-민감 코드.** 플러그인이 `reviewers/` 하위에 reviewer persona 파일을 shipping한다면, persona를 약화(규칙 제거, 임계치 완화)하는 PR은 보안 리뷰 대상. test-suite 편집과 같은 신중함으로 persona 편집을 treat.

## 금지 패턴 (Forbidden Patterns)

리뷰에서 발견 시 이름으로 cite. 전체 정의는 [`docs/philosophy/devbrew-harness-philosophy.md §3`](docs/philosophy/devbrew-harness-philosophy.md).

- **PRD theater** — refined되지 않는 placeholder ACs (OMC).
- **Polite stop** — 긍정적 리뷰 후 다음 액션으로 가지 않고 내러티브 요약 narrate (OMC Ralph §7). Approval gate와 구분: gate는 사용자가 redirect 가능, polite stop은 acknowledge만 가능.
- **Self-approval** — 같은 턴의 writer/reviewer (Law 2 위반).
- **Tool scoping 누락으로 인한 role leakage** — default-everything 도구 접근의 reviewer/planner/interviewer agent (Law 2 위반, AP11 참조).
- **LOC가 성공 metric** — 결과가 아니라 volume 보상.
- **Trivia ceremony** — 한 문장 diff에 full pipeline 실행 (Anthropic *Best Practices*).
- **Production의 프레임워크 추상화** — Claude Code primitive를 감싸는 DSL과 클래스 계층 (Anthropic *Building Effective Agents*).
- **모호한 skill 이름** — `helper`, `utils`, `"I can help you..."`.
- **Subagent spray** — trivia에 대한 fan-out; single-agent를 default로, multi-agent는 justify. 선언 없는 N ≥ 5 fan-out은 review 게이트.
- **Unbounded autonomy** — max-iteration count, wall-clock budget, repeat 감지, 사용자-override kill switch 없는 루프 (AP16 참조). OMC의 Sisyphus framing 거부.
- **Unchallenged consensus** — 여러 리뷰어가 agree하거나 루프가 converge할 때 다음 pass는 rubber stamp가 아니라 adversarial이어야 함 (AP14 참조). Agreement는 공격의 초대, bypass가 아님.
- **Chat-only state** — 대화에만 있는 사실은 compaction 후 죽음.
- **Silent fallback demotion** — optional-dep fallback은 loudly log해야 함.
- **Both-models-agree-therefore-correct** — agreement는 signal, proof가 아님 (gstack ETHOS).
- **선언되지 않은 플러그인 의존성** — prerequisites에 리스트 없이 `other-plugin:agent-name` dispatch.
- **Stale pre-built indexes** — vector store 없음, RAG 없음, cached AST 없음. Glob + grep, just-in-time, 매번 (Anthropic *Effective Context Engineering*).
- **State 파일의 secret** — state 파일 (`.claude/*.local.md`)은 의도치 않게 공유될 수 있음. 토큰/API-key/풀-PII 기록 금지; placeholder 참조 사용 (P21).
- **선언되지 않은 `cost_class`** — frontmatter에 `cost_class` 선언 없이 multi-model 또는 N-parallel 비용을 incur할 수 있는 스킬은 review 게이트 (P22).
- **v1.0.0+ 플러그인의 CHANGELOG 누락** — v1.0.0 이상 플러그인이 CHANGELOG entry 없이 PR을 shipping하는 것은 review 게이트 (P23).

## Git Workflow

GitHub Flow. `main`에서 분기, PR로 다시 merge. 상세는 [`docs/git-workflow/`](docs/git-workflow/).

- Branch: `main`에서 `feature/*` 또는 `fix/*`. Kebab-case, 2-4 단어.
- Commit: Conventional Commits (`<type>(<scope>): <description>`).
- PR: squash merge. [`docs/git-workflow/pr-process.md`](docs/git-workflow/pr-process.md) 참조.
- `project-init` 플러그인이 branch 이름과 commit format을 자동 검증.
- `main`에서 feature branch를 업데이트할 때 `git rebase`보다 `git merge` 선호.
- Default `gh pr merge --squash --delete-branch`; squash merge 후 로컬 branch도 force-delete.

## 언어 & 번역

CLAUDE.md와 `docs/philosophy/*.md`는 **영어를 canonical 버전**으로 authoring. 한국어 번역은 `*.ko.md` 동반 파일로 살며 **full content parity** — 요약 아님, gloss 아님. 모든 원칙, anti-pattern, 금지 패턴, load-bearing 인용이 양쪽 버전에 존재. 한국어 `*.ko.md`는 영어 소스를 건드리는 **같은 PR**에서 업데이트됨. 한쪽만 업데이트하는 PR은 리뷰에서 거절. 언어 drift 없음.

## 이 리포를 편집할 때

- `plugins/<name>/`를 건드리는 모든 PR에 **플러그인 version bump**.
- 영어 소스와 같은 PR에서 **`<plugin>.ko.md` 업데이트** (요약이 아니라 full content parity).
- 새 플러그인은 README에 **어떤 철학 원칙을 instantiate하는지 cite** (예: *"Laws 1 and 2를 gate-based pipeline dispatch로 구현"*).
- **버그가 리뷰를 탈출하면**, 해결책은 잡았어야 할 reviewer persona 파일을 편집하는 것. 코드만 패치하는 게 아님. 그 commit이 compounding 이벤트 (Law 3).

## References

- [`docs/philosophy/devbrew-harness-philosophy.md`](docs/philosophy/devbrew-harness-philosophy.md) — 전체 철학 (영어): 20+ 원칙, 17 anti-pattern, 10 primitive, 6 tension with pick, attribution map, 원문 인용.
- [`docs/philosophy/devbrew-harness-philosophy.ko.md`](docs/philosophy/devbrew-harness-philosophy.ko.md) — 한국어 동반 파일.
- [`docs/git-workflow/`](docs/git-workflow/) — branching, commit, PR process.
- [`plugins/quality-gates/README.md`](plugins/quality-gates/README.md) — 3-gate pipeline으로 Laws 1–2를 구현하는 레퍼런스 — pr-review-toolkit, feature-dev, superpowers agent에 dispatch.
- [`plugins/project-init/README.md`](plugins/project-init/README.md) — git-workflow enforcement과 branch/commit validation.
