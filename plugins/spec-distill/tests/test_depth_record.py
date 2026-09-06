import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "depth_record.py"

PAIRS = {"session_id": "sidA", "counts": {"total": 7, "eligible": 6, "with_block": 6,
         "substantive_form": 5, "terminal": 1, "skipped": 1},
         "pairs": [{"s": f"S{i}", "eligible": True, "block": "x", "substantive": True,
                    "terminal": False, "user_text": "t", "round": 1, "next_round": 2} for i in range(1, 7)],
         "human_sample": [{"s": "S1", "s_excerpt": "", "block_excerpt": ""},
                          {"s": "S2", "s_excerpt": "", "block_excerpt": ""},
                          {"s": "S3", "s_excerpt": "", "block_excerpt": ""},
                          {"s": "S4", "s_excerpt": "", "block_excerpt": ""}]}
AUDITOR_OK = """정리했다.
```depth-audit
pairs:
  - s: S1
    label: dug
    reason: "a"
  - s: S2
    label: not_dug
    reason: "b"
  - s: S3
    label: undecidable
    reason: "c"
  - s: S4
    label: dug
    reason: "d"
  - s: S5
    label: bogus
    reason: "e"
  - s: S9
    label: dug
    reason: "표본·짝 밖"
```
"""


def run(td, pairs=PAIRS, auditor=AUDITOR_OK, human=None, out_name="x-interview.json", prior=()):
    td = Path(td)
    (td / "pairs.json").write_text(json.dumps(pairs), encoding="utf-8")
    if auditor is not None:
        (td / "raw.txt").write_text(auditor, encoding="utf-8")
    (td / "x-interview.audit.md").write_text("# audit\n", encoding="utf-8")
    depth = td / "depth"; depth.mkdir(exist_ok=True)
    for i, rec in enumerate(prior):
        (depth / f"prior{i}.json").write_text(json.dumps(rec), encoding="utf-8")
    human = human if human is not None else {"skipped": False, "labels": {"S1": "dug", "S2": "dug", "S3": "dug", "S4": "not_dug"}}
    cmd = [sys.executable, str(SCRIPT), str(td / "pairs.json"), "--auditor", str(td / "raw.txt"),
           "--human", json.dumps(human), "--audit", str(td / "x-interview.audit.md"),
           "--out", str(depth / out_name), "--date", "2026-09-06"]
    # 자식의 stdout 인코딩을 로케일에 맡기지 않는다 — 이 스크립트의 출력은 전부 한국어라
    # C 로케일에서 UnicodeEncodeError 로 죽으면 «측정이 게이트가 아니다» 가 깨진다.
    p = subprocess.run(cmd, capture_output=True, encoding="utf-8",
                       env={"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
    rec = json.loads((depth / out_name).read_text(encoding="utf-8")) if (depth / out_name).exists() else None
    return p.returncode, p.stdout, rec


def prior_record(dug, not_dug, k, v):
    return {"date": "2026-09-01", "brief": "b.md", "session_id": "p",
            "pairs": {"total": 5, "eligible": 4, "with_block": 4, "substantive_form": 4, "terminal": 1},
            "auditor": {"dug": 2, "not_dug": 2, "undecidable": 0, "held": 0, "unavailable": False},
            "human": {"sampled": 4, "dug": dug, "not_dug": not_dug, "undecidable": 0, "unlabeled": 0,
                      "auditor_missing": 0, "agreement": [k, v]}}


class DepthRecord(unittest.TestCase):
    def test_merge_lines_and_file(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out, rec = run(td)
            self.assertEqual(rc, 0)
            self.assertIn("- 깊이 측정(형식): 짝 7 중 되비추기 블록 있음 6 · 내용 있는 줄 ≥1 5 · terminal 1", out)
            self.assertIn("- 깊이 측정(auditor): dug 2 · not_dug 1 · undecidable 1 · held 1 · unavailable 0", out)
            # 사람: S1 dug / S2 dug / S3 dug / S4 not_dug.
            # 분모 v = 양쪽이 dug|not_dug 인 표본 = S1,S2,S4 → 3.
            # 분자 k = 그중 라벨이 «같은» 것 = S1 뿐 → 1
            #          (S2 사람 dug vs auditor not_dug · S4 사람 not_dug vs auditor dug — 둘 다 불일치).
            # S3 는 auditor 가 undecidable 이라 분모 밖 → auditor_missing 1.
            self.assertIn("- 깊이 측정(사람): 표본 4 — dug 3 · not_dug 1 · undecidable 0 · 미라벨 0 · auditor 일치 1/3 (auditor 판정 없는 표본 1 별도)", out)
            self.assertIn("- 판정자 조건: 조건 미도달 (1/5)", out)
            self.assertIn("**처분:**", out)
            self.assertEqual(rec["human"]["agreement"], [1, 3])
            self.assertEqual(rec["auditor"]["held"], 1)
            self.assertEqual(rec["brief"].endswith("x-interview.md"), True)
            self.assertEqual(rec["date"], "2026-09-06")

    def test_sentinel_missing_is_unavailable_not_zero(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out, rec = run(td, auditor="no block here")
            self.assertEqual(rc, 0)
            self.assertIn("unavailable 1", out)
            self.assertTrue(rec["auditor"]["unavailable"])
            self.assertIn("auditor 일치 자료 부족", out)

    def test_auditor_file_missing_still_exit0(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out, rec = run(td, auditor=None)
            self.assertEqual(rc, 0); self.assertIn("unavailable 1", out)

    def test_human_skipped_is_unlabeled(self):
        with tempfile.TemporaryDirectory() as td:
            rc, out, rec = run(td, human={"skipped": True, "labels": {}})
            self.assertIn("미라벨 4", out)
            self.assertEqual(rec["human"]["unlabeled"], 4)
            self.assertIn("auditor 일치 자료 부족", out)

    def test_sample_zero(self):
        with tempfile.TemporaryDirectory() as td:
            p = dict(PAIRS); p["human_sample"] = []
            rc, out, rec = run(td, pairs=p, human={"skipped": False, "labels": {}})
            self.assertIn("- 깊이 측정(사람): 표본 없음", out)
            self.assertEqual(rec["human"]["sampled"], 0)

    def test_condition_A_boundary_30pct(self):
        # 이번 인터뷰가 dug 3 · not_dug 1 (합 4) 을 넣는다. prior 넷을 더해 적격 5.
        # Σnot_dug = 1 + 1+1+0+0 = 3 · Σ(dug+not_dug) = 4 + 2+2+1+1 = 10 → 30% (경계, 도달)
        prior = [prior_record(1, 1, 2, 2), prior_record(1, 1, 2, 2),
                 prior_record(1, 0, 1, 1), prior_record(1, 0, 1, 1)]
        with tempfile.TemporaryDirectory() as td:
            _, out, _ = run(td, prior=prior)
            self.assertIn("판정자 투입 조건 도달", out)
        # 분모만 늘린다(넷째를 dug 2 로) → Σ = 11, 3/11 ≈ 27% → 미도달
        prior[3] = prior_record(2, 0, 1, 1)
        with tempfile.TemporaryDirectory() as td:
            _, out, _ = run(td, prior=prior)
            self.assertNotIn("판정자 투입 조건 도달", out)

    def test_condition_B_boundary_70pct(self):
        # 이번 인터뷰의 k/v = 1/3. prior 로 Σk/Σv 를 정확히 0.70 과 그 아래 양쪽에 둔다.
        # Σk = 1 + 2+2+1+1 = 7 · Σv = 3 + 2+2+1+2 = 10 → 0.70 (경계 — 제외 아님)
        prior = [prior_record(2, 0, 2, 2), prior_record(2, 0, 2, 2),
                 prior_record(1, 0, 1, 1), prior_record(2, 0, 1, 2)]
        with tempfile.TemporaryDirectory() as td:
            _, out, _ = run(td, prior=prior)
            self.assertNotIn("auditor 계수는 근거에서 제외", out)
        prior[0] = prior_record(2, 0, 1, 2)   # Σk = 6 → 0.60 → 제외
        with tempfile.TemporaryDirectory() as td:
            _, out, _ = run(td, prior=prior)
            self.assertIn("auditor 계수는 근거에서 제외", out)

    def test_ineligible_interviews_do_not_count(self):
        # 전부 undecidable 인 인터뷰는 5건 계수에 안 든다
        prior = [prior_record(0, 0, 0, 0)] * 4
        with tempfile.TemporaryDirectory() as td:
            _, out, _ = run(td, prior=prior)
            self.assertIn("조건 미도달 (1/5)", out)

    def test_bad_pairs_json_records_not_crash(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td); (td / "pairs.json").write_text("{not json", encoding="utf-8")
            p = subprocess.run([sys.executable, str(SCRIPT), str(td / "pairs.json"), "--auditor", "x",
                                "--human", "{}", "--audit", "a.audit.md", "--out", str(td / "d" / "o.json")],
                               capture_output=True, encoding="utf-8")
            self.assertEqual(p.returncode, 0)
            self.assertIn("기록 불가", p.stdout)

    def test_pairs_counts_key_missing_is_not_recorded_as_zero(self):
        # 「0 으로 기록」은 거짓 clean 이다 — 산출자 스키마가 깨지면 «기록 불가» 다.
        with tempfile.TemporaryDirectory() as td:
            p = dict(PAIRS)
            p["counts"] = {k: v for k, v in PAIRS["counts"].items() if k != "with_block"}
            rc, out, rec = run(td, pairs=p)
            self.assertEqual(rc, 0)
            self.assertIn("기록 불가", out)
            self.assertIsNone(rec)


if __name__ == "__main__":
    unittest.main()
