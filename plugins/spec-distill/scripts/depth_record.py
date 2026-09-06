#!/usr/bin/env python3
"""depth_record.py — 세 층(형식·auditor·사람)을 병합해 기록한다 (spec §3.2~§3.4, v0.56.0).

항상 exit 0. 측정이지 게이트가 아니다(C5) — 실패는 «기록 불가: <이유>» 로 표면화한다.
처분 회계는 adjudication.Ledger(항목 파손 → held, 센티널 부재 → source_failed).
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adjudication import Ledger  # noqa: E402
from render_disposition import disposition_lines  # noqa: E402

LABELS = ("dug", "not_dug", "undecidable")
# 측정 파일 §3.3 의 `pairs` 다섯 칸. 산출자(depth_pairs.py)가 늘 함께 낸다 —
# 하나라도 없으면 「0 으로 기록」이 아니라 KeyError 로 «기록 불가» 다(0 은 거짓 clean).
PAIR_KEYS = ("total", "eligible", "with_block", "substantive_form", "terminal")
SENTINEL_RE = re.compile(r"```depth-audit[ \t]*\n(.*?)\n```", re.DOTALL)
ITEM_RE = re.compile(r"^\s*-\s+s\s*:\s*(\S+)\s*$")
FIELD_RE = re.compile(r"^\s+(label|reason)\s*:\s*(.*?)\s*$")


def parse_auditor(raw, ledger):
    """센티널 블록 → {S: label}. 블록 부재는 None(unavailable) — 0건과 구분.

    수집 루프에는 `continue` 가 없다 — 항목 줄과 필드 줄은 «버리는» 자리가 아니라
    «모으는» 자리이고, 여기에 처분을 부르면 회계가 실제로 버린 적 없는 것을 센다.
    """
    m = SENTINEL_RE.search(raw or "")
    if not m:
        ledger.source_failed(
            "depth-auditor", "depth-audit 센티널 블록 부재/빈 출력", primary=True)
        return None
    items, cur = [], None
    for ln in m.group(1).splitlines():
        im = ITEM_RE.match(ln)
        fm = FIELD_RE.match(ln)
        if im:
            cur = {"s": im.group(1)}
            items.append(cur)
        elif fm and cur is not None:
            cur[fm.group(1)] = fm.group(2).strip().strip('"')
    labels = {}
    for it in items:
        lab = it.get("label")
        if lab not in LABELS:
            ledger.hold(it.get("s", "?"), "항목 파손: label %r 는 어휘 밖" % (lab,))
            continue
        labels[it["s"]] = lab
        ledger.accept(it["s"])
    return labels


def condition_line(depth_dir, ledger):
    """spec §3.4 — 적격 인터뷰 5건부터 두 조건을 본다.

    원장을 인자로 받는다: 이 루프의 두 버리는 분기(판독 불가 · 적격 아님)가
    자기 처분을 부를 수 있어야 하기 때문이다. 판독 실패는 «셀 수 없음»이고
    (0 건이 아니다), 규칙에 의한 제외는 «억제»다.
    """
    e = nd = tot = k = v = 0
    for path in sorted(glob.glob(os.path.join(depth_dir, "*.json"))):
        name = os.path.basename(path)
        try:
            with open(path, encoding="utf-8") as fh:
                rec = json.load(fh)
            h = rec["human"]
            d, n = int(h["dug"]), int(h["not_dug"])
            ak, av = h["agreement"]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            ledger.uncountable(name, "측정 파일 판독 불가: %s" % exc)
            continue
        if d + n < 1:
            ledger.suppressed(name, "적격 아님(dug+not_dug=0)")
            continue
        e += 1
        nd += n
        tot += d + n
        k += int(ak)
        v += int(av)
    if e < 5:
        return "조건 미도달 (%d/5)" % e
    parts = []
    if tot and nd / tot >= 0.30:
        parts.append("판정자 투입 조건 도달 — 다음 사이클이 닫힘 거부권 에이전트를 "
                     "설계한다 (not_dug %d/%d)" % (nd, tot))
    if v == 0:
        parts.append("auditor 일치 자료 부족")
    elif k / v < 0.70:
        parts.append("auditor 계수는 근거에서 제외 — 사람 표본을 늘린다 "
                     "(일치 %d/%d)" % (k, v))
    return " · ".join(parts) if parts else "조건 미도달 (%d/5)" % e


def main(argv):
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("pairs")
    for opt in ("--auditor", "--human", "--audit", "--out"):
        ap.add_argument(opt, required=True)
    ap.add_argument("--date", default=None)
    try:
        a = ap.parse_args(argv[1:])
        with open(a.pairs, encoding="utf-8") as fh:
            pairs = json.load(fh)
        human_in = a.human
        if human_in.startswith("@"):
            with open(human_in[1:], encoding="utf-8") as fh:
                human_in = fh.read()
        human = json.loads(human_in or "{}")
        if not isinstance(human, dict):
            raise TypeError("--human 이 객체가 아니다: %s" % type(human).__name__)
        counts = pairs["counts"]
        pair_counts = {key: int(counts[key]) for key in PAIR_KEYS}
        sample = [s["s"] for s in pairs.get("human_sample", [])]
        pair_ids = {p["s"] for p in pairs.get("pairs", [])}
        hl = {} if human.get("skipped") else dict(human.get("labels") or {})
    except (SystemExit, OSError, ValueError, KeyError, TypeError) as exc:
        print("- 깊이 측정: 기록 불가 — %s" % exc)
        return 0

    ledger = Ledger(items="open")
    try:
        with open(a.auditor, encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    except OSError as exc:
        raw = ""
        ledger.uncountable("auditor raw", "파일 판독 실패: %s" % exc)
    labels = parse_auditor(raw, ledger)
    unavailable = labels is None
    labels = labels or {}
    for s in list(labels):
        if s not in pair_ids:
            ledger.suppressed(s, "짝 목록 밖의 S")
            del labels[s]
    rep = ledger.report()
    aud = {lab: sum(1 for x in labels.values() if x == lab) for lab in LABELS}
    aud["held"] = rep["counts"]["held"]
    aud["unavailable"] = unavailable

    hum = {"sampled": len(sample), "dug": 0, "not_dug": 0, "undecidable": 0,
           "unlabeled": 0, "auditor_missing": 0, "agreement": [0, 0]}
    for s in sample:
        h = hl.get(s)
        if h not in LABELS:
            hum["unlabeled"] += 1
            ledger.suppressed(s, "사람 미라벨")
            continue
        hum[h] += 1
        if h == "undecidable":
            ledger.suppressed(s, "사람 판단불가 — auditor 일치 계수 밖")
            continue
        al = labels.get(s)
        if al in ("dug", "not_dug"):
            hum["agreement"][1] += 1
            hum["agreement"][0] += int(al == h)
        else:
            hum["auditor_missing"] += 1

    date = a.date or datetime.date.today().isoformat()
    brief = (a.audit[:-len(".audit.md")] + ".md"
             if a.audit.endswith(".audit.md") else a.audit)
    rec = {"date": date, "brief": brief, "session_id": pairs.get("session_id", ""),
           "pairs": pair_counts, "auditor": aud, "human": hum}
    out_dir = os.path.dirname(os.path.abspath(a.out))
    try:
        os.makedirs(out_dir, exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=1)
    except OSError as exc:
        print("- 깊이 측정: 기록 불가 — 측정 파일 쓰기 실패: %s" % exc)
        return 0

    k, v = hum["agreement"]
    agree = "자료 부족" if v == 0 else "%d/%d" % (k, v)
    print("- 깊이 측정(형식): 짝 %d 중 되비추기 블록 있음 %d · 내용 있는 줄 ≥1 %d · terminal %d"
          % (pair_counts["total"], pair_counts["with_block"],
             pair_counts["substantive_form"], pair_counts["terminal"]))
    print("- 깊이 측정(auditor): dug %d · not_dug %d · undecidable %d · held %d · unavailable %d"
          % (aud["dug"], aud["not_dug"], aud["undecidable"], aud["held"],
             1 if unavailable else 0))
    if hum["sampled"] == 0:
        print("- 깊이 측정(사람): 표본 없음")
    else:
        print("- 깊이 측정(사람): 표본 %d — dug %d · not_dug %d · undecidable %d · 미라벨 %d"
              " · auditor 일치 %s (auditor 판정 없는 표본 %d 별도)"
              % (hum["sampled"], hum["dug"], hum["not_dug"], hum["undecidable"],
                 hum["unlabeled"], agree, hum["auditor_missing"]))
    print("- 판정자 조건: %s" % condition_line(out_dir, ledger))
    line1, line2, adv = disposition_lines(ledger.report(), ledger.held_by_class())
    print(line1)
    print(line2)
    for x in adv + ledger.reasons():
        print("advisory: %s" % x)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
