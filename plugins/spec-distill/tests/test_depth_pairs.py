import json
import subprocess
import tempfile
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


class ParsingDoesNotMisassign(unittest.TestCase):
    """v0.56.0 B2/B3 — 조용한 오배정·오계수 회귀 고정.

    셋 다 «오류 없이 틀린 값을 낸다» 는 부류다. 예외도 rc≠0 도 없어서 스위트를
    green 으로 두고 지나간다 — 그래서 값 자체를 단언한다.
    """

    def _run(self, text):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "state.md"
            p.write_text(text, encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPT), str(p)],
                               capture_output=True, text=True,
                               env={"PYTHONDONTWRITEBYTECODE": "1"})
            return r.returncode, json.loads(r.stdout)

    def _fixture(self):
        return (FX / "depth-state-normal.md").read_text(encoding="utf-8")

    def test_field_order_does_not_move_a_body_to_another_anchor(self):
        """항목의 «필드 순서»만 바꿔도 결과가 같아야 한다.

        `- id:` 만 항목 시작으로 보면 `- source:` 로 시작하는 항목에서 새 항목이 열리지
        않아, 뒤따르는 `round`·`text` 가 **앞 S 를 덮어쓴다**. 실측(수정 전): S4 가 사라지고
        그 본문이 S3 에 붙었으며 rc 는 0 이었다. 누락보다 나쁜 실패다 — 측정이 틀린 값을
        자신 있게 낸다.
        """
        base = self._fixture()
        old = ('  - id: S4\n    source: verbatim\n    round: 2\n'
               '    text: "서버 로그에는 아무것도 없었다"\n')
        new = ('  - source: verbatim\n    id: S4\n    round: 2\n'
               '    text: "서버 로그에는 아무것도 없었다"\n')
        self.assertIn(old, base, "픽스처가 바뀌었다 — 이 단언이 공허하다")
        rc0, want = self._run(base)
        rc1, got = self._run(base.replace(old, new, 1))
        self.assertEqual((rc0, rc1), (0, 0))
        self.assertEqual(got["counts"], want["counts"], "필드 순서가 계수를 바꿨다")
        self.assertEqual({p["s"]: p["user_text"] for p in got["pairs"]},
                         {p["s"]: p["user_text"] for p in want["pairs"]},
                         "필드 순서가 본문을 다른 S 에 붙였다")

    def test_item_without_id_is_unmeasurable_not_silently_dropped(self):
        """id 를 못 읽은 항목은 «없던 답» 이 아니라 «못 읽은 답» 이다 → rc 3."""
        base = self._fixture()
        broken = base.replace('  - id: S4\n', '  - notid: S4\n', 1)
        self.assertNotEqual(broken, base)
        rc, d = self._run(broken)
        self.assertEqual(rc, 3, d)
        self.assertIn("unmeasurable", d)
        self.assertIn("id", d["unmeasurable"])

    def test_round_inline_comment_does_not_drop_the_pair(self):
        """`round: 1 # answered R1` 이 문자열로 읽혀 그 S 가 조용히 빠지면 안 된다."""
        base = self._fixture()
        old = '  - id: S2\n    source: chosen\n    round: 1\n'
        self.assertIn(old, base, "픽스처가 바뀌었다 — 이 단언이 공허하다")
        rc, d = self._run(base.replace(old, old.rstrip('\n') + ' # answered R1\n', 1))
        self.assertEqual(rc, 0, d)
        self.assertIn("S2", [p["s"] for p in d["pairs"]], "주석 하나로 S2 가 사라졌다")
        self.assertEqual(d["counts"]["skipped"], 1,
                         "주석 달린 round 가 skipped 로 세어졌다")

    def test_middle_round_gap_is_not_counted_as_terminal(self):
        """중간 라운드 결번은 «인터뷰가 끝났다» 가 아니다 (spec §3.2).

        실측(수정 전): `## R2` 만 `## Round 2` 로 바꾸면 terminal 이 1 → 3 으로 오르고
        적격 답이 6 → 4 로 줄었다. 뒤 라운드(R3·R4)가 인터뷰가 끝나지 않았음을 증명하는데도
        S2·S3 가 사람 표본에서 사라진다 — 측정이 **안전해 보이는 방향으로** 거짓말한다.
        """
        base = self._fixture()
        self.assertIn('## R2', base, "픽스처가 바뀌었다 — 이 단언이 공허하다")
        rc, d = self._run(base.replace('## R2', '## Round 2', 1))
        self.assertEqual(rc, 0, d)
        self.assertEqual(d["counts"]["terminal"], 1,
                         "결번이 terminal 로 세어졌다 — 뒤 라운드가 존재하는데도")
        self.assertEqual(d["counts"]["eligible"], 6,
                         "결번이 적격 짝을 줄였다 — 그 답들이 사람 표본에서 사라진다")
        # 그러나 «블록을 못 찾았다» 는 사실은 사라지지 않는다 — 그것이 정직한 공시 자리다.
        self.assertEqual(d["counts"]["with_block"], 4,
                         "결번으로 못 찾은 블록이 with_block 에서 드러나지 않는다")


if __name__ == "__main__":
    unittest.main()
