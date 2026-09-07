#!/usr/bin/env python3
"""depth_pairs.py — state 본문에서 «답→다음 행동» 짝을 뽑는다 (spec §3.1, v0.57.0).

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


def _strip_inline_comment(raw):
    """YAML 인라인 주석(앞에 공백 또는 줄 시작이 오는 `#`)을 뗀다.

    따옴표 안의 `#` 은 값으로 보존한다(예: `text: "이슈 #12"`) — 따옴표 밖에서만
    주석 시작으로 본다. 사람이 읽으라고 붙인 주석은 «값 영역의 내용»이 아니다.
    """
    out, quote = [], None
    for i, c in enumerate(raw):
        if quote:
            out.append(c)
            if c == quote:
                quote = None
            continue
        if c in "\"'":
            quote = c; out.append(c); continue
        if c == "#" and (i == 0 or raw[i - 1].isspace()):
            break
        out.append(c)
    return "".join(out)


def parse_statements(fm):
    """`user_statements` → [{id, round, text}]. round 는 int 또는 원문 문자열.

    «아무것도 안 적혀 있다»(정상적인 빈 세션)와 «뭔가 적혀 있는데 항목을 못 읽었다»
    (파싱 실패)를 가른다 — 후자는 ValueError 로 올려 호출자가 rc 3(측정 불가)으로
    구분하게 한다. 전자(명시적 `[]` — 뒤에 사람이 읽으라고 붙인 주석이 있어도 — 또는
    값 영역이 비어 있고 그 아래도 비어 있음)는 빈 리스트를 정상 반환한다. 주석은
    데이터가 아니므로 «내용이 있는가» 판정 전에 먼저 뗀다(예: SKILL.md 템플릿의
    `user_statements: []                  # 매 round 끝 append. …`).
    """
    lines = fm.splitlines()
    start = next((i for i, ln in enumerate(lines) if re.match(r"^user_statements\s*:", ln)), None)
    if start is None:
        raise ValueError("user_statements 키 부재")
    key_m = re.match(r"^user_statements\s*:\s*(.*)$", lines[start])
    inline = _strip_inline_comment(key_m.group(1) if key_m else "").strip()
    if re.fullmatch(r"\[\s*\]", inline):
        return []
    items, cur, i, saw_content = [], None, start + 1, bool(inline)
    while i < len(lines):
        ln = lines[i]
        if ln.strip() and not ln[0].isspace() and not ln.lstrip().startswith("-"):
            break
        if ln.strip():
            saw_content = True
        # 새 항목의 시작은 **불릿**이지 `- id:` 라는 «특정 키» 가 아니다. `- id:` 만 항목
        # 시작으로 보면 필드 순서가 다른 항목(`- source: …` / `  id: …`)에서 새 항목이
        # 열리지 않고 `cur` 가 앞 항목을 계속 가리켜, 뒤따르는 `round`·`text` 가 **앞 S 의
        # 필드를 덮어쓴다**. 실측(필드 순서만 바꾼 fixture): S4 가 통째로 사라지고 그 본문이
        # S3 에 붙었다 — 오류 없이. 조용한 오배정은 누락보다 나쁘다(측정이 틀린 값을 자신
        # 있게 낸다). 그래서 불릿을 경계로 삼고 `id` 는 다른 필드와 같은 자격으로 읽는다.
        bm = re.match(r"^(\s*)-\s+(.*)$", ln)
        if bm:
            cur = {"id": None, "round": None, "text": ""}
            items.append(cur)
            indent = len(bm.group(1))
            fm = re.match(r"^(id|round|text)\s*:\s*(.*)$", bm.group(2))
            if not fm:
                i += 1
                continue
            key, raw = fm.group(1), fm.group(2).strip()
        else:
            fm = re.match(r"^(\s*)(id|round|text)\s*:\s*(.*)$", ln)
            if not fm or cur is None:
                i += 1
                continue
            indent, key, raw = len(fm.group(1)), fm.group(2), fm.group(3).strip()
        if key == "id":
            # 주석은 데이터가 아니다 — 키 줄에서 이미 떼고 있는 것과 같은 관례.
            cur["id"] = _unquote(_strip_inline_comment(raw).strip().rstrip(",").strip()) or None
            i += 1
            continue
        if key == "round":
            # `round: 1 # answered R1` 을 문자열로 읽으면 그 S 가 조용히 짝에서 빠진다.
            # round 는 정수 자리이므로 주석을 떼는 것이 안전하다(text 에는 하지 않는다 —
            # 사용자 원문에 `#` 가 정당하게 들어간다).
            raw = _strip_inline_comment(raw).strip()
            cur["round"] = int(raw) if re.fullmatch(r"-?\d+", raw) else _unquote(raw)
            i += 1
            continue
        if raw in ("|", "|-", "|+", ">", ">-", ">+"):
            buf = []
            i += 1
            while i < len(lines) and (not lines[i].strip()
                                      or len(lines[i]) - len(lines[i].lstrip()) > indent):
                buf.append(lines[i].strip()); i += 1
            cur["text"] = "\n".join(buf).strip()
            continue
        cur["text"] = _unquote(raw)
        i += 1
    if not items and saw_content:
        raise ValueError("user_statements 파싱 실패 — 리스트 형식이 아니거나 항목을 읽을 수 없다")
    # id 없는 항목은 «빈 항목» 이 아니라 «읽지 못한 항목» 이다. 통째로 버리면 total 만
    # 줄어 「그런 답은 없었다」로 기록되므로, 측정 불가로 올려 rc 3 으로 구분되게 한다.
    nameless = [n for n, it in enumerate(items, 1) if not it["id"]]
    if nameless:
        raise ValueError(
            "user_statements 항목 %s 에 id 가 없다 — 본문이 다른 S 에 붙을 수 있어 "
            "«측정 불가» 로 낸다" % (nameless,))
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
    # spec §3.2: 「**마지막 라운드**의 답은 다음 라운드가 없으므로 짝에서 제외하고 terminal
    # 로 센다」. `nxt not in rounds` 는 그 정의가 아니다 — **중간 라운드 결번**까지 terminal
    # 로 삼는다. 실측: `## R2` 하나만 `## Round 2` 로 바꾸면(R3·R4 는 그대로) terminal 이
    # 1 → 3 으로 오르고 적격 답이 6 → 4 로 줄었다. 뒤 라운드의 존재가 인터뷰가 끝나지
    # 않았음을 증명하는데도 그 답들이 「잴 것이 없는 답」으로 분류돼 사람 표본에서 사라진다
    # — 측정이 **안전해 보이는 방향으로** 거짓말한다. terminal 은 뒤에 라운드가 하나도
    # 없을 때만 참이다. 결번으로 블록을 못 찾은 답은 terminal 이 아니라 `with_block` 에서
    # 빠지는 것으로 드러난다(짝은 남고 사람 표본에도 남는다).
    last_round = max(rounds)
    pairs, skipped = [], 0
    for st in stmts:
        if not isinstance(st["round"], int) or st["round"] < 0:
            skipped += 1; continue
        nxt = st["round"] + 1
        terminal = st["round"] >= last_round
        block = (None if terminal or nxt not in rounds
                 else find_block(rounds[nxt], st["id"]))
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
