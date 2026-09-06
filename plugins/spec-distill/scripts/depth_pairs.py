#!/usr/bin/env python3
"""depth_pairs.py — state 본문에서 «답→다음 행동» 짝을 뽑는다 (spec §3.1, v0.55.0).

usage: depth_pairs.py <state.local.md> [--sample N] [--seed STR]
  rc 0  JSON(짝·계수·사람 표본)      rc 3  {"unmeasurable": "<이유>"}      rc 2  usage
측정이지 게이트가 아니다 — 호출자는 rc 3 을 «측정 불가»로 기록하고 종료를 막지 않는다(C5).
서드파티 YAML 을 쓰지 않는다(리포 관례).
"""
import argparse
import json
import random
import re
import sys
from pathlib import Path

FM_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
ROUND_H_RE = re.compile(r"^##\s+R(\d+)\s*$", re.MULTILINE)
BLOCK_H_RE = re.compile(r"^###\s+직전 답에서\s+—\s+(.*)$")
LINE_KEYS = ("함의", "상충", "확인한 사실", "위험")
NONE_TOKENS = {"없음", "«없음»", "\"없음\"", "'없음'"}


def anchor_re(s):
    return re.compile(r"(?<![A-Za-z])" + re.escape(s) + r"\b")


def _unquote(raw):
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1].replace('\\"', '"')
    return raw


def parse_statements(fm):
    """`user_statements` → [{id, round, text}]. round 는 int 또는 원문 문자열.

    «아무것도 안 적혀 있다»(정상적인 빈 세션)와 «뭔가 적혀 있는데 항목을 못 읽었다»
    (파싱 실패)를 가른다 — 후자는 ValueError 로 올려 호출자가 rc 3(측정 불가)으로
    구분하게 한다. 전자(명시적 `[]` 또는 값 영역이 비어 있고 그 아래도 비어 있음)는
    빈 리스트를 정상 반환한다.
    """
    lines = fm.splitlines()
    start = next((i for i, ln in enumerate(lines) if re.match(r"^user_statements\s*:", ln)), None)
    if start is None:
        raise ValueError("user_statements 키 부재")
    key_m = re.match(r"^user_statements\s*:\s*(.*)$", lines[start])
    inline = key_m.group(1).strip() if key_m else ""
    if re.fullmatch(r"\[\s*\]", inline):
        return []
    items, cur, i, saw_content = [], None, start + 1, bool(inline)
    while i < len(lines):
        ln = lines[i]
        if ln.strip() and not ln[0].isspace() and not ln.lstrip().startswith("-"):
            break
        if ln.strip():
            saw_content = True
        m = re.match(r"^\s*-\s+id\s*:\s*(\S+)", ln)
        if m:
            cur = {"id": m.group(1).rstrip(","), "round": None, "text": ""}
            items.append(cur); i += 1; continue
        m = re.match(r"^(\s*)(round|text)\s*:\s*(.*)$", ln)
        if m and cur is not None:
            key, raw = m.group(2), m.group(3).strip()
            if key == "round":
                cur["round"] = int(raw) if re.fullmatch(r"-?\d+", raw) else _unquote(raw)
                i += 1; continue
            if raw in ("|", "|-", "|+", ">", ">-", ">+"):
                indent = len(m.group(1)); buf = []; i += 1
                while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > indent):
                    buf.append(lines[i].strip()); i += 1
                cur["text"] = "\n".join(buf).strip(); continue
            cur["text"] = _unquote(raw)
        i += 1
    if not items and saw_content:
        raise ValueError("user_statements 파싱 실패 — 리스트 형식이 아니거나 항목을 읽을 수 없다")
    return items


def split_rounds(body):
    """{round_no: text} — `## R<n>` 헤딩으로 자른다."""
    hs = list(ROUND_H_RE.finditer(body))
    out = {}
    for j, h in enumerate(hs):
        end = hs[j + 1].start() if j + 1 < len(hs) else len(body)
        out[int(h.group(1))] = body[h.end():end]
    return out


def find_block(round_text, s):
    """R 텍스트 안에서 «### 직전 답에서 — …S<k>…» 블록 본문(다음 ###/## 전까지) 또는 None."""
    lines = round_text.splitlines()
    want = anchor_re(s)
    for i, ln in enumerate(lines):
        m = BLOCK_H_RE.match(ln)
        if m and want.search(m.group(1)):
            buf = []
            for nxt in lines[i + 1:]:
                if nxt.startswith("### ") or nxt.startswith("## "):
                    break
                buf.append(nxt)
            return "\n".join(buf).strip()
    return None


def substantive(block):
    if not block:
        return False
    for key in LINE_KEYS:
        m = re.search(r"^\s*[-*]\s+" + re.escape(key) + r"\s*:\s*(.*)$", block, re.MULTILINE)
        if m and m.group(1).strip() and m.group(1).strip() not in NONE_TOKENS:
            return True
    return False


def measure(text, sample_n, seed):
    m = FM_RE.match(text)
    if not m:
        raise ValueError("frontmatter 부재")
    fm, body = m.group(1), m.group(2)
    sid_m = re.search(r"^session_id:\s*(\S+)", fm, re.MULTILINE)
    sid = sid_m.group(1) if sid_m else ""
    stmts = parse_statements(fm)
    rounds = split_rounds(body)
    if not rounds:
        raise ValueError("본문에 `## R<n>` 헤딩이 없다 — 라운드 기록 형식(§1.1) 미준수 또는 구세션")
    pairs, skipped = [], 0
    for st in stmts:
        if not isinstance(st["round"], int) or st["round"] < 0:
            skipped += 1; continue
        nxt = st["round"] + 1
        terminal = nxt not in rounds
        block = None if terminal else find_block(rounds[nxt], st["id"])
        pairs.append({"s": st["id"], "round": st["round"], "next_round": nxt,
                      "user_text": st["text"], "block": block,
                      "substantive": substantive(block), "terminal": terminal,
                      "eligible": (not terminal) and bool(st["text"].strip())})
    eligible = [p for p in pairs if p["eligible"]]
    k = min(sample_n, len(eligible))
    chosen = random.Random(seed or sid).sample(eligible, k) if k else []
    sample = [{"s": p["s"], "s_excerpt": p["user_text"][:200],
               "block_excerpt": (p["block"] or "")[:300]} for p in chosen]
    counts = {"total": len(pairs), "eligible": len(eligible),
              "with_block": sum(1 for p in pairs if p["block"] is not None),
              "substantive_form": sum(1 for p in pairs if p["substantive"]),
              "terminal": sum(1 for p in pairs if p["terminal"]), "skipped": skipped}
    return {"session_id": sid, "pairs": pairs, "counts": counts, "human_sample": sample}


def main(argv):
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("state"); ap.add_argument("--sample", type=int, default=4); ap.add_argument("--seed", default=None)
    try:
        a = ap.parse_args(argv[1:])
    except SystemExit:
        return 2
    try:
        text = Path(a.state).read_text(encoding="utf-8")
        out = measure(text, max(0, a.sample), a.seed)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(json.dumps({"unmeasurable": str(exc)}, ensure_ascii=False))
        return 3
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
