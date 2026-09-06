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
PAIR_KEYS = ("total", "eligible", "with_block", "substantive_form", "terminal", "skipped")
SENTINEL_RE = re.compile(r"```depth-audit[ \t]*\n(.*?)\n```", re.DOTALL)
ITEM_RE = re.compile(r"^\s*-\s+s\s*:\s*(\S+)\s*$")
FIELD_RE = re.compile(r"^\s+(label|reason)\s*:\s*(.*?)\s*$")
# 값 없는 매핑 키 = YAML 구조 줄이지 «못 읽은 데이터»가 아니다. depth-auditor 의 출력
# 계약 자체가 `pairs:` 를 컨테이너 키로 싣는다(agents/depth-auditor.md) — 이것을 «인식 못 한
# 줄» 로 세면 정상 출력마다 오탐 공시가 붙는다. `- s:`(값 없는 항목)는 여기 안 걸린다:
# 불릿으로 시작해 `[A-Za-z_]` 와 안 맞으므로 제대로 «못 읽은 줄» 로 남는다.
CONTAINER_RE = re.compile(r"^\s*[A-Za-z_][\w-]*\s*:\s*$")


def parse_auditor(raw, ledger):
    """센티널 블록 → {S: label}. 「잴 수 없었다」(None)와 「재 보니 0」을 가른다.

    수집 루프에서 항목 줄·필드 줄은 «버리는» 자리가 아니라 «모으는» 자리라 처분을
    부르지 않는다 — 거기에 처분을 부르면 회계가 실제로 버린 적 없는 것을 센다.
    다만 **어느 쪽으로도 인식되지 않은 줄**은 다르다: 그것은 모으지도 못한 것이므로
    세어야 한다. 「펜스를 찾았다」를 충분조건으로 보고 인식 못 한 줄을 조용히 버리면,
    파손된 출력이 `dug 0 · not_dug 0 · held 0 · unavailable 0` 으로 — 즉 **「측정했고
    0 건」**으로 — 기록된다(실측: `S1: dug` 처럼 항목 마커가 다른 펜스, 그리고 `*` 불릿
    펜스 둘 다). 이 리포의 규칙: 「셀 수 없음」과 「0」은 다른 사실이다.
    """
    m = SENTINEL_RE.search(raw or "")
    if not m:
        ledger.source_failed(
            "depth-auditor", "depth-audit 센티널 블록 부재/빈 출력", primary=True)
        return None
    items, cur, unread = [], None, 0
    for ln in m.group(1).splitlines():
        im = ITEM_RE.match(ln)
        fm = FIELD_RE.match(ln)
        if im:
            cur = {"s": im.group(1)}
            items.append(cur)
        elif fm and cur is not None:
            cur[fm.group(1)] = fm.group(2).strip().strip('"')
        elif ln.strip() and not CONTAINER_RE.match(ln):
            # 빈 줄·구조 줄은 «버린 항목» 이 아니라서 처분을 부르지 않는다. 그래서
            # `continue` 로 먼저 걸러내지 않고 이 술어 안에 접어 둔다 — 별도 분기로 두면
            # 「버리는 자리인데 처분이 없다」로 배선 검사에 걸리고, 면제 목록만 길어진다.
            unread += 1
    if unread:
        ledger.uncountable(
            "depth-auditor 펜스",
            "인식 못 한 줄 %d 개 — 항목/필드 어느 형태도 아니다" % unread)
    if not items:
        # 내용은 있는데 항목이 0 이면 «판정 0 건» 이 아니라 «판정을 읽지 못했다» 다.
        ledger.source_failed(
            "depth-auditor",
            "펜스는 있으나 항목 0 — 출력 형식이 계약과 다르다(0 건이 아니라 판독 실패)",
            primary=True)
        return None
    # 같은 S 에 여러 판정이 올 수 있다. 같은 라벨의 중복은 **흡수**(계수하되 degrade 아님),
    # 서로 **다른** 라벨은 auditor 가 자기모순한 것이므로 그 S 는 **셀 수 없다**. 뒤엣것이
    # 앞엣것을 덮어쓰게 두면 모순이 `흡수 0 · 보류 0` 인 채로 공시 없이 사라진다(실측).
    by_s = {}
    for it in items:
        by_s.setdefault(it.get("s", "?"), []).append(it.get("label"))
    labels = {}
    for s, labs in by_s.items():
        bad = [x for x in labs if x not in LABELS]
        if bad:
            ledger.hold(s, "항목 파손: label %r 는 어휘 밖" % (bad[0],))
            continue
        distinct = sorted(set(labs))
        if len(distinct) > 1:
            # 접두는 `adjudication._HOLD_CLASSES` 의 어휘를 쓴다 — 새 접두를 만들면 그
            # 모듈이 「분류되지 않았다」 advisory 를 내고, 공시가 소음으로 읽힌다.
            # 상충하는 두 판정은 그 S 의 «항목»을 읽을 수 없게 만든 것이므로 항목 파손이다.
            ledger.hold(s, "항목 파손: 같은 S 에 상충하는 판정 %s — 어느 쪽도 셀 수 없다"
                        % (" vs ".join(distinct),))
            continue
        if len(labs) > 1:
            ledger.absorbed(s, "같은 판정 %d 회 중복" % len(labs))
        labels[s] = labs[0]
        ledger.accept(s)
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
            # `int()` 변환은 **언패킹과 같은 try 안**에 있어야 한다. 밖에 두면
            # `"agreement":["bad",1]` 같은 이형 값이 아래 누산에서 uncaught ValueError 를
            # 내고, 그때는 이미 앞의 세 줄이 출력된 뒤라 «기록 불가» 조차 남지 않는다 —
            # 실측: rc=1 + 부분 출력. spec C5 의 「항상 exit 0 · 실패는 기록 불가로
            # 표면화」 계약 위반이다.
            ak, av = int(ak), int(av)
        except (OSError, ValueError, KeyError, TypeError) as exc:
            ledger.uncountable(name, "측정 파일 판독 불가: %s" % exc)
            continue
        if d + n < 1:
            ledger.suppressed(name, "적격 아님(dug+not_dug=0)")
            continue
        e += 1
        nd += n
        tot += d + n
        k += ak
        v += av
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
    # `skipped`(round 값이 정수가 아니어서 짝을 못 만든 S)는 **영구 기록과 표시 양쪽에**
    # 실린다. 산출자는 늘 세고 있었는데 소비자가 둘 다에서 빼는 바람에, 그 누락이 하류에서
    # 보이지 않았다 — 빠진 답이 있다는 사실 자체가 사라지면 «전부 쟀다» 와 구분되지 않는다.
    print("- 깊이 측정(형식): 짝 %d 중 되비추기 블록 있음 %d · 내용 있는 줄 ≥1 %d · terminal %d"
          " · round 불명 %d"
          % (pair_counts["total"], pair_counts["with_block"],
             pair_counts["substantive_form"], pair_counts["terminal"],
             pair_counts["skipped"]))
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
