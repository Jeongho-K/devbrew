---
name: quality-pipeline
description: >
  This skill should be used when the user wants to run quality gates, verify code
  quality, check PR readiness, or run the QG pipeline. Triggered by commands like
  "/qg", "run quality gates", "verify my implementation", "check code quality",
  "is my PR ready to merge", or automatically on PR creation via hook. Executes a
  single gate per turn; the Stop hook manages pipeline progression automatically.
---

# Quality Gates — Gate Executor

You are executing a **single gate** of the quality pipeline. The Stop hook manages
pipeline progression (gate-to-gate transitions, iteration counting, loop-back on
code changes). You do NOT manage state files or pipeline flow.

## Arguments

Parse the following from the prompt parameters:

- `gate`: Which gate to execute (1, 2, or 3)
- `plan_path`: Plan file path (or "auto")
- `pr_url`: PR URL (optional)
- `available_plugins`: Comma-separated list of available plugins
- `iteration`: Current Gate 2 iteration number (Gate 2 only)
- `max_iterations`: Maximum Gate 2 iterations (Gate 2 only)
- `previous_findings`: Summary from last Gate 2 iteration (Gate 2 only)

If this is the first gate invocation (no parameters in the prompt), determine the gate
from any `/qg` arguments (gate1, gate2, gate3) or default to gate=1.

## Dependency Check

If `available_plugins` is provided in the prompt parameters, use it directly.

Otherwise (first invocation only), run the pre-flight dependency checks per
[references/dependency-check.md](references/dependency-check.md) to build the
`available_plugins` list.

## Gate Execution

### Gate 1: Plan Verification

Dispatch the plan-verifier agent:

```
Agent(
  subagent_type="quality-gates:plan-verifier",
  prompt="Verify plan implementation completeness.
    plan_path: <plan_path or 'auto'>
    project_dir: <current working directory>
    available_plugins: <available_plugins list>"
)
```

Read the agent's report. Check the Verdict line.

**Evidence-Based Verification (conditional):**

If `available_plugins` includes `superpowers` AND the plan-verifier report
contains items in "Likely implemented" or "Possibly implemented" status:

```
Skill("superpowers:verification-before-completion")
```

Follow the skill's gate function:
1. IDENTIFY: Determine which command proves the implementation works
2. RUN: Execute the full command
3. READ: Check full output and exit code
4. VERIFY: Does the output confirm the implementation?

Integrate evidence into Gate 1's verdict.
Note: This step executes commands but does NOT modify any code.

**Output Gate 1 result to user:**
```
## Gate 1: Plan Verification — [PASS/FAIL/SKIP]
[verdict explanation]
[key findings summary]
[evidence-based verification results, if executed]
```

**Handle verdict:**
- PASS → emit signal with verdict="PASS"
- SKIP → emit signal with verdict="SKIP"
- FAIL →
  Report blocking gaps to the user.
  Ask: "N blocking items remain. Should I implement them, or proceed anyway?"
  - If implement: implement the items, then emit signal with verdict="RETRY"
  - If proceed: emit signal with verdict="PASS_WITH_WARNINGS"

### Gate 2: PR Review

Dispatch the pr-reviewer agent:

```
Agent(
  subagent_type="quality-gates:pr-reviewer",
  prompt="Run iterative PR review.
    pr_url: <pr_url>
    max_iterations: <max_iterations>
    iteration: <iteration>
    project_dir: <current working directory>
    previous_findings: <previous_findings or 'none'>
    available_plugins: <available_plugins list>
    plan_path: <plan_path or empty>"
)
```

Read the agent's report. Check the Verdict line.

**Output Gate 2 result to user:**
```
## Gate 2: PR Review (iter [iteration]) — [PASS/FAIL/NEEDS_RESTART]
[verdict explanation]
[agents run and key findings]
```

**Handle verdict:**
- PASS → emit signal with verdict="PASS"
- NEEDS_RESTART → emit signal with verdict="NEEDS_RESTART"
- FAIL → emit signal with verdict="FAIL"

### Gate 3: Runtime Verification

Dispatch the runtime-verifier agent:

```
Agent(
  subagent_type="quality-gates:runtime-verifier",
  prompt="Verify application runtime behavior.
    project_dir: <current working directory>
    plan_path: <plan_path>
    project_type: auto
    app_start_command: auto
    app_url: auto"
)
```

Read the agent's report. Check the Verdict line.

**Output Gate 3 result to user:**
```
## Gate 3: Runtime Verification — [PASS/FAIL/SKIP/NEEDS_RESTART]
[verdict explanation]
[checks performed and results]
```

**Handle verdict:**
- PASS → emit signal with verdict="PASS"
- SKIP → emit signal with verdict="SKIP"
- NEEDS_RESTART → emit signal with verdict="NEEDS_RESTART"
- FAIL → emit signal with verdict="FAIL"

## Special Prompts from Stop Hook

The Stop hook may inject special prompts that start with keywords.
Handle them as follows:

### MAX_TOTAL_ITERATIONS_EXCEEDED

Pipeline exceeded maximum total iterations. Present to user:
1. **Extend** — add 3 more iterations
2. **Accept as-is** — proceed with current state
3. **Abort** — stop pipeline

Based on choice:
- Extend: `<qg-signal action="extend" additional="3" />`
- Accept: `<qg-signal action="complete" />`
- Abort: `<qg-signal action="abort" reason="User chose to abort" />`

### GATE2_MAX_EXCEEDED

Gate 2 exceeded maximum review iterations. Report remaining issues and present:
1. **Proceed to Gate 3** anyway
2. **Abort** pipeline

Based on choice:
- Proceed: `<qg-signal gate="2" verdict="PASS_WITH_WARNINGS" summary="Proceeding with remaining issues" files_changed="" />`
- Abort: `<qg-signal action="abort" reason="User chose to abort" />`

### GATE3_FAIL

Gate 3 failed. Present:
1. **Fix issues** (will restart from Gate 1)
2. **Skip** runtime verification
3. **Abort** pipeline

Based on choice:
- Fix: fix the issues, then `<qg-signal gate="3" verdict="NEEDS_RESTART" summary="Fixed runtime issues" files_changed="list,of,changed,files" />`
- Skip: `<qg-signal gate="3" verdict="SKIP" summary="User chose to skip" files_changed="" />`
- Abort: `<qg-signal action="abort" reason="User chose to abort" />`

## Final Summary

When the Stop hook signals this is the last gate (no more gates after this),
output the final pipeline summary:

```
## Quality Gates Pipeline — Complete

### Gate Results
| Gate | Status | Details |
|------|--------|---------|
| 1. Plan Verification | [status] | [details] |
| 2. PR Review | [status] | [details] |
| 3. Runtime Verification | [status] | [details] |

### Summary of Changes Made
- [file]: [what was changed] (Gate N)

PR is ready for merge.
```

## Signal Tag Rules

After each gate completes, you **MUST** output a signal tag. This is how the Stop
hook knows what happened and what to do next.

**Gate completion signals:**
```xml
<qg-signal gate="N" verdict="VERDICT" summary="one-line summary" files_changed="comma,separated,list" />
```

Verdict values:
- `PASS` — Gate succeeded, no issues
- `FAIL` — Gate failed, issues remain
- `SKIP` — Gate skipped (no plan file, non-web project, etc.)
- `NEEDS_RESTART` — Code was changed, pipeline should restart from Gate 1
- `PASS_WITH_WARNINGS` — Gate passed with non-blocking warnings
- `RETRY` — Gate needs to re-run (Gate 1 implemented missing items)

For Gate 2, include the `iteration` attribute:
```xml
<qg-signal gate="2" verdict="PASS" iteration="3" summary="All issues resolved" files_changed="" />
```

**Pipeline control signals:**
```xml
<qg-signal action="complete" />
<qg-signal action="abort" reason="description" />
<qg-signal action="extend" additional="3" />
```

## Rules

- NEVER write to or read from `.claude/quality-gates.local.md` — the Stop hook manages it
- ALWAYS emit exactly one `<qg-signal>` tag at the end of your response
- Output each gate's result to the user immediately
- If an agent dispatch fails (error), report the error and emit signal with verdict="FAIL"
- The `files_changed` attribute must list every file modified during this gate (comma-separated), or empty string if none
- The `summary` attribute should be a concise one-line description of the gate result
