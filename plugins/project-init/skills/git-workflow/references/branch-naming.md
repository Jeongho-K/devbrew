# Branch Naming Convention

## Pattern

```regex
^(feature|fix)/[\w.-]+$
```

## Valid Examples

| Branch Name | Reason |
|-------------|--------|
| `feature/project-init` | New plugin |
| `feature/user-auth` | New feature |
| `feature/qg-multi-plugin-delegation` | Descriptive feature name |
| `fix/hook-timeout` | Bug fix |
| `fix/post-tool-use-output-type` | Specific fix |
| `fix/null-pointer` | Bug fix |

## Invalid Examples

| Branch Name | Problem | Correction |
|-------------|---------|------------|
| `my-branch` | Missing prefix | `feature/my-branch` |
| `Feature/auth` | Uppercase prefix | `feature/auth` |
| `feature/Add_User` | Mixed case, underscore | `feature/add-user` |
| `feat/login` | Wrong prefix abbreviation | `feature/login` |
| `bugfix/crash` | Non-standard prefix | `fix/crash` |
| `feature/a` | Too short, not descriptive | `feature/auth-module` |

## Guidelines

- **Prefix**: Only `feature/` or `fix/` (lowercase)
- **Description**: kebab-case, 2-4 words, descriptive
- **Length**: Keep the full branch name under 50 characters
- **No issue numbers** in branch names (v1)
- **No nested paths**: `feature/auth/login` is not allowed — use `feature/auth-login`
