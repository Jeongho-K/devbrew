#!/usr/bin/env python3
"""1회용 스윕 (v0.55.0) — audit fixture 의 닫힌 원장 행에 실재 S 앵커를, §2 Budget 에
`coverage-mapper 1` 을 주입한다. 판정을 바꾸지 않는다 — 실행 전후 test_check_brief.sh 의
ok/no 집합이 같아야 한다. 재실행은 멱등이다(이미 앵커·토큰이 있으면 건드리지 않는다).

usage: python3 sweep_anchor_fixtures.py [<fixtures-dir>]   (기본: 이 파일의 디렉토리)
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))
import check_brief as cb  # noqa: E402

ANCHOR_RE = re.compile(r"(?<![A-Za-z])S\d+\b")
ROW_RE = re.compile(r"^(\s*[-*]\s+)((?:floor:\w+|derived:[^—]+?)\s*—\s*closed\s*—\s*)(.*?)(\s*)$")
MAPPER_RE = re.compile(r"coverage-mapper\s+\d+")


def pick_anchor(payload_text: str, audit_text: str) -> str:
    anchors = cb.verbatim_anchors(audit_text)
    if payload_text:
        anchors |= cb.payload_verbatim_anchors(payload_text)
    nums = sorted(int(a[1:]) for a in anchors if a[1:].isdigit())
    return f"S{nums[0]}" if nums else "S1"


def sweep_audit(audit: Path) -> tuple[int, int]:
    text = audit.read_text(encoding="utf-8")
    fm = cb._frontmatter(text)
    m = re.search(r"^payload:\s*(\S+)\s*$", fm, re.MULTILINE)
    payload_text = ""
    if m and (audit.parent / m.group(1)).is_file():
        payload_text = (audit.parent / m.group(1)).read_text(encoding="utf-8")
    anchor = pick_anchor(payload_text, text)
    sec1 = cb._section_text(text, "1", "Coverage Ledger")
    rows = 0
    if sec1.strip():
        new_lines = []
        for ln in text.splitlines():
            r = ROW_RE.match(ln)
            if (
                r
                and ln in sec1
                and r.group(3).strip()
                and not ANCHOR_RE.search(r.group(3))
            ):
                ln = f"{r.group(1)}{r.group(2)}{r.group(3)} (@{anchor})"
                rows += 1
            new_lines.append(ln)
        text = "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")
    sec2 = cb._section_text(text, "2", "Budget")
    budget = 0
    if sec2.strip() and not MAPPER_RE.search(sec2):
        hdr = re.search(r"^##\s+2\.\s+Budget[^\n]*\n", text, re.MULTILINE)
        text = text[:hdr.end()] + "\n- agent dispatch: coverage-mapper 1\n" + text[hdr.end():]
        budget = 1
    if rows or budget:
        audit.write_text(text, encoding="utf-8")
    return rows, budget


def main(argv: list[str]) -> int:
    d = Path(argv[1]) if len(argv) > 1 else HERE
    tot_rows = tot_budget = files = 0
    for a in sorted(d.glob("*.audit.md")):
        r, b = sweep_audit(a)
        if r or b:
            files += 1
        tot_rows += r
        tot_budget += b
    print(f"files_touched={files} rows_anchored={tot_rows} budget_lines_added={tot_budget}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
