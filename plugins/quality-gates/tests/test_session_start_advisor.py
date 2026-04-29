"""Tests for the SessionStart advisor (read-only)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "hooks" / "session-start-advisor.py"

ACTIVE_STATE = """---
status: active
current_gate: 2
total_iterations: 1
---
# Quality Gates Pipeline State
"""

DONE_STATE = """---
status: done
current_gate: 3
---
# Quality Gates Pipeline State
"""


def run_advisor(cwd):
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({}),
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return proc


class TestAdvisor(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.tmp, ".claude"), exist_ok=True)

    def test_no_state_silent(self):
        proc = run_advisor(self.tmp)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")

    def test_active_state_prints_one_liner(self):
        Path(self.tmp, ".claude/quality-gates.local.md").write_text(ACTIVE_STATE)
        proc = run_advisor(self.tmp)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("/qg", proc.stdout)
        self.assertIn("--reset", proc.stdout)

    def test_done_state_silent(self):
        Path(self.tmp, ".claude/quality-gates.local.md").write_text(DONE_STATE)
        proc = run_advisor(self.tmp)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")

    def test_does_not_mutate_files(self):
        state_path = Path(self.tmp, ".claude/quality-gates.local.md")
        session_path = Path(self.tmp, ".claude/quality-gates-session.local.md")
        state_path.write_text(ACTIVE_STATE)
        session_path.write_text("- /a\n- /b\n")
        before = (state_path.read_text(), session_path.read_text())
        run_advisor(self.tmp)
        after = (state_path.read_text(), session_path.read_text())
        self.assertEqual(before, after)

    def test_kill_switch(self):
        Path(self.tmp, ".claude/quality-gates.local.md").write_text(ACTIVE_STATE)
        env = os.environ.copy()
        env["DEVBREW_DISABLE_QUALITY_GATES"] = "1"
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps({}),
            capture_output=True,
            text=True,
            cwd=self.tmp,
            env=env,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")


if __name__ == "__main__":
    unittest.main()
