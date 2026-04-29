#!/usr/bin/env python3
"""SessionStart hook: advisory only — never mutates state.

Prints a one-line message to stdout if a /qg pipeline appears in-flight.
Honors CLAUDE.md rule: SessionStart hooks are read-only advisors.

Kill switch: DEVBREW_DISABLE_QUALITY_GATES=1
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

STATE_FILE = Path(".claude/quality-gates.local.md")
ACTIVE_STATUSES = {"active", "in_progress", "running"}


def main() -> int:
    if os.environ.get("DEVBREW_DISABLE_QUALITY_GATES") == "1":
        return 0
    if not STATE_FILE.exists():
        return 0
    try:
        text = STATE_FILE.read_text()
    except OSError:
        return 0
    m = re.search(r"^status:\s*(\S+)", text, re.MULTILINE)
    if not m or m.group(1).strip().lower() not in ACTIVE_STATUSES:
        return 0
    sys.stdout.write(
        "[quality-gates] In-flight pipeline detected. Run `/qg` to resume "
        "or `/qg --reset` to clear.\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
