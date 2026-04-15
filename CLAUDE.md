# CLAUDE.md

> **Specify before you code. Review before you ship. Compound before you forget.**
>
> *The bottleneck is not the model. It's the spec, the review, and the memory. devbrew's job is to fix all three without the user having to remember to.*

devbrew is a plugin marketplace for Claude Code. Every plugin under `plugins/*` inherits the principles below. The full harness philosophy — with attribution, anti-pattern library, and direct quotes from the four source harnesses (oh-my-claudecode, gstack, ouroboros, compound-engineering) plus Anthropic's engineering writing — lives at [`docs/philosophy/devbrew-harness-philosophy.md`](docs/philosophy/devbrew-harness-philosophy.md). This file is the preloaded context anchor: tight enough to earn its slot, dense enough to guide every plugin decision.

## The Three Laws

**Law 1 — Clarity Before Code.** No implementation proceeds while the spec is ambiguous. Every plugin that ships code must have a real refusal mechanism — at minimum a **structural gate** (mandatory sections: Context/Why, Goals, Non-goals, Constraints, Acceptance Criteria, Files to Modify, Verification Plan, Rejected Alternatives, Metadata) that the plugin cannot silently skip. Adversarial self-review is strongly recommended on top of the structural baseline; numerical scoring is allowed but discouraged (see philosophy doc §5.3). *Trivia escape:* changes whose **diff can be described in one sentence** (Anthropic, *Claude Code Best Practices*) bypass the gate — typos, renames, comment-only edits, single-file formatting. Anything multi-file or behavior-changing goes through.

**Law 2 — Writer and Reviewer Must Never Share a Pass.** The same turn that writes code may not approve it. Isolation is physical, not prompted: use `allowed-tools` / `disallowed-tools` frontmatter so a reviewer literally cannot `Write`/`Edit`. A reviewer with write access is not a reviewer. Verification is load-bearing infrastructure, not an afterthought — invest in making it rock-solid.

**Law 3 — Every Cycle Must Leave the System Smarter.** Compounding is a named step with a discoverability check, not an optional wrap-up. When a cycle produces a lesson, the harness captures it to a file AND verifies the next session will actually find it — auto-editing the index (`AGENTS.md`/`CLAUDE.md`) when discoverability is at risk. Writing to a file no future agent reads is theater.

*Hierarchy:* Law N overrides Law N+1 on conflict. Clarity first, independence second, compounding third.

## Plugin Shape

Every plugin in `plugins/*` follows the canonical directory structure in [`docs/philosophy/devbrew-harness-philosophy.md §4.0`](docs/philosophy/devbrew-harness-philosophy.md) and satisfies all of the following:

- **`.claude-plugin/plugin.json`** with required `name`, `description`, `version` (optional: `author`, `license`, `repository`, `integrity`). **Bump `version` on every PR that touches the plugin** following SemVer: major = removing/renaming a public surface or breaking an agent contract; minor = new command/skill/agent/hook or additive capability; patch = fix, typo, prompt tightening, persona checklist expansion. Missed bumps silently stale cache keys.
- **`CHANGELOG.md` once the plugin hits v1.0.0.** Entries follow `## [version] — YYYY-MM-DD` with Added/Changed/Deprecated/Removed/Fixed/Security subsections. Breaking changes carry a migration note. One-minor deprecation window before any removal.
- **`README.md` lists "Principles Instantiated"** — which of the philosophy's 20+ principles this plugin embodies, one line each. Required. This is a compounding substrate (Law 3) — future search across plugin READMEs finds every instantiation of a principle.
- **Scoped agents.** Every agent has explicit `allowedTools`/`disallowedTools`; no agent runs with default-everything. Role prompts begin with *"You are X. You are responsible for Y. You are NOT responsible for Z."* A reviewer with Write access is a bug (Law 2).
- **Declared dependencies with minimum versions.** Any plugin that dispatches `other-plugin:agent-name` lists `other-plugin` in its README prerequisites with a minimum version. Silent coupling is a bug. For security-critical dependencies, pin to a git SHA or tag via `plugin.json`'s optional `integrity` field.
- **Graceful degradation with loud logging.** Missing optional dependencies downgrade capability, not crash. The user must be able to tell, from the output, that a fallback ran.
- **`cost_class` declared for every skill.** `low` | `medium` | `high` | `variable` based on worst-case behavior. `high` skills must invoke an explicit `AskUserQuestion` approval gate before spending. Fan-out factor N declared in `<Use_When>` when sub-agents are dispatched; N ≥ 5 is a hard review gate.
- **Markdown state, not JSON.** Plugin state lives in `.claude/<plugin>.local.md` with YAML frontmatter + narrative body. **`.claude/*.local.md` is git-ignored at repo root** — state files can contain paths, branch names, PR URLs and must not be committed. **Never write secrets (tokens, API keys, full PII) to state files**; use placeholder references instead. State files are auto-deleted on success, preserved on failure for debugging.
- **Kill switches.** Every hook this plugin installs has an opt-out: `DEVBREW_DISABLE_<PLUGIN>=1` or `DEVBREW_SKIP_HOOKS=<plugin>:<hook-name>`. Harness behavior that matters must be overridable. Kill switches are also security controls — no hook may refuse to respect its kill switch.
- **Hook coexistence.** Hooks must be commutative within the same event — another plugin may hook the same event without breaking yours. Signal tags use `<{plugin}-signal>` namespace. `SessionStart` hooks are read-only advisors, never mutate. Each installed hook is documented in the README's "Hooks Installed" section with a one-line "why this couldn't be a skill" justification.
- **Progressive disclosure for skills.** Skill names are gerunds (`running-quality-gates`, `authoring-specs`); command names are short imperatives (`qg`, `review`). Declarative triggers, skill bodies as complete contracts with `<Good>`/`<Bad>` anti-examples. No vague names (`helper`, `utils`, `"I can help you..."`).
- **Persona files are security-sensitive code.** If the plugin ships reviewer persona files under `reviewers/`, PRs that weaken a persona (remove a rule, relax a threshold) are flagged for security review. Treat persona edits with the same care as test-suite edits.

## Forbidden Patterns

Cite these by name when found in reviews. Full definitions in [`docs/philosophy/devbrew-harness-philosophy.md §3`](docs/philosophy/devbrew-harness-philosophy.md).

- **PRD theater** — placeholder acceptance criteria that never get refined (OMC).
- **Polite stop** — narrating a summary after a positive review instead of proceeding to the next action (OMC Ralph §7). Distinct from an approval gate: a gate lets the user redirect; a polite stop only lets them acknowledge.
- **Self-approval** — writer and reviewer in the same turn (Law 2 violation).
- **Role leakage via missing tool scoping** — a reviewer/planner/interviewer agent with default-everything tool access (Law 2 violation, see AP11).
- **LOC as success metric** — rewarding volume instead of outcome.
- **Trivia ceremony** — running the full pipeline on a one-sentence diff (Anthropic *Best Practices*).
- **Framework abstraction in production** — DSLs and class hierarchies wrapping Claude Code primitives (Anthropic *Building Effective Agents*).
- **Vague skill names** — `helper`, `utils`, `"I can help you..."`.
- **Subagent spray** — fan-out for trivia; default to single-agent, justify multi-agent. Fan-out ≥ 5 without declared justification is a review gate.
- **Unbounded autonomy** — a loop without a max-iteration count, wall-clock budget, repeat detection, and user-override kill switch (see AP16). OMC's Sisyphus framing rejected.
- **Unchallenged consensus** — when multiple reviewers agree or a loop converges, the next pass must be adversarial, not a rubber stamp (see AP14). Agreement is an invitation to attack, not a bypass.
- **Chat-only state** — facts only in the conversation are dead after compaction.
- **Silent fallback demotion** — optional-dep fallbacks must log loudly.
- **Both-models-agree-therefore-correct** — agreement is signal, not proof (gstack ETHOS).
- **Undeclared plugin dependencies** — dispatching `other-plugin:agent-name` without listing it in prerequisites.
- **Stale pre-built indexes** — no vector stores, no RAG, no cached ASTs. Glob + grep, just-in-time, every time (Anthropic *Effective Context Engineering*).
- **Secrets in state files** — state files (`.claude/*.local.md`) may be shared accidentally. Never write tokens/API-keys/full-PII; use placeholder references (P21).
- **Undeclared `cost_class`** — a skill that may incur multi-model or N-parallel cost without a declared `cost_class` in its frontmatter is a review gate (P22).
- **Missing CHANGELOG for v1.0.0+ plugins** — a plugin at or above v1.0.0 that ships a PR without a CHANGELOG entry is a review gate (P23).

## Git Workflow

GitHub Flow. Branch from `main`, merge back via PR. Details in [`docs/git-workflow/`](docs/git-workflow/).

- Branch: `feature/*` or `fix/*` from `main`. Kebab-case, 2-4 words.
- Commit: Conventional Commits (`<type>(<scope>): <description>`).
- PR: squash merge. See [`docs/git-workflow/pr-process.md`](docs/git-workflow/pr-process.md).
- `project-init` plugin auto-validates branch naming and commit format.
- Prefer `git merge` over `git rebase` when updating feature branches from `main`.
- Default `gh pr merge --squash --delete-branch`; force-delete local branch after squash merge.

## Language & Translations

CLAUDE.md and `docs/philosophy/*.md` are authored in **English as the canonical version**. Korean translations live as `*.ko.md` companions with **full content parity** — not summaries, not glosses. Every principle, anti-pattern, forbidden pattern, and load-bearing quote appears in both versions. The Korean `*.ko.md` is updated **in the same PR** that touches the English source; a PR that updates one without the other is rejected in review. No language drift.

## When Editing This Repo

- **Bump plugin version** on every PR that touches `plugins/<name>/`.
- **Update `<plugin>.ko.md`** in the same PR as the English source (full content parity, not a summary).
- **New plugins cite which philosophy principles they instantiate** in their README (e.g., *"Implements Laws 1 and 2 via gate-based pipeline dispatch"*).
- **When a bug escapes review**, the fix is to edit the reviewer persona file that should have caught it, not just patch the code. That commit is the compounding event (Law 3).

## References

- [`docs/philosophy/devbrew-harness-philosophy.md`](docs/philosophy/devbrew-harness-philosophy.md) — full philosophy: 20+ principles, 17 anti-patterns, 10 primitives, 6 tensions with picks, attribution map, direct quotes preserved verbatim.
- [`docs/philosophy/devbrew-harness-philosophy.ko.md`](docs/philosophy/devbrew-harness-philosophy.ko.md) — Korean companion.
- [`docs/git-workflow/`](docs/git-workflow/) — branching, commits, PR process.
- [`plugins/quality-gates/README.md`](plugins/quality-gates/README.md) — reference implementation of Laws 1–2 via a 3-gate pipeline that dispatches to pr-review-toolkit, feature-dev, and superpowers agents.
- [`plugins/project-init/README.md`](plugins/project-init/README.md) — git-workflow enforcement and branch/commit validation.
