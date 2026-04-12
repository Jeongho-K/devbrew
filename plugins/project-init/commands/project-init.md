---
description: "Show git workflow rules, create branches, or guide PR creation"
argument-hint: "[show|branch <name>|pr]"
allowed-tools: [Bash, Read, Skill, Glob, Grep]
---

# project-init

Manage the project's git workflow: view rules, create branches, or prepare PRs.

**Arguments:** $ARGUMENTS

## Instructions

Parse the subcommand from `$ARGUMENTS`:

### `/project-init` or `/project-init show`

Display the git workflow rules by invoking the skill:

Use `Skill("project-init:git-workflow")` to load and present the workflow rules to the user.

### `/project-init branch <name>`

Create a new branch from latest `main`.

1. Validate the branch name matches `feature/*` or `fix/*` pattern
   - If not, suggest the corrected name and ask the user to confirm
2. Ensure starting from latest main:
   ```bash
   git checkout main && git pull origin main
   ```
3. Create the branch:
   ```bash
   git checkout -b <name>
   ```
4. Confirm success and remind next steps:
   > Branch `<name>` created from latest main.
   > Next: make changes, commit, then `/project-init pr` when ready.

### `/project-init pr`

Guide PR creation for the current branch.

1. Check the current branch: `git branch --show-current`
   - If on `main`, warn and stop — must be on a feature/fix branch
2. Validate branch name follows convention
3. Push to remote:
   ```bash
   git push -u origin <current-branch>
   ```
4. Create PR:
   ```bash
   gh pr create --title "..." --body "..."
   ```
   - Title: derive from branch name and recent commits
   - Body: include Summary and Test Plan sections
5. Note: if `quality-gates` plugin is installed, the quality pipeline will auto-trigger after PR creation

### Quick Reference

| Command | Effect |
|---------|--------|
| `/project-init` | Show git workflow rules |
| `/project-init show` | Show git workflow rules |
| `/project-init branch feature/my-plugin` | Create branch from main |
| `/project-init pr` | Push and create PR |
