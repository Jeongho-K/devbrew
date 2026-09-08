# docreview 엔진 결함 (PR 1b) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `shared/docreview/` 엔진의 승인 차단 술어를 전방 포인터로 바꾸고, 그 술어가 서는 전제(재상승 예약 누적·상호배제·탈출구)를 함께 만들며, 검증 공백 넷을 닫는다 — 엔진에 호출자가 0 인 마지막 시점에.

**Architecture:** 만료된 채택(`expired`)이 승인을 막는지는 `decides` 레코드의 `superseded_by` 전방 포인터 하나가 정한다. 그 포인터는 재상승 루프가 후속 `decide` 를 실제로 만든 그 라운드의 `finalize` 안에서, 후속 id 가 확정된 뒤 한 번만 쓰인다. 예약은 누적하되 사용자 재결정과 상호배제이고, 후속이 끝내 안 생기면 사용자가 게이트 1단계에서 채택·기각으로 치운다.

**Tech Stack:** python 3.9.6(`match` 없음) · bash 3.2(macOS) · 셸 락(`shared/tests/*.sh`) + 변이 매트릭스(`test_docreview_mutations.sh`) + 행동 케이스(`shared/tests/fixtures/docreview/cases.sh`)

**Spec:** `docs/superpowers/specs/2026-09-06-document-review-redesign-design.md` — §6.4(승인의 도출) · §8.1 · §8.2 · §9 · §10 의 PR 1b 행 · §11 의 AC20~AC27 · §12 의 「수정(1b — 엔진 결함)」

## Global Constraints

- 이 PR 이 끝나도 **엔진의 호출자는 0** 이다. 어떤 skill 도 이 스크립트를 부르지 않는다 — 진입 skill 전환은 PR 2~5.
- 모든 python 실행에 `PYTHONDONTWRITEBYTECODE=1`. 같은 길이의 변이가 낡은 `.pyc` 를 못 넘어 거짓 GREEN·거짓 RED 를 낸다.
- 셸은 **bash 3.2** 기준(macOS). `<<<` here-string·`declare -A`·`${var^^}` 금지. `$()` 안에 heredoc 금지.
- 파이프에 rc 를 걸지 않는다 — `cmd | tail` 뒤의 `$?` 는 `tail` 의 것이다. 죽은 스크립트가 성공으로 읽힌다.
- 문서·주석의 코드 인용은 **심볼·앵커**로 한다. `path:NNN` 줄번호 인용 금지 — 편집이 즉시 낡게 만든다.
- **baseline(2026-09-07, main 기준):** `shared/tests` 21 GREEN · `plugins/quality-gates/tests` 셸 104 + python 20 GREEN · `plugins/spec-distill/tests` 셸 63 중 **선재 RED 1건**(`test_no_write_matcher_hooks_repo.sh` — 주 단언은 통과하고 자기 양성 대조가 실패) + python 21 GREEN. 그 하나 말고 RED 가 보이면 이 PR 이 만든 것이다. `test_handoff_design_mode.sh` 는 동시 부하에서 한 번 rc=1 을 낸 적이 있으니 빨개지면 **재현부터** 하라.
- 회귀 비교는 rc 만이 아니라 **실패 줄 수**도 본다. 이미 RED 인 파일 안의 새 실패는 rc 로는 안 보인다.
- 두 플러그인의 `.claude-plugin/plugin.json` bump 와 CHANGELOG 는 마지막 태스크에서. **버전 숫자는 머지 직전에 정한다** — 브랜치에서 못 박으면 먼저 머지되는 쪽이 이기고, 같은 값은 충돌 없이 병합돼 bump 가 조용히 사라진다.
- 매니페스트 경로는 `plugins/<name>/.claude-plugin/plugin.json` 이다(플러그인 루트가 아니다).

## File Structure

| 파일 | 이 PR 에서의 책임 |
|---|---|
| `shared/docreview/scripts/docreview_state.py` | `cmd_observe_diff`(예약 누적·dedup·포인터 초기화) · `gate_summary`(술어 + adopted 를 둘로 분리) · `render_gate`(차단 만료 렌더) · `cmd_decide`(만료 재결정 수용, 선택지 둘) |
| `shared/docreview/scripts/docreview_route.py` | `cmd_finalize` 의 재상승 루프(대상이 `expired` 일 때만 후속 생성 + id 확정 후 포인터 기록 + 미소비 예약 계수) · verdict 어휘 강제 계수 · 마지막에 함수 분해 |
| `shared/docreview/scripts/docreview_anchor.py` | `cmd_check_intent` 일반 경로의 앵커 실재 검사 |
| `shared/tests/fixtures/docreview/cases.sh` | 새 행동 케이스 아홉 |
| `shared/tests/test_docreview_state.sh` · `test_docreview_route.sh` · `test_docreview_intent.sh` | 새 케이스 호출 |
| `shared/tests/test_docreview_mutations.sh` | 새 변이 셀 열둘 |
| `plugins/quality-gates/tests/lib/extract_codex_invocations.py` · `codex_observation.sh` | 심볼릭 링크 배포 러너를 모집단에 넣는다(한 커밋) |

---

### Task 1: 심볼릭 링크 배포 러너를 두 수집기의 모집단에 넣는다

모집단을 바꾸는 유일한 태스크라 **첫 커밋**이다. 뒤 태스크의 RED 와 섞이면 무엇이 무엇을 깼는지 안 보인다.

**Files:**
- Modify: `plugins/quality-gates/tests/lib/extract_codex_invocations.py` (심볼릭 링크 skip 분기 + 그 자리 주석)
- Modify: `plugins/quality-gates/tests/lib/codex_observation.sh` (`obs_invoke` 의 `case` 표)
- Modify: `shared/tests/test_runner_disposition.sh` (헤더의 연기 기록)
- Test: `plugins/quality-gates/tests/test_sandbox_enforced.sh` (기존 락 — 새 단언 추가 없이 모집단이 넓어지는 것으로 잰다)

**Interfaces:**
- Consumes: 없음(이 PR 의 첫 태스크)
- Produces: `test_sandbox_enforced.sh` 의 후보 집합에 `run_docreview_codex_reviewer.sh` 가 들어온 상태. 뒤 태스크는 이 파일을 안 건드린다.

- [ ] **Step 1: 현재 모집단을 기록한다(변경 전 관측)**

```bash
cd /Users/jeonghokim/Downloads/devbrew
PYTHONDONTWRITEBYTECODE=1 python3 plugins/quality-gates/tests/lib/extract_codex_invocations.py . > /tmp/pop-before.txt 2>&1
grep -c docreview /tmp/pop-before.txt
```
Expected: `0` — 링크로 배포된 러너가 모집단에 없다. 이 0 이 이 태스크가 닫는 공백이다.
**`.`(root_dir)는 필수 인자다** — 빼면 스크립트가 `Usage:` 만 찍고 종료해 수정 여부와 «무관하게» 0 이 나온다. 그 0 은 관측이 아니다.

- [ ] **Step 2: 두 수집기와 `obs_invoke` arm 을 같은 편집으로 고친다**

세 편집이 **한 커밋**이어야 한다. `test_sandbox_enforced.sh` 는 두 수집기가 같은 후보 집합을 낸다는 standing assertion 을 갖고, `obs_known_candidates` 는 `declare -f obs_invoke` 로 case 라벨을 되읽어 대조한다 — 하나만 넓히면 그 자리에서 RED 다.

① `extract_codex_invocations.py` — 심볼릭 링크 skip 을 없앤다. 지금 그 자리는 `if not p.is_file() or p.is_symlink(): ... continue` 이고 바로 위 주석이 이 공백을 「PR 2 에서 판단한다」로 미뤄 뒀다. `p.is_file()` 은 심볼릭 링크를 따라가므로 링크 대상이 파일이면 True 다 — 즉 `is_symlink()` 절만 빼면 링크가 모집단에 든다:

```python
        if not p.is_file():
            continue
```

같은 자리의 주석은 **삭제하지 말고 갱신**한다 — 「왜 지금 링크를 포함하는가」가 다음 독자에게 필요한 사실이다:

```python
        # 심볼릭 링크로 배포된 러너도 모집단이다. `p.is_file()` 은 링크를 따라가므로
        # 링크 대상이 실재 파일이면 여기 든다. 예전엔 `p.is_symlink()` 로 건너뛰었고
        # 그 결과 `shared/docreview/` 의 러너가 이 보안 락에 한 번도 안 보였다 —
        # 위험 창(첫 호출자)이 열리기 전에 모집단을 먼저 넓힌다(설계 §16 S17).
```

② `codex_observation.sh` — 재귀 스캔이 링크를 포함하게 하고, `obs_invoke` 의 `case "$base" in` 표에 arm 을 더한다. 형제 arm(`run_spec_codex_reviewer.sh` 등)의 인자 형태를 그대로 따른다:

```bash
    run_docreview_codex_reviewer.sh)
      # 인자 넷 — <profile> <doc> <project_dir> <out_yaml>.
      "$cand" "$OBS_TMP/profile.md" "$OBS_TMP/doc.md" "$OBS_TMP" "$OBS_TMP/out.yaml" >/dev/null 2>&1
      ;;
```

인자 이름·개수는 `shared/docreview/scripts/run_docreview_codex_reviewer.sh` 의 실제 인자 파싱을 읽어 맞춘다. **추측하지 말고 그 파일을 열어 확인하라** — 형제 러너들끼리도 인자 형태가 다르다.

③ `shared/tests/test_runner_disposition.sh` 헤더의 연기 기록을 갱신한다. 지금 그 헤더는 「위험 창은 … PR 2 에 열린다 … 그때 도출기의 skip 을 다시 판단한다」라 적혀 있어, 이 커밋 뒤에는 거짓 인용이다. 「PR 1b 에서 모집단을 넓혔다(설계 §16 S17) — 이 락은 이제 링크 배포 러너를 본다」로 바꾼다.

- [ ] **Step 3: 모집단이 실제로 넓어졌는지 잰다**

```bash
cd /Users/jeonghokim/Downloads/devbrew
PYTHONDONTWRITEBYTECODE=1 python3 plugins/quality-gates/tests/lib/extract_codex_invocations.py . > /tmp/pop-after.txt 2>&1
grep -c docreview /tmp/pop-after.txt
```
Expected: `1` 이상(실측 기준 3 — 링크 둘 + 정본 하나). 0 이면 skip 제거가 안 먹은 것이다 — 스캔 root 가 `shared/` 를 안 덮는지 먼저 보라.

- [ ] **Step 4: 두 락을 돌린다**

```bash
cd /Users/jeonghokim/Downloads/devbrew
export PYTHONDONTWRITEBYTECODE=1
bash plugins/quality-gates/tests/test_sandbox_enforced.sh; echo "rc=$?"
bash plugins/quality-gates/tests/test_extract_codex_invocations.sh; echo "rc=$?"
bash shared/tests/test_runner_disposition.sh; echo "rc=$?"
```
Expected: 셋 다 rc=0. `test_sandbox_enforced.sh` 의 출력에 `run_docreview_codex_reviewer.sh` 가 이름으로 나와야 한다 — 안 나오면 모집단에 안 든 것이고, 「인자 표 부재」로 나오면 arm 이 안 붙은 것이다(둘은 다른 실패다).

- [ ] **Step 5: 러너의 격리 플래그에 이빨이 있는지 잰다(양성 대조)**

```bash
cd /Users/jeonghokim/Downloads/devbrew
cp shared/docreview/scripts/run_docreview_codex_reviewer.sh /tmp/runner.bak
sed -i.bak 's/-s read-only//' shared/docreview/scripts/run_docreview_codex_reviewer.sh
PYTHONDONTWRITEBYTECODE=1 bash plugins/quality-gates/tests/test_sandbox_enforced.sh; echo "변이 rc=$?"
cp /tmp/runner.bak shared/docreview/scripts/run_docreview_codex_reviewer.sh
rm -f shared/docreview/scripts/run_docreview_codex_reviewer.sh.bak
git diff --stat shared/docreview/scripts/run_docreview_codex_reviewer.sh
```
Expected: 변이 rc **≠ 0**(AC25 — 락이 이 러너의 `-s read-only` 를 실제로 잰다), 복원 후 `git diff` 빈 출력. 변이 rc 가 0 이면 모집단에는 들었지만 플래그를 안 재는 것이라 여기서 멈추고 왜인지 밝혀라.

- [ ] **Step 6: 커밋**

```bash
cd /Users/jeonghokim/Downloads/devbrew
git add plugins/quality-gates/tests/lib/extract_codex_invocations.py \
        plugins/quality-gates/tests/lib/codex_observation.sh \
        shared/tests/test_runner_disposition.sh
git commit -m "fix(qg): 심볼릭 링크 배포 codex 러너를 두 수집기 모집단에 넣는다 (AC25)"
```

---

### Task 2: 재상승 예약을 누적하고, dedup 하고, 소비되지 못한 것을 센다

**Files:**
- Modify: `shared/docreview/scripts/docreview_state.py` — `cmd_observe_diff` 의 `st["reraise"]` 대입
- Modify: `shared/docreview/scripts/docreview_route.py` — `cmd_finalize` 의 재상승 루프 + `route_report`
- Modify: `shared/docreview/scripts/docreview_state.py` — `gate_summary` 의 `counts` · `render_gate`
- Test: `shared/tests/fixtures/docreview/cases.sh` (새 케이스 둘) · `shared/tests/test_docreview_state.sh` · `shared/tests/test_docreview_mutations.sh` (새 셀 셋)

**Interfaces:**
- Consumes: 없음
- Produces: 디스크의 `st["reraise"]` 가 **누적 목록**이고 `finding_id` 로 유일하다. `route_report` 에 `reraise_unconsumed: <int>`. `gate_summary()["counts"]["reraise_unconsumed"]`. Task 3 의 전방 포인터가 이 위에 선다.

- [ ] **Step 1: 실패하는 케이스를 쓴다**

`shared/tests/fixtures/docreview/cases.sh` 에 추가한다. 첫 케이스는 「`finalize` 가 재상승 루프 전에 빠져나간 라운드의 예약이 살아남는가」다 — `no_pending_recritic` 조기 반환이 그 상황을 만든다(`prepare-recritic` 없이 `finalize` 를 부르면 `fail("no_pending_recritic")`).

```bash
case_AC21_reraise_accumulates() {
  local d; d="$(r1 "$PROF_SD/design-doc.md" "$FX/design-sample.md")"; seed_findings "$d" "[$F_DEC]"
  py docreview_state.py decide --state-dir "$d" --id 'aaaa0001#r1.1' --choice adopt --quote '채택' >/dev/null
  next_round "$d" "$FX/design-sample.md" >/dev/null        # 라운드 2 — 변경 없음 → expired + 예약
  assert_eq "$(st_yaml "$d" '[r["finding_id"] for r in st["reraise"]]')" "['aaaa0001#r1.1']" "AC21: 라운드 2 의 만료가 예약을 남긴다"
  # finalize 가 재상승 루프 «전에» 빠져나간다 — prepare-recritic 이 없으므로 no_pending_recritic.
  py docreview_route.py finalize --state-dir "$d" --doc "$FX/design-sample.md" --recritic-skipped >/dev/null 2>&1
  assert_eq "$(st_yaml "$d" '[r["finding_id"] for r in st["reraise"]]')" "['aaaa0001#r1.1']" "AC21: 조기 반환한 finalize 는 예약을 소비하지 않는다"
  next_round "$d" "$FX/design-sample.md" >/dev/null        # 라운드 3 — observe-diff 가 다시 돈다
  assert_eq "$(st_yaml "$d" '[r["finding_id"] for r in st["reraise"]]')" "['aaaa0001#r1.1']" "AC21: 다음 라운드 observe-diff 가 그 예약을 지우지 않는다(누적)"
  rm -rf "$d"
}
```

둘째 케이스는 dedup 이다 — 같은 `finding_id` 의 예약이 두 번 쌓이지 않는다:

```bash
case_AC21_reraise_dedup() {
  local d; d="$(r1 "$PROF_SD/design-doc.md" "$FX/design-sample.md")"; seed_findings "$d" "[$F_DEC]"
  py docreview_state.py decide --state-dir "$d" --id 'aaaa0001#r1.1' --choice adopt --quote '채택' >/dev/null
  next_round "$d" "$FX/design-sample.md" >/dev/null
  next_round "$d" "$FX/design-sample.md" >/dev/null
  next_round "$d" "$FX/design-sample.md" >/dev/null
  assert_eq "$(st_yaml "$d" 'len(st["reraise"]), len({r["finding_id"] for r in st["reraise"]})')" "(1, 1)" "AC21: 같은 계보의 예약은 라운드를 넘어도 하나다(dedup)"
  rm -rf "$d"
}
```

`shared/tests/test_docreview_state.sh` 의 케이스 호출 목록에 둘을 더한다(그 파일의 기존 호출 형식을 그대로 따르라).

- [ ] **Step 2: 실패를 확인한다**

```bash
cd /Users/jeonghokim/Downloads/devbrew
PYTHONDONTWRITEBYTECODE=1 bash shared/tests/test_docreview_state.sh; echo "rc=$?"
```
Expected: rc≠0. 셋째 단언(「다음 라운드 observe-diff 가 그 예약을 지우지 않는다」)이 `[]` 로 실패한다 — 지금은 대입이라 덮어쓴다.

- [ ] **Step 3: 누적 + dedup 을 구현한다**

`docreview_state.py` 의 `cmd_observe_diff` 에서 `st["reraise"] = reraise` 를 아래로 바꾼다:

```python
    # 재상승 예약은 누적한다(설계 §6.4) — `finalize` 가 재상승 루프 전에 빠져나간 라운드의
    # 예약이 살아남아야 그것을 «소비하는» finalize 가 후속을 만든다. 대입으로 덮어쓰면
    # 다음 라운드 observe-diff 가 그 예약을 지워 후속이 영영 안 생긴다.
    # dedup 은 `finding_id` 로 한다 — 같은 계보에 라운드당 후속 하나(AC21).
    pending = list(st.get("reraise") or [])
    seen = {r["finding_id"] for r in pending}
    for r in reraise:
        if r["finding_id"] in seen:
            continue
        pending.append(r)
        seen.add(r["finding_id"])
    st["reraise"] = pending
```

그리고 아래 `_emit(...)` 의 `"reraise": reraise` 를 `"reraise": pending` 으로 바꾼다 — 호출자가 보는 것이 디스크의 사실이어야 한다.

- [ ] **Step 4: 미소비 예약 계수를 더한다**

`docreview_route.py` 의 `cmd_finalize` 재상승 루프에서 `if not f0: continue` 가 지금 예약을 조용히 버린다. 버리지 말고 센다:

```python
    reraise_unconsumed = 0
    for r in st.get("reraise") or []:
        f0 = prev.get(r["finding_id"])
        if not f0:
            reraise_unconsumed += 1   # 대상 finding 부재 — 버리지 않고 센다(공시는 게이트가)
            continue
        final.append({...})           # 기존 본문 그대로
    st["reraise"] = []
```

`st["rounds"][str(n)]["route_report"]` 딕셔너리에 `"reraise_unconsumed": reraise_unconsumed,` 를 더하고, 같은 함수의 `out` 딕셔너리에도 같은 키를 더한다.

`docreview_state.py` 의 `gate_summary` 에서 counts 튜플을 넓힌다:

```python
    g["counts"] = {k: rep.get(k, 0) for k in ("rejected", "bucket_conflicts", "lineage_mismatch",
                                              "revived", "reraise_unconsumed")}
```

`render_gate` 의 기각 계수 줄에 한 항목을 더한다:

```python
    out.append("기각 %d건(재비판) · 사용자 기각 %d · drop %d · bucket 충돌 %d · 계보 지목 불일치 %d · 기각 계보 재상승 %d · 미소비 재상승 예약 %d"
               % (c["rejected"], c["user_rejected"], len(g["dropped"]), c["bucket_conflicts"],
                  c["lineage_mismatch"], c["revived"], c["reraise_unconsumed"]))
```

- [ ] **Step 5: 통과를 확인하고 회귀를 본다**

```bash
cd /Users/jeonghokim/Downloads/devbrew
export PYTHONDONTWRITEBYTECODE=1
red=""; for f in shared/tests/test_*.sh; do bash "$f" >/dev/null 2>&1 || red="$red $(basename $f)"; done; echo "RED:${red:- none}"
```
Expected: `RED: none`. `test_docreview_route.sh` 나 `test_docreview_state.sh` 가 빨개지면 기존 단언이 `reraise` 를 라운드-국소 목록으로 읽고 있던 것이다 — 그 단언을 누적 의미로 고쳐라(값을 맞추려 구현을 되돌리지 마라).

- [ ] **Step 6: 변이 셀 셋을 더한다**

`shared/tests/test_docreview_mutations.sh` 의 마지막 셀 뒤에 붙인다. 세 변이가 각각 **판정 `caught`** 여야 한다(단순 RED 가 아니다 — `classify_result` 가 traceback 을 `unmeasurable` 로 내므로 크래시 변이는 셀 자체를 RED 로 만든다):

```bash
# ⑬ 예약 누적 → 대입 복원. 조기 반환 라운드의 예약이 다음 observe-diff 에 사라진다.
mut reraise_overwrite case_AC21_reraise_accumulates sed_state \
  's/^    st\["reraise"\] = pending$/    st["reraise"] = reraise/'
# ⑭ dedup 제거 — 같은 계보의 예약이 라운드마다 쌓인다.
mut reraise_no_dedup case_AC21_reraise_dedup sed_state \
  's/^        if r\["finding_id"\] in seen:$/        if False:/'
# ⑮ 미소비 예약을 다시 조용히 버린다 — 계수가 0 으로 굳는다.
mut reraise_loss_uncounted case_AC21_unconsumed_counted sed_route \
  's/^            reraise_unconsumed += 1.*$/            pass/'
```

셀 ⑮ 가 지목하는 `case_AC21_unconsumed_counted` 를 `cases.sh` 에 더한다 — 대상 finding 이 없는 예약을 손으로 심고 `finalize` 를 태워 계수가 1 인지 본다:

```bash
case_AC21_unconsumed_counted() {
  local d; d="$(route_r1 "$PROF_SD/design-doc.md" "$FX/design-sample.md")"
  python3 "$FX/st_set_reraise.py" "$d/docreview-state.md" 'zzzz9999#r1.1'
  py docreview_route.py prepare-recritic --state-dir "$d" --critic "$FX/critic-nolayer2.txt" --codex "$FX/codex-failed.yaml" > "$d/prep2.json"
  py docreview_route.py finalize --state-dir "$d" --recritic "$FX/recritic-missing.txt" --doc "$FX/design-sample.md" > "$d/fin.json"
  assert_eq "$(jget "$d/fin.json" 'd["reraise_unconsumed"]')" "1" "AC21: 대상 finding 이 없는 예약은 버려지지 않고 계수된다"
  assert_eq "$(py docreview_state.py gate --state-dir "$d" | jgets 'd["counts"]["reraise_unconsumed"]')" "1" "AC21: 그 계수가 게이트에 실린다"
  rm -rf "$d"
}
```

헬퍼 `shared/tests/fixtures/docreview/st_set_reraise.py` 를 새로 만든다(형제 `st_get.py` 의 state 판독 방식을 그대로 재사용하되 쓰기다):

```python
#!/usr/bin/env python3
"""state 파일의 st["reraise"] 에 지정 finding_id 예약 하나를 심는다(픽스처 전용)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "shared" / "docreview" / "scripts"))
from docreview_state import load_state, save_state  # noqa: E402
d = str(pathlib.Path(sys.argv[1]).parent)
st = load_state(d)
st["reraise"] = [{"finding_id": sys.argv[2], "kind": "apply", "reason": "픽스처가 심은 미소비 예약"}]
save_state(d, st, "fixture: seed unconsumed reraise")
```

- [ ] **Step 7: 매트릭스를 돌린다**

```bash
cd /Users/jeonghokim/Downloads/devbrew
PYTHONDONTWRITEBYTECODE=1 bash shared/tests/test_docreview_mutations.sh; echo "rc=$?"
```
Expected: rc=0, 새 셀 셋이 전부 `caught`. `no_teeth` 가 나오면 그 케이스가 그 규칙을 안 재는 것이고, `unmeasurable` 이 나오면 변이가 크래시를 만든 것이다 — 둘은 다른 실패이고 고치는 방법도 다르다(전자는 케이스를, 후자는 sed 를 바꾼다).

- [ ] **Step 8: 커밋**

```bash
cd /Users/jeonghokim/Downloads/devbrew
git add shared/docreview/scripts/docreview_state.py shared/docreview/scripts/docreview_route.py \
        shared/tests/fixtures/docreview/cases.sh shared/tests/fixtures/docreview/st_set_reraise.py \
        shared/tests/test_docreview_state.sh shared/tests/test_docreview_mutations.sh
git commit -m "fix(docreview): 재상승 예약을 누적·dedup 하고 미소비 예약을 계수한다 (AC21)"
```

---

### Task 3: 전방 포인터 `superseded_by` — 술어·기록·초기화

이 PR 의 중심이다. **`case_T22b_expired_superseded_unblocks` 가 이 태스크에서 깨진다** — 그 케이스는 `seed_findings` 로 후속을 심어 차단이 풀리는지 보는데, `record-findings` 는 `PUBLIC_FIELDS` 필터를 지나므로 `superseded_by` 를 쓸 수 없다. 새 술어에서는 그 후속이 차단을 풀지 않는 것이 **옳은 동작**이다. 케이스를 고쳐라(구현을 되돌리지 마라).

**Files:**
- Modify: `shared/docreview/scripts/docreview_state.py` — `gate_summary`(술어 · `adopted` 분리) · `cmd_observe_diff`(새 permit 이 열릴 때 포인터 초기화)
- Modify: `shared/docreview/scripts/docreview_route.py` — `cmd_finalize` 재상승 루프(상태 가드 + id 확정 후 기록)
- Test: `shared/tests/fixtures/docreview/cases.sh`(T22b 재작성 + 새 케이스 셋) · `test_docreview_mutations.sh`(셀 셋)

**Interfaces:**
- Consumes: Task 2 의 누적 예약(`st["reraise"]` 는 누적 목록)
- Produces: `st["decides"][fid]["superseded_by"]` — 값은 후속 finding 의 최종 id 문자열, 없으면 키 부재. `gate_summary()` 가 `"adopted"`(채택 대기)와 `"blocked_expired"`(미승계 만료)를 **따로** 낸다. Task 4 의 렌더가 후자를 쓴다.

- [ ] **Step 1: 실패하는 케이스를 쓴다 — 비의무 후속 넷**

설계 AC20 ①. 네 후속(비차단 `ask` · `drop` · `defer` · 재비판 `reject`)이 각각 와도 차단이 유지돼야 한다. `cases.sh` 에 `F_DEC_R2` 형제 넷을 더한다 — 처분만 다르고 나머지는 같다:

```bash
# AC20 ① — 만료를 가리키지만 «의무를 지지 않는» 후속 넷. 처분만 다르다.
F_SUCC_ASK='{"id":"aaaa0001#r2.1","lineage":"aaaa0001#r1.1","bucket":"aaaa0001","supersedes":"aaaa0001#r1.1","origin":"auto","layer":2,"category":"ambiguity","anchor":"#12-files-to-modify","edit_scope":"#12-files-to-modify","disposition":"ask","summary":"후속: 물어보기","evidence":null,"blocks":[]}'
F_SUCC_DEFER='{"id":"aaaa0001#r2.1","lineage":"aaaa0001#r1.1","bucket":"aaaa0001","supersedes":"aaaa0001#r1.1","origin":"auto","layer":2,"category":"ambiguity","anchor":"#12-files-to-modify","edit_scope":"#12-files-to-modify","disposition":"defer","summary":"후속: plan 으로","evidence":null,"blocks":[]}'
F_SUCC_DROP='{"id":"aaaa0001#r2.1","lineage":"aaaa0001#r1.1","bucket":"aaaa0001","supersedes":"aaaa0001#r1.1","origin":"auto","layer":2,"category":"ambiguity","anchor":"#12-files-to-modify","edit_scope":"#12-files-to-modify","disposition":"drop","summary":"후속: 버림","evidence":null,"blocks":[]}'
F_SUCC_REJ='{"id":"aaaa0001#r2.1","lineage":"aaaa0001#r1.1","bucket":"aaaa0001","supersedes":"aaaa0001#r1.1","origin":"auto","layer":2,"category":"ambiguity","anchor":"#12-files-to-modify","edit_scope":"#12-files-to-modify","disposition":"decide","state":"rejected","summary":"후속: 재비판이 기각","evidence":"오탐","blocks":[],"kind":"pre"}'

case_AC20_nonobligation_successors_still_block() {
  local succ
  for succ in "$F_SUCC_ASK" "$F_SUCC_DEFER" "$F_SUCC_DROP" "$F_SUCC_REJ"; do
    local d; d="$(r1 "$PROF_SD/design-doc.md" "$FX/design-sample.md")"; seed_findings "$d" "[$F_DEC]"
    py docreview_state.py decide --state-dir "$d" --id 'aaaa0001#r1.1' --choice adopt --quote '채택' >/dev/null
    next_round "$d" "$FX/design-sample.md" >/dev/null      # 변경 없음 → expired
    seed_findings "$d" "[$succ]"
    local disp; disp="$(printf '%s' "$succ" | jgets 'd["disposition"] + ("/" + d["state"] if d.get("state") else "")')"
    assert_eq "$(py docreview_state.py gate --state-dir "$d" | jgets 'd["blocked_expired"], d["approval_ready"]')" \
      "(['aaaa0001#r1.1'], False)" "AC20①: 의무를 안 지는 후속($disp)은 차단을 풀지 않는다"
    rm -rf "$d"
  done
}
```

- [ ] **Step 2: 실패를 확인한다**

```bash
cd /Users/jeonghokim/Downloads/devbrew
PYTHONDONTWRITEBYTECODE=1 bash shared/tests/test_docreview_state.sh; echo "rc=$?"
```
Expected: rc≠0. 지금 술어는 역방향 스캔이라 네 후속 전부가 차단을 풀고, `blocked_expired` 키는 아예 없다.

- [ ] **Step 3: 술어를 바꾸고 `adopted` 를 둘로 나눈다**

`docreview_state.py` 의 `gate_summary` 에서 `superseded` 집합 계산과 `"adopted"` 항목을 통째로 바꾼다:

```python
    # 만료가 승인을 막는지는 «전방» 포인터 하나가 정한다(설계 §6.4). 역방향으로 세면
    # (「나를 가리키는 finding 이 있다」) 의무를 안 지는 후속 — 비차단 ask · drop ·
    # defer · 재비판 reject — 이 하나만 와도 차단이 풀린다. 라우터의 자동 계보 연결이
    # 지목 없는 finding 에도 supersedes 를 붙이기 때문이다. superseded_by 를 쓰는 곳은
    # 재상승 루프 하나뿐이라 그 기록은 의무의 증거다. 기록이 없으면 막는다 — fail-closed.
    g = {
        ...
        "adopted": sorted(i for i, d in dec.items() if d["state"] == "adopted"),
        "blocked_expired": sorted(i for i, d in dec.items()
                                  if d["state"] == "expired" and not d.get("superseded_by")),
        ...
    }
```

`approval_ready` 를 두 키 모두로 막는다:

```python
    g["approval_ready"] = (not g["open_decide"] and not g["adopted"]
                           and not g["blocked_expired"] and not g["unapplied_fix"])
```

- [ ] **Step 4: 재상승 루프가 포인터를 쓴다 — id 확정 뒤, 대상이 `expired` 일 때만**

`docreview_route.py` 의 재상승 루프는 `final.append(...)` 로 dict 만 만들고 id 는 한참 뒤 `it["id"] = "%s#r%d.%d"` 에서 배정된다. 그래서 기록은 **두 걸음**이다.

첫째, 루프에 상태 가드를 넣는다(설계 §6.4 ①) — 이미 재결정돼 `adopted` 인 항목에는 후속을 만들지도 포인터를 쓰지도 않는다. 이것이 「예약과 사용자 결정 중 먼저 온 하나만 후속을 만든다」의 절반이다:

```python
    for r in st.get("reraise") or []:
        f0 = prev.get(r["finding_id"])
        if not f0:
            reraise_unconsumed += 1
            continue
        d0 = st["decides"].get(r["finding_id"])
        if not d0 or d0.get("state") != "expired":
            continue          # 사용자가 이미 재결정했다 — 의무는 그 결정이 진다
        final.append({..., "supersedes": r["finding_id"], "_source": "reraise"})
    st["reraise"] = []
```

둘째, id 배정 루프(`it["id"] = "%s#r%d.%d" % (b, n, k)`) **뒤에**, 포인터를 한 번 쓴다:

```python
    # 전방 포인터(설계 §6.4) — 후속의 최종 id 가 확정된 뒤에만 쓸 수 있다. 쓰는 곳은
    # 여기 하나뿐이고, 대상이 지금 expired 인 경우로 이미 좁혀져 있다(위 가드).
    for it in everything:
        if it.get("_source") != "reraise":
            continue
        d0 = st["decides"].get(it.get("supersedes"))
        if d0 is not None and d0.get("state") == "expired":
            d0["superseded_by"] = it["id"]
```

- [ ] **Step 5: 포인터를 만료 «1회» 에 묶는다**

설계 §6.4 ②. 항목이 `expired` 를 벗어날 때 포인터를 비운다. `cmd_observe_diff` 의 permit 처리에서 `d["state"] = "applied"` 와 `d["state"] = "expired"` 둘 다에 앞서 초기화한다 — 재채택된 permit 이 열린 시점이 「이 만료 인스턴스가 끝난」 시점이다:

```python
        p["consumed"] = True
        d.pop("superseded_by", None)   # 이 만료 인스턴스는 끝났다 — 낡은 포인터가 다음 만료를 풀면 안 된다
        if hit:
            d["state"] = "applied"
            ...
```

- [ ] **Step 6: 재만료 케이스를 쓴다(AC20 ③)**

```bash
case_AC20_reexpiry_blocks_again() {
  local d; d="$(route_r1 "$PROF_SD/design-doc.md" "$FX/design-sample.md")"
  local gid; gid="$(fsum "$d" 'Non-goals' '["id"]')"
  py docreview_state.py decide --state-dir "$d" --id "$gid" --choice adopt --quote '채택' >/dev/null
  next_round "$d" "$FX/design-sample.md" >/dev/null        # 라운드 2 — 변경 없음 → expired
  py docreview_route.py prepare-recritic --state-dir "$d" --critic "$FX/critic-nolayer2.txt" --codex "$FX/codex-failed.yaml" > "$d/prep2.json"
  py docreview_route.py finalize --state-dir "$d" --recritic "$FX/recritic-missing.txt" --diff "$d/diff2.json" --doc "$FX/design-sample.md" > "$d/fin2.json"
  local succ; succ="$(jget "$d/fin2.json" '[x["id"] for x in d["findings"] if "expired" in x["summary"]][0]')"
  assert_eq "$(st_yaml "$d" 'st["decides"]["'"$gid"'"].get("superseded_by")')" "$succ" "AC20②: 재상승 루프가 후속 id 를 전방 포인터로 남긴다"
  assert_eq "$(py docreview_state.py gate --state-dir "$d" | jgets 'd["blocked_expired"]')" "[]" "AC20②: 포인터가 찍힌 만료는 더 막지 않는다"
  # 후속을 채택했는데 또 미적중 → 재만료. 낡은 포인터가 아니라 빈 포인터로 다시 막아야 한다.
  py docreview_state.py decide --state-dir "$d" --id "$succ" --choice adopt --quote '이번엔 적용' >/dev/null
  next_round "$d" "$FX/design-sample.md" >/dev/null        # 라운드 3 — 또 변경 없음
  assert_eq "$(st_yaml "$d" 'st["decides"]["'"$succ"'"]["state"], st["decides"]["'"$succ"'"].get("superseded_by")')" "('expired', None)" "AC20③: 재만료한 항목의 포인터는 비어 있다"
  assert_eq "$(py docreview_state.py gate --state-dir "$d" | jgets '"'"$succ"'" in d["blocked_expired"]')" "True" "AC20③: 재만료는 다시 막는다(낡은 포인터가 안 푼다)"
  rm -rf "$d"
}
```

- [ ] **Step 7: `case_T22b` 를 새 계약으로 고친다**

기존 T22b 의 둘째 단언(`seed_findings "$d" "[$F_DEC_R2]"` 뒤 「후속이 생기면 만료 항목은 안 막고」)은 이제 **거짓**이다 — `record-findings` 는 포인터를 못 쓴다. 그 단언을 뒤집어 그 사실 자체를 락으로 만든다:

```bash
  seed_findings "$d" "[$F_DEC_R2]"                        # record-findings 경로 — 포인터를 쓰지 않는다
  assert_eq "$(py docreview_state.py gate --state-dir "$d" | jgets 'd["blocked_expired"], d["approval_ready"]')" "(['aaaa0001#r1.1'], False)" "T22b: 후속 finding 이 «있어도» 포인터가 없으면 계속 막는다(역방향 스캔 금지)"
```

그 뒤 이어지던 「후속을 채택·적용하면 승인이 다시 열린다」 단언은 `case_AC20_reexpiry_blocks_again` 이 실제 `finalize` 경로로 이미 잰다 — T22b 에서는 지우고, 지웠다는 사실을 케이스 주석 한 줄로 남겨라(다음 독자가 커버리지 손실로 오해하지 않게).

- [ ] **Step 8: 변이 셀 셋 — 셋째가 변별 변이다**

```bash
# ⑯ 전방 포인터 대입 삭제 → 후속이 생겨도 영구히 막는다.
mut fwd_pointer_never_written case_AC20_reexpiry_blocks_again sed_route \
  's/^            d0\["superseded_by"\] = it\["id"\]$/            pass/'
# ⑰ 포인터 초기화 삭제 → 재만료를 낡은 포인터가 푼다(조용한 승인).
mut fwd_pointer_not_cleared case_AC20_reexpiry_blocks_again sed_state \
  's/^        d\.pop("superseded_by", None).*$/        pass/'
# ⑱ 술어를 역방향 supersedes 스캔으로 복원 — 이 셀이 「전방이냐 역방이냐」의 유일한 변별기다.
#    앞의 둘은 «막느냐 마느냐» 만 흔들고 방향을 구별하지 않는다.
mut predicate_backward_scan case_AC20_nonobligation_successors_still_block sed_state \
  's/if d\["state"\] == "expired" and not d\.get("superseded_by")/if d["state"] == "expired" and i not in {f.get("supersedes") for f in st["findings"].values() if f.get("supersedes")}/'
```

셀 ⑱ 의 치환 대상 문자열은 Step 3 에서 쓴 것과 **글자 그대로** 같아야 한다. 치환기는 매치 0 건에도 성공을 내므로, 안 맞으면 변이가 무동작이 되어 `no_teeth` 로 떨어진다 — 그때 케이스를 고치지 말고 **패턴을 먼저 의심하라**.

- [ ] **Step 9: 전체 실행**

```bash
cd /Users/jeonghokim/Downloads/devbrew
export PYTHONDONTWRITEBYTECODE=1
red=""; for f in shared/tests/test_*.sh; do bash "$f" >/dev/null 2>&1 || red="$red $(basename $f)"; done; echo "RED:${red:- none}"
```
Expected: `RED: none`, 새 셀 셋이 `caught`.

- [ ] **Step 10: 커밋**

```bash
cd /Users/jeonghokim/Downloads/devbrew
git add shared/docreview/scripts/ shared/tests/fixtures/docreview/cases.sh \
        shared/tests/test_docreview_state.sh shared/tests/test_docreview_mutations.sh
git commit -m "fix(docreview): 만료 차단을 전방 포인터 superseded_by 로 판정한다 (AC20)"
```

---

### Task 4: 탈출구 — 만료 재결정(채택·기각만)과 게이트 렌더

**Files:**
- Modify: `shared/docreview/scripts/docreview_state.py` — `cmd_decide`(수용 집합 · 선택지 · 예약 폐기) · `render_gate`
- Test: `shared/tests/fixtures/docreview/cases.sh` · `test_docreview_state.sh` · `test_docreview_mutations.sh`

**Interfaces:**
- Consumes: Task 3 의 `gate_summary()["blocked_expired"]`, Task 2 의 누적 예약
- Produces: `cmd_decide` 가 `expired` 를 받되 `--choice hold` 는 `fail("decide_hold_not_allowed_for_expired", ...)`. 재결정이 그 `finding_id` 의 예약을 `st["reraise"]` 에서 제거한다.

- [ ] **Step 1: 실패하는 케이스를 쓴다**

```bash
case_AC22_expired_escape_hatch() {
  local d; d="$(r1 "$PROF_SD/design-doc.md" "$FX/design-sample.md")"; seed_findings "$d" "[$F_DEC]"
  py docreview_state.py decide --state-dir "$d" --id 'aaaa0001#r1.1' --choice adopt --quote '채택' >/dev/null
  next_round "$d" "$FX/design-sample.md" >/dev/null        # expired + 예약
  # ① 렌더 본문에 차단 항목의 id 가 나온다.
  assert_eq "$(py docreview_state.py gate --state-dir "$d" --render | grep -c 'aaaa0001#r1.1')" "1" "AC22①: 차단 중인 만료 항목이 게이트 본문에 렌더된다"
  # ② 「보류」는 거부한다 — held 는 열린 decide 에도 차단 만료에도 안 들어 승인을 열어 버린다.
  py docreview_state.py decide --state-dir "$d" --id 'aaaa0001#r1.1' --choice hold --quote '나중에' >/dev/null 2>&1
  assert_eq "$?" "1" "AC22②: 만료의 「보류」는 거부된다"
  assert_eq "$(py docreview_state.py gate --state-dir "$d" | jgets 'd["approval_ready"]')" "False" "AC22②: 거부됐으므로 여전히 막힌다"
  # ③ 「기각」이 예약을 함께 폐기한다.
  py docreview_state.py decide --state-dir "$d" --id 'aaaa0001#r1.1' --choice reject --quote '이건 안 한다' >/dev/null
  assert_eq "$(st_yaml "$d" 'st["decides"]["aaaa0001#r1.1"]["state"], st["reraise"]')" "('rejected', [])" "AC22③: 만료 기각 → rejected + 미소비 예약 폐기"
  assert_eq "$(py docreview_state.py gate --state-dir "$d" | jgets 'd["approval_ready"]')" "True" "AC22③: 사용자가 치웠으므로 승인이 열린다"
  rm -rf "$d"
}
case_AC22_nonexpired_states_still_refused() {
  local d st
  for st in reject hold; do
    d="$(r1 "$PROF_SD/design-doc.md" "$FX/design-sample.md")"; seed_findings "$d" "[$F_DEC]"
    py docreview_state.py decide --state-dir "$d" --id 'aaaa0001#r1.1' --choice "$st" --quote '첫 결정' >/dev/null
    py docreview_state.py decide --state-dir "$d" --id 'aaaa0001#r1.1' --choice adopt --quote '다시' >/dev/null 2>&1
    assert_eq "$?" "1" "AC22③: 첫 결정이 $st 였던 항목의 재결정은 거부된다"
    rm -rf "$d"
  done
  d="$(r1 "$PROF_SD/design-doc.md" "$FX/design-sample.md")"; seed_findings "$d" "[$F_DEC]"
  py docreview_state.py decide --state-dir "$d" --id 'aaaa0001#r1.1' --choice adopt --quote '채택' >/dev/null
  next_round "$d" "$FX/design-sample-r2.md" >/dev/null     # 변경 관측 → applied
  py docreview_state.py decide --state-dir "$d" --id 'aaaa0001#r1.1' --choice reject --quote '되돌려' >/dev/null 2>&1
  assert_eq "$?" "1" "AC22③: applied 의 재결정도 거부된다"
  rm -rf "$d"
}
```

- [ ] **Step 2: 실패 확인 → `cmd_decide` 를 고친다**

`docreview_state.py` 의 `cmd_decide` 진입 가드를 바꾼다:

```python
    # 만료(expired)만 재결정을 받는다(설계 §6.4 탈출구) — 후속이 끝내 안 생기는 입력에
    # 사용자의 길이 없으면 영구 차단이다. rejected · held · applied 는 이미 누군가 의무를
    # 졌거나 소멸한 것이라 다시 열지 않는다.
    if d["state"] not in ("open", "expired"):
        return fail("decide_not_open", id=a.id, state=d["state"])
    # 만료의 선택지는 「채택」과 「기각」 둘뿐이다. 「보류」는 항목을 held 로 내려
    # 열린 decide 에도 차단 만료에도 안 들게 만들어 «한 번의 보류로 승인이 열린다» —
    # 탈출구가 아니라 구멍이다.
    if d["state"] == "expired" and a.choice == "hold":
        return fail("decide_hold_not_allowed_for_expired", id=a.id)
```

그리고 결정이 확정된 뒤(`st["decision_log"].append(entry)` 근처) 그 계보의 미소비 예약을 폐기한다 — 상호배제의 나머지 절반이다:

```python
    # 예약과 사용자 결정 중 «먼저 온 하나만» 후속을 만든다(설계 §6.4). 재결정이 왔으므로
    # 이 finding 의 미소비 예약은 폐기한다 — 안 그러면 뒤늦게 소비된 예약이 이미 처리된
    # 계보에 후속을 또 만들어 한 계보에 병렬 의무가 선다.
    st["reraise"] = [r for r in (st.get("reraise") or []) if r["finding_id"] != a.id]
```

- [ ] **Step 3: 렌더에 차단 만료를 낸다**

`render_gate` 의 `open_decide` 루프 **뒤에** 더한다:

```python
    for fid in g["blocked_expired"]:
        f = F[fid]
        d = st["decides"].get(fid) or {}
        tail = " — 「채택」은 원복 의무를 관측 없이 종결한다" if d.get("kind") == "post" else ""
        out.append("[만료·차단] %s — %s (채택 / 기각%s)" % (fid, f.get("summary"), tail))
```

`post` 꼬리는 설계 §6.4 의 마지막 문장이 요구한다 — 사후 만료의 「채택」은 원복을 관측 없이 끝내므로 그 뜻이 항목 옆에 보여야 한다.

- [ ] **Step 4: 통과 확인**

```bash
cd /Users/jeonghokim/Downloads/devbrew
export PYTHONDONTWRITEBYTECODE=1
bash shared/tests/test_docreview_state.sh; echo "rc=$?"
```
Expected: rc=0. `case_T20_hold_becomes_ask`(열린 `decide` 의 보류)는 계속 통과해야 한다 — 거부는 `expired` 에만 걸린다.

- [ ] **Step 5: 변이 셀 셋 — 셋째가 음의 락의 짝이다**

```bash
# ⑲ 만료 수용을 되돌린다 → 탈출구가 사라져 영구 차단.
mut expired_redecide_refused case_AC22_expired_escape_hatch sed_state \
  's/if d\["state"\] not in ("open", "expired"):/if d["state"] != "open":/'
# ⑳ 만료의 「보류」 거부를 지운다 → 보류 한 번에 승인이 열린다.
mut expired_hold_allowed case_AC22_expired_escape_hatch sed_state \
  's/^    if d\["state"\] == "expired" and a\.choice == "hold":$/    if False:/'
# ㉑ 가드를 세 상태까지 «넓힌다» — 음의 요구(rejected·held·applied 거부)는 넓히는 변이로만 잰다.
mut redecide_guard_widened case_AC22_nonexpired_states_still_refused sed_state \
  's/if d\["state"\] not in ("open", "expired"):/if False:/'
```

- [ ] **Step 6: 전체 실행 + 커밋**

```bash
cd /Users/jeonghokim/Downloads/devbrew
export PYTHONDONTWRITEBYTECODE=1
red=""; for f in shared/tests/test_*.sh; do bash "$f" >/dev/null 2>&1 || red="$red $(basename $f)"; done; echo "RED:${red:- none}"
git add shared/docreview/scripts/docreview_state.py shared/tests/fixtures/docreview/cases.sh \
        shared/tests/test_docreview_state.sh shared/tests/test_docreview_mutations.sh
git commit -m "fix(docreview): 만료 재결정 탈출구(채택·기각) + 게이트 렌더 (AC22)"
```

---

### Task 5: `check-intent` 일반 fix 경로의 앵커 실재 검사

**Files:**
- Modify: `shared/docreview/scripts/docreview_anchor.py` — `cmd_check_intent` 의 일반(비-insert-after) 분기
- Test: `shared/tests/fixtures/docreview/cases.sh` · `shared/tests/test_docreview_intent.sh` · `test_docreview_mutations.sh`

**Interfaces:**
- Consumes: 없음(독립)
- Produces: 사유 리터럴 `anchor_unresolved`. 거부는 `escalate()` 경로를 지나 그 `fix` 를 `escalated` 로 만든다.

- [ ] **Step 1: 실패하는 케이스를 쓴다**

기전: `classify_anchor` 는 앵커를 못 찾으면 `{"found": False, ..., "fix_allowed": "*" in prof["fix_anchors"]}` 를 낸다 — `fix_anchors: ["*"]` 프로필에서 **없는 앵커가 `fix_allowed`** 다. 그래서 슬러그 오타가 보호 부류 검사를 통째로 건너뛴다. generic 프로필이 그 와일드카드를 쓴다.

```bash
case_AC23_general_fix_anchor_unresolved() {
  local d; d="$(r1 "$PROF_QG/generic.md" "$FX/design-sample.md")"
  local f='{"id":"eeee0001#r1.1","lineage":"eeee0001#r1.1","bucket":"eeee0001","origin":"reviewer","layer":2,"category":"placeholder","anchor":"#12-files-to-modifyy","edit_scope":"#12-files-to-modifyy","disposition":"fix","summary":"슬러그 오타","evidence":null,"blocks":[]}'
  seed_findings "$d" "[$f]"
  local out; out="$(py docreview_anchor.py check-intent 'eeee0001#r1.1' --intent '#12-files-to-modifyy' --state-dir "$d" 2>&1)"; local rc=$?
  assert_eq "$rc" "1" "AC23: 스냅샷에 없는 앵커의 일반 fix 는 거부된다"
  assert_eq "$(printf '%s' "$out" | jgets 'd["reason"]')" "anchor_unresolved" "AC23: 사유는 anchor_unresolved — insert_after_unresolved 와 다른 문자열"
  assert_eq "$(st_yaml "$d" 'st["fixes"]["eeee0001#r1.1"]["state"], [e["finding_id"] for e in st["escalated"]]')" "('escalated', ['eeee0001#r1.1'])" "AC23: 거부는 escalate 경로 — 다음 라운드 decide 로 올라간다(단순 거부면 pending 으로 남아 영구히 승인을 막는다)"
  rm -rf "$d"
}
```

`--intent` 를 `edit_scope` 와 같게 준 이유는 앞선 `scope_outside_edit_scope` 가드에 먼저 걸리지 않게 하기 위해서다. 그 가드에 걸리면 이 케이스는 **엉뚱한 사유로** 통과한다 — 사유 문자열을 단언하는 이유가 그것이다.

- [ ] **Step 2: 실패 확인**

```bash
cd /Users/jeonghokim/Downloads/devbrew
PYTHONDONTWRITEBYTECODE=1 bash shared/tests/test_docreview_intent.sh; echo "rc=$?"
```
Expected: rc≠0 — 지금은 통과(`fix_allowed` True)라 `rc` 가 0 이다.

- [ ] **Step 3: 구현**

`cmd_check_intent` 의 `else:`(비-insert-after) 분기에서 `immutable` 검사 **뒤**, `fix_allowed` 검사 **앞**에 넣는다. 순서가 중요하다 — `immutable` 을 가장 먼저 보는 기존 규칙(그 사유가 더 강한 사실이다)을 지키고, 「없는 앵커」는 「fix_anchors 밖」보다 앞선다(없는 것을 「목록 밖」이라 부르면 사유가 흐려진다):

```python
    else:
        if cls["immutable"]:
            return escalate("anchor_immutable")
        if not cls["found"] and target != PREAMBLE:
            return escalate("anchor_unresolved")
        if not cls["fix_allowed"]:
            return escalate("anchor_not_in_fix_anchors")
        if cls["protected"]:
            return escalate("anchor_protected")
```

`docstring` 의 두 계약 설명에 한 문장을 더한다 — 「일반 경로도 앵커 실재를 본다. `fix_anchors: ["*"]` 프로필에서 없는 앵커가 `fix_allowed` 로 분류되기 때문이다(insert-after 경로의 `insert_after_unresolved` 와 사유 문자열이 다르다)」.

- [ ] **Step 4: 통과 확인 + 변이 셀**

```bash
# ㉒ 일반 경로의 앵커 실재 검사 제거 — 슬러그 오타가 보호 검사를 건너뛴다.
mut general_anchor_unresolved_off case_AC23_general_fix_anchor_unresolved sed_anchor \
  's/^        if not cls\["found"\] and target != PREAMBLE:$/        if False:/'
```

```bash
cd /Users/jeonghokim/Downloads/devbrew
export PYTHONDONTWRITEBYTECODE=1
red=""; for f in shared/tests/test_*.sh; do bash "$f" >/dev/null 2>&1 || red="$red $(basename $f)"; done; echo "RED:${red:- none}"
```
Expected: `RED: none`, 새 셀 `caught`.

- [ ] **Step 5: 커밋**

```bash
cd /Users/jeonghokim/Downloads/devbrew
git add shared/docreview/scripts/docreview_anchor.py shared/tests/fixtures/docreview/cases.sh \
        shared/tests/test_docreview_intent.sh shared/tests/test_docreview_mutations.sh
git commit -m "fix(docreview): check-intent 일반 fix 경로가 앵커 실재를 본다 (AC23)"
```

---

### Task 6: `_permit_covers` 의 라운드 경계에 이빨을 만든다

코드는 안 바꾼다. **락만 더한다** — 지금 그 비교를 지워도 네 락 144 단언이 전부 GREEN 이다.

**Files:**
- Test only: `shared/tests/fixtures/docreview/cases.sh` · `shared/tests/test_docreview_route.sh` · `test_docreview_mutations.sh`

**Interfaces:**
- Consumes: 없음
- Produces: `case_AC24_stale_permit_does_not_cover`

- [ ] **Step 1: 왜 지금 GREEN 인지 먼저 확인한다**

`_permit_covers` 는 `cmd_finalize` 의 `elif cls["protected"] and d != "decide" and not _permit_covers(st, n, it["anchor"])` 한 자리에서만 불린다. 그 분기를 permit 이 존재한 채 지나는 케이스(`case_T11_permit_keeps_disposition` · `case_T22_permit_expired_reraise`)는 **전부 permit 의 `round` 가 곧 현재 `n`** 이라, `int(p["round"]) == n` 을 지워도 결과가 안 변한다. `permits` 는 `consumed` 표시만 되고 **삭제되지 않으므로** 지난 라운드의 permit 이 그대로 남는다 — 그것이 이 락이 재야 할 상황이다.

```bash
cd /Users/jeonghokim/Downloads/devbrew
cp shared/docreview/scripts/docreview_route.py /tmp/route.bak
sed -i.bak 's/if int(p\["round"\]) == n and anchor in p\["apply_anchors"\]/if anchor in p["apply_anchors"]/' shared/docreview/scripts/docreview_route.py
export PYTHONDONTWRITEBYTECODE=1
red=""; for f in shared/tests/test_docreview_*.sh; do bash "$f" >/dev/null 2>&1 || red="$red $(basename $f)"; done; echo "변이 상태 RED:${red:- none}"
cp /tmp/route.bak shared/docreview/scripts/docreview_route.py; rm -f shared/docreview/scripts/docreview_route.py.bak
git diff --stat shared/docreview/scripts/docreview_route.py
```
Expected: `변이 상태 RED: none` — 그것이 이 태스크의 존재 이유다. 복원 후 `git diff` 는 빈 출력.

- [ ] **Step 2: 낡은 permit 케이스를 쓴다**

라운드 1 에 채택해 permit(라운드 2)을 만들고, 라운드 3 에서 같은 보호 앵커의 `fix` finding 이 오면 그 permit 은 이미 낡았으므로 **승격돼야** 한다:

```bash
case_AC24_stale_permit_does_not_cover() {
  local d; d="$(route_r1 "$PROF_SD/design-doc.md" "$FX/design-sample.md")"
  local gid; gid="$(fsum "$d" 'Non-goals' '["id"]')"
  py docreview_state.py decide --state-dir "$d" --id "$gid" --choice adopt --quote '채택' >/dev/null
  local anc; anc="$(st_yaml "$d" 'list(st["permits"].values())[0]["apply_anchors"][0]')"
  next_round "$d" "$FX/design-sample-r2.md" >/dev/null     # 라운드 2 — permit 소모
  next_round "$d" "$FX/design-sample-r2.md" >/dev/null     # 라운드 3 — permit 은 라운드 2 의 것, 이제 낡았다
  assert_eq "$(st_yaml "$d" 'st["round"], [p["round"] for p in st["permits"].values()]')" "(3, [2])" "AC24: 라운드 3 인데 permit 은 라운드 2 의 것(permits 는 삭제되지 않는다)"
  local t; t="$(mktemp -t cr-XXXXXX.txt)"
  printf '```docreview-layer1\n[]\n```\n```docreview-layer2\n- ref: c1\n  category: ambiguity\n  anchor: "%s"\n  disposition: fix\n  summary: "낡은 permit 앵커의 새 fix"\n```\n' "$anc" > "$t"
  py docreview_route.py prepare-recritic --state-dir "$d" --critic "$t" --codex "$FX/codex-failed.yaml" > "$d/prep3.json"
  py docreview_route.py finalize --state-dir "$d" --recritic "$FX/recritic-missing.txt" --diff "$d/diff3.json" --doc "$FX/design-sample-r2.md" > "$d/fin3.json"
  assert_eq "$(fsum "$d" '낡은 permit' '["disposition"]')" "decide" "AC24: 라운드가 지난 permit 은 보호 승격을 막지 못한다"
  assert_eq "$(fsum "$d" '낡은 permit' '["promotion"]')" "protected" "AC24: 승격 사유는 protected"
  rm -rf "$d" "$t"
}
```

`$anc` 가 실제로 **보호 부류**인지 먼저 확인하라 — 아니면 이 케이스는 승격 분기 자체에 안 들어가고 통과가 공허해진다:

```bash
cd /Users/jeonghokim/Downloads/devbrew
PYTHONDONTWRITEBYTECODE=1 python3 shared/docreview/scripts/docreview_anchor.py protected '<그 앵커>' \
  --profile plugins/spec-distill/references/docreview-profiles/design-doc.md \
  --snapshot <라운드 3 스냅샷 경로>
```
보호가 아니면 `design-doc.md` 프로필의 `protected_headings` 에 실제로 매칭되는 앵커를 가진 finding 으로 `gid` 를 바꿔라.

- [ ] **Step 3: 케이스가 GREEN 인지 확인하고 변이 셀을 더한다**

```bash
# ㉓ permit 의 라운드 경계 삭제 — 낡은 permit 이 영원히 보호 승격을 막는다.
mut permit_round_unbounded case_AC24_stale_permit_does_not_cover sed_route \
  's/if int(p\["round"\]) == n and anchor in p\["apply_anchors"\]/if anchor in p["apply_anchors"]/'
```

```bash
cd /Users/jeonghokim/Downloads/devbrew
export PYTHONDONTWRITEBYTECODE=1
bash shared/tests/test_docreview_mutations.sh; echo "rc=$?"
```
Expected: rc=0, `permit_round_unbounded` 가 `caught`. `no_teeth` 면 Step 2 의 앵커가 보호 부류가 아니거나 permit 이 그 앵커를 안 덮는 것이다.

- [ ] **Step 4: 커밋**

```bash
cd /Users/jeonghokim/Downloads/devbrew
git add shared/tests/fixtures/docreview/cases.sh shared/tests/test_docreview_route.sh \
        shared/tests/test_docreview_mutations.sh
git commit -m "test(docreview): _permit_covers 의 라운드 경계에 낡은-permit 픽스처로 이빨을 준다 (AC24)"
```

---

### Task 7: 재비판 verdict 어휘 밖 값을 강제로 계수한다

**Files:**
- Modify: `shared/docreview/scripts/docreview_route.py` — `cmd_finalize` 의 `vd = str(v.get("verdict") or "confirm")` 뒤 분기
- Test: `shared/tests/fixtures/docreview/cases.sh` · `test_docreview_route.sh` · `test_docreview_mutations.sh`

**Interfaces:**
- Consumes: 없음
- Produces: 어휘 밖 verdict 가 `Ledger.coerced` 에 남아 `adjudication_coerced` 로 나온다.

- [ ] **Step 1: 지금 무엇이 사라지는지 확인한다**

`vd` 뒤의 분기는 `reject` · `raise` 아닌 값을 전부 `else` 로 흘려 조용히 `confirm` 취급하고 원장에 아무것도 안 남긴다. 형제 처분 정규화(`normalize()`)는 같은 상황에서 `ledger.coerced("disposition", disp, None)` 을 남긴다 — 대칭이 깨져 있고, CLAUDE.md 의 「판정기가 항목을 버리면 센다」에 걸린다. 먼저 `cmd_finalize` 의 그 분기와 `normalize()` 의 `coerced` 호출을 **둘 다 열어 읽어라** — 인자 순서와 개수를 형제에서 가져온다(추측 금지).

- [ ] **Step 2: 실패하는 케이스**

```bash
case_AC27_unknown_verdict_coerced() {
  local d; d="$(route_r1 "$PROF_SD/design-doc.md" "$FX/design-sample.md" "$FX/critic-r1.txt" "$FX/codex-failed.yaml" "--skip")"
  py docreview_route.py prepare-recritic --state-dir "$d" --critic "$FX/critic-r1.txt" --codex "$FX/codex-failed.yaml" > "$d/prep.json"
  local rt; rt="$(mktemp -t rt-XXXXXX.txt)"
  printf '```docreview-recritic\nverdicts:\n  - f: "f1"\n    verdict: maybe\nadded: []\n```\n' > "$rt"
  py docreview_route.py finalize --state-dir "$d" --recritic "$rt" --doc "$FX/design-sample.md" > "$d/fin.json"
  assert_eq "$(jget "$d/fin.json" 'd["adjudication_coerced"] >= 1')" "True" "AC27(1b): 어휘 밖 verdict 는 조용히 confirm 이 되지 않고 coerced 로 계수된다"
  rm -rf "$d" "$rt"
}
```

- [ ] **Step 3: 구현 — `else` 앞에 어휘 검사**

```python
        if vd == "reject":
            ...
        elif vd == "raise":
            ...
        else:
            if vd != "confirm":
                # 어휘 밖 값을 조용히 confirm 으로 흘리지 않는다 — 형제 normalize() 가
                # 처분에 대해 하는 것과 같은 계약(CLAUDE.md 「판정기가 항목을 버리면 센다」).
                L.coerced("verdict", vd, "confirm")
            ...
```
`L.coerced` 의 인자 순서·개수는 `normalize()` 의 호출을 그대로 따른다.

- [ ] **Step 4: 변이 셀 + 실행 + 커밋**

```bash
# ㉔ 어휘 밖 verdict 의 강제 계수 제거 — 다시 조용히 confirm 이 된다.
mut unknown_verdict_silent case_AC27_unknown_verdict_coerced sed_route \
  's/^                L\.coerced("verdict", vd, "confirm")$/                pass/'
```

```bash
cd /Users/jeonghokim/Downloads/devbrew
export PYTHONDONTWRITEBYTECODE=1
red=""; for f in shared/tests/test_*.sh; do bash "$f" >/dev/null 2>&1 || red="$red $(basename $f)"; done; echo "RED:${red:- none}"
git add shared/docreview/scripts/docreview_route.py shared/tests/fixtures/docreview/cases.sh \
        shared/tests/test_docreview_route.sh shared/tests/test_docreview_mutations.sh
git commit -m "fix(docreview): 재비판 verdict 어휘 밖 값을 coerced 로 계수한다 (AC27 1b 절반)"
```

---

### Task 8: `cmd_finalize` 분해 + AC26 오라클 + 릴리스

**마지막 커밋**이다. 동작을 바꾸지 않는다. 여기까지의 모든 동작 변경이 이미 커밋돼 있어야 「분해가 무엇을 깼나」가 구별된다.

**Files:**
- Modify: `shared/docreview/scripts/docreview_route.py` — `cmd_finalize` 분해
- Modify: `shared/tests/test_docreview_mutations.sh` — 새 셀 다섯 + 치환 앵커 적중 검사
- Create: `shared/tests/fixtures/docreview/golden/` — 대표 `finalize` 시나리오의 골든 출력
- Modify: 두 플러그인의 `CHANGELOG.md` · `.claude-plugin/plugin.json` · `README.md`

**Interfaces:**
- Consumes: Task 2~7 의 모든 변경
- Produces: PR 1b 의 최종 상태

- [ ] **Step 1: 분해 «전에» 골든을 뜬다 — 이것이 오라클의 절반이다**

변이 매트릭스 판정 비교만으로는 「동작 무변경」을 못 잰다(셀 밖 동작 변화가 통과한다). 대표 시나리오 셋의 `finalize` 출력과 state 를 먼저 고정한다:

```bash
cd /Users/jeonghokim/Downloads/devbrew
mkdir -p shared/tests/fixtures/docreview/golden
export PYTHONDONTWRITEBYTECODE=1
for c in case_T11_permit_keeps_disposition case_T22_reraise_appears_in_next_round case_T05_T06_reject; do
  ( REPO_ROOT="$(pwd)"; SCRIPTS="$(pwd)/shared/docreview/scripts"
    . shared/tests/assert.sh; . shared/tests/fixtures/docreview/cases.sh
    "$c" ) > "shared/tests/fixtures/docreview/golden/$c.out" 2>&1
done
wc -l shared/tests/fixtures/docreview/golden/*.out
```
케이스가 자기 임시 디렉토리를 지우므로 `fin.json` 자체는 안 남는다 — 골든은 **단언별 통과/실패 줄**이다. 그것으로 충분하다: 분해가 어떤 단언의 결과를 바꾸면 diff 에 뜬다.

- [ ] **Step 2: 분해가 깨뜨리기 쉬운 넷에 셀을 세운다 — 분해 «전에»**

이 Step 을 쓸 당시 매트릭스에는 계보 해소 2패스 순서 · `blocks` 재매핑 · `escalated` 이월 · bucket 충돌 계수를 겨눈 셀이 **하나도 없다**(셀 수는 그 뒤로 늘었다 — 현재 값은 `grep -cE '^mut(_expect)? ' shared/tests/test_docreview_mutations.sh` 가 센다. 리터럴을 다시 박으면 같은 방식으로 다시 낡는다). 분해 전에 세워야 분해가 그것을 깼을 때 소리가 난다. 각 셀은 그 규칙을 하향으로 뒤집는 최소 치환이어야 하고, 판정이 `caught` 여야 한다. 지목할 케이스는 각각 `cases.sh` 에서 그 규칙을 실제로 지나는 것을 골라라 — 없으면 케이스를 먼저 만들어라(그 자체가 커버리지 공백의 증거다).

다섯째 셀은 이 PR 의 fail-closed 를 떠받치는 불변식이다: **재상승 후속은 `items` 에 안 들어가 same_as 흡수 · 재비판 `reject` · 처분 강제를 지나지 않는다.** 재상승 계보를 겨눈 재비판 픽스처를 넣어도 후속이 `open decide` 로 남는지 재라.

- [ ] **Step 3: 분해한다**

`cmd_finalize` 를 책임 단위로 쪼갠다. 최소한 이 넷은 각각 함수여야 한다 — 재비판 verdict 처리 · 사후/이월 auto decide 생성(얼림 diff · escalated · reraise) · id/계보 해소 · 보고서 조립. 시그니처는 구현자가 정하되 **전역 상태를 인자로 넘기고 반환값으로 돌려준다**(`nonlocal` 을 늘리지 마라 — 그것이 쪼갠 함수를 다시 붙여 놓는다).

- [ ] **Step 4: 오라클 셋을 전부 돌린다**

```bash
cd /Users/jeonghokim/Downloads/devbrew
export PYTHONDONTWRITEBYTECODE=1
# ① 골든 동치
for c in case_T11_permit_keeps_disposition case_T22_reraise_appears_in_next_round case_T05_T06_reject; do
  ( REPO_ROOT="$(pwd)"; SCRIPTS="$(pwd)/shared/docreview/scripts"
    . shared/tests/assert.sh; . shared/tests/fixtures/docreview/cases.sh
    "$c" ) > "/tmp/$c.after" 2>&1
  diff "shared/tests/fixtures/docreview/golden/$c.out" "/tmp/$c.after" && echo "골든 동치: $c"
done
# ② 행동 케이스 전수
red=""; for f in shared/tests/test_*.sh; do bash "$f" >/dev/null 2>&1 || red="$red $(basename $f)"; done; echo "RED:${red:- none}"
# ③ 변이 매트릭스 — 판정이 셀마다 같은가
bash shared/tests/test_docreview_mutations.sh > /tmp/mut-after.txt 2>&1; echo "rc=$?"
grep -c "^  ✓" /tmp/mut-after.txt
```
Expected: 골든 셋 동치 · `RED: none` · 매트릭스 rc=0.

- [ ] **Step 5: 치환 앵커가 여전히 적중하는지 확인한다 — 조용한 무동작 잡기**

치환기는 **매치 0 건에도 성공을 낸다.** 분해로 패턴이 사라지면 변이가 아무것도 안 바꾸고 셀이 `no_teeth` 로 떨어지는데, 그 사유는 「락이 규칙을 안 잰다」가 아니라 「패턴이 안 맞는다」다 — 오도된다. 매트릭스 출력에 `no_teeth` 가 하나라도 있으면 **먼저 패턴을 의심하라**:

```bash
cd /Users/jeonghokim/Downloads/devbrew
grep -n "안 잡힘" /tmp/mut-after.txt || echo "no_teeth 없음"
```
Expected: `no_teeth 없음`. 있으면 그 셀의 치환 문자열을 분해 후 코드에 맞춰 갱신하고, **갱신했다는 사실을 셀 주석에 남겨라**(다음 독자가 「이 셀은 원래 무엇을 겨눴나」를 잃지 않게).

- [ ] **Step 6: 릴리스 — 버전은 여기서 «머지 직전» 값으로 정한다**

```bash
cd /Users/jeonghokim/Downloads/devbrew
git fetch origin
for p in spec-distill quality-gates; do
  printf "%s origin/main=" "$p"
  git show origin/main:plugins/$p/.claude-plugin/plugin.json | python3 -c 'import json,sys;print(json.load(sys.stdin)["version"])'
done
```
그 값에서 **minor 를 하나 올린다**(둘 다 새 surface 없는 동작 수정이지만 게이트 술어가 바뀌므로 patch 가 아니다). 브랜치를 딴 시점의 값이 아니라 **지금 `origin/main` 의 값**을 기준으로 하라 — 그 사이 다른 PR 이 선점했으면 같은 값을 쓰게 되고, 같은 값은 **충돌 없이 auto-merge 되어 이쪽 bump 가 조용히 사라진다.** 정한 뒤 확인:

```bash
cd /Users/jeonghokim/Downloads/devbrew
for p in spec-distill quality-gates; do
  git merge-tree "$(git merge-base origin/main HEAD)" origin/main HEAD \
    | grep -A3 "plugins/$p/.claude-plugin/plugin.json" | head -8
done
```
충돌 목록이 아니라 **병합 결과의 값**을 읽어라.

두 `CHANGELOG.md` 에 `## [<version>] — 2026-09-07` 블록을 Added/Changed/Fixed 로 쓴다. `README.md` 의 「Principles Instantiated」에 이 PR 이 구현한 것을 한 줄 더한다(전방 포인터 = 「판정기가 항목을 버리면 센다」와 fail-closed 의 instantiation).

- [ ] **Step 7: 최종 전수 실행 — 셸과 python 둘 다**

```bash
cd /Users/jeonghokim/Downloads/devbrew
export PYTHONDONTWRITEBYTECODE=1
red=""
for f in $(find shared/tests plugins/*/tests -name 'test_*.sh' | grep -v '/spike/'); do
  bash "$f" >/dev/null 2>&1 || red="$red $f"
done
echo "셸 RED:${red:- none}"
# python 은 **플러그인 tests/ 최상위만** 돈다 — 하위 디렉토리(fixtures/·oracle/)에는
# 다른 테스트의 «입력»인 파일들이 산다(의도적으로 실패하는 픽스처 · 숨김 오라클).
# 재귀로 돌리면 유령 RED 6건이 매번 뜨고, 유령 RED 는 곧 풍경이 되어 진짜를 가린다.
# 셸 쪽과 규칙이 «다른» 이유가 이것이다: 셸의 tests/harness/ 에는 진짜 락이 있었다.
for P in spec-distill quality-gates; do
  for f in plugins/$P/tests/test_*.py; do
    ( cd "plugins/$P/tests" && python3 -m unittest "$(basename "${f%.py}")" ) >/dev/null 2>&1 || echo "python RED: $f"
  done
done
```
Expected: 셸 RED 는 **선재 둘뿐**(`test_no_write_matcher_hooks_repo.sh` · `harness/test_skill_orchestration_behavior.sh` — Global Constraints 참조), python RED 없음. 다른 이름이 나오면 이 PR 이 만든 것이다 — 단 flaky 둘은 단독 재실행으로 재현부터 하라.

- [ ] **Step 8: 커밋 + PR**

```bash
cd /Users/jeonghokim/Downloads/devbrew
git add -A
git commit -m "refactor(docreview): cmd_finalize 분해 + AC26 오라클 · 릴리스"
git push -u origin feature/docreview-engine-defects
```
PR 본문에는 ① 무엇을 고쳤나(결함 일곱) ② 검증(변이 셀 몇 개가 새로 `caught` 인가, 골든 동치, baseline 대비 회귀 0) ③ **의도적으로 안 고친 것**(있으면 근거와 함께 — PR 2 로 넘기는 목록이 여기 남는다) ④ 버전과 그 값을 정한 방법을 적는다.

---

## Self-Review

**1. Spec coverage** — AC20(Task 3) · AC21(Task 2) · AC22(Task 4) · AC23(Task 5) · AC24(Task 6) · AC25(Task 1) · AC26(Task 8) · AC27 1b 절반(Task 7). AC27 의 나머지 절반(실제 agent 출력과의 스키마 합치)은 설계가 PR 2 로 명시했다. §6.4 의 넷(전방 포인터 · 만료 1회 결속 · 예약 누적/상호배제 · 탈출구)이 Task 2~4 에 있다. §12 의 1b 파일 목록 전부가 어느 태스크엔가 있다.

**2. Placeholder scan** — Task 6 Step 2 의 `<그 앵커>` · `<라운드 3 스냅샷 경로>` 와 Task 8 Step 2 의 「지목할 케이스를 골라라」는 **의도적으로 열린 자리**다. 전자는 프로필의 `protected_headings` 실측이 필요하고(플랜이 값을 박으면 프로필이 바뀔 때 조용히 틀린다), 후자는 어느 케이스가 그 규칙을 지나는지가 앞 태스크들의 결과에 달렸다. 둘 다 「무엇을 어떻게 확인하는가」를 함께 적었으므로 구현자가 추측하지 않는다.

**3. Type consistency** — `superseded_by` 는 전 태스크에서 `st["decides"][fid]` 의 필드이고 값은 finding id 문자열이다(findings 쪽이 아니다 — `PUBLIC_FIELDS` 를 안 건드린다). `blocked_expired` 는 `gate_summary()` 의 키로 Task 3 이 만들고 Task 4 의 렌더가 쓴다. `reraise_unconsumed` 는 Task 2 가 `route_report` 와 `counts` 양쪽에 같은 이름으로 넣는다.

**4. 이 플랜이 못 정한 것** — Task 1 의 `obs_invoke` arm 인자 형태와 Task 7 의 `L.coerced` 시그니처는 **실제 파일을 열어 형제에서 가져오라**고만 적었다. 플랜이 값을 박으면 그것이 틀렸을 때 구현자가 플랜을 믿고 틀린 값을 쓴다.
