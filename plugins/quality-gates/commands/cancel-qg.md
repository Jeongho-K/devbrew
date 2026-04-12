---
description: "Cancel active quality gates pipeline"
allowed-tools: ["Bash(test -f .claude/quality-gates.local.md:*)", "Bash(rm .claude/quality-gates.local.md)", "Read(.claude/quality-gates.local.md)"]
hide-from-slash-command-tool: "true"
---

# Cancel Quality Gates

To cancel the active quality gates pipeline:

1. Check if `.claude/quality-gates.local.md` exists using Bash: `test -f .claude/quality-gates.local.md && echo "EXISTS" || echo "NOT_FOUND"`

2. **If NOT_FOUND**: Say "No active quality gates pipeline found."

3. **If EXISTS**:
   - Read `.claude/quality-gates.local.md` to get current status from the frontmatter fields (`status`, `current_gate`, `total_iterations`)
   - Remove the file using Bash: `rm .claude/quality-gates.local.md`
   - Report: "Cancelled quality gates pipeline (was at Gate N, iteration M)"
