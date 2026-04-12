# project-init

GitHub Flow git workflow plugin for Claude Code. Defines branch naming conventions, branch lifecycle rules, and PR process.

## Architecture

```
plugins/project-init/
├── .claude-plugin/plugin.json       # Plugin metadata
├── README.md                        # This file
├── commands/
│   └── project-init.md              # /project-init [show|branch|pr]
├── hooks/
│   ├── hooks.json                   # PostToolUse hook config
│   └── post-tool-use.py             # Branch naming validator
└── skills/
    └── git-workflow/
        ├── SKILL.md                 # Git workflow rules
        └── references/
            └── branch-naming.md     # Branch naming details
```

## Features

| Component | Role |
|-----------|------|
| **git-workflow skill** | Core workflow rules — Claude references this for all git decisions |
| **PostToolUse hook** | Validates branch naming on `git checkout -b` / `git switch -c` |
| **`/project-init` command** | User entry point — show rules, create branches, guide PR creation |

## Git Workflow Rules

- **Branch model**: GitHub Flow (`main` + `feature/*` / `fix/*`)
- **Branch unit**: One branch per plugin (e.g., `feature/project-init`)
- **Branch naming**: `feature/<name>` or `fix/<name>` (kebab-case)
- **Branch lifecycle**: Create from `main`; rebase from `main` when continuing work
- **PR process**: Branch → Work → Push → `gh pr create` → Review → Merge

## Integration

Works alongside `quality-gates` plugin — when `gh pr create` runs, quality-gates auto-triggers its 3-gate pipeline.

## Usage

```
/project-init              # Show workflow rules
/project-init branch <n>   # Create branch from main
/project-init pr           # Guide PR creation
```
