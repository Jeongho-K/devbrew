import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "depth_pairs.py"
FX = Path(__file__).resolve().parent / "fixtures"


def run(fx, *args):
    p = subprocess.run([sys.executable, str(SCRIPT), str(FX / fx), *args],
                       capture_output=True, text=True, env={"PYTHONDONTWRITEBYTECODE": "1"})
    return p.returncode, p.stdout


class DepthPairs(unittest.TestCase):
    def test_normal_counts_and_sample(self):
        rc, out = run("depth-state-normal.md", "--sample", "4")
        self.assertEqual(rc, 0, out)
        d = json.loads(out)
        self.assertEqual(d["counts"], {"total": 7, "eligible": 6, "with_block": 6,
                                       "substantive_form": 5, "terminal": 1, "skipped": 1})
        self.assertEqual(len(d["human_sample"]), 4)
        by = {p["s"]: p for p in d["pairs"]}
        self.assertTrue(by["S7"]["terminal"])
        self.assertFalse(by["S2"]["substantive"])
        self.assertTrue(by["S3"]["substantive"])
        self.assertEqual(by["S1"]["next_round"], 1)      # round 0 → R1
        self.assertIn("TTL 은 원인이 아니다", by["S3"]["block"])

    def test_two_answers_two_blocks(self):
        rc, out = run("depth-state-normal.md")
        by = {p["s"]: p for p in json.loads(out)["pairs"]}
        self.assertIsNotNone(by["S4"]["block"]); self.assertIsNotNone(by["S5"]["block"])
        self.assertNotIn("S5", by["S4"]["block"])  # 블록은 S 마다 분리

    def test_sample_is_reproducible_without_replacement(self):
        _, a = run("depth-state-normal.md", "--sample", "4")
        _, b = run("depth-state-normal.md", "--sample", "4")
        sa = [x["s"] for x in json.loads(a)["human_sample"]]
        self.assertEqual(sa, [x["s"] for x in json.loads(b)["human_sample"]])
        self.assertEqual(len(set(sa)), 4)
        _, c = run("depth-state-normal.md", "--sample", "4", "--seed", "other")
        self.assertEqual(len(json.loads(c)["human_sample"]), 4)

    def test_eligible_0_1_3(self):
        for fx, n in (("depth-state-elig0.md", 0), ("depth-state-elig1.md", 1), ("depth-state-elig3.md", 3)):
            rc, out = run(fx, "--sample", "4")
            self.assertEqual(rc, 0, out)
            d = json.loads(out)
            self.assertEqual(d["counts"]["eligible"], n, fx)
            self.assertEqual(len(d["human_sample"]), n, fx)
        self.assertEqual(json.loads(run("depth-state-elig0.md")[1])["human_sample"], [])

    def test_no_round_heading_is_unmeasurable_rc3(self):
        rc, out = run("depth-state-noround.md")
        self.assertEqual(rc, 3)
        self.assertIn("unmeasurable", json.loads(out))

    def test_all_none_block_counts_zero_substantive(self):
        rc, out = run("depth-state-allnone.md")
        self.assertEqual(rc, 0)
        d = json.loads(out)
        self.assertEqual(d["counts"]["substantive_form"], 0)
        self.assertEqual(d["counts"]["with_block"], 1)

    def test_non_seed_s1_round1_pairs_with_r2(self):
        # S1 이 round: 1 이면(비-seed 경로) R1 과 짝짓지 않고 R2 와 짝짓는다.
        import tempfile
        src = (FX / "depth-state-elig1.md").read_text(encoding="utf-8").replace("round: 0", "round: 1", 1)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "s.md"; p.write_text(src, encoding="utf-8")
            out = subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True).stdout
            by = {x["s"]: x for x in json.loads(out)["pairs"]}
            self.assertEqual(by["S1"]["next_round"], 2)

    def test_missing_file_rc3(self):
        rc, out = run("does-not-exist.md")
        self.assertEqual(rc, 3)


if __name__ == "__main__":
    unittest.main()
