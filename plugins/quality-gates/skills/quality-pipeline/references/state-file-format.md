# State File Format

Create/update `.claude/quality-gates.local.md` in the current project directory to track pipeline state.

**Initial state (create at pipeline start):**

```markdown
---
status: gate1
current_gate: 1
total_iterations: 1
gate2_iteration: 0
max_total_iterations: 5
max_gate2_iterations: 5
plan_file: <detected or provided plan path>
pr_url: <PR URL if provided>
started_at: "<current ISO timestamp>"
---

# Quality Gates Pipeline State

## Pipeline History
- [<timestamp>] Pipeline started (iteration 1)
```

Update this file after each gate completes. Use Edit tool to update the YAML frontmatter and append to the history section.
