---
name: git-workflow
description: >
  This skill should be used when the user wants to understand or follow the
  project's git workflow, create branches, prepare PRs, or needs guidance on
  branch strategy. Triggered by commands like "/project-init", "create a branch",
  "make a new branch", "prepare a PR", "what's the branch strategy",
  "start working on a feature", "start a new plugin", or any git workflow question.
  Encodes GitHub Flow with branch naming conventions, lifecycle rules, and PR process.
---

# Git Workflow

You are following this project's git workflow. Apply these rules when making git decisions.

## Branch Model: GitHub Flow

- `main` is the production branch — always deployable
- All work happens on short-lived `feature/*` or `fix/*` branches
- No `develop`, `release`, or `staging` branches

## Branch Naming Convention

| Prefix | Use | Example |
|--------|-----|---------|
| `feature/<name>` | New feature or plugin | `feature/project-init` |
| `fix/<name>` | Bug fix | `fix/hook-timeout` |

- Use **kebab-case** for the description
- Keep it concise: 2-4 words

See [references/branch-naming.md](references/branch-naming.md) for details and regex pattern.

## Branch Unit

Branches are created **per plugin**. Each plugin gets its own feature branch.

- New plugin → `feature/<plugin-name>` (e.g., `feature/project-init`)
- Fix in existing plugin → `fix/<description>` (e.g., `fix/post-tool-use-output-type`)

## Branch Lifecycle

### Creating a branch

Always start from latest `main`:

```bash
git checkout main
git pull origin main
git checkout -b feature/<name>
```

### Continuing work on an existing branch

When reusing a feature branch for follow-up work (not deleting after merge), sync with main first:

```bash
git checkout feature/<name>
git fetch origin
git rebase origin/main
```

Or merge approach:

```bash
git checkout feature/<name>
git fetch origin
git merge origin/main
```

### After PR merge

- Delete the branch if work is complete: `git branch -d feature/<name>`
- Or keep and rebase from main for follow-up work (see above)

## PR Process

Full flow from branch creation to merge:

1. **Create branch** from `main` (see above)
2. **Work** — make changes, commit with descriptive messages
3. **Push** to remote: `git push -u origin feature/<name>`
4. **Create PR**: `gh pr create --title "..." --body "..."`
5. **Review** — if `quality-gates` plugin is installed, the pipeline auto-triggers on `gh pr create`
6. **Address feedback** — push additional commits
7. **Merge** — after approval, merge via GitHub

## Integration with quality-gates

When `gh pr create` runs and the `quality-gates` plugin is installed:
- The PostToolUse hook auto-triggers the 3-gate quality pipeline
- This plugin handles **before PR** (branching, naming, PR creation)
- `quality-gates` handles **after PR creation** (quality verification)
- They are complementary and loosely coupled

## Rules for Claude

- **ALWAYS** check current branch before starting work: `git branch --show-current`
- **NEVER** commit directly to `main`
- **ALWAYS** use `feature/*` or `fix/*` branch naming
- When asked to "start working on X" → create a properly named branch first
- When asked to "create a PR" → follow the full PR process above
- If currently on `main` and about to make changes → STOP and create a branch first
- When switching to an existing feature branch → check if it needs rebase from main
