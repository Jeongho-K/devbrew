---
description: "Run the quality gates pipeline (plan verification → PR review → runtime verification)"
argument-hint: "[gate1|gate2|gate3] [--skip-runtime] [--plan <path>] [--pr-url <url>]"
allowed-tools: ["Bash(${CLAUDE_PLUGIN_ROOT}/scripts/setup-qg.sh:*)", "Agent", "Skill", "Bash", "Read", "Edit", "Write", "Glob", "Grep"]
---

# Quality Gates Pipeline

Run the 3-gate quality verification pipeline to ensure code quality before PR merge.

**Arguments:** $ARGUMENTS

## Instructions

Execute the setup script to initialize the pipeline:

```!
"${CLAUDE_PLUGIN_ROOT}/scripts/setup-qg.sh" $ARGUMENTS
```

Now invoke `Skill("quality-gates:quality-pipeline")` with gate=1 (or the gate specified in $ARGUMENTS) to begin the first gate.

When you finish the gate, emit a `<qg-signal>` tag. The Stop hook handles pipeline progression automatically.

### Quick Reference

| Command | Effect |
|---------|--------|
| `/qg` | Full pipeline (Gate 1 → 2 → 3) |
| `/qg gate1` | Plan verification only |
| `/qg gate2` | PR review only |
| `/qg gate3` | Runtime verification only |
| `/qg --skip-runtime` | Gates 1 & 2 only (skip runtime) |
| `/qg --plan <path>` | Use specific plan file |
| `/qg --pr-url <url>` | Specify PR URL |
| `/cancel-qg` | Cancel active pipeline |

### Gates

1. **Plan Verification** — Checks all planned items are implemented
2. **PR Review** — Iterative code review using pr-review-toolkit (review → fix → re-review)
3. **Runtime Verification** — Launches app and verifies behavior with browser automation

### Pipeline Rules

- Pipeline progression managed by Stop hook (no manual gate transitions needed)
- If any gate requires code changes → automatic restart from Gate 1
- Gate 2 iterates up to 5 times internally
- Full pipeline restarts up to 5 times
- State tracked in `.claude/quality-gates.local.md` (managed by hook scripts)
