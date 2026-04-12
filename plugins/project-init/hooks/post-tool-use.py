#!/usr/bin/env python3
"""PostToolUse hook for project-init plugin.

Detects branch creation commands (git checkout -b, git switch -c) and
validates branch naming against the convention: feature/* or fix/*.
Warns via systemMessage if the name doesn't match — does not block.
"""

import json
import re
import sys

BRANCH_PATTERN = re.compile(r"^(feature|fix)/[\w.-]+$")
BRANCH_CREATE_PATTERN = re.compile(
    r"git\s+(?:checkout\s+-b|switch\s+-c)\s+(\S+)"
)


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        print(json.dumps({}))
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name != "Bash":
        print(json.dumps({}))
        sys.exit(0)

    command = tool_input.get("command", "")

    match = BRANCH_CREATE_PATTERN.search(command)
    if not match:
        print(json.dumps({}))
        sys.exit(0)

    branch_name = match.group(1)

    # Allow main branch checkout (not really creation, but defensive)
    if branch_name == "main":
        print(json.dumps({}))
        sys.exit(0)

    if BRANCH_PATTERN.match(branch_name):
        print(json.dumps({}))
        sys.exit(0)

    # Suggest correction: strip any wrong prefix and re-add feature/
    suggestion = branch_name
    if "/" in suggestion:
        # Has a wrong prefix like bugfix/ or feat/ — strip it
        suggestion = suggestion.split("/", 1)[1]
    suggestion = f"feature/{suggestion}"

    result = {
        "systemMessage": (
            f'project-init: Branch "{branch_name}" does not follow naming convention.\n'
            f"Expected: feature/<description> or fix/<description>\n"
            f"Suggested: git branch -m {suggestion}"
        )
    }

    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()
