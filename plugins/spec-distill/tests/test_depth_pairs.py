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
        self.assertIn("unmeasurable", json.loads(out))

    def test_no_frontmatter_is_unmeasurable_rc3(self):
        rc, out = run("depth-state-nofrontmatter.md")
        self.assertEqual(rc, 3)
        self.assertIn("unmeasurable", json.loads(out))

    def test_missing_user_statements_key_is_unmeasurable_rc3(self):
        rc, out = run("depth-state-nostatementskey.md")
        self.assertEqual(rc, 3)
        self.assertIn("unmeasurable", json.loads(out))

    def test_unparseable_user_statements_is_unmeasurable_rc3(self):
        # `user_statements:` 값이 리스트가 아니라 스칼라 문자열 — 항목 0개로 조용히
        # 위장하지 않고 파싱 실패로 구분돼야 한다(정상적인 빈 세션과 출력이 달라야 함).
        rc, out = run("depth-state-badstatements.md")
        self.assertEqual(rc, 3)
        self.assertIn("unmeasurable", json.loads(out))

    def test_empty_user_statements_list_is_rc0_total0(self):
        # 양의 짝: 명시적으로 빈 `user_statements: []` 는 파싱 실패가 아니라 정상적인
        # 0 이다 — 위 파싱-실패 테스트가 이 케이스까지 rc 3 으로 끌고 가지 않는지 고정.
        rc, out = run("depth-state-emptystatements.md")
        self.assertEqual(rc, 0, out)
        d = json.loads(out)
        self.assertEqual(d["counts"]["total"], 0)
        self.assertEqual(d["pairs"], [])
        self.assertEqual(d["human_sample"], [])

    def test_elig0_and_allnone_still_rc0(self):
        # 회귀 고정: 파싱-실패 감지를 넣어도 "적격 0"·"블록 있으나 전부 없음" 같은
        # 정상적인 내용 결과는 여전히 rc 0 이어야 한다(측정이 게이트가 되면 안 된다).
        for fx in ("depth-state-elig0.md", "depth-state-allnone.md"):
            rc, out = run(fx)
            self.assertEqual(rc, 0, out)

    def test_skill_template_trailing_comment_is_rc0_total0(self):
        # 회귀 락: plugins/spec-distill/skills/conducting-interview/SKILL.md 의
        # `user_statements: []                  # 매 round 끝 append. …` 그 줄을
        # 그대로 옮긴 fixture. 파싱-실패 감지가 «주석 뒤 문자열」을 내용으로 잘못 세면
        # 막 시작한 정상 세션이 rc 3(측정 불가)으로 오분류된다 — 원래 버그보다 나쁜
        # 회귀이므로 반드시 rc 0 + total 0 이어야 한다.
        rc, out = run("depth-state-templatecomment.md")
        self.assertEqual(rc, 0, out)
        self.assertEqual(json.loads(out)["counts"]["total"], 0)

    def test_user_statements_inline_comment_boundary_matrix(self):
        # 여섯 경계: 키 뒤 아무것도 없음 / 공백만 / 주석만 / `[]`+주석 / 항목 전부
        # malformed / 정상 항목 1개. 앞 넷과 마지막은 rc 0, malformed 만 rc 3.
        import tempfile

        def make(stmts_line, extra_block=""):
            return ("---\nsession_id: bx\n" + stmts_line + "\n" + extra_block
                    + "---\n\n## R1\n\n### 답\n→ (대기)\n")

        cases = [
            ("키 뒤 아무것도 없음", "user_statements:", "", 0, 0),
            ("공백만", "user_statements:   ", "", 0, 0),
            ("주석만", "user_statements: # 아직 없음", "", 0, 0),
            ("[]+주석", "user_statements: []   # 나중에 채움", "", 0, 0),
            ("항목 전부 malformed", "user_statements:", "  이상한 값\n", 3, None),
            ("정상 항목 1개", "user_statements:",
             "  - id: S1\n    round: 0\n    text: \"ok\"\n", 0, 1),
        ]
        with tempfile.TemporaryDirectory() as td:
            for label, line, extra, want_rc, want_total in cases:
                p = Path(td) / (label.replace(" ", "_") + ".md")
                p.write_text(make(line, extra), encoding="utf-8")
                r = subprocess.run([sys.executable, str(SCRIPT), str(p)],
                                   capture_output=True, text=True)
                self.assertEqual(r.returncode, want_rc, (label, r.stdout, r.stderr))
                d = json.loads(r.stdout)
                if want_rc == 0:
                    self.assertEqual(d["counts"]["total"], want_total, label)
                else:
                    self.assertIn("unmeasurable", d, label)


if __name__ == "__main__":
    unittest.main()
