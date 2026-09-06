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


class UncountableIsNotZero(unittest.TestCase):
    """v0.56.0 B1/B2/B4 — 「셀 수 없음」이 「0」으로 둔갑하지 않는다.

    넷 다 스위트를 red 로 만들지 않는 부류였다: 셋은 그럴듯한 숫자를 내고, 넷째는
    이미 부분 출력을 낸 뒤 죽어 실패 기록조차 남기지 않았다.
    """

    def _fence(self, body):
        return "머리말\n```depth-audit\n%s\n```\n" % body

    def test_unreadable_fence_is_unavailable_not_measured_zero(self):
        """항목을 하나도 못 읽은 펜스는 `unavailable` 이다.

        실측(수정 전): `S1: dug` 처럼 항목 마커가 계약과 다른 펜스를 먹이면
        `dug 0 · not_dug 0 · held 0 · unavailable 0` — 즉 **「재 보니 0」** 으로 기록됐다.
        auditor 의 실제 판정 둘이 소리 없이 사라진 채로.
        """
        raw = self._fence("S1: dug — 새 위험을 끌어냈다\nS3: not_dug — 되풀이뿐")
        with tempfile.TemporaryDirectory() as td:
            rc, out, rec = run(td, auditor=raw)
            self.assertEqual(rc, 0, out)
            self.assertTrue(rec["auditor"]["unavailable"],
                            "판독 실패가 «측정했고 0» 으로 기록됐다: %r" % (rec["auditor"],))
            self.assertIn("unavailable 1", out)

    def test_partially_unreadable_fence_counts_the_lines_it_dropped(self):
        """일부만 읽힌 펜스 — 못 읽은 줄이 **계수**돼야 한다.

        항목이 0 인 펜스는 위 테스트가 `unavailable` 로 잡지만, **일부** 항목이 읽히면
        `unavailable` 은 False 다. 그때 못 읽은 줄을 그냥 버리면 auditor 의 판정 하나가
        회계에 아무 흔적도 남기지 않고 사라진다 — 「측정했다」와 구분되지 않는다.
        (실측: 이 케이스가 없으면 «인식 못 한 줄 계수» 를 통째로 지워도 스위트가 green.)
        """
        raw = self._fence('- s: S1\n  label: dug\n  reason: "ok"\n'
                          'S3: not_dug — 형식이 다른 줄')
        with tempfile.TemporaryDirectory() as td:
            rc, out, rec = run(td, auditor=raw)
            self.assertEqual(rc, 0, out)
            self.assertFalse(rec["auditor"]["unavailable"],
                             "일부는 읽혔는데 전체를 판독 실패로 밀었다")
            self.assertEqual(rec["auditor"]["dug"], 1, out)
            self.assertIn("인식 못 한 줄", out,
                          "못 읽은 줄이 세어지지도 공시되지도 않았다:\n%s" % out)

    def test_wellformed_fence_reports_no_unread_lines(self):
        """음의 짝 — 정상 펜스에서 「인식 못 한 줄」이 뜨면 오탐이다."""
        with tempfile.TemporaryDirectory() as td:
            _, out, _ = run(td)
            self.assertNotIn("인식 못 한 줄", out)

    def test_empty_fence_still_unavailable(self):
        """음의 짝 — 원래도 unavailable 이던 경로가 그대로인지."""
        with tempfile.TemporaryDirectory() as td:
            _, out, rec = run(td, auditor="```depth-audit\n```\n")
            self.assertTrue(rec["auditor"]["unavailable"])

    def test_wellformed_fence_is_not_falsely_unavailable(self):
        """양의 짝 — 정상 펜스를 «판독 실패» 로 밀어 넣지 않는지.

        위 둘만 두면 `return None` 을 무조건 하도록 만들어도 통과한다.
        """
        with tempfile.TemporaryDirectory() as td:
            _, out, rec = run(td)
            self.assertFalse(rec["auditor"]["unavailable"])
            self.assertEqual(rec["auditor"]["dug"], 2)

    def test_conflicting_labels_for_one_s_are_counted_not_absorbed(self):
        """같은 S 의 상충하는 두 판정은 흡수돼 사라지면 안 된다.

        실측(수정 전): `not_dug` 뒤에 온 `dug` 가 앞엣것을 덮어써 `dug 1` 이 되고
        회계에는 `흡수 0 · 보류 0` 이 남았다 — 모순이 공시 없이 사라졌다.
        """
        raw = self._fence('- s: S1\n  label: not_dug\n  reason: "첫"\n'
                          '- s: S1\n  label: dug\n  reason: "충돌"')
        with tempfile.TemporaryDirectory() as td:
            rc, out, rec = run(td, auditor=raw)
            self.assertEqual(rc, 0, out)
            self.assertEqual(rec["auditor"]["dug"], 0, out)
            self.assertEqual(rec["auditor"]["not_dug"], 0, out)
            self.assertGreaterEqual(rec["auditor"]["held"], 1,
                                    "판정 충돌이 계수되지 않았다: %r" % (rec["auditor"],))
            self.assertIn("상충하는 판정", out)

    def test_duplicate_identical_labels_are_absorbed_and_disclosed(self):
        """같은 라벨의 중복은 흡수다 — 소실이 아니지만 **계수는 한다**."""
        raw = self._fence('- s: S1\n  label: dug\n  reason: "첫"\n'
                          '- s: S1\n  label: dug\n  reason: "같은 판정"')
        with tempfile.TemporaryDirectory() as td:
            _, out, rec = run(td, auditor=raw)
            self.assertEqual(rec["auditor"]["dug"], 1)
            self.assertEqual(rec["auditor"]["held"], 0)
            self.assertIn("흡수 1", out)

    def test_bad_agreement_value_keeps_the_always_exit_0_contract(self):
        """`agreement` 이형 값이 uncaught ValueError 로 계약을 깨면 안 된다 (spec C5).

        실측(수정 전): `int()` 변환이 예외 처리 «밖» 이라 `["bad",1]` 하나가
        `condition_line()` 안에서 rc=1 을 냈고, **이미 세 줄이 출력된 뒤**라 실패 기록도
        남지 않았다.
        """
        prior = [prior_record(1, 1, 1, 2) for _ in range(4)]
        bad = prior_record(1, 1, 0, 0)
        bad["human"]["agreement"] = ["bad", 1]
        with tempfile.TemporaryDirectory() as td:
            rc, out, rec = run(td, prior=prior + [bad])
            self.assertEqual(rc, 0, "항상 exit 0 계약이 깨졌다:\n%s" % out)
            self.assertIn("판정자 조건:", out, "조건 줄 앞에서 죽었다")
            self.assertIn("셀 수 없음", out, "판독 불가가 표면화되지 않았다")

    def test_skipped_is_visible_in_both_record_and_display(self):
        """`skipped` 는 영구 기록과 표시 계수 **양쪽에** 실린다.

        산출자는 늘 세고 있었는데 소비자가 둘 다에서 빼는 바람에, 빠진 답이 있다는
        사실 자체가 하류에서 사라졌다 — 그러면 «전부 쟀다» 와 구분되지 않는다.
        """
        with tempfile.TemporaryDirectory() as td:
            _, out, rec = run(td)
            self.assertEqual(rec["pairs"]["skipped"], PAIRS["counts"]["skipped"])
            self.assertIn("- 깊이 측정(형식): 짝 7 중 되비추기 블록 있음 6 · 내용 있는 줄 ≥1 5"
                          " · terminal 1 · round 불명 1", out)


if __name__ == "__main__":
    unittest.main()
