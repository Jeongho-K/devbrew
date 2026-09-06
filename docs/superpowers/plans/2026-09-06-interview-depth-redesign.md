# 인터뷰 깊이 재설계 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** spec-distill `conducting-interview` 의 매 라운드가 직전 사용자 답에서 도출한 «직전 답에서 — S<k>» 블록으로 시작하고, 차원은 사용자 발화 앵커(`S<N>`)를 인용해야만 닫히며, 종료 시 깊이가 스크립트·에이전트·사람 세 층으로 audit 과 인터뷰별 측정 파일에 기록되게 한다. Phase 0(`framing-requests`)에는 seed «다시 검증할 것» 문단·첫 라운드 워크트리·handoff 직전 커밋 셋만 붙는다.

**Architecture:** (1) 결정론 게이트 `check_brief.py` 에 닫힘-앵커 검사와 coverage-mapper 예산 검사를 더하고 기존 fixture 86개를 스크립트로 일괄 정합시킨다. (2) 새 스크립트 둘(`depth_pairs.py` 짝 추출·표본, `depth_record.py` 병합·기록·조건 판정)과 도구 0 에이전트 하나(`depth-auditor`)가 종료 직전 Step A.7 에서 돈다. (3) SKILL 산문은 4-block·teach-beat·정체 트리거를 잃고 라운드 규약·닫힘·재개방·dispatch 규칙을 얻는다 — 락은 전부 블록 스코프 + mutation. (4) Phase 0 은 §4.1(seed 규약)·§4.2(워크트리, 별 task 묶음) 둘로 나뉘고 §4.2 는 Task 1 실측 결과에 맞춰 명령을 확정한다.

**Tech Stack:** python3 표준 라이브러리만(서드파티 YAML 금지 — 기존 스크립트 관례), bash 3.2(macOS) 셸 락 + `shared/tests/assert.sh`, `python3 -m unittest`(pytest 금지), `claude -p` 헤드리스 프로브(`CLAUDE_CONFIG_DIR` 격리).

**Spec:** `docs/superpowers/specs/2026-09-06-interview-depth-redesign-design.md` (이하 «spec». `brief C<n>` = 인터뷰 brief §2 항목, 접두 없는 `C<n>` = spec Constraints, `SKILL C43` = 현행 SKILL 내부 번호)

## Global Constraints

- 작업 디렉토리는 워크트리 `/Users/jeonghokim/Downloads/devbrew/.claude/worktrees/interview-depth-redesign`, 브랜치 `feature/interview-depth-redesign`. 모든 명령은 이 절대경로에서 돈다 — 상대경로로 main repo 에 파일을 만드는 drift 를 막는다.
- Task 2 에서 main(`319ed43`, spec-distill 0.54.0)을 **merge** 한다(rebase 금지). 그 뒤 `plugin.json` 은 `0.54.0 → 0.55.0`, CHANGELOG 헤딩 `## [0.55.0] — 2026-09-06`. 새 agent 파일에 `model:` 줄을 넣지 않는다(0.54.0 규약, 락 `MODEL_KEY="^[\"']?model[\"']?[[:space:]]*:"`).
- 커밋은 Conventional Commits. 본문 끝:
  ```
  Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_019tSwADsaxxgPy2VfzCEXKs
  ```
  워크트리 git 가드가 복합 명령·heredoc·`git` 을 포함한 `&&` 체인을 거부하므로 커밋 메시지는 파일로 쓰고 `git commit -q -F <file>` 한 줄로 커밋한다.
- 스크래치 디렉토리 `SCR=.claude/spec-distill/idr-scratch` (리포 `.gitignore:219` 가 `/.claude/*` 를 무시하므로 git 밖). 첫 사용 전 `mkdir -p "$SCR"`.
- 락 규약 (spec C13): 산문 락은 헤더가 아니라 **본문 고유 문구를 awk 블록 스코프**로 잡고, 통째 삭제·부정문·값 변경 mutation 으로 RED 를 확인한 뒤 `git checkout -- <file>` 로 복원한다. **변이 전에 반드시 커밋**(checkout 은 HEAD 로 되돌린다).
- 새 셸 테스트 첫 줄 아래 `# guards: <glob>` 헤더를 둔다(리포 관례). 파이썬 실행은 항상 `PYTHONDONTWRITEBYTECODE=1`.
- 건드리지 않는다: `scripts/check_seed.py` · `scripts/check_verbatim_coverage.py` · `scripts/section6.py` · `skills/reviewing-brief/` · `skills/reviewing-spec/` · `hooks/*` · `agents/steelman-builder.md` · `agents/blind-spot-prober.md` · `templates/interview-brief-template.md` · spec 자체(C11 — 실측 결과는 이 plan 의 «부록 A» 와 CHANGELOG 로).
- 측정은 게이트가 아니다(C5·NG8): `depth_pairs.py` 의 rc 3 을 제외한 어떤 측정 결과도 종료를 막지 않고, `depth_record.py` 는 **항상 exit 0** 이다.
- 처분 규약: 모든 `Agent(` dispatch 자리 바로 아래 40줄 안에 `// **처분** — consumer=<…> · fail-<open|closed>[ · disclosure=<리터럴>]` 한 줄. `consumer=` 가 `.py` 면 그 파일이 `from adjudication import Ledger` 를 하고, 그 파일의 **모든 for 문의 버리는 분기**(`continue`/`break`/`return`)가 `Ledger` 처분 메서드를 부른다(`shared/tests/test_adjudication_wiring.sh`), 그리고 `from render_disposition import …` 로 여덟 카운트 키를 소비한다(`test_adjudication_consumed.sh`).
- 20줄 이상 완전 동일 블록을 두 파일에 두지 않는다(`shared/tests/test_no_new_duplication.sh`). fixture 변형은 파일 복제가 아니라 **테스트 실행 시 정상 fixture 에서 생성**한다(기존 T1/T2 관례).

---

## File Structure

| 파일 | 책임 (한 가지) |
|---|---|
| `plugins/spec-distill/scripts/check_brief.py` | +`coverage_anchor_failures(audit_text, anchors)` · +`budget_mapper_failures(audit_text)` · `gate()` 가 둘을 부른다 |
| `plugins/spec-distill/tests/fixtures/sweep_anchor_fixtures.py` (신규, 1회용·커밋) | 기존 audit fixture 의 닫힌 행에 실재 S 앵커, §2 에 `coverage-mapper 1` 일괄 주입 |
| `plugins/spec-distill/scripts/depth_pairs.py` (신규) | state 본문 → `(S<k>, R<r+1> 블록)` 짝 + 표본. rc 3 = 측정 불가 |
| `plugins/spec-distill/scripts/depth_record.py` (신규) | auditor raw + 사람 라벨 → audit §2 세 줄 · `depth/<basename>.json` · 조건 판정. `Ledger` 소비자 |
| `plugins/spec-distill/agents/depth-auditor.md` (신규) | 짝의 내용 라벨. `tools: []`, `model` 없음, 센티널 `depth-audit` |
| `plugins/spec-distill/skills/conducting-interview/SKILL.md` | 라운드 규약(§1)·닫힘·재개방·dispatch(§2)·state 스키마. 순감 |
| `plugins/spec-distill/skills/conducting-interview/references/finishing.md` | Step A.7 깊이 측정 · 원장 직렬화 규칙(S앵커·재개방 접미) · 게이트 텍스트 요약 |
| `plugins/spec-distill/agents/coverage-mapper.md` | Input(seed·재검증 문단)·dispatch 규칙 문구 교체(stale 어휘 제거) |
| `plugins/spec-distill/templates/interview-audit-template.md` | §1 재개방 접미 예시 · §2 `coverage-mapper <k>` · 깊이 측정 세 줄 |
| `plugins/spec-distill/skills/framing-requests/SKILL.md` | §4.1 seed 규약 절 · §4.2 워크트리 절 · kill switch · 게이트 커밋/경로 |
| `plugins/spec-distill/references/compression.md` · `templates/interview-seed-template.md` | «(사용자 확인)»·«다시 검증할 것 —» 규약과 예시 |
| `docs/superpowers/interview/depth/.gitkeep` (신규) | 인터뷰별 측정 파일 디렉토리 |
| tests: `test_check_brief.sh`(+AC3·4·5) · `test_depth_pairs.py`(신규) · `test_depth_record.py`(신규) · `test_depth_auditor_frontmatter.sh`(신규) · `test_brief_agents.sh`(격리 집합에 depth-auditor) · `test_conducting_interview_stage.sh`(락 교체) · `test_request_framing_command.sh`(+AC11·12) · `test_stale_terms.sh`(+6 어휘) | 각 AC 의 락 |
| `plugin.json` · `CHANGELOG.md` · `README.md` | 0.55.0 · 이력(실측 결과 포함) · Principles |
| 이 plan 의 «부록 A — V6 실측 결과» | Task 1 산출물 (spec 은 편집하지 않는다) |

Task 순서: 1(실측) → 2(merge·baseline) → 3~5(게이트) → 6~8(측정 스크립트·에이전트) → 9(finishing) → 10~11(SKILL) → 12(§4.1) → **13(§4.2 — 별 묶음, 실측이 막히면 이 task 만 뒤로 뺀다)** → 14(버전·문서·전수 검증) → 15(사람 e2e).

---

### Task 1: V6 — native 워크트리 도구 실측 (격리 헤드리스)

**Files:**
- Create: `$SCR/v6/` (프로브 리포·설정·결과) · 이 plan 파일의 «부록 A» 절(Task 14 가 채운다)
- Test: 없음 (측정 task — 산출물은 결과 표)

**Interfaces:**
- Produces: `$SCR/v6/results.md` — (a)~(e) 다섯 행 표 + raw 출력. Task 13 이 명령 다섯 단계를 이 표에 맞추고, Task 14 가 표를 «부록 A» 와 CHANGELOG 에 옮긴다.

재는 것(spec §4.2): (a) native 도구가 만드는 브랜치명, (b) base ref(`worktree.baseRef` 기본값 vs `head` — 로컬에만 있는 main 커밋이 들어오는지), (c) 워크트리 안에서 플러그인 훅과 `CLAUDE_PLUGIN_ROOT` 가 해석되는지, (d) 종료 시 워크트리·브랜치 잔존(keep/remove 프롬프트 «모양»은 헤드리스에서 실측 불가 — 그렇게 적는다), (e) 격리 세션의 git 가드가 `git branch -m` 과 `git commit -F` 를 허용하는지.

- [ ] **Step 1: 격리 설정 + 격리 증명**

```bash
SCR=.claude/spec-distill/idr-scratch; mkdir -p "$SCR/v6/config" "$SCR/v6/plugin/hooks"
export CLAUDE_CONFIG_DIR="$PWD/$SCR/v6/config"
claude plugin list 2>&1 | head -5
```
Expected: 플러그인 0개(또는 «no plugins»). 설치 캐시의 플러그인이 보이면 격리가 안 된 것 — 진행하지 않는다.

- [ ] **Step 2: 프로브 플러그인 (훅 발화 관측용)**

`$SCR/v6/plugin/.claude-plugin/plugin.json`:
```json
{"name": "idr-probe", "description": "worktree probe hook", "version": "0.0.1"}
```
`$SCR/v6/plugin/hooks/hooks.json`:
```json
{"hooks": {"PostToolUse": [{"matcher": "Bash", "hooks": [{"type": "command",
  "command": "printf 'fired cwd=%s root=%s\\n' \"$PWD\" \"${CLAUDE_PLUGIN_ROOT:-unset}\" >> \"$IDR_PROBE_LOG\""}]}]}}
```

- [ ] **Step 3: 프로브 리포 — origin 과 로컬-전용 커밋**

```bash
git init -q "$SCR/v6/repo"
```
그 디렉토리 안에서(각각 단순 명령 하나씩): `git commit -q --allow-empty -m 'c1'` → `git clone -q --bare . ../origin.git` → `git remote add origin ../origin.git` → `git fetch -q origin` → `git branch --set-upstream-to=origin/main main` (기본 브랜치가 `master` 면 `git branch -m main` 먼저) → `git commit -q --allow-empty -m 'c2-local-only'`. 확인: `git log --oneline origin/main` 은 c1 만, `git log --oneline main` 은 c2·c1.

- [ ] **Step 4: 프롬프트 파일**

`$SCR/v6/prompt.txt`:
```
You are inside a probe repository. Do exactly the following, one tool call each, and do not stop on refusals — record them.
1. Call the EnterWorktree tool with name "probe-topic".
2. Run: git branch --show-current
3. Run: git log --oneline -1
4. Run: printf '%s\n' "${CLAUDE_PLUGIN_ROOT:-unset}"
5. Run: git branch -m feature/probe-topic
6. Run: git branch --show-current
7. Run: git commit -q --allow-empty -F msg.txt   (msg.txt exists in the repo root; if the worktree lacks it, first run: printf 'chore: probe commit\n' > msg.txt)
8. Run: git log --oneline -1
9. Run: pwd
Then print a fenced block with info string PROBE-RESULT containing lines: tool_available=<yes|no>, branch_after_enter=<...>, head_after_enter=<...>, plugin_root=<...>, rename_result=<ok|refused: <text>>, branch_after_rename=<...>, commit_result=<ok|refused: <text>>, head_after_commit=<...>, cwd=<...>. If the EnterWorktree tool is not available, say tool_available=no and still run steps 2-9 in the current directory.
```

- [ ] **Step 5: 실행 ×2 (기본 baseRef · `head`)**

`$SCR/v6/settings-head.json`: `{"worktree": {"baseRef": "head"}}`
```bash
printf 'chore: probe commit\n' > "$SCR/v6/repo/msg.txt"
IDR_PROBE_LOG="$PWD/$SCR/v6/hook-default.log" claude -p "$(cat "$SCR/v6/prompt.txt")" --dangerously-skip-permissions --plugin-dir "$PWD/$SCR/v6/plugin" --output-format json > "$SCR/v6/run-default.json" 2> "$SCR/v6/run-default.err"
```
(두 번째 실행은 `--settings "$PWD/$SCR/v6/settings-head.json"` 을 더하고 로그·출력 파일명을 `-head` 로. 두 실행 사이에 `git -C "$SCR/v6/repo" worktree prune` 과 `git -C "$SCR/v6/repo" branch -D feature/probe-topic` 으로 리셋한다 — 첫 실행이 브랜치를 남겼다면.)
실행 전 `cd "$SCR/v6/repo"` 가 필요하다 — `claude -p` 는 cwd 를 리포로 잡는다. 셸 가드 때문에 `cd` 는 별도 호출로.

- [ ] **Step 6: 관측 수집**

각 실행에 대해: `PROBE-RESULT` 블록(`run-*.json` 의 `result` 필드에서 grep), `hook-*.log`(훅 발화 여부와 `root=` 값), 종료 후 `git -C "$SCR/v6/repo" worktree list` 와 `git -C "$SCR/v6/repo" branch -a`(잔존 여부, (d)), `git -C "$SCR/v6/repo" log --oneline -1 <worktree branch>`(c2-local-only 포함 여부, (b)).

- [ ] **Step 7: 결과 표 작성** — `$SCR/v6/results.md`

```markdown
| 항목 | 기본 baseRef | baseRef=head | 근거 파일 |
|---|---|---|---|
| (a) 브랜치명 | <branch_after_enter> | <…> | run-*.json |
| (b) base ref — c2-local-only 포함? | <yes/no> | <yes/no> | git log |
| (c) 훅 발화 · CLAUDE_PLUGIN_ROOT | <fired n회 · root=…> | <…> | hook-*.log |
| (d) 종료 후 워크트리/브랜치 잔존 | <…> | <…> | worktree list · branch -a |
| (d') keep/remove 프롬프트 모양 | 헤드리스 실측 불가 | 〃 | — |
| (e) `git branch -m` / `git commit -F` | <ok/refused: …> | <…> | run-*.json |
| tool_available | <yes/no> | <…> | run-*.json |
```
아래에 raw `PROBE-RESULT` 블록 두 개를 그대로 붙인다. **어느 칸도 추정으로 채우지 않는다** — 관측이 없으면 «관측 없음: <이유>».

- [ ] **Step 8: Task 13 분기 결정 기록** — 같은 파일 끝에 한 줄:
  - `tool_available=yes` 이고 (e) 둘 다 ok → Task 13 은 spec §4.2 의 1~5 단계 그대로.
  - (e) 중 `git branch -m` 거부 → Task 13 2단계를 «`EnterWorktree(name=feature/<kebab-topic>)` 로 이름에 접두를 넣어 rename 생략» 으로 바꾼다((a) 가 이름을 그대로 쓰는 경우만; 접두가 붙으면 rename 은 사용자에게 수동 안내).
  - `tool_available=no`(헤드리스) → Task 13 은 진행하되 SKILL 산문에 «도구 부재 시 현재 디렉토리» 강등 경로를 주 경로와 같은 무게로 적고, 대화형 실측은 Task 15(사람 e2e) 관찰 항목에 넣는다.

- [ ] **Step 9: 커밋 없음** (스크래치는 git 밖). 격리 해제: `unset CLAUDE_CONFIG_DIR` — 이후 task 는 실제 설정으로 돈다.

---

### Task 2: main 0.54.0 merge + V5 baseline

**Files:**
- Modify: (merge 로 들어오는 파일 64개 — 손대지 않는다)
- Create: `$SCR/baseline_before.txt` · `$SCR/run_all_locks.sh`

**Interfaces:**
- Produces: `$SCR/run_all_locks.sh` — 셸 락 전수의 `✗` 줄을 `파일<TAB>메시지` 로 정렬해 내고, 파이썬 unittest 의 마지막 요약 줄을 낸다. Task 14 가 같은 스크립트로 사후 집합을 만들어 diff 한다.

- [ ] **Step 1: main 위치 확인**

```bash
git rev-parse --short main
git log --oneline -1 main
```
Expected: `319ed43 Merge branch 'feature/agent-model-unpin' …`. 다르면 사용자에게 알리고 그 커밋으로 진행한다(더 앞선 main 도 merge 대상이다).

- [ ] **Step 2: merge (rebase 금지)**

```bash
git merge --no-edit main
git status --short
```
Expected: 충돌 없음(이 브랜치는 `docs/` 만 만졌다). 충돌이 나면 `plugins/spec-distill/CHANGELOG.md` 뿐일 것이고, main 쪽 `[0.54.0]` 절을 위에 두고 해결한다. `git log --oneline -1` 이 merge 커밋.

- [ ] **Step 3: merge 결과 확인**

```bash
grep -c '^model:' plugins/spec-distill/agents/*.md
grep -n '"version"' plugins/spec-distill/.claude-plugin/plugin.json
```
Expected: 각 agent 0, version `0.54.0`.

- [ ] **Step 4: baseline 러너**

`$SCR/run_all_locks.sh` 를 Write 도구로 만든다:
```bash
#!/usr/bin/env bash
# 리포(워크트리) 루트에서 실행. 셸 락 전수의 ✗ 줄 + 파이썬 요약 줄.
cd "$(git rev-parse --show-toplevel)" || exit 1
for t in plugins/spec-distill/tests/test_*.sh shared/tests/test_*.sh; do
  bash "$t" 2>/dev/null | grep -E '^[[:space:]]*✗' | sed "s|^|$t	|"
done | sort
echo "PY: $(PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s plugins/spec-distill/tests -p 'test_*.py' 2>&1 | tail -1)"
```

- [ ] **Step 5: baseline 캡처**

```bash
bash "$SCR/run_all_locks.sh" > "$SCR/baseline_before.txt" 2>&1
wc -l "$SCR/baseline_before.txt"
tail -1 "$SCR/baseline_before.txt"
```
결과 줄 수와 `PY:` 줄을 이 plan 의 «부록 B — baseline» 에 적는다(Task 14). 선재 RED(메모리: 워크트리에서 NG9 선재 RED 1건 등)는 «풍경»이 아니라 **줄 단위로 이름이 있어야** 사후 diff 가 새 실패를 가른다.

- [ ] **Step 6: 커밋** — merge 커밋은 Step 2 에서 이미 생겼다. 추가 커밋 없음.

### Task 3: 기존 fixture 스윕 — 닫힌 행에 S 앵커 · §2 에 `coverage-mapper 1`

**Files:**
- Create: `plugins/spec-distill/tests/fixtures/sweep_anchor_fixtures.py`
- Modify: `plugins/spec-distill/tests/fixtures/*.audit.md` (86개, 스크립트가 편집)
- Test: `plugins/spec-distill/tests/test_check_brief.sh` (변경 없음 — ok/no 집합 동일성이 판정)

**Interfaces:**
- Consumes: `check_brief._section_text` · `_entry_lines` · `_strip_bullet` · `verbatim_anchors` · `payload_verbatim_anchors` · `resolve_audit` 은 쓰지 않는다(payload 는 audit frontmatter `payload:` basename 으로 찾는다).
- Produces: 스윕 뒤 fixture 는 Task 4·5 의 새 검사를 통과한다. 다른 task 가 의존하는 함수 없음.

실측(착수 전 census): audit fixture 89개 중 86개에 앵커 없는 닫힌 행 513개, §2 에 `coverage-mapper` 토큰 0개, audit §6 앵커가 아예 없는 것 11개. 그래서 앵커 선택은 «payload §6 ∪ audit §6 의 앵커 중 가장 작은 번호, 없으면 `S1`» 이다 — `S1` 은 N1b 가 모든 정상 payload 에 요구하는 앵커라 정상 fixture 에서는 항상 실재한다.

- [ ] **Step 1: 스윕 전 ok/no 집합 캡처**

```bash
bash plugins/spec-distill/tests/test_check_brief.sh > "$SCR/tcb_before.txt" 2>&1
grep -cE '^\s*✓' "$SCR/tcb_before.txt"; grep -cE '^\s*✗' "$SCR/tcb_before.txt"
```

- [ ] **Step 2: 스윕 스크립트 작성** — `plugins/spec-distill/tests/fixtures/sweep_anchor_fixtures.py`

```python
#!/usr/bin/env python3
"""1회용 스윕 (v0.55.0) — audit fixture 의 닫힌 원장 행에 실재 S 앵커를, §2 Budget 에
`coverage-mapper 1` 을 주입한다. 판정을 바꾸지 않는다 — 실행 전후 test_check_brief.sh 의
ok/no 집합이 같아야 한다. 재실행은 멱등이다(이미 앵커·토큰이 있으면 건드리지 않는다).

usage: python3 sweep_anchor_fixtures.py [<fixtures-dir>]   (기본: 이 파일의 디렉토리)
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "scripts"))
import check_brief as cb  # noqa: E402

ANCHOR_RE = re.compile(r"(?<![A-Za-z])S\d+\b")
ROW_RE = re.compile(r"^(\s*[-*]\s+)((?:floor:\w+|derived:[^—]+?)\s*—\s*closed\s*—\s*)(.*?)(\s*)$")
MAPPER_RE = re.compile(r"coverage-mapper\s+\d+")


def pick_anchor(payload_text: str, audit_text: str) -> str:
    anchors = cb.verbatim_anchors(audit_text)
    if payload_text:
        anchors |= cb.payload_verbatim_anchors(payload_text)
    nums = sorted(int(a[1:]) for a in anchors if a[1:].isdigit())
    return f"S{nums[0]}" if nums else "S1"


def sweep_audit(audit: Path) -> tuple[int, int]:
    text = audit.read_text(encoding="utf-8")
    fm = cb._frontmatter(text)
    m = re.search(r"^payload:\s*(\S+)\s*$", fm, re.MULTILINE)
    payload_text = ""
    if m and (audit.parent / m.group(1)).is_file():
        payload_text = (audit.parent / m.group(1)).read_text(encoding="utf-8")
    anchor = pick_anchor(payload_text, text)
    sec1 = cb._section_text(text, "1", "Coverage Ledger")
    rows = 0
    if sec1.strip():
        new_lines = []
        for ln in text.splitlines():
            r = ROW_RE.match(ln)
            if r and ln in sec1 and not ANCHOR_RE.search(r.group(3)):
                ln = f"{r.group(1)}{r.group(2)}{r.group(3)} (@{anchor})"
                rows += 1
            new_lines.append(ln)
        text = "\n".join(new_lines) + ("\n" if text.endswith("\n") else "")
    sec2 = cb._section_text(text, "2", "Budget")
    budget = 0
    if sec2.strip() and not MAPPER_RE.search(sec2):
        hdr = re.search(r"^##\s+2\.\s+Budget[^\n]*\n", text, re.MULTILINE)
        text = text[:hdr.end()] + "\n- agent dispatch: coverage-mapper 1\n" + text[hdr.end():]
        budget = 1
    if rows or budget:
        audit.write_text(text, encoding="utf-8")
    return rows, budget


def main(argv: list[str]) -> int:
    d = Path(argv[1]) if len(argv) > 1 else HERE
    tot_rows = tot_budget = files = 0
    for a in sorted(d.glob("*.audit.md")):
        r, b = sweep_audit(a)
        if r or b:
            files += 1
        tot_rows += r
        tot_budget += b
    print(f"files_touched={files} rows_anchored={tot_rows} budget_lines_added={tot_budget}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```
주의: `ln in sec1` 은 원장 절 안의 줄만 고친다 — 다른 절에 같은 모양의 행이 있어도 건드리지 않는다. `## 2. Budget` 헤딩 뒤 빈 줄 하나를 두고 삽입한다(템플릿의 빈 줄 관례).

- [ ] **Step 3: 실행 + 멱등 확인**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 plugins/spec-distill/tests/fixtures/sweep_anchor_fixtures.py
PYTHONDONTWRITEBYTECODE=1 python3 plugins/spec-distill/tests/fixtures/sweep_anchor_fixtures.py
```
Expected: 첫 실행 `files_touched≈86 rows_anchored≈513 budget_lines_added≈86`, 둘째 실행 전부 0.

- [ ] **Step 4: 판정 불변 확인**

```bash
bash plugins/spec-distill/tests/test_check_brief.sh > "$SCR/tcb_after_sweep.txt" 2>&1
diff <(grep -E '^\s*[✓✗]' "$SCR/tcb_before.txt") <(grep -E '^\s*[✓✗]' "$SCR/tcb_after_sweep.txt") && echo SAME
```
Expected: `SAME`. 다르면 스윕이 판정을 바꾼 것 — 그 fixture 를 열어 어느 검사가 흔들렸는지 보고 스크립트를 고친다(fixture 를 손으로 고치지 않는다).

- [ ] **Step 5: 커밋**

```bash
git add plugins/spec-distill/tests/fixtures/
git commit -q -F "$SCR/msg_t3.txt"
```
메시지: `test(spec-distill): audit fixture 스윕 — 닫힌 행 S앵커·§2 coverage-mapper 1 주입 (판정 불변)`

---

### Task 4: `check_brief.py` — 닫힘 S앵커 게이트 (AC3)

**Files:**
- Modify: `plugins/spec-distill/scripts/check_brief.py` (`coverage_ledger_failures` 뒤에 함수 추가, `gate()` 의 `coverage ledger` 블록 직후에 호출, `main()` 의 `coverage` 서브커맨드 출력에 `anchor_failures` 키 추가)
- Test: `plugins/spec-distill/tests/test_check_brief.sh` (파일 끝 `finish` 앞에 추가)

**Interfaces:**
- Produces: `coverage_anchor_failures(audit_text: str, anchors: set[str]) -> list[str]` — audit §1 의 `closed` 행(floor·derived·박제) 마다 evidence 에 앵커 `(?<![A-Za-z])S\d+\b` 가 ≥1 이고 **인용된 앵커 전부**가 `anchors` 에 실재해야 한다. 실패 문자열: `floor:<dim> evidence cites no S<N> anchor` · `floor:<dim> evidence anchor S7 not found in §6` (derived 는 `derived:<name> …`). 상수 `ANCHOR_RE`.
- 호출 규약: `gate()` 는 `anchors = payload_verbatim_anchors(text) | verbatim_anchors(audit_text)` 를 넘긴다 — 이미 bijection C 가 쓰는 같은 집합.

- [ ] **Step 1: 실패하는 테스트** — `test_check_brief.sh` 의 `finish` 직전에 추가

```bash
# --- v0.55.0 AC3: 닫힌 행의 닫힘 근거는 실재 S 앵커 (spec §2.1) ---------------------
# fixture 를 파일로 복제하지 않는다(중복 락) — 정상 쌍에서 실행 시 생성한다(T1/T2 관례).
ac3_pair() {  # $1 = stem. $TMPD/$1.md + $1.audit.md 를 정상 쌍에서 만든다.
  cp "$FX/interview-brief-valid.md" "$TMPD/$1.md"
  cp "$FX/interview-brief-valid.audit.md" "$TMPD/$1.audit.md"
  sed -i.bak "s|^audit_file:.*|audit_file: $1.audit.md|" "$TMPD/$1.md"; rm -f "$TMPD/$1.md.bak"
  sed -i.bak "s|^payload:.*|payload: $1.md|" "$TMPD/$1.audit.md"; rm -f "$TMPD/$1.audit.md.bak"
}
ac3_gate() { python3 "$SCRIPT" gate "$TMPD/$1.md" 2>/dev/null; }

# (c) 실재 S 인용 → 통과 (스윕된 정상 fixture 그대로)
ac3_pair c_ok
ac3_gate c_ok >/dev/null && ok "AC3(c): 닫힌 행이 실재 S 를 인용하면 통과" || no "AC3(c): 실재 S 인용이 통과해야 한다"

# (a) 앵커 없음 → red, 메시지에 차원명 + 'cites no'
ac3_pair a_none
sed -i.bak 's|^- floor:landscape — closed — .*$|- floor:landscape — closed — §4 Next.js SSR 인용|' "$TMPD/a_none.audit.md"; rm -f "$TMPD/a_none.audit.md.bak"
out="$(ac3_gate a_none)"; rc=$?
{ [[ $rc -ne 0 ]] && grep -q 'floor:landscape evidence cites no S' <<<"$out"; } \
  && ok "AC3(a): 앵커 없는 닫힌 행 → red + 차원명 메시지" || no "AC3(a): 앵커 없는 닫힌 행이 통과했거나 메시지 부재"

# (b) §6 에 없는 S 인용 → red
ac3_pair b_dangling
sed -i.bak 's|^- floor:skepticism — closed — \(.*\)$|- floor:skepticism — closed — S77 판정|' "$TMPD/b_dangling.audit.md"; rm -f "$TMPD/b_dangling.audit.md.bak"
out="$(ac3_gate b_dangling)"; rc=$?
{ [[ $rc -ne 0 ]] && grep -q 'floor:skepticism evidence anchor S77 not found' <<<"$out"; } \
  && ok "AC3(b): §6 에 없는 S 인용 → red" || no "AC3(b): dangling S 가 통과했거나 메시지 부재"

# (d) 우연 토큰 OQS3 는 앵커가 아니다 → red (앵커 0개로 판정)
ac3_pair d_token
sed -i.bak 's|^- floor:blind_spot — closed — .*$|- floor:blind_spot — closed — OQS3 참조|' "$TMPD/d_token.audit.md"; rm -f "$TMPD/d_token.audit.md.bak"
out="$(ac3_gate d_token)"; rc=$?
{ [[ $rc -ne 0 ]] && grep -q 'floor:blind_spot evidence cites no S' <<<"$out"; } \
  && ok "AC3(d): OQS3 류 우연 토큰은 앵커로 세지 않는다" || no "AC3(d): OQS3 가 앵커로 통과했다"

# derived 행과 박제 행도 대상이다
ac3_pair e_derived
sed -i.bak 's|^- derived:rendering-strategy — closed — .*$|- derived:rendering-strategy — closed — SSR/islands 선택이 축|' "$TMPD/e_derived.audit.md"; rm -f "$TMPD/e_derived.audit.md.bak"
out="$(ac3_gate e_derived)"; rc=$?
{ [[ $rc -ne 0 ]] && grep -q 'derived:rendering-strategy evidence cites no S' <<<"$out"; } \
  && ok "AC3: derived 닫힌 행도 앵커 필수" || no "AC3: derived 행이 앵커 없이 통과"
ac3_pair f_frozen
sed -i.bak 's|^- floor:open_questions — closed — .*$|- floor:open_questions — closed — 사용자-승인 박제(@S1) — §Open Questions 참조|' "$TMPD/f_frozen.audit.md"; rm -f "$TMPD/f_frozen.audit.md.bak"
ac3_gate f_frozen >/dev/null && ok "AC3: 박제 행 «사용자-승인 박제(@S1) — …» 통과" || no "AC3: 접두 뒤 앵커를 가진 박제 행이 red"

# mutation: 검사 함수를 무력화하면 (a) 가 통과해야 한다 — 락의 이빨 확인 (PYTHONDONTWRITEBYTECODE)
mut="$TMPD/check_brief_mut.py"
sed 's/^def coverage_anchor_failures(.*$/&\n    return []/' "$SCRIPT" > "$mut"
cp "$REPO_ROOT/plugins/spec-distill/scripts/section6.py" "$TMPD/" 2>/dev/null || true
PYTHONDONTWRITEBYTECODE=1 python3 "$mut" gate "$TMPD/a_none.md" >/dev/null 2>&1 \
  && ok "AC3(mutation): 검사 함수를 비우면 (a) 가 통과 — 락이 그 함수에 걸려 있다" \
  || no "AC3(mutation): 함수를 비웠는데도 red — 판정이 다른 곳에서 나온다(락 무의미)"
```
(`section6.py` 복사는 `check_brief.py` 가 형제 모듈을 import 할 때 `$TMPD` 에서도 찾게 하려는 것이다. import 가 `sys.path[0]` 기준이면 필요하고, 아니면 무해하다 — 실행해서 확인.)

- [ ] **Step 2: RED 확인**

```bash
bash plugins/spec-distill/tests/test_check_brief.sh 2>&1 | grep -E 'AC3'
```
Expected: (c)·박제 는 ✓(아직 검사가 없으니 통과), (a)(b)(d)·derived 는 ✗, mutation 은 sed 가 매치 못 해 ✗.

- [ ] **Step 3: 구현** — `coverage_ledger_failures` 바로 뒤

```python
# 닫힘 근거 앵커 (v0.55.0, spec §2.1). 단어 경계 없이 `S\d+` 를 쓰면 `OQS3`·`STS1` 같은
# 우연 토큰이 앵커로 잡힌다 — 앞이 영문자가 아니어야 한다.
ANCHOR_RE = re.compile(r"(?<![A-Za-z])S\d+\b")
LEDGER_ROW_RE = re.compile(r"^(floor:\w+|derived:[^—]+?)\s*—\s*(\S+)\s*—\s*(.*)$")


def coverage_anchor_failures(audit_text: str, anchors: set) -> list[str]:
    """audit §1 의 **닫힌 행마다** evidence 가 실재 `S<N>` 앵커를 인용하는가 (AC3).

    Form-only: «그 S 가 닫힘을 정당화하는가»는 보지 않는다(spec §2.1 이 그 한계를
    OQ6 으로 공시한다). 인용된 앵커는 **전부** 실재해야 한다 — 재개방 접미의
    `conflicts_with` S 도 사용자 발화이므로 같은 요구를 받는다. `derived: N/A`
    sentinel 과 open 행은 대상이 아니다(form 검사가 따로 잡는다)."""
    sec = _section_text(audit_text, "1", "Coverage Ledger")
    fails: list[str] = []
    for ln in _entry_lines(sec):
        body = _strip_bullet(ln).strip()
        m = LEDGER_ROW_RE.match(body)
        if not m or m.group(2).strip() != "closed":
            continue
        key, evidence = m.group(1).strip(), m.group(3)
        cited = ANCHOR_RE.findall(evidence)
        if not cited:
            fails.append(f"{key} evidence cites no S<N> anchor")
            continue
        for s in cited:
            if s not in anchors:
                fails.append(f"{key} evidence anchor {s} not found in §6")
    return fails
```
`gate()` — 기존 `cov = coverage_ledger_failures(audit_text)` 블록 바로 뒤:
```python
        anc = coverage_anchor_failures(
            audit_text, payload_verbatim_anchors(text) | verbatim_anchors(audit_text))
        if anc:
            failures.append(f"coverage anchors: {anc}")
```
(같은 `if audit_text and not any(m.startswith("1.") …)` 가드 안에 둔다.) `main()` 의 `coverage` 서브커맨드: `print(json.dumps({"failures": coverage_ledger_failures(audit_text), "anchor_failures": coverage_anchor_failures(audit_text, payload_verbatim_anchors(text) | verbatim_anchors(audit_text))}, ensure_ascii=False))`.

- [ ] **Step 4: GREEN + 회귀 없음**

```bash
bash plugins/spec-distill/tests/test_check_brief.sh 2>&1 | tail -1
bash plugins/spec-distill/tests/test_check_brief.sh 2>&1 | grep -E '✗'
```
Expected: `Fail: 0`(스윕 전 baseline 에 ✗ 가 있었으면 그 집합과 동일).

- [ ] **Step 5: 수동 mutation (앵커 삭제·번호 +1·행 삭제)** — 스윕된 정상 fixture 사본에서 각각 한 번씩 `gate` 를 돌려 red 를 눈으로 확인하고, 결과 세 줄을 `$SCR/ac3_mutation.txt` 에 남긴다(Task 14 CHANGELOG 의 Verification 줄 재료).

- [ ] **Step 6: 커밋** — `feat(spec-distill): check_brief 닫힘 근거 S앵커 게이트 (AC3)`

---

### Task 5: `check_brief.py` — §2 `coverage-mapper ≥1` 게이트 + 재개방 접미 fixture (AC4·AC5)

**Files:**
- Modify: `plugins/spec-distill/scripts/check_brief.py` (`budget_mapper_failures` 추가, `gate()` 호출, advisories 합류)
- Test: `plugins/spec-distill/tests/test_check_brief.sh`

**Interfaces:**
- Produces: `budget_mapper_failures(audit_text: str) -> tuple[list[str], list[str]]` = `(failures, advisories)`. §2 Budget 에서 `MAPPER_RE = re.compile(r"coverage-mapper\s+(\d+)(?:\s*\((unavailable:[^)]*)\))?")` 첫 매치. 없음 → failure `§2 Budget: coverage-mapper <k> line missing`; k≥1 → 통과; k=0 + unavailable 사유 → advisory `coverage-mapper 0 (unavailable: …) — dispatch 없이 통과 (advisory, 사람이 확인)`; k=0 사유 없음 → failure `§2 Budget: coverage-mapper 0 without unavailable reason`. `gate()` 의 JSON `advisories` 에 실린다(기존 `WEB_DISABLED_ADVISORY` 와 같은 채널 — finishing.md Step B 가 이 채널을 게이트 텍스트에 싣는다, Task 9).

- [ ] **Step 1: 실패하는 테스트** — AC3 블록 뒤에 추가

```bash
# --- v0.55.0 AC4: §2 Budget 의 coverage-mapper <k> (k>=1 게이트, 0+unavailable advisory) ---
ac3_pair m_ok
ac3_gate m_ok >/dev/null && ok "AC4: coverage-mapper 1 → 통과" || no "AC4: coverage-mapper 1 이 red"
ac3_pair m_missing
sed -i.bak '/coverage-mapper/d' "$TMPD/m_missing.audit.md"; rm -f "$TMPD/m_missing.audit.md.bak"
out="$(ac3_gate m_missing)"; rc=$?
{ [[ $rc -ne 0 ]] && grep -q 'coverage-mapper <k> line missing' <<<"$out"; } \
  && ok "AC4: coverage-mapper 줄 부재 → red" || no "AC4: 부재가 통과"
ac3_pair m_zero
sed -i.bak 's|coverage-mapper 1|coverage-mapper 0|' "$TMPD/m_zero.audit.md"; rm -f "$TMPD/m_zero.audit.md.bak"
out="$(ac3_gate m_zero)"; rc=$?
{ [[ $rc -ne 0 ]] && grep -q 'coverage-mapper 0 without unavailable reason' <<<"$out"; } \
  && ok "AC4: coverage-mapper 0 (사유 없음) → red" || no "AC4: 0 이 사유 없이 통과"
ac3_pair m_unavail
sed -i.bak 's|coverage-mapper 1|coverage-mapper 0 (unavailable: Agent 도구 부재)|' "$TMPD/m_unavail.audit.md"; rm -f "$TMPD/m_unavail.audit.md.bak"
out="$(ac3_gate m_unavail)"; rc=$?
{ [[ $rc -eq 0 ]] && grep -q '"advisories": \[.*unavailable' <<<"$out"; } \
  && ok "AC4: coverage-mapper 0 (unavailable: …) → advisory 통과, advisories 채널에 실림" \
  || no "AC4: unavailable sentinel 이 red 이거나 advisory 가 비었다"

# --- v0.55.0 AC5: 재개방 접미 «(재개방 n회 — 사유)» 가 원장 regex 를 깨지 않는다 ---
ac3_pair r_reopen
sed -i.bak 's|^- floor:landscape — closed — \(.*\)$|- floor:landscape — closed — \1 (재개방 1회 — S1 과 충돌)|' "$TMPD/r_reopen.audit.md"; rm -f "$TMPD/r_reopen.audit.md.bak"
ac3_gate r_reopen >/dev/null && ok "AC5: 재개방 접미가 붙은 닫힌 행 통과" || no "AC5: 재개방 접미가 원장 검사를 깬다"
```

- [ ] **Step 2: RED 확인** — `grep -E 'AC4|AC5'`: `m_ok`·`r_reopen` ✓, 나머지 ✗.

- [ ] **Step 3: 구현** — `coverage_anchor_failures` 뒤

```python
MAPPER_RE = re.compile(r"coverage-mapper\s+(\d+)(?:\s*\((unavailable:[^)]*)\))?")


def budget_mapper_failures(audit_text: str) -> tuple[list[str], list[str]]:
    """audit §2 Budget 의 `coverage-mapper <k>` (v0.55.0, spec §2.3·C4).

    k>=1 통과. `coverage-mapper 0 (unavailable: <이유>)` 는 advisory 통과 — 침묵과 0 을
    가른다. **이 검사가 못 잡는 것**: sentinel 은 피검자가 쓰는 문구라, dispatch 를 건너뛴
    턴이 같은 문구를 적으면 «도구 부재»와 구분하지 못한다. 그래서 advisory 는 조용히
    통과하지 않고 Step B 게이트 텍스트로 사람에게 간다."""
    sec = _section_text(audit_text, "2", "Budget")
    m = MAPPER_RE.search(sec)
    if not m:
        return ["§2 Budget: coverage-mapper <k> line missing"], []
    k, reason = int(m.group(1)), m.group(2)
    if k >= 1:
        return [], []
    if reason:
        return [], [f"coverage-mapper 0 ({reason}) — dispatch 없이 통과 (advisory, 사람이 확인)"]
    return ["§2 Budget: coverage-mapper 0 without unavailable reason"], []
```
`gate()`: `advisories: list[str] = []` 선언을 audit 블록 **앞**으로 올리고, audit §2 가 있을 때(`not any(m.startswith("2.") for m in amiss)`) `bf, ba = budget_mapper_failures(audit_text); failures += [f"coverage-mapper budget: {x}" for x in bf]; advisories += ba`.

- [ ] **Step 4: GREEN** — `bash plugins/spec-distill/tests/test_check_brief.sh 2>&1 | tail -1` → `Fail: 0`.

- [ ] **Step 5: 커밋** — `feat(spec-distill): §2 coverage-mapper ≥1 게이트 + 재개방 접미 락 (AC4·AC5)`

### Task 6: `depth_pairs.py` — 짝 추출 · 표본 · 측정 불가 (AC6)

**Files:**
- Create: `plugins/spec-distill/scripts/depth_pairs.py` · `plugins/spec-distill/tests/test_depth_pairs.py` · `plugins/spec-distill/tests/fixtures/depth-state-{normal,elig0,elig1,elig3,noround,allnone}.md`
- Test: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest plugins.spec-distill… ` 는 경로에 하이픈이 있어 모듈 경로로 못 부른다 — `python3 -m unittest discover -s plugins/spec-distill/tests -p 'test_depth_pairs.py'` 로 부른다.

**Interfaces:**
- CLI: `python3 depth_pairs.py <state.local.md> [--sample N] [--seed STR]` (기본 N=4, seed=state 의 `session_id`).
- stdout(rc 0) JSON:
  ```json
  {"session_id": "…",
   "pairs": [{"s": "S3", "round": 1, "next_round": 2, "user_text": "…", "block": "…|null",
              "substantive": true, "terminal": false, "eligible": true}],
   "counts": {"total": n, "eligible": e, "with_block": m, "substantive_form": p, "terminal": t, "skipped": k},
   "human_sample": [{"s": "S3", "s_excerpt": "≤200자", "block_excerpt": "≤300자"}]}
  ```
  `skipped` = `round` 가 정수가 아닌 발화(예: `review-1`) — 짝 대상 밖. 이 필드는 spec 이 plan 에 위임한 세부다.
- rc 3 + stdout `{"unmeasurable": "<이유>"}`: 파일 판독 불가 · frontmatter 부재 · `user_statements` 부재/파싱 실패 · 본문에 `## R<n>` 헤딩 0개. rc 2 = 사용법.
- 규칙(spec §3.1): 짝 = `(S<k>(round r), R<r+1> 의 «### 직전 답에서 — …S<k>…» 블록 | None)`. `terminal` = 본문에 `## R<r+1>` 이 없음. `eligible` = not terminal and `user_text.strip()` 비어있지 않음. `substantive` = 블록의 네 줄(`- 함의:`·`- 상충:`·`- 확인한 사실:`·`- 위험:`) 중 «없음» 이 아닌 값이 ≥1. 표본 = eligible 에서 `random.Random(seed).sample(…, min(N, len))` 비복원. `round: 0` 인 S1 은 R1 과 짝(S1 이 `round: 1` 이면 R2 와 짝 — 비-seed 경로).
- Task 8 이 `pairs[].s`·`block`·`eligible`·`human_sample[].s`·`counts` 를 그대로 읽는다.

- [ ] **Step 1: fixture 6종** — `plugins/spec-distill/tests/fixtures/depth-state-normal.md`

```markdown
---
session_id: depthfixture01
phase: 1
coverage:
  floor:
    root_problem:   {status: closed, evidence: "S3 (@S3)", reopened: 0, reopen_log: []}
user_statements:
  - id: S1
    source: verbatim
    round: 0
    text: |
      ---
      type: interview-seed
      ---
      로그인이 가끔 실패한다.
  - id: S2
    source: chosen
    round: 1
    text: "맞다"
  - id: S3
    source: chosen
    round: 1
    text: "TTL 늘려봤는데 안 됨"
  - id: S4
    source: verbatim
    round: 2
    text: "서버 로그에는 아무것도 없었다"
  - id: S5
    source: chosen
    round: 2
    text: "클라이언트 경합 의심"
  - id: S6
    source: verbatim
    round: 3
    text: "재현이 안 되면 멈춰라"
  - id: S7
    source: chosen
    round: 4
    text: "이대로 종료"
  - id: S8
    source: verbatim
    round: review-1
    text: "리뷰 라운드 발화"
---

## R1

### 직전 답에서 — S1
- 함의: 실패가 간헐이라 재현 경로가 먼저다
- 상충: 없음
- 확인한 사실: src/auth 에 재시도 로직 없음
- 위험: 없음

### 지금 이해
간헐 로그인 실패.

### 다음 결정
재현 우선 · 추천: 로그 수집 · 트레이드오프: 시간

### 질문
Q1 (되비추기 확인): 간헐 실패가 맞나요?
Q2: 먼저 무엇을 볼까요?

### 답
→ S2, S3

## R2

### 직전 답에서 — S2
- 함의: 없음
- 상충: 없음
- 확인한 사실: 없음
- 위험: 없음

### 직전 답에서 — S3
- 함의: TTL 은 원인이 아니다
- 상충: 없음
- 확인한 사실: 없음
- 위험: TTL 을 다시 늘리면 같은 실패

### 질문
Q1 (되묻기): …

### 답
→ S4, S5

## R3

### 직전 답에서 — S4
- 함의: 서버는 요청을 못 받았다
- 상충: 없음
- 확인한 사실: 없음
- 위험: 없음

### 직전 답에서 — S5
- 함의: 없음
- 상충: S4 와 부딪힘 — → landscape 재개방: 서버 무기록
- 확인한 사실: 없음
- 위험: 없음

### 답
→ S6

## R4

### 직전 답에서 — S6
- 함의: 재현 실패는 정직하게 보고
- 상충: 없음
- 확인한 사실: 없음
- 위험: 없음

### 답
→ S7
```
기대: total 7(S8 은 skipped 1) · terminal 1(S7, R5 없음) · eligible 6 · with_block 6 · substantive_form 5(S2 블록만 넷 다 «없음») · 표본 4.

나머지 다섯은 위 파일의 변형(각각 별 파일로 **손으로** 쓰되 20줄 동일 블록이 생기지 않게 발화 텍스트를 다르게 한다):
- `depth-state-elig0.md`: `user_statements` 에 S1(round 0)만 있고 본문 `## R1` 이 있되 «직전 답에서» 블록 없음 → S1 은 terminal 이 아니지만… 주의: R1 이 있으면 S1 은 terminal 이 아니다. eligible 0 을 만들려면 S1 의 `text: ""`(빈 문자열) 로 둔다 → eligible 0, `human_sample: []`.
- `depth-state-elig1.md`: S1(round 0, 본문 있음)·S2(round 1) 와 `## R1`·`## R2`(S2 는 terminal? R2 가 있으면 S1 이 eligible, S2 는 R3 없음 → terminal) → eligible 1, 표본 1.
- `depth-state-elig3.md`: S1·S2·S3(round 0·1·2), `## R1`·`## R2`·`## R3`, S3 terminal → eligible 3, 표본 3.
- `depth-state-noround.md`: frontmatter 는 normal 과 같되 본문에 `## R` 헤딩이 하나도 없다(«Round 1 — 4-block 요지» 같은 옛 산문) → rc 3.
- `depth-state-allnone.md`: elig1 과 같되 S1 블록의 네 줄 전부 «없음» → substantive_form 0, rc 0.

- [ ] **Step 2: 실패하는 테스트** — `plugins/spec-distill/tests/test_depth_pairs.py`

```python
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
```

- [ ] **Step 3: RED** — `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s plugins/spec-distill/tests -p 'test_depth_pairs.py'` → 전부 ERROR(스크립트 부재).

- [ ] **Step 4: 구현** — `plugins/spec-distill/scripts/depth_pairs.py`

```python
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
    """`user_statements` → [{id, round, text}]. round 는 int 또는 원문 문자열."""
    lines = fm.splitlines()
    start = next((i for i, ln in enumerate(lines) if re.match(r"^user_statements\s*:", ln)), None)
    if start is None:
        raise ValueError("user_statements 키 부재")
    if re.match(r"^user_statements\s*:\s*\[\s*\]\s*$", lines[start]):
        return []
    items, cur, i = [], None, start + 1
    while i < len(lines):
        ln = lines[i]
        if ln.strip() and not ln[0].isspace() and not ln.lstrip().startswith("-"):
            break
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
```

- [ ] **Step 5: GREEN** — 같은 unittest 명령 → `OK`. 실패하면 fixture 기대값과 구현 중 **fixture 를 먼저 의심하지 말고** 규칙(§3.1)에 비춰 어느 쪽이 틀렸는지 적고 고친다.

- [ ] **Step 6: 커밋** — `feat(spec-distill): depth_pairs.py — 답→다음 행동 짝 추출·표본 (AC6)`

---

### Task 7: `depth-auditor` 에이전트 + frontmatter 락 + 격리 집합 등식 갱신 (AC7 일부)

**Files:**
- Create: `plugins/spec-distill/agents/depth-auditor.md` · `plugins/spec-distill/tests/test_depth_auditor_frontmatter.sh`
- Modify: `plugins/spec-distill/tests/test_brief_agents.sh` (`EXPECTED_ISOLATED` 에 `depth-auditor` 추가 — 등식 락은 리터럴 목록이라 다섯째를 넣지 않으면 RED)

**Interfaces:**
- Produces: agent 이름 `depth-auditor`(dispatch 는 `spec-distill:depth-auditor`), 입력 슬롯 `<pairs>${PAIRS_INLINE}</pairs>`(`input_slots: tag pairs / var PAIRS_INLINE / kind artifact`), 출력 계약 = 펜스 info string `depth-audit` 의 YAML 블록:
  ```
  ```depth-audit
  pairs:
    - s: S3
      label: dug
      reason: "S3 의 «TTL 늘려봤는데 안 됨»에서 «TTL 은 원인이 아니다»가 따라 나왔다"
  ```
  ```
  라벨 어휘 `dug | not_dug | undecidable`. Task 8 의 파서가 이 모양만 읽는다.

- [ ] **Step 1: 실패하는 락** — `plugins/spec-distill/tests/test_depth_auditor_frontmatter.sh`

```bash
#!/usr/bin/env bash
# guards: plugins/spec-distill/agents/depth-auditor.md
# AC7 — depth-auditor 도구 표면 0 · model 키 부재 · 출력 계약 · 입력 격리 문장.
set -u -o pipefail
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
AGENT="$REPO_ROOT/plugins/spec-distill/agents/depth-auditor.md"
. "$REPO_ROOT/shared/tests/assert.sh"
if [ "${1:-}" = "--emit-scanned" ]; then echo "plugins/spec-distill/agents/depth-auditor.md"; exit 0; fi
[ -f "$AGENT" ] || { no "agent 파일 부재: $AGENT"; finish; exit $?; }
FM="$(awk 'NR==1&&$0=="---"{f=1;next} f&&$0=="---"{exit} f' "$AGENT")"
grep -qE '^name: depth-auditor$' <<<"$FM" && ok "name: depth-auditor" || no "name 불일치"
tl="$(printf '%s\n' "$FM" | sed -n 's/^tools:[[:space:]]*//p' | head -1)"; tl="${tl%"${tl##*[![:space:]]}"}"
case "$tl" in "[]"|"[ ]") ok "tools: [] (도구 표면 0 — Law 2)";; *) no "tools 가 빈 리스트가 아니다: '$tl'";; esac
MODEL_KEY="^[\"']?model[\"']?[[:space:]]*:"
grep -qE "$MODEL_KEY" <<<"$FM" && no "frontmatter 에 model 키가 있다 (0.54.0 규약 위반)" || ok "model 키 없음 (tier-unpinned)"
grep -qE '^cost_class: (low|medium|high|variable)$' <<<"$FM" && ok "cost_class 선언" || no "cost_class 없음"
grep -qE '^\s+- tag: pairs$' <<<"$FM" && grep -qE '^\s+var: PAIRS_INLINE$' <<<"$FM" \
  && ok "input_slots: pairs/PAIRS_INLINE" || no "input_slots 에 pairs 슬롯이 없다"
# 본문 계약 — frontmatter 제외 본문에서
BODY="$(awk 'c>=2{print} /^---$/{c++}' "$AGENT")"
grep -qF '```depth-audit' <<<"$BODY" && ok "출력 계약: depth-audit 센티널" || no "depth-audit 센티널 부재"
grep -qE 'dug \| not_dug \| undecidable|dug.*not_dug.*undecidable' <<<"$BODY" && ok "라벨 어휘 셋" || no "라벨 어휘 부재"
grep -qF '짝 목록 밖' <<<"$BODY" && ok "입력 격리 문장(짝 목록 밖을 보지 마라)" || no "입력 격리 문장 부재"
grep -qE 'S<k> 의 어느 부분|어느 부분에서' <<<"$BODY" && ok "이유 줄에 출처 부분 요구" || no "출처 부분 요구 부재"
# 예시 짝 셋(관련 → dug / 다른 답에서 → not_dug / 무관 → not_dug) 이 본문에 있다
[ "$(grep -cE '^\s+label: (dug|not_dug)' <<<"$BODY")" -ge 3 ] && ok "예시 짝 ≥3" || no "예시 짝이 3개 미만"
finish
```

- [ ] **Step 2: RED** — `bash plugins/spec-distill/tests/test_depth_auditor_frontmatter.sh` → 파일 부재 1 ✗. 그리고 `bash plugins/spec-distill/tests/test_brief_agents.sh | grep 'L:'` 는 아직 ✓(agent 가 없으니).

- [ ] **Step 3: agent 작성** — `plugins/spec-distill/agents/depth-auditor.md`

```markdown
---
name: depth-auditor
description: >
  Use this agent at the end of a spec-distill interview to label answer→next-action
  pairs for DEPTH — whether the interviewer's «직전 답에서» block drew something out of
  the user's answer S<k> that was not already in S<k>. Receives the pair list inline as
  a single `<pairs>${PAIRS_INLINE}</pairs>` block; owns no tools, reads no files. Emits a
  `depth-audit` sentinel YAML block. Labels are a measurement consumed by
  scripts/depth_record.py, never a gate.

  <example>Context: conducting-interview reached Step A.7 depth measurement.
  user: "깊이 라벨링 해줘"
  assistant: "I'll dispatch the depth-auditor agent with the pair list inlined."</example>
tools: []
color: cyan
cost_class: low
input_slots:
  - tag: pairs
    var: PAIRS_INLINE
    kind: artifact
---

# depth-auditor (측정 — 게이트 아님)

당신은 인터뷰 짝 `(S<k>, «직전 답에서 — S<k>» 블록)` 마다 **그 블록이 S<k> 에서 따라 나오되
S<k> 에 없던 것을 하나라도 적었는가**를 라벨한다. 짝 목록 밖의 것은 보지 마라 — 당신은 도구가
없고, 받은 것이 전부다.

**당신의 책임이 아닌 것**: 원장·닫힘의 정당성, 답의 품질, 다음 질문의 좋고 나쁨, 인터뷰
전체의 판정. 당신의 라벨은 사람 표본과 대조되는 계수이지 근거가 아니다.

## 라벨

- `dug` — 함의·상충·확인한 사실·위험 중 **S<k> 에서 따라 나온** 내용이 하나라도 있고 그것이
  S<k> 에 이미 있던 말의 되풀이가 아니다.
- `not_dug` — 네 줄이 전부 «없음»이거나, 적힌 것이 S<k> 의 되풀이거나, **다른 답**에서 나온
  것이거나, S<k> 와 **무관한** 정보다. 무관한 정보를 많이 적은 블록도 `not_dug` 다.
- `undecidable` — S<k> 발췌가 잘려 판단할 수 없거나 블록이 비어 있다(블록 없음은 `not_dug`
  가 아니라 `undecidable` 로 두고 이유에 «블록 없음»을 적는다).

이유 줄에는 **S<k> 의 어느 부분에서** 그것이 따라 나왔는지(또는 왜 안 따라 나오는지)를 한 줄로.

## 예시 짝

```depth-audit
pairs:
  - s: S3
    label: dug
    reason: "S3 «TTL 늘려봤는데 안 됨»에서 «TTL 은 원인이 아니다»(함의)와 «다시 늘리면 같은 실패»(위험)가 따라 나왔다"
  - s: S5
    label: not_dug
    reason: "블록의 «서버는 요청을 못 받았다»는 S4 에서 나온 것이고 S5 «클라이언트 경합 의심»에서 따라 나온 줄이 없다"
  - s: S6
    label: not_dug
    reason: "«확인한 사실: 배포 파이프라인이 두 개다»는 S6 «재현이 안 되면 멈춰라»와 무관하다"
```

## 출력 (이 형식만 — 다른 산문 없이)

```depth-audit
pairs:
  - s: S<k>
    label: dug | not_dug | undecidable
    reason: "<한 줄>"
```

입력에 있는 모든 짝을 정확히 한 번씩 낸다. 짝을 빼거나 더하지 않는다.
```

- [ ] **Step 4: 격리 집합 등식 갱신** — `test_brief_agents.sh` 의 `EXPECTED_ISOLATED="brief-critic\nbrief-readback\nseed-critic\nseed-readback"` 에 `depth-auditor` 줄을 더한다(정렬은 비교 시 `sort` 가 한다). 주석에 «v0.55.0 depth-auditor 편입» 한 줄.

- [ ] **Step 5: GREEN 셋**

```bash
bash plugins/spec-distill/tests/test_depth_auditor_frontmatter.sh | tail -1
bash plugins/spec-distill/tests/test_brief_agents.sh | tail -1
bash shared/tests/test_agent_input_slots.sh | tail -1
```
Expected: 셋 다 `Fail: 0`. `test_agent_input_slots.sh` 가 `undelivered` 를 내면 Task 9 의 dispatch 자리가 아직 없어서다 — 그 경우 Task 9 뒤에 재확인한다고 적고 넘어간다(선언 없는 태그 전달 `undeclared` 만 지금 0 이어야 한다).

- [ ] **Step 6: mutation** — 커밋 후 `tools: []` → `tools: Read` 로 바꿔 두 락(frontmatter·등식) 모두 RED 확인, `git checkout -- plugins/spec-distill/agents/depth-auditor.md`.

- [ ] **Step 7: 커밋** — `feat(spec-distill): depth-auditor 에이전트 (tools: [], depth-audit 센티널) + 격리 집합 등식 (AC7)`

### Task 8: `depth_record.py` — 병합 · audit §2 줄 · 인터뷰별 측정 파일 · 조건 판정 (AC8)

**Files:**
- Create: `plugins/spec-distill/scripts/depth_record.py` · `plugins/spec-distill/tests/test_depth_record.py` · `docs/superpowers/interview/depth/.gitkeep`
- Test: `python3 -m unittest discover -s plugins/spec-distill/tests -p 'test_depth_record.py'` · `bash shared/tests/test_adjudication_wiring.sh` · `bash shared/tests/test_adjudication_consumed.sh`

**Interfaces:**
- CLI: `python3 depth_record.py <pairs.json> --auditor <raw.txt> --human <json-string|@file> --audit <audit.md> --out <depth/<basename>.json> [--date YYYY-MM-DD]`
- `--human` JSON: `{"skipped": false, "labels": {"S3": "dug", "S5": "not_dug", "S6": "undecidable"}}`. `skipped: true` 또는 표본 S 가 `labels` 에 없음 → 그 S 는 `unlabeled`. 표본 0 이면 `{"skipped": false, "labels": {}}` 와 `sampled: 0`.
- stdout(항상 rc 0): audit §2 에 붙일 세 줄 + 조건 줄 + 처분 두 줄(`render_disposition.disposition_lines`) + advisory. 어떤 실패도 `- 깊이 측정: 기록 불가 — <이유>` 한 줄 + rc 0.
  ```
  - 깊이 측정(형식): 짝 <n> 중 되비추기 블록 있음 <m> · 내용 있는 줄 ≥1 <p> · terminal <t>
  - 깊이 측정(auditor): dug <a> · not_dug <b> · undecidable <c> · held <h> · unavailable <0|1>
  - 깊이 측정(사람): 표본 <s> — dug <x> · not_dug <y> · undecidable <z> · 미라벨 <w> · auditor 일치 <k>/<v> (auditor 판정 없는 표본 <u> 별도)
  - 판정자 조건: <조건 미도달 (<e>/5) | 판정자 투입 조건 도달 — … | auditor 계수는 근거에서 제외 — … | 자료 부족>
  ```
  분모 0(v=0) 이면 일치 칸은 `자료 부족`. 표본 0 이면 사람 줄은 `표본 없음`.
- 측정 파일(spec §3.3 스키마 그대로): `{"date","brief","session_id","pairs":{total,eligible,with_block,substantive_form,terminal},"auditor":{dug,not_dug,undecidable,held,unavailable},"human":{sampled,dug,not_dug,undecidable,unlabeled,auditor_missing,agreement:[k,v]}}`. `brief` = `--audit` 경로의 `.audit.md` → `.md`.
- 조건(spec §3.4): `dirname(--out)/*.json` 전부(방금 쓴 것 포함). 적격 인터뷰 = `human.dug + human.not_dug ≥ 1`. 적격 ≥5 일 때: A `Σnot_dug / Σ(dug+not_dug) ≥ 0.30` → 「판정자 투입 조건 도달 — 다음 사이클이 닫힘 거부권 에이전트를 설계한다」; B `Σk / Σv < 0.70` → 「auditor 계수는 근거에서 제외 — 사람 표본을 늘린다」(`Σv == 0` → 「자료 부족」). 둘 다면 ` · ` 로 이어 붙인다. 적격 <5 → 「조건 미도달 (<e>/5)」.
- 처분 회계: `Ledger(items="open")`. auditor 항목 라벨 정상 → `accept`; 라벨 어휘 밖·`s` 없음 → `hold(item, "항목 파손: …")`; 센티널 부재/빈 출력/파일 부재 → `source_failed("depth-auditor", why, primary=True)` + `auditor.unavailable = true`; 표본 밖 S 를 auditor 가 냈으면 `suppressed(s, "표본·짝 밖")`; 사람 미라벨 → `suppressed(s, "사람 미라벨")`. **모든 for 문의 `continue` 는 그 직전에 처분을 부른다**(wiring 락).

- [ ] **Step 1: 디렉토리** — `docs/superpowers/interview/depth/.gitkeep` (빈 파일).

- [ ] **Step 2: 실패하는 테스트** — `plugins/spec-distill/tests/test_depth_record.py`

```python
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
    p = subprocess.run(cmd, capture_output=True, text=True, env={"PYTHONDONTWRITEBYTECODE": "1"})
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
            # 사람: S1 dug/S2 dug/S3 dug/S4 not_dug. 일치 분모 v = 양쪽 dug|not_dug 인 짝 = S1,S2,S4 → 3; 일치 k = S1,S4 → 2. S3 는 auditor undecidable → auditor_missing 1
            self.assertIn("- 깊이 측정(사람): 표본 4 — dug 3 · not_dug 1 · undecidable 0 · 미라벨 0 · auditor 일치 2/3 (auditor 판정 없는 표본 1 별도)", out)
            self.assertIn("- 판정자 조건: 조건 미도달 (1/5)", out)
            self.assertIn("**처분:**", out)
            self.assertEqual(rec["human"]["agreement"], [2, 3])
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
        # 이번 인터뷰 dug3/not_dug1 + prior 4건 → 적격 5. Σnot_dug/Σ = 3/10 = 30% → 도달
        prior = [prior_record(2, 1, 2, 3), prior_record(2, 1, 2, 3), prior_record(1, 0, 1, 1), prior_record(2, 0, 2, 2)]
        with tempfile.TemporaryDirectory() as td:
            _, out, _ = run(td, prior=prior)
            self.assertIn("판정자 투입 조건 도달", out)
        # 29%: 분모를 늘린다(추가 dug) → 미도달
        prior[3] = prior_record(3, 0, 3, 3)
        with tempfile.TemporaryDirectory() as td:
            _, out, _ = run(td, prior=prior)
            self.assertNotIn("판정자 투입 조건 도달", out)

    def test_condition_B_boundary_70pct(self):
        # 이번 k/v = 2/3. prior 로 Σk/Σv 를 정확히 0.70 (7/10) 과 0.69 미만 양쪽에 둔다
        prior = [prior_record(2, 0, 2, 2), prior_record(2, 0, 2, 2), prior_record(1, 0, 1, 1), prior_record(2, 0, 0, 2)]
        with tempfile.TemporaryDirectory() as td:   # Σk=2+2+2+1+0=7, Σv=3+2+2+1+2=10 → 0.70 → 제외 아님
            _, out, _ = run(td, prior=prior)
            self.assertNotIn("auditor 계수는 근거에서 제외", out)
        prior[0] = prior_record(2, 0, 1, 2)          # Σk=6 → 0.60 → 제외
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
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0)
            self.assertIn("기록 불가", p.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: RED** — discover 명령 → ERROR 전부.

- [ ] **Step 4: 구현** — `plugins/spec-distill/scripts/depth_record.py`

```python
#!/usr/bin/env python3
"""depth_record.py — 세 층(형식·auditor·사람)을 병합해 기록한다 (spec §3.2~§3.4, v0.55.0).

항상 exit 0. 측정이지 게이트가 아니다(C5) — 실패는 «기록 불가: <이유>» 로 표면화한다.
처분 회계는 adjudication.Ledger(항목 파손 → held, 센티널 부재 → source_failed).
"""
import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from adjudication import Ledger  # noqa: E402
from render_disposition import disposition_lines  # noqa: E402

LABELS = ("dug", "not_dug", "undecidable")
SENTINEL_RE = re.compile(r"```depth-audit[ \t]*\n(.*?)\n```", re.DOTALL)
ITEM_RE = re.compile(r"^\s*-\s+s\s*:\s*(\S+)\s*$")
FIELD_RE = re.compile(r"^\s+(label|reason)\s*:\s*(.*?)\s*$")


def parse_auditor(raw, L):
    """센티널 블록 → {S: label}. 블록 부재는 None(unavailable) — 0건과 구분."""
    m = SENTINEL_RE.search(raw or "")
    if not m:
        L.source_failed("depth-auditor", "depth-audit 센티널 블록 부재/빈 출력", primary=True)
        return None
    items, cur = [], None
    for ln in m.group(1).splitlines():
        im = ITEM_RE.match(ln)
        if im:
            cur = {"s": im.group(1)}; items.append(cur); continue
        fm = FIELD_RE.match(ln)
        if fm and cur is not None:
            cur[fm.group(1)] = fm.group(2).strip().strip('"')
    labels = {}
    for it in items:
        lab = it.get("label")
        if lab not in LABELS:
            L.hold(it.get("s", "?"), "항목 파손: label %r 는 어휘 밖" % (lab,))
            continue
        labels[it["s"]] = lab
        L.accept(it["s"])
    return labels


def condition_line(depth_dir):
    e = nd = tot = k = v = 0
    for path in sorted(glob.glob(os.path.join(depth_dir, "*.json"))):
        try:
            with open(path, encoding="utf-8") as fh:
                rec = json.load(fh)
            h = rec["human"]
            d, n = int(h["dug"]), int(h["not_dug"])
            ak, av = h["agreement"]
        except (OSError, ValueError, KeyError, TypeError):
            continue  # 판독 불가 파일은 조건 계수 밖 — 아래 uncountable 로 센다
        if d + n < 1:
            continue
        e += 1; nd += n; tot += d + n; k += int(ak); v += int(av)
    if e < 5:
        return "조건 미도달 (%d/5)" % e
    parts = []
    if tot and nd / tot >= 0.30:
        parts.append("판정자 투입 조건 도달 — 다음 사이클이 닫힘 거부권 에이전트를 설계한다 (not_dug %d/%d)" % (nd, tot))
    if v == 0:
        parts.append("auditor 일치 자료 부족")
    elif k / v < 0.70:
        parts.append("auditor 계수는 근거에서 제외 — 사람 표본을 늘린다 (일치 %d/%d)" % (k, v))
    return " · ".join(parts) if parts else "조건 미도달 (%d/5)" % e


def main(argv):
    ap = argparse.ArgumentParser(add_help=False)
    for a in ("pairs",):
        ap.add_argument(a)
    for a in ("--auditor", "--human", "--audit", "--out"):
        ap.add_argument(a, required=True)
    ap.add_argument("--date", default=None)
    try:
        a = ap.parse_args(argv[1:])
        with open(a.pairs, encoding="utf-8") as fh:
            pairs = json.load(fh)
        human_in = a.human[1:] if a.human.startswith("@") else a.human
        if a.human.startswith("@"):
            with open(human_in, encoding="utf-8") as fh:
                human_in = fh.read()
        human = json.loads(human_in or "{}")
        counts = pairs["counts"]; sample = [s["s"] for s in pairs.get("human_sample", [])]
    except (SystemExit, OSError, ValueError, KeyError, TypeError) as exc:
        print("- 깊이 측정: 기록 불가 — %s" % exc)
        return 0

    L = Ledger(items="open")
    try:
        with open(a.auditor, encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    except OSError as exc:
        raw = ""
        L.uncountable("auditor raw", "파일 판독 실패: %s" % exc)
    labels = parse_auditor(raw, L)
    unavailable = labels is None
    labels = labels or {}
    pair_ids = {p["s"] for p in pairs.get("pairs", [])}
    for s in list(labels):
        if s not in pair_ids:
            L.suppressed(s, "짝 목록 밖의 S")
            del labels[s]
    rep = L.report()
    aud = {lab: sum(1 for x in labels.values() if x == lab) for lab in LABELS}
    aud["held"] = rep["counts"]["held"]; aud["unavailable"] = unavailable

    hl = {} if human.get("skipped") else {k2: v2 for k2, v2 in (human.get("labels") or {}).items()}
    hum = {"sampled": len(sample), "dug": 0, "not_dug": 0, "undecidable": 0, "unlabeled": 0,
           "auditor_missing": 0, "agreement": [0, 0]}
    for s in sample:
        h = hl.get(s)
        if h not in LABELS:
            hum["unlabeled"] += 1
            L.suppressed(s, "사람 미라벨")
            continue
        hum[h] += 1
        if h == "undecidable":
            continue
        al = labels.get(s)
        if al in ("dug", "not_dug"):
            hum["agreement"][1] += 1
            hum["agreement"][0] += int(al == h)
        else:
            hum["auditor_missing"] += 1

    if a.date:
        date = a.date
    else:
        import datetime
        date = datetime.date.today().isoformat()
    audit_path = a.audit
    brief = audit_path[:-len(".audit.md")] + ".md" if audit_path.endswith(".audit.md") else audit_path
    rec = {"date": date, "brief": brief, "session_id": pairs.get("session_id", ""),
           "pairs": {k2: counts.get(k2, 0) for k2 in ("total", "eligible", "with_block", "substantive_form", "terminal")},
           "auditor": aud, "human": hum}
    try:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(rec, fh, ensure_ascii=False, indent=1)
    except OSError as exc:
        print("- 깊이 측정: 기록 불가 — 측정 파일 쓰기 실패: %s" % exc)
        return 0

    k, v = hum["agreement"]
    agree = "자료 부족" if v == 0 else "%d/%d" % (k, v)
    print("- 깊이 측정(형식): 짝 %d 중 되비추기 블록 있음 %d · 내용 있는 줄 ≥1 %d · terminal %d"
          % (rec["pairs"]["total"], rec["pairs"]["with_block"], rec["pairs"]["substantive_form"], rec["pairs"]["terminal"]))
    print("- 깊이 측정(auditor): dug %d · not_dug %d · undecidable %d · held %d · unavailable %d"
          % (aud["dug"], aud["not_dug"], aud["undecidable"], aud["held"], 1 if unavailable else 0))
    if hum["sampled"] == 0:
        print("- 깊이 측정(사람): 표본 없음")
    else:
        print("- 깊이 측정(사람): 표본 %d — dug %d · not_dug %d · undecidable %d · 미라벨 %d · auditor 일치 %s (auditor 판정 없는 표본 %d 별도)"
              % (hum["sampled"], hum["dug"], hum["not_dug"], hum["undecidable"], hum["unlabeled"], agree, hum["auditor_missing"]))
    print("- 판정자 조건: %s" % condition_line(os.path.dirname(os.path.abspath(a.out))))
    line1, line2, adv = disposition_lines(L.report(), L.held_by_class())
    print(line1); print(line2)
    for x in adv + L.reasons():
        print("advisory: %s" % x)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
```
`condition_line` 의 두 `continue` 는 판독 불가·비적격 파일을 버리는 분기다 — wiring 락이 처분 호출을 요구하므로 함수에 `L` 을 넘겨 첫 분기에 `L.uncountable(path, "측정 파일 판독 불가")`, 둘째에 `L.suppressed(path, "적격 아님(dug+not_dug=0)")` 를 `continue` 앞에 넣는다(위 코드에 반영하고 호출부를 `condition_line(dir, L)` 로). 테스트 `test_condition_A_boundary_30pct` 의 산술: 이번 인터뷰 dug 3·not_dug 1 + prior (2,1)(2,1)(1,0)(2,0) → Σnot_dug 3, Σ 10 → 0.30 도달; 넷째를 (3,0) 으로 바꾸면 3/11 → 미도달.

- [ ] **Step 5: GREEN + 회계 락 셋**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s plugins/spec-distill/tests -p 'test_depth_record.py'
bash shared/tests/test_adjudication_wiring.sh | tail -3
bash shared/tests/test_adjudication_consumed.sh | tail -3
```
Expected: `OK`; wiring 은 `depth_record.py` 의 for 문 버리는 분기 전부에 처분 호출이 있어 새 실패 0(선재 실패는 baseline 과 대조); consumed 는 `render_disposition` import 로 여덟 키 소비. wiring 이 어느 분기를 지목하면 그 분기 직전에 처분 호출을 넣는다 — 면제 목록(`check_wiring.py` 의 EXEMPTIONS)에 넣지 않는다.

- [ ] **Step 6: 커밋** — `feat(spec-distill): depth_record.py — 세 층 병합·측정 파일·판정자 조건 (AC8)` (`.gitkeep` 포함)

### Task 9: `finishing.md` — Step A.7 깊이 측정 · 원장 직렬화 규칙 · 게이트 텍스트 · audit 템플릿 (AC9·AC10·AC7 처분)

**Files:**
- Modify: `plugins/spec-distill/skills/conducting-interview/references/finishing.md` (Step A 4 항 보강, Step A.5 뒤에 `### Step A.7` 신설, B-2 게이트 question 텍스트) · `plugins/spec-distill/templates/interview-audit-template.md`
- Test: `plugins/spec-distill/tests/test_conducting_interview_stage.sh` (Step A.7 블록 스코프 락 추가) · `bash shared/tests/test_dispatch_disposition.sh` · `bash shared/tests/test_agent_input_slots.sh`

**Interfaces:**
- Consumes: Task 6 CLI(`depth_pairs.py "$STATE" --sample 4`, rc 3), Task 7 의 `spec-distill:depth-auditor` + `<pairs>${PAIRS_INLINE}</pairs>`, Task 8 CLI.
- Produces: Step B 게이트 question 의 `깊이: <세 줄 요약>` 슬롯과 `advisories` 슬롯(check_brief 의 `coverage-mapper 0 (unavailable…)` advisory 가 여기 실린다).

- [ ] **Step 1: 실패하는 락** — `test_conducting_interview_stage.sh` 의 `finish` 앞

```bash
# --- v0.55.0 Step A.7 깊이 측정 (finishing.md, 블록 스코프) --------------------------
a7_block="$(awk '/^### Step A\.7/{f=1;print;next} /^### /{f=0} f' "$FIN")"
a7_flat="$(tr '\n' ' ' <<<"$a7_block" | tr -s ' ')"
{ [[ -n "$a7_block" ]] && grep -qF 'depth_pairs.py' <<<"$a7_block"; } \
  && ok "A.7: 깊이 측정 절이 있고 depth_pairs.py 를 부른다" || no "A.7: 절 부재 또는 depth_pairs.py 호출 없음"
grep -qF 'spec-distill:depth-auditor' <<<"$a7_block" && ok "A.7: depth-auditor dispatch" || no "A.7: depth-auditor dispatch 없음"
grep -qF 'consumer=plugins/spec-distill/scripts/depth_record.py' <<<"$a7_block" && ok "A.7: 처분 줄이 depth_record.py 를 소비자로" || no "A.7: 처분 줄 부재"
grep -qF 'depth_record.py' <<<"$a7_block" && ok "A.7: depth_record.py 호출" || no "A.7: depth_record.py 호출 없음"
grep -qE 'pairs_rc[^.]{0,40}3[^.]{0,60}측정 불가' <<<"$a7_flat" && ok "A.7: rc 3 → «측정 불가» 기록" || no "A.7: rc 3 처분 없음"
grep -qE '기록한다[^.]{0,20}막지 않는다|막지 않는다' <<<"$a7_flat" && ok "A.7: «기록한다, 막지 않는다» (C5)" || no "A.7: 비게이트 선언 없음"
grep -qE '표본[^.]{0,10}0[^.]{0,30}(띄우지 않는다|호출 안 함|호출하지 않는다)' <<<"$a7_flat" && ok "A.7: 표본 0 이면 라벨 질문 없음" || no "A.7: 표본 0 처분 없음"
grep -qF '미라벨' <<<"$a7_block" && grep -qF 'unavailable' <<<"$a7_block" && ok "A.7: 미라벨·unavailable 어휘" || no "A.7: 미라벨/unavailable 어휘 부재"
grep -qE 'heredoc' <<<"$a7_block" && grep -qE '리다이렉트' <<<"$a7_block" && ok "A.7: raw 저장은 파일 리다이렉트(heredoc 금지)" || no "A.7: raw 저장 방식 미명시"
grep -q '파고들었다' <<<"$a7_block" && grep -q '안 팠다' <<<"$a7_block" && grep -q '판단불가' <<<"$a7_block" && ok "A.7: 사람 라벨 선택지 셋" || no "A.7: 사람 라벨 선택지 부재"
grep -qF 'min(4' <<<"$a7_block" && ok "A.7: 질문 수 min(4, 적격)" || no "A.7: 표본 상한 규칙 부재"
# B-2 게이트 텍스트에 깊이 요약과 advisories 슬롯
b2_block="$(awk '/^#### B-2/{f=1;print;next} /^#### /{f=0} f' "$FIN")"
grep -qF '깊이:' <<<"$b2_block" && ok "B-2: question 에 깊이 요약 슬롯" || no "B-2: 깊이 요약 슬롯 부재"
grep -qF 'coverage-mapper 0' <<<"$b2_block" && ok "B-2: coverage-mapper unavailable advisory 가 게이트 텍스트에" || no "B-2: mapper advisory 슬롯 부재"
# Step A 4 항: 직렬화 규칙 (S앵커·재개방 접미)
stepa4="$(awk '/^4\. \*\*Coverage Ledger 직렬화/{f=1} f&&/^5\. /{exit} f' "$FIN")"
grep -qE 'S<N>|S\\d\+|S 앵커' <<<"$stepa4" && grep -qF '재개방' <<<"$stepa4" && ok "Step A 4: 직렬화가 S앵커·재개방 접미를 요구" || no "Step A 4: 직렬화 규칙에 S앵커/재개방 부재"
grep -qF 'coverage-mapper <k>' <<<"$stepa4" && ok "Step A 4: §2 coverage-mapper <k> 직렬화" || no "Step A 4: coverage-mapper <k> 부재"
# audit 템플릿
TPL="$REPO_ROOT/plugins/spec-distill/templates/interview-audit-template.md"
grep -qF '깊이 측정(형식)' "$TPL" && grep -qF '깊이 측정(auditor)' "$TPL" && grep -qF '깊이 측정(사람)' "$TPL" && ok "AC10: audit 템플릿 §2 깊이 세 줄" || no "AC10: 템플릿 §2 깊이 줄 부재"
grep -qF '(재개방' "$TPL" && ok "AC10: 템플릿 §1 재개방 접미 예시" || no "AC10: 재개방 접미 예시 부재"
grep -qF 'coverage-mapper <k>' "$TPL" && ok "AC10: 템플릿 §2 coverage-mapper <k>" || no "AC10: 템플릿 coverage-mapper 부재"
grep -qE 'path \(a\|b\|c\|d\)' "$TPL" && no "AC10: 템플릿 §5 에 경로 (c) 잔존" || ok "AC10: 템플릿 §5 경로 (c) 제거"
```

- [ ] **Step 2: RED** — `bash plugins/spec-distill/tests/test_conducting_interview_stage.sh | grep -E 'A\.7|B-2: (question|coverage)|Step A 4|AC10'` 전부 ✗.

- [ ] **Step 3: finishing.md 편집 (a) Step A 4 항** — «4. **Coverage Ledger 직렬화**(게이트 *전*)» 문단 끝에 덧붙인다:

```markdown
   **닫힌 행의 evidence 는 그 차원을 닫은 사용자 발화 `S<N>` 을 인용한다**(게이트가 검사한다 —
   `floor:<dim> evidence cites no S<N> anchor`). 어느 S 인지의 규약: root_problem = 재구성 동의 S ·
   landscape = 외부 근거 되비추기 처분 S · skepticism = steelman 판정 S · blind_spot = 숨은 가정·
   실패 양식 처분 S · open_questions = OQ 목록 확인 S. 사용자-승인 박제 행은 앵커가 접두 **뒤**에
   온다: `사용자-승인 박제(@S12) — §Open Questions 참조`. 재개방된 차원은 행 끝에
   `(재개방 <n>회 — <마지막 사유>)` 접미를 붙인다(state `reopen_log` 의 마지막 항목).
   같은 시점에 **audit §2 Budget** 에 `coverage-mapper <k>` 를 쓴다(state
   `orchestration.coverage_mapper_dispatches`). dispatch 가 불가능했던 환경이면
   `coverage-mapper 0 (unavailable: <이유>)` — 게이트는 이를 advisory 로 통과시키고 Step B 가
   사람에게 보인다.
```

- [ ] **Step 4: finishing.md 편집 (b) Step A.7** — `### Step A.5` 절 끝(«산출물 4종 … Step B 게이트로 넘어옵니다.» 뒤) 과 `### Step B` 사이에 삽입:

```markdown
### Step A.7 — 깊이 측정 (세 층, 게이트 아님 · v0.55.0)

«답 직후 파고들었는가»를 스크립트(형식)·`depth-auditor`(내용)·사람(≤4개 라벨)이 각각 세고,
결과는 audit §2 세 줄과 `docs/superpowers/interview/depth/<brief-basename>.json` 하나로 남는다.
**어느 층의 결과도 종료를 막지 않는다 — 기록한다, 막지 않는다.** 측정 불가·unavailable·미라벨은
전부 그렇게 **기록**된다(C5).

```bash
PR="${CLAUDE_PLUGIN_ROOT:-./plugins/spec-distill}"
ROOT="$(python3 "$PR/scripts/state_path.py" state-root)"
harness_sid="$(python3 "$PR/scripts/state_path.py" session-id)"
STATE="$ROOT/$harness_sid/state.local.md"
PAIRS="$ROOT/$harness_sid/depth-pairs.json"
AUD_RAW="$ROOT/$harness_sid/depth-auditor-raw.txt"
python3 "$PR/scripts/depth_pairs.py" "$STATE" --sample 4 > "$PAIRS"; pairs_rc=$?
```

- `pairs_rc` 가 3 이면 auditor 도 사람 라벨도 돌리지 않고 audit §2 에
  `- 깊이 측정: 측정 불가 — <stdout 의 unmeasurable 값>` 한 줄을 쓰고 Step B 로 간다.
- `pairs_rc` 가 0 이면 `$PAIRS` 의 `pairs` 배열을 **그대로 inline** 해 dispatch 한다:

```javascript
Agent({
  description: "Depth audit of answer→next-action pairs",
  subagent_type: "spec-distill:depth-auditor",
  // **처분** — consumer=plugins/spec-distill/scripts/depth_record.py · fail-open
  prompt: `아래 짝마다 «직전 답에서» 블록이 S 에 없던 함의·상충·사실·위험을 하나라도 적었는지 판정하라.
라벨은 dug | not_dug | undecidable, 각각 한 줄 이유(S 의 어느 부분에서인지). 짝 목록 밖의 것은 보지 마라.
<pairs>${PAIRS_INLINE}</pairs>` })
```

- auditor 의 raw 출력은 **요약·전사 없이** `$AUD_RAW` 에 저장한다 — heredoc 이 아니라 **파일
  리다이렉트**로(`printf '%s' "$RAW" > "$AUD_RAW"`; raw 에 `'`·`)` 가 섞이면 heredoc-in-`$()`
  파싱이 깨진 전례). dispatch 가 불가능하면(Agent 도구 부재·kill switch) 빈 파일을 두고
  `depth_record.py` 가 «unavailable» 로 기록하게 한다 — 0건으로 적지 않는다.
- 사람 라벨: `$PAIRS` 의 `human_sample` 이 표본이다(`min(4, 적격 짝)` 개). **표본이 0 이면
  질문을 띄우지 않는다**(«표본 없음»). 표본이 있으면 `AskUserQuestion` **한 번**, 질문 수 = 표본 수:

```javascript
AskUserQuestion({ questions: [ /* 표본마다 하나, ≤4 */ {
  header: "깊이 S<k>",
  question: "답 S<k>: «<s_excerpt ≤200자>» → 다음 라운드의 «직전 답에서» 블록: «<block_excerpt ≤300자>». 이 블록이 답에서 새로 끌어낸 것이 있나요?",
  options: [
    {label: "파고들었다", description: "블록에 답에서 따라 나온, 답에 없던 함의·상충·사실·위험이 있다"},
    {label: "안 팠다",   description: "네 줄이 «없음»이거나 답의 되풀이·무관한 정보뿐이다"},
    {label: "판단불가",  description: "발췌만으로는 알 수 없다"}],
  multiSelect: false } ] })
```

  «기타»에 «나중에» 류가 오거나 질문을 건너뛰면 그 표본은 **미라벨**이다. 답을
  `{"skipped": false, "labels": {"S3": "dug", …}}` (파고들었다→`dug`, 안 팠다→`not_dug`,
  판단불가→`undecidable`) 로 만들어 파일 `$ROOT/$harness_sid/depth-human.json` 에 쓴다.

```bash
AUDIT="docs/superpowers/interview/<file>.audit.md"        # Step A 가 쓴 경로
BASENAME="$(basename "$AUDIT" .audit.md)"
python3 "$PR/scripts/depth_record.py" "$PAIRS" --auditor "$AUD_RAW" \
  --human "@$ROOT/$harness_sid/depth-human.json" --audit "$AUDIT" \
  --out "docs/superpowers/interview/depth/$BASENAME.json"
```

  stdout 의 처음 네 줄(`- 깊이 측정(형식)…` · `(auditor)…` · `(사람)…` · `- 판정자 조건: …`)을
  **audit §2 Budget 에 그대로 붙인다**. 처분 두 줄과 `advisory:` 줄은 사용자에게 그대로 보인다.
  스크립트는 항상 exit 0 이고 실패는 `- 깊이 측정: 기록 불가 — <이유>` 로 온다 — 그 줄도 §2 에
  붙인다. 측정 파일은 `Write` 가 아니라 스크립트가 쓴다(디렉토리는 워크트리 안이라 어느 쪽도
  된다 — 스크립트가 쓰는 이유는 라벨 병합을 orchestrator 가 손으로 하지 않기 위해서다).
- 이 단계는 Step A 5 의 게이트 **뒤**에 돈다 — §2 에 줄이 늘어도 게이트는 §2 의
  `coverage-mapper <k>` 만 본다. 붙인 뒤 `check_brief.py gate` 를 한 번 더 돌려 §2 삽입이
  다른 검사를 건드리지 않았음을 확인한다.
```

- [ ] **Step 5: finishing.md 편집 (c) B-2 게이트 텍스트** — `question:` 문자열을 다음으로 바꾼다:

```
question: "interview brief 완결: <brief-path> (구조 게이트 통과, 리뷰 <verdict 요약>). 확정 후보·방향성 항목·readback gap은 위 목록대로. 깊이: <audit §2 의 깊이 측정 세 줄 요약 | 측정 불가 — <이유>>. 게이트 advisory: <check_brief 의 advisories 한 줄씩 (예: coverage-mapper 0 (unavailable: …)) | 없음>. degrade: <record 한 줄씩 | degrade 없음>. 다음 단계?",
```
그리고 그 위 «degrade 채널» 문단 뒤에 한 문단: «`check_brief.py gate` 의 `advisories` 도 이 텍스트에 싣는다 — `coverage-mapper 0 (unavailable: …)` 은 게이트가 관측할 수 없는 사실(실제 dispatch 여부)을 사람에게 넘기는 유일한 자리다.»

- [ ] **Step 6: audit 템플릿** — `templates/interview-audit-template.md`:
  - `source:` 줄을 `spec-distill conducting-interview v0.55.0` 으로.
  - §1 의 `- derived:<name> …` 뒤에 주석 줄: `(재개방된 차원은 행 끝에 «(재개방 <n>회 — <사유>)», 박제는 «사용자-승인 박제(@S<N>) — §Open Questions 참조». 모든 closed 행의 evidence 는 실재 S<N> 을 인용한다.)`
  - §2 를:
    ```
    - 질문 라운드: <n> · agent dispatch: <n> · coverage-mapper <k> · codex 실호출: <n> (성공 <n>)
    - 깊이 측정(형식): 짝 <n> 중 되비추기 블록 있음 <m> · 내용 있는 줄 ≥1 <p> · terminal <t>
    - 깊이 측정(auditor): dug <a> · not_dug <b> · undecidable <c> · held <h> · unavailable <0|1>
    - 깊이 측정(사람): 표본 <s> — dug <x> · not_dug <y> · undecidable <z> · 미라벨 <w> · auditor 일치 <k>/<v> (auditor 판정 없는 표본 <u> 별도)
    - 판정자 조건: <depth_record.py 출력 한 줄>
    ```
  - §5 `- round <n>: <path (a|b|c|d)> — …` → `<path (a|b|d)>`.

- [ ] **Step 7: GREEN + 처분·슬롯 락**

```bash
bash plugins/spec-distill/tests/test_conducting_interview_stage.sh | tail -1
bash shared/tests/test_dispatch_disposition.sh | tail -1
bash shared/tests/test_agent_input_slots.sh | tail -1
bash plugins/spec-distill/tests/test_check_brief.sh | tail -1
```
Expected: 전부 `Fail: 0`(선재 실패는 baseline 과 대조). dispatch 락이 `A2` 로 앵커 배정 실패를 내면 처분 줄이 `Agent(` 줄 아래 40줄 안에 있는지, 그 사이에 다른 dispatch 가 없는지 본다.

- [ ] **Step 8: mutation** — 커밋 후 Step A.7 절을 통째로 지워 A.7 락 전부 RED 확인, 복원.

- [ ] **Step 9: 커밋** — `feat(spec-distill): finishing Step A.7 깊이 측정 + 원장 직렬화 S앵커·재개방 + audit 템플릿 (AC9·AC10)`

---

### Task 10: SKILL.md §1 — 라운드 규약 · AskUserQuestion 둘 · 되묻기 · 제거 (AC1·AC2, G7)

**Files:**
- Modify: `plugins/spec-distill/skills/conducting-interview/SKILL.md` (현행 408줄; 절 `## 4-block Korean format`(:81-97) → 교체, `## C43 4-path routing`(:99-110) 의 (c) 행 제거, `## teach-beat`(:112-130) 삭제, `## 사용자 발화 기록` 표의 (c) 행 제거, `## C44` 의 (c) 줄 제거, 머리말(:13-24)·State body 문장(:59) 갱신)
- Test: `plugins/spec-distill/tests/test_conducting_interview_stage.sh` (teach-beat 락 5개 삭제 → 새 락)

**Interfaces:**
- Produces: 절 이름 `## 라운드 규약 — «직전 답에서» 블록 + 질문 둘` (Task 11 의 닫힘 규칙이 이 절의 «Q1 에 답한 S» 어휘를 가리킨다), `## 되묻기로 바뀌는 조건`. state 본문 형식 = Task 6 파서가 읽는 그 형식(헤딩 리터럴 `## R<n>` · `### 직전 답에서 — S<k>` · 네 줄 키 `함의/상충/확인한 사실/위험`).

- [ ] **Step 1: 락 교체 (RED 먼저)** — `test_conducting_interview_stage.sh`:
  (a) `# teach-beat 섹션 (scoped …)` 부터 `C12: firing time …` 단언까지(:295-311) 삭제.
  (b) 그 자리에:

```bash
# --- v0.55.0 §1 라운드 규약 (블록 스코프 — 4-block·teach-beat 대체) ---------------------
round_block="$(awk '/^## 라운드 규약/{f=1;print;next} /^## /{f=0} f' "$SKILL")"
round_flat="$(tr '\n' ' ' <<<"$round_block" | tr -s ' ')"
{ [[ -n "$round_block" ]] && grep -qF '### 직전 답에서 — S<k>' <<<"$round_block"; } \
  && ok "AC1: 라운드 규약 절 + «### 직전 답에서 — S<k>» 블록 형식" || no "AC1: 라운드 규약 절/블록 형식 부재"
for key in '- 함의:' '- 상충:' '- 확인한 사실:' '- 위험:'; do
  grep -qF "$key" <<<"$round_block" && ok "AC1: 네 줄 키 $key" || no "AC1: 네 줄 키 $key 부재"
done
grep -qF '## R<n>' <<<"$round_block" && ok "AC1: state 본문 헤딩 ## R<n> (depth_pairs 계약)" || no "AC1: ## R<n> 헤딩 부재"
grep -qF 'Q1 은 생략할 수 없다' <<<"$round_flat" && ok "AC1: «Q1 은 생략할 수 없다»" || no "AC1: Q1 불가생략 문장 부재"
grep -qF 'R1 은 S1 을 되비춘다' <<<"$round_flat" && ok "AC1: «R1 은 S1 을 되비춘다»" || no "AC1: R1/S1 문장 부재"
grep -qE '넷 다 «없음»[^.]{0,60}되묻기|전부 «없음»[^.]{0,60}되묻기' <<<"$round_flat" && ok "AC1: 전부 «없음» → Q1 되묻기 (G1 이행 규칙)" || no "AC1: 전부-없음 규칙 부재"
grep -qE '인자 없이[^.]{0,40}/interview[^.]{0,80}R2 부터' <<<"$round_flat" && ok "AC1: 비-seed 경로의 R1 예외" || no "AC1: 비-seed R1 규약 부재"
q_js="$(awk '/^## 라운드 규약/{f=1} f&&/^```javascript/{j=1;next} j&&/^```/{exit} j' "$SKILL")"
[[ "$(grep -c 'header:' <<<"$q_js")" -eq 2 ]] && grep -q 'AskUserQuestion(' <<<"$q_js" \
  && ok "AC2: AskUserQuestion 한 번에 질문 둘(header 2개)" || no "AC2: AskUserQuestion 질문 수가 2가 아니다"
grep -qF '(권장)' <<<"$q_js" && ok "AC2: 첫 선택지가 추천 (권장)" || no "AC2: 추천 선택지 부재"
grep -qF '고르면 무엇이 달라지는가' <<<"$round_flat" && ok "AC2: description = 고르면 무엇이 달라지는가" || no "AC2: description 규칙 부재"
grep -qE 'Q1 의 선택지는 둘|«맞다» / «모르겠다»' <<<"$round_flat" && ok "AC2: Q1 선택지 둘(맞다/모르겠다), 수정은 기타" || no "AC2: Q1 선택지 규칙 부재"
grep -qF 'provisional_on' <<<"$round_flat" && ok "AC2: Q2 의 provisional_on 규칙" || no "AC2: provisional_on 부재"
reask_block="$(awk '/^## 되묻기로 바뀌는 조건/{f=1;print;next} /^## /{f=0} f' "$SKILL")"
{ [[ -n "$reask_block" ]] && grep -q '이유' <<<"$reask_block" && grep -q '사례' <<<"$reask_block" && grep -q '실패 조건' <<<"$reask_block"; } \
  && ok "C1: 되묻기 세 축(이유·사례·실패 조건)" || no "C1: 되묻기 절/세 축 부재"
grep -qE '추측[^.]{0,20}첫 선택지' <<<"$(tr '\n' ' ' <<<"$reask_block")" && ok "C1: 인터뷰어 추측이 첫 선택지" || no "C1: 추측-첫-선택지 규칙 부재"
# 제거 (G7·AC1·AC14) — 존재 검사가 아니라 부재 검사이므로 CI_ALL 전체
for tok in 'teach-lite' 'teach-heavy' 'teach-beat' '4-block' '막힌 결정' 'general-purpose'; do
  grep -qF -- "$tok" "${CI_ALL[@]}" && no "G7: «$tok» 잔존" || ok "G7: «$tok» 제거됨"
done
[[ "$(wc -l < "$SKILL")" -lt 408 ]] && ok "G7: SKILL.md 줄 수 $(wc -l < "$SKILL") < 408 (순감)" || no "G7: SKILL.md 줄 수 $(wc -l < "$SKILL") ≥ 408"
```
  주의: `4-block`·`막힌 결정`·`general-purpose` 가 `plugins/spec-distill/references/*.md`(CI_ALL) 에 선재하면 그 토큰만 `"${CI_FILES[@]}"` 로 좁힌다 — 착수 시 `grep -n` 으로 확인하고 결과를 주석에 적는다.
  (c) `:415` 부근 주석 «:122 'teach-beat 최대 1회'» 는 주석이라 그대로 둬도 되지만 거짓 인용이 되므로 «(v0.55.0 에서 teach-beat 절 제거 — 이 스코프 근거는 R3 절 자체)» 로 고친다.

- [ ] **Step 2: RED** — 새 락 전부 ✗(제거 검사 셋은 ✗, 줄 수 ✗). `grep -c '✗'` 를 기록.

- [ ] **Step 3: SKILL.md 편집** — 다음 텍스트를 각 자리에 넣는다.

  (a) 머리말 `:13-24` 의 «4-block Korean Socratic format으로 round를 진행하되» → «매 라운드를 «직전 답에서» 블록으로 시작하고 AskUserQuestion 질문 둘로 묻되». `:59` «State body: 각 round의 4-block 출력 + …» → «State body: 각 라운드의 §1.1 기록(`## R<n>` 형식 그대로 — `depth_pairs.py` 가 읽는 계약) + coverage-mapper 출력 transcript.»

  (b) `## 4-block Korean format …` 절 전체(:81-97)를 아래로 교체:

```markdown
## 라운드 규약 — «직전 답에서» 블록 + 질문 둘

인터뷰어의 다음 행동은 사용자의 직전 답에서 나온다. 사용자에게 보이는 출력과 state 본문 기록이
**같은 형식**이다 — 측정 스크립트(`depth_pairs.py`)가 state 본문을 읽기 때문이다. 4-block 은 없다.

```markdown
## R<n>

### 직전 답에서 — S<k>
- 함의: <이 답이 사실이면 따라오는 것>
- 상충: <이전 답 S<j> / 외부 근거 / 코드 사실과 부딪히는 점 — 재개방이면 «→ <차원> 재개방: <사유>»> (없으면 «없음»)
- 확인한 사실: <답을 받고 코드·문서에서 찾아본 것> (없으면 «없음»)
- 위험: <이 답대로 가면 무너질 수 있는 것> (없으면 «없음»)

### 지금 이해
<문제의 현재 재구성 — 바뀐 부분만 한두 문장>

### 다음 결정
<무엇을 정하는지 한 줄> · 추천: <첫 선택지> · 트레이드오프: <선택지별 한 줄>

### 질문
Q1 (되비추기 확인 | 되묻기): <본문>
Q2: <본문>

### 답
→ S<m>[, S<m+1>]
```

- `## R<n>` 은 1부터 순증. 직전 라운드가 발화를 둘 만들었으면(Q1·Q2) **`### 직전 답에서 — S<k>`
  블록을 발화마다 하나씩** 둔다 — 한 블록에 두 S 를 섞으면 어느 답에서 무엇이 나왔는지가 사라진다.
  각 블록의 네 줄은 **그 S 에서** 따라 나오는 것만 적는다(다른 답·무관한 정보는 «없음»).
- **R1 은 S1 을 되비춘다** — S1 이 seed(`round: 0`)이면 seed 의 «다시 검증할 것» 문단 항목이 R1 의
  함의·상충·위험 줄을 채운다. **인자 없이 `/interview` 를 부른 경로**(S1 이 없고 첫 사용자 답이 S1 이
  되는 호환 경로)에서는 R1 이 «직전 답에서» 블록 없이 «지금 이해 + 다음 결정 + Q2» 만으로 성립하고
  규약은 R2 부터 적용된다; coverage-mapper 첫 dispatch 도 R1 답을 받은 뒤 R2 전에 일어난다.
- 네 줄 중 하나라도 «없음»이 아니어야 «형식 층에서 성립»이다. **넷 다 «없음»이면** 그 라운드는
  «S<k> 에서 아무것도 못 끌어냈다»는 기록이 되고 **그 라운드의 Q1 은 되묻기여야 한다**(아래 절).
  블록을 아예 쓰지 않는 것만이 라운드 불성립이다.
- «상충» 줄이 외부 근거(landscape·steelman·premortem 출력)를 싣는다 — 열린 질문으로 흘려보내지 않고
  «맞나?»로 사용자 처분을 받는다. 경로 (a)(코드·문서에서 찾을 수 있는 것)는 «확인한 사실» 줄로
  들어간다 — 묻기 전에 찾을 수 있는 것을 먼저 찾는다.

### 질문 — AskUserQuestion 한 번, 질문 둘

```javascript
AskUserQuestion({
  questions: [
    { header: "직전 답",  question: "<S<k> 에서 끌어낸 것을 한 절로 — 용어와 기술 사실을 풀어서>. 맞나요?",
      options: [
        {label: "맞다",     description: "이대로 <차원> 을 진행/닫는다 — <고르면 달라지는 것>"},
        {label: "모르겠다", description: "판단불가로 기록하고 Open Question 후보로 둔다"}],
      multiSelect: false },
    { header: "<결정 이름>", question: "<무엇을 정하는지 한 줄> · <용어 풀이> · <관련 기술 사실> · 추천은 첫 선택지",
      options: [
        {label: "<추천> (권장)", description: "고르면 <결과>"},
        {label: "<대안 1>",      description: "고르면 <결과>"},
        {label: "<대안 2>",      description: "고르면 <결과>"}],
      multiSelect: false }
  ]
})
```

- **Q1 은 생략할 수 없다.** Q1 이 항상 먼저고 Q2 는 새 결정 하나다.
- **Q1 의 선택지는 둘뿐이다**(«맞다» / «모르겠다»). 틀린 부분은 사용자가 «기타» 자유 입력에 적는다 —
  선택지를 고르면서 동시에 자유 입력을 남기는 동작은 도구에 없다. «기타» 텍스트는 `verbatim` S 로
  기록되고 다음 라운드 Q1 이 그것을 다시 되비춘다(같은 주제 최대 2회 — 3회째는 §3 Open Questions 로
  박제하고 넘어간다).
- **Q2 는 Q1 의 확인과 독립이어야 한다.** Q2 가 Q1 이 되비춘 해석에 기대면 그 라운드는 Q1 만 낸다.
  독립인데도 Q1 이 «모르겠다»·«기타(수정)» 이면 Q2 의 답은 state 에 `provisional_on: S<k>` 를 달고,
  그 표시가 해소(다음 라운드 되비추기 «맞다»)되기 전에는 어느 차원의 닫힘 근거로도 쓰지 않는다.
- 각 선택지의 `description` 은 «고르면 무엇이 달라지는가»를 담고, question 본문은 무엇을 정하는지·
  용어·기술 사실을 푼다. 기계 검사는 없다 — 사람 e2e 가 본다.
- 두 답은 `user_statements` 에 `S<m>`·`S<m+1>` 로 append 된다(`source: chosen`, «기타» 입력은
  `verbatim`). 번호 공식은 «사용자 발화 기록» 절 그대로.

## 되묻기로 바뀌는 조건

되비추기가 **성립하지 않는 답**에서 Q1 은 되묻기가 된다 — 보류(«모르겠다/둘 다/아무거나»), 한 단어 답,
추천안 즉시 동의(이유 없이 «추천»), 근거 없는 단정(휴리스틱, 기계화 안 함). Q1 본문은 **이유·사례·
실패 조건** 중 하나를 묻고 인터뷰어의 추측을 첫 선택지로 둔다:

```
Q1 (되묻기): «<S<k>>»라고 답하셨는데, 왜 그렇게 봤는지가 <차원> 을 닫는 데 필요합니다.
  - «내 추측: <이유 A>» (권장)  — 고르면 <결과>
  - «<이유 B>»                 — 고르면 <결과>
  - «잘 모르겠다»              — 판단불가로 기록, OQ 후보
```

세 축이 도구상자의 전부다. 목록을 더 두지 않는다.
```

  (c) `## C43 4-path routing` 표에서 `(c) **ambiguity**` 행을 지우고 «매 round의 4-block에서 어떤 path로 routing했는지» → «매 라운드의 «확인한 사실»·«질문» 에 어떤 path 인지». (d) 행의 «C51 5-type framework 사용 — … 라벨링 후» → «essence/root cause 류 — 라벨 강제 없음».
  (d) `## teach-beat` 절 삭제.
  (e) `## 사용자 발화 기록` 표의 `sub-agent ambiguity 답안 | c` 행 삭제. `## C44` 의 «(c) sub-agent adversarial: streak +1» 줄 삭제.

- [ ] **Step 4: GREEN + 줄 수**

```bash
bash plugins/spec-distill/tests/test_conducting_interview_stage.sh | tail -1
wc -l plugins/spec-distill/skills/conducting-interview/SKILL.md
```
줄 수가 408 이상이면 «지금 이해/다음 결정» 설명 문단이 아니라 **`## 5 통과 의례` 표 아래 R2·R3 의 중복 서술**(kill switch 산문이 R2 와 coverage-mapper 절에 두 번)을 한 곳으로 모아 줄인다. Task 11 이 정체 트리거 절(~35줄)을 더 지우므로 최종 판정은 Task 11 뒤다 — 이 시점에는 «Task 11 뒤 < 408» 을 목표로 하고 이 task 의 줄 수 단언은 Task 11 커밋 전까지 RED 를 허용한다(그 사실을 커밋 메시지에 적는다).

- [ ] **Step 5: 커밋** — `feat(spec-distill): conducting-interview §1 라운드 규약 — 직전 답에서 블록·질문 둘·되묻기, 4-block/teach-beat/경로(c) 제거 (AC1·AC2)`

---

### Task 11: SKILL.md §2 — 닫힘 규칙 · 재개방 · coverage-mapper dispatch 교체 · state 스키마 · coverage-mapper 에이전트 · stale-term (AC5·C4·AC14)

**Files:**
- Modify: `plugins/spec-distill/skills/conducting-interview/SKILL.md` (state 스키마 `:32-57`, `## coverage-mapper dispatch (C11)` `:172-229`, `## In-flight state migration` `:367-402`, `## seed 를 입력으로 받았을 때` `:319-340`, 새 절 `## 닫힘 · 재개방`) · `plugins/spec-distill/agents/coverage-mapper.md` · `plugins/spec-distill/tests/test_stale_terms.sh` · `plugins/spec-distill/tests/test_conducting_interview_stage.sh`
- Test: 위 두 락 + `bash plugins/spec-distill/tests/test_coverage_mapper_frontmatter.sh`

**Interfaces:**
- Produces: state 키 `coverage.floor.<dim>.{status,evidence,reopened,reopen_log}` · `orchestration.{focused_dimension,blind_spot_dispatched,coverage_mapper_dispatches}`; 제거 어휘 셋(`no_progress_streak`·`stall_episode`·`coverage_mapper_dispatched_episode`) + teach 셋이 `test_stale_terms.sh` 에 등재된다.

- [ ] **Step 1: 락 교체 (RED)** — `test_conducting_interview_stage.sh`:
  (a) `:177` `has 'no_progress_streak' …`, `:183-184` 두 줄 → 부재 검사로 반전:
  ```bash
  for tok in no_progress_streak stall_episode coverage_mapper_dispatched_episode; do
    grep -q "$tok" "${CI_ALL[@]}" && no "AC5/C4: $tok 잔존 (정체 트리거 제거)" || ok "AC5/C4: $tok 제거됨"
  done
  has 'coverage_mapper_dispatches' "C4: orchestration.coverage_mapper_dispatches in schema"
  has 'reopen_log' "AC5: reopen_log in schema"
  has 'reopened' "AC5: reopened in schema"
  ```
  (b) `:203` migration 리터럴 → `` '`orchestration`: `{focused_dimension: null, blind_spot_dispatched: false, coverage_mapper_dispatches: 0}`' `` 로 교체하고 메시지에 «(v0.55.0)».
  (c) `:318-320` («연속 3 probe|no_progress») 삭제, `:356-366` (judgment_para·code_spans·유한성 근거) 삭제. 대신:
  ```bash
  covmap_flat="$(tr '\n' ' ' <<<"$covmap_block" | tr -s ' ')"
  grep -qE 'R1[^.]{0,30}첫 질문 전[^.]{0,20}필수 1회' <<<"$covmap_flat" && ok "C4: R1 첫 질문 전 필수 1회" || no "C4: R1 필수 dispatch 규칙 부재"
  grep -qE '재개방[^.]{0,20}최대 1회' <<<"$covmap_flat" && ok "C4: 재개방 시 최대 1회" || no "C4: 재개방 dispatch 규칙 부재"
  grep -qE '상한[^.]{0,6}2' <<<"$covmap_flat" && grep -qF 'coverage_mapper_dispatches' <<<"$covmap_block" && ok "C4: 상한 2 + 카운터" || no "C4: 상한 2/카운터 부재"
  grep -qE 'coverage-mapper 0 \(unavailable' <<<"$covmap_block" && ok "C4: unavailable sentinel 규약" || no "C4: unavailable sentinel 부재"
  close_block="$(awk '/^## 닫힘 · 재개방/{f=1;print;next} /^## /{f=0} f' "$SKILL")"
  close_flat="$(tr '\n' ' ' <<<"$close_block" | tr -s ' ')"
  { [[ -n "$close_block" ]] && grep -qE '사용자가 답한 S[^.]{0,10}뒤에만 닫' <<<"$close_flat"; } && ok "AC1/G2: «차원은 사용자가 답한 S 뒤에만 닫는다»" || no "AC1/G2: 닫힘 규칙 부재"
  grep -qE '횟수[^.]{0,30}닫힘 근거가 아니' <<<"$close_flat" && ok "G2: 이벤트 횟수는 닫힘 근거 아님" || no "G2: 횟수-비근거 문장 부재"
  grep -qF 'closed → open' <<<"$close_block" && ok "AC5: closed → open 전이" || no "AC5: closed → open 부재"
  grep -qF '→ <차원> 재개방' <<<"$close_block" && ok "AC5: 상충 줄에 → 재개방" || no "AC5: 상충-재개방 표기 부재"
  grep -qE '다시 닫힐 때[^.]{0,20}새 S|새 S[^.]{0,20}인용' <<<"$close_flat" && ok "AC5: 재개방 후 닫힘은 새 S" || no "AC5: 새-S 규칙 부재"
  grep -qE '상한[^.]{0,10}없|무상한' <<<"$close_flat" && ok "C3: 재개방 무상한" || no "C3: 무상한 문장 부재"
  for dim in root_problem landscape skepticism blind_spot open_questions; do
    grep -q "$dim" <<<"$close_block" && ok "§2.1: $dim 의 닫힘 발화 규약" || no "§2.1: $dim 닫힘 발화 규약 부재"
  done
  ```
  (d) `## seed 를 입력으로 받았을 때` 스코프(`seed_flat`)에 한 줄: `grep -qF '다시 검증할 것' <<<"$seed_flat" && ok "AC11: seed 의 «다시 검증할 것» 문단을 R1/coverage-mapper 입력으로" || no "AC11: seed 재검증 문단 소비 부재"`.
  (e) `test_stale_terms.sh` — V7a 블록 뒤에 같은 3-way 모양으로:
  ```bash
  # V10 (v0.55.0): 깊이 재설계가 제거한 어휘 — production 잔존 0 (SKILL·references·agents·templates·README)
  scan -InE 'no_progress_streak|stall_episode|coverage_mapper_dispatched_episode|teach-lite|teach-heavy|teach-beat' "${prod_files[@]}"
  if [[ $SCAN_RC -ge 2 ]]; then no "V10: grep 자체 실패(exit=$SCAN_RC):"; printf '%s\n' "$SCAN_OUT"
  elif [[ $SCAN_RC -eq 0 ]]; then no "V10: v0.55.0 제거 어휘가 production 에 잔존:"; printf '%s\n' "$SCAN_OUT"
  else ok "V10: v0.55.0 제거 어휘 production 잔존 0"; fi
  ```

- [ ] **Step 2: RED** — 두 스위트 실행, 새 단언 ✗ 확인.

- [ ] **Step 3: SKILL.md 편집**

  (a) state 스키마(:32-57) 의 `coverage.floor` 다섯 줄을 `{status: open, evidence: "", reopened: 0, reopen_log: []}` 로, `derived:` 주석에 `reopened, reopen_log` 추가, `orchestration:` 을
  ```yaml
  orchestration:                       # orchestrator 소유, agent read-only
    focused_dimension: null            # 현재 probe 대상 차원 이름 또는 null
    blind_spot_dispatched: false       # C8 인터뷰당 1회 보장
    coverage_mapper_dispatches: 0      # 상한 2 — R1 첫 질문 전 1 + 재개방 시 ≤1
  ```
  (b) `## coverage-mapper dispatch (C11)` 절을 아래로 교체(웹 kill switch 블록·`Agent(` dispatch·처분 줄·advisory 문단은 **그대로 유지**):
  ```markdown
  ## coverage-mapper dispatch (상한 2)

  `coverage-mapper` 는 고정 floor 위 **주제-도출 차원**을 *제안*하는 advisory 에이전트다(admit 은
  orchestrator, G2). dispatch 는 둘뿐이다:

  1. **R1 첫 질문 전 필수 1회.** 입력: seed 전문(S1)과 그 «다시 검증할 것» 문단, 원장 초기 상태.
     출력의 derived 차원을 admit 한 뒤에야 R1 질문이 나간다. 인자 없이 부른 경로에서는 R1 답을
     받은 뒤 R2 전에.
  2. **재개방 시 최대 1회.** 재개방이 새 파생 차원을 함의할 수 있어서다. 두 번째 재개방부터는 없다.

  상한 2, 카운터 `orchestration.coverage_mapper_dispatches`. 종료 시 audit §2 에 `coverage-mapper <k>`
  를 쓰고 게이트가 k≥1 을 검사한다. dispatch 가 불가능한 환경(Agent 도구 부재)은
  `coverage-mapper 0 (unavailable: <이유>)` 로 적는다 — 게이트는 advisory 로 통과시키고 Step B 가
  사람에게 보인다(침묵과 0 은 다르다).
  ```
  (c) 새 절 `## 닫힘 · 재개방` 을 `## blind-spot-prober dispatch` 앞에:
  ```markdown
  ## 닫힘 · 재개방

  **차원은 «그 차원의 되비추기에 사용자가 답한 S» 뒤에만 닫는다.** sweep·steelman·prober 의 **횟수**는
  닫힘 근거가 아니다 — 그 출력은 «상충/위험» 줄로 돌아와 사용자 처분 S 를 받은 뒤 닫힌다. 원장 행의
  evidence 는 그 S 를 인용하고, `check_brief.py` 가 앵커 실재를 검사한다(«어느 S 가 닫힘을
  정당화하는가»는 보지 않는다 — 그 한계는 spec OQ6).
  다섯 floor 의 닫힘 발화: root_problem = 재구성 동의 S · landscape = 외부 근거 되비추기 처분 S ·
  skepticism = steelman 판정 S · blind_spot = 숨은 가정·실패 양식 처분 S · open_questions = OQ 목록
  확인 S. `provisional_on` 이 해소되지 않은 S 는 닫힘 근거가 아니다.

  **재개방 — `closed → open` 을 허용한다.** 조건: 새 답·외부 근거·코드 사실이 그 차원의 닫힘 근거 S 와
  충돌할 때(판단은 orchestrator). 기록: 그 차원의 `reopened` +1, `reopen_log` 에
  `{round, reason, conflicts_with: S<N>}` append, 그 라운드의 «상충» 줄에 «→ <차원> 재개방: <사유>».
  상한 없음 — 라운드는 사용자 답으로만 돌아 사용자가 시계다. 재개방된 차원이 다시 닫힐 때는 **새 S** 를
  인용한다(게이트는 최신 닫힘의 evidence 를 본다).
  ```
  (d) migration 절: `orchestration` 열거를 `{focused_dimension: null, blind_spot_dispatched: false, coverage_mapper_dispatches: 0}` 로, floor seed 를 `{status: open, evidence: "", reopened: 0, reopen_log: []}` 로, 근거 문단의 «coverage-mapper 재dispatch 바운드 … 에피소드 필드» 를 «coverage-mapper 상한 카운터(`coverage_mapper_dispatches`)와 재개방 원장(`reopen_log`)이 디스크에서 읽힌다» 로, advisory 문자열을 `[spec-distill v0.55.0] state schema migration: reopen ledger + coverage_mapper_dispatches added (stall trigger retired).`
  (e) seed 절: 첫 bullet 뒤에 «**seed 의 마지막 문단 «다시 검증할 것 —»** 이 R1 의 «직전 답에서 — S1» 블록(함의·상충·위험)과 coverage-mapper 첫 dispatch 의 입력이다. 문단이 없으면 seed 본문 전체를 그 입력으로 쓰되 무표시 문장은 전부 미확인이다.»

- [ ] **Step 4: coverage-mapper.md** — `## Input` 을 «seed 전문(S1)과 «다시 검증할 것» 문단 / 원장 상태(floor + derived) / 재개방이면 `reopen_log` 마지막 항목» 으로, 동작 규칙 4 를 «**bounded dispatch**: R1 첫 질문 전 1회 + 재개방 시 ≤1회, 상한 2(conducting-interview 가 제어)» 로, description 의 «dispatch is bounded by C11» → «dispatch is bounded to two per interview», example 의 «3 consecutive probes stayed…» → «The interviewer is about to ask the first round question from a seed.». `test_coverage_mapper_frontmatter.sh` 의 `derived_dimensions`·`neglect_flag` 키는 유지.

- [ ] **Step 5: README 의 4-block 문장 4곳(`:7`·`:22`·`:36`·`:141`)** → «직전 답에서 블록 + 질문 둘» 어휘로(Task 14 의 README 갱신과 같은 커밋이어도 되지만 stale 락이 README 를 보므로 여기서 한다). `commands/interview.md:46` 도 같이.

- [ ] **Step 6: GREEN + 줄 수**
```bash
bash plugins/spec-distill/tests/test_conducting_interview_stage.sh | tail -1
bash plugins/spec-distill/tests/test_stale_terms.sh | tail -1
bash plugins/spec-distill/tests/test_coverage_mapper_frontmatter.sh | tail -1
bash plugins/spec-distill/tests/test_conducting_interview_internal.sh | tail -1
wc -l plugins/spec-distill/skills/conducting-interview/SKILL.md
```
Expected: 전부 `Fail: 0`, 줄 수 < 408.

- [ ] **Step 7: mutation** — 커밋 후 `## 닫힘 · 재개방` 절 통째 삭제 → 락 ≥8 RED; `closed → open` 을 `closed → closed` 로 → 1 RED; 복원.

- [ ] **Step 8: 커밋** — `feat(spec-distill): 닫힘=S앵커·재개방·coverage-mapper 상한 2·state 스키마 (AC5·C4·AC14)`

### Task 12: Phase 0 §4.1 — seed «(사용자 확인)»·«다시 검증할 것 —» 규약 (AC11)

**Files:**
- Modify: `plugins/spec-distill/skills/framing-requests/SKILL.md` (`## 무엇을 남기고 무엇을 깎는가` 절 끝에 소절 추가) · `plugins/spec-distill/references/compression.md` (새 절) · `plugins/spec-distill/templates/interview-seed-template.md` (예시 마지막 문단 + 표 행)
- Test: `plugins/spec-distill/tests/test_request_framing_command.sh` (`# guards:` 확장 + 블록 스코프 락) · `bash plugins/spec-distill/tests/test_check_seed.sh` · `bash plugins/spec-distill/tests/test_seed_one_sentence.sh` (무변경 확인) · `bash plugins/spec-distill/tests/test_compression_adopters.sh`

**Interfaces:**
- Produces: seed 산문 규약 셋 — 확정 표시 «(사용자 확인)» 하나 · 마지막 문단 «다시 검증할 것 —» · 그 밖은 미확인. Task 11 (e) 가 이미 소비자 쪽 문장을 넣었다. `check_seed.py` diff 0.

- [ ] **Step 1: 실패하는 락** — `test_request_framing_command.sh`: 2행 `# guards:` 를 `plugins/spec-distill/commands/request-framing.md plugins/spec-distill/skills/framing-requests/SKILL.md plugins/spec-distill/references/compression.md plugins/spec-distill/templates/interview-seed-template.md` 로, `--emit-scanned` 분기에 세 경로를 더 echo. `finish` 앞에:

```bash
# --- v0.55.0 AC11: seed 산문 규약 (블록 스코프) -------------------------------------------
SK="$ROOT/plugins/spec-distill/skills/framing-requests/SKILL.md"
CMP="$ROOT/plugins/spec-distill/references/compression.md"
TPL="$ROOT/plugins/spec-distill/templates/interview-seed-template.md"
conv_block="$(awk '/^### 확정 표시와 «다시 검증할 것»/{f=1;print;next} /^##/{f=0} f' "$SK")"
conv_flat="$(tr '\n' ' ' <<<"$conv_block" | tr -s ' ')"
{ [[ -n "$conv_block" ]] && grep -qF '(사용자 확인)' <<<"$conv_block"; } && ok "AC11: SKILL 규약 절 + «(사용자 확인)» 표시" || no "AC11: 규약 절/확정 표시 부재"
grep -qF '다시 검증할 것 —' <<<"$conv_block" && ok "AC11: 마지막 문단 «다시 검증할 것 —»" || no "AC11: 재검증 문단 규약 부재"
grep -qE '그 밖[^.]{0,30}미확인|나머지[^.]{0,30}미확인' <<<"$conv_flat" && ok "AC11: 무표시 = 미확인" || no "AC11: 무표시=미확인 문장 부재"
grep -qE '태그[^.]{0,30}(쓰지 않|없)' <<<"$conv_flat" && ok "AC11: 태그 문법 없음 (check_seed 정합)" || no "AC11: 태그 금지 문장 부재"
cmp_block="$(awk '/^## 확정 표시와 마지막 문단/{f=1;print;next} /^## /{f=0} f' "$CMP")"
{ [[ -n "$cmp_block" ]] && grep -qF '(사용자 확인)' <<<"$cmp_block" && grep -qF '다시 검증할 것 —' <<<"$cmp_block"; } \
  && ok "AC11: compression.md 규약 절" || no "AC11: compression.md 규약 절 부재"
tpl_ex="$(awk '/^```markdown/{f=1;next} f&&/^```/{exit} f' "$TPL")"
grep -qF '(사용자 확인)' <<<"$tpl_ex" && ok "AC11: seed 템플릿 예시에 확정 표시" || no "AC11: 템플릿 예시 확정 표시 부재"
[[ "$(printf '%s\n' "$tpl_ex" | grep -v '^\s*$' | tail -1 | head -c 400)" == *"다시 검증할 것"* || "$(awk -v RS='' 'END{print}' <<<"$tpl_ex")" == "다시 검증할 것 —"* ]] \
  && ok "AC11: 템플릿 예시의 마지막 문단이 «다시 검증할 것 —»로 시작" || no "AC11: 템플릿 마지막 문단 규약 위반"
# check_seed.py 는 손대지 않는다 — Task 착수 커밋(main merge) 대비 diff 0
[[ -z "$(git -C "$ROOT" diff --name-only main -- plugins/spec-distill/scripts/check_seed.py)" ]] \
  && ok "AC11: check_seed.py 무변경 (diff 0 vs main)" || no "AC11: check_seed.py 가 변경됐다"
```

- [ ] **Step 2: RED** — `bash plugins/spec-distill/tests/test_request_framing_command.sh | grep AC11` 전부 ✗(마지막 diff 단언만 ✓).

- [ ] **Step 3: framing-requests SKILL.md** — `## 무엇을 남기고 무엇을 깎는가` 절 끝(«…그보다 오래 남아야 합니다.» 뒤)에:

```markdown
### 확정 표시와 «다시 검증할 것»

seed 는 태그를 쓰지 않습니다(`check_seed.py` 가 본문 태그를 금지하고, 슬롯 존재 검사 추가는
`tests/test_seed_one_sentence.sh` 가 막습니다). 대신 산문 규약 셋으로 Phase 1 이 무엇을 다시 물을지
가릅니다:

- **확정 표시는 «(사용자 확인)» 하나.** 이 표시가 붙은 문장만 Phase 1 이 다시 묻지 않습니다. brief §2 로
  옮겨질 때 `source: verbatim`, ✎ 에 «Phase 0 확인».
- **마지막 문단은 «다시 검증할 것 —»로 시작**해, Phase 0 이 추론·외부·열린 것으로 아는 항목을 산문으로
  나열합니다. 예: «다시 검증할 것 — 종료 술어가 이벤트 완료라는 것은 Phase 0 이 구현을 읽고 본 원인
  후보이지 확정이 아니다. …». Phase 1 은 이 문단을 R1 의 «직전 답에서 — S1» 블록과 coverage-mapper 첫
  dispatch 의 입력으로 씁니다.
- **그 밖의 모든 문장은 미확인**입니다. 필요하면 Phase 1 이 되비추기로 검증합니다.

문단이 없어도 깨지지 않습니다 — 지금과 같은 태그 없는 산문으로 떨어질 뿐이고, 냉독(seed-readback)이
그 부재를 사람에게 보입니다.
```

- [ ] **Step 4: compression.md** — `## 이 규약은 앞 단계의 결정을 봉인하지 않는다` 앞에 새 절:

```markdown
## 확정 표시와 마지막 문단

seed 에서 **확정 표시는 «(사용자 확인)» 하나**다 — 사용자가 실제로 확인한 문장에만 붙는다. **마지막
문단은 «다시 검증할 것 —»로 시작**해 추론·외부·열린 항목을 산문으로 나열한다. 그 밖의 문장은 전부
미확인이다. 태그가 아니라 산문인 이유는 `check_seed.py` 의 태그 금지와 같다 — 라벨은 권위로 읽혀
하류를 끈다.
```

- [ ] **Step 5: seed 템플릿** — 예시 펜스 안: «세션 스토어를 바꾸는 개편은 이번에 하지 않는다 — 다음 분기에 따로 할 예정이라 지금 손대면 두 번 일이 된다. (사용자 확인)» 로 표시를 붙이고, 펜스 끝 문단 뒤에 빈 줄 + «다시 검증할 것 — 클라이언트 경합은 내 의심이지 확인된 것이 아니다. 서버 로그가 없었다는 것은 그때 한 번 본 것이라 다시 봐야 한다.» 추가. 표에 행 `| 다시 검증할 것 — 경합 의심·로그 부재 | 방향의 근거이되 미확인 — Phase 1 이 되비춘다 | 아니오 |`. `## 쓰지 말 것` 에 «- **«(사용자 확인)» 을 추론에** — 사용자가 확인하지 않은 문장에 붙이면 Phase 1 이 그것을 다시 묻지 않는다.»

- [ ] **Step 6: GREEN** — 위 락 + `test_check_seed.sh`·`test_seed_one_sentence.sh`·`test_compression_adopters.sh`·`test_seed_agents.sh`·`test_seed_gate_wiring.sh` 전부 `Fail: 0`(선재 실패는 baseline 대조). 템플릿 예시가 `check_seed.py gate` 를 여전히 통과하는지: 예시 펜스 본문을 임시 파일로 뽑아 `python3 plugins/spec-distill/scripts/check_seed.py gate <tmp-seed> <tmp-audit>` 로 확인(audit 은 `## 1. 원문` 절 하나짜리 임시 파일).

- [ ] **Step 7: 커밋** — `feat(spec-distill): seed 산문 규약 — (사용자 확인)·다시 검증할 것 문단 (AC11)`

---

### Task 13: Phase 0 §4.2 — 워크트리 질문 · 5단계 · kill switch · handoff 직전 커밋 · 게이트 경로 (AC12·AC13) — **별 묶음**

> Task 1 의 `$SCR/v6/results.md` 없이는 시작하지 않는다. (e) 가 «refused» 이거나 `tool_available=no` 면 Step 8 의 분기표대로 명령을 바꾼다. 이 task 가 막혀도 Task 14 는 §4.2 항목을 CHANGELOG 에 «미출하 — 사유» 로 적고 진행한다(§1~§3 독립 출하).

**Files:**
- Modify: `plugins/spec-distill/skills/framing-requests/SKILL.md` (`## 확산` 앞에 `## 워크트리 — 진입 직후` 절, `## 확정 — proceed 게이트` 의 ①/② 커밋 절차와 «다음 세션 첫 턴» 경로, `## kill switch` 한 줄)
- Test: `plugins/spec-distill/tests/test_request_framing_command.sh`

**Interfaces:**
- Produces: kill switch `DEVBREW_SPEC_DISTILL_DISABLE_WORKTREE=1`; 커밋 메시지 리터럴 `docs(interview): <topic> interview seed + audit`; audit §5 문구 «워크트리 없음 — <이유>».

- [ ] **Step 1: 실패하는 락** — 같은 테스트 파일 `finish` 앞:

```bash
# --- v0.55.0 AC12: 워크트리 (블록 스코프) -------------------------------------------------
wt_block="$(awk '/^## 워크트리 — 진입 직후/{f=1;print;next} /^## /{f=0} f' "$SK")"
wt_flat="$(tr '\n' ' ' <<<"$wt_block" | tr -s ' ')"
{ [[ -n "$wt_block" ]] && grep -qF 'AskUserQuestion(' <<<"$wt_block"; } && ok "AC12: 워크트리 절 + 단독 AskUserQuestion" || no "AC12: 워크트리 절/질문 부재"
grep -qE 'audit[^.]{0,20}첫 write[^.]{0,10}전|첫 write 전' <<<"$wt_flat" && ok "AC12: audit 첫 write 전에 묻는다" || no "AC12: 시점(첫 write 전) 부재"
grep -qF 'feature/<kebab-topic>' <<<"$wt_block" && ok "AC12: feature/<kebab-topic> 이름" || no "AC12: 브랜치 이름 규약 부재"
[[ "$(grep -cE '^[1-5]\. ' <<<"$wt_block")" -eq 5 ]] && ok "AC12: 5단계 절차" || no "AC12: 5단계가 아니다 ($(grep -cE '^[1-5]\. ' <<<"$wt_block"))"
grep -qF 'DEVBREW_SPEC_DISTILL_DISABLE_WORKTREE' <<<"$wt_block" && ok "AC12: kill switch 를 절이 본다" || no "AC12: 절에 kill switch 부재"
grep -qF '워크트리 없음 —' <<<"$wt_block" && ok "AC12: 거절/부재 시 audit §5 문구" || no "AC12: 강등 문구 부재"
grep -qE '(거절|부재|스위치)[^.]{0,60}seed[^.]{0,20}막지 않' <<<"$wt_flat" && ok "AC12: 어느 경우도 seed 작성을 막지 않는다" || no "AC12: 비차단 선언 부재"
ks_block="$(awk '/^## kill switch/{f=1;print;next} /^## /{f=0} f' "$SK")"
grep -qF 'DEVBREW_SPEC_DISTILL_DISABLE_WORKTREE=1' <<<"$ks_block" && ok "AC12: kill switch 목록 등재" || no "AC12: kill switch 목록에 없다"
gate_block="$(awk '/^## 확정 — proceed 게이트/{f=1;print;next} /^## /{f=0} f' "$SK")"
gate_flat="$(tr '\n' ' ' <<<"$gate_block" | tr -s ' ')"
grep -qF 'docs(interview): <topic> interview seed + audit' <<<"$gate_block" && ok "AC12: 커밋 메시지 리터럴 (C10 과 동일)" || no "AC12: 커밋 메시지 리터럴 부재/불일치"
grep -qE '(①|②)[^.]{0,80}handoff 직전[^.]{0,40}커밋' <<<"$gate_flat" && ok "AC12: ①/② 에서 handoff 직전 커밋" || no "AC12: 커밋 시점 규칙 부재"
grep -qE '(③|④)[^.]{0,40}커밋하지 않' <<<"$gate_flat" && ok "AC12: ③/④ 는 커밋 없음" || no "AC12: ③/④ 비커밋 규칙 부재"
grep -qE '워크트리 절대경로|절대경로' <<<"$gate_flat" && ok "AC12: 게이트 텍스트에 워크트리 경로" || no "AC12: 게이트 경로 안내 부재"
grep -qF 'git commit -q -F' <<<"$gate_block" && ok "AC12: 커밋은 -F 파일 한 줄 명령" || no "AC12: 커밋 명령 모양 부재"
```

- [ ] **Step 2: RED** 확인.

- [ ] **Step 3: SKILL.md — `## 확산` 바로 앞에 절 삽입** (아래는 Task 1 결과가 «tool_available=yes · (e) 둘 다 ok» 인 기본형. Step 8 분기표는 이 절 안의 2단계·강등 문단만 바꾼다):

```markdown
## 워크트리 — 진입 직후

이 skill 에 들어온 **첫 행동**이다 — `## 확산` 1번(audit 첫 write) **전**에 묻는다. 그래야 audit 이
처음부터 워크트리 안에 쓰이고 «main 에 쓴 audit 을 옮기는» 절차가 필요 없다. 이름 파일
(`interview-basename`)은 세션 디렉토리(main repo 의 state root)에 있어 cwd 이동과 무관하다.

`DEVBREW_SPEC_DISTILL_DISABLE_WORKTREE=1` 이거나 `EnterWorktree` 도구가 없으면 **묻지 않고** 현재
디렉토리에서 진행한다. 그 밖에는 단독 `AskUserQuestion` 하나:

```javascript
AskUserQuestion({ questions: [{
  header: "워크트리",
  question: "`feature/<kebab-topic>` 워크트리를 만들고 거기서 시작할까요? 이 브랜치 하나에서 인터뷰·설계·계획·구현까지 갑니다. 거절하면 현재 디렉토리에서 진행합니다.",
  options: [
    {label: "만들고 시작 (권장)", description: "고르면 이 세션의 cwd 가 그 워크트리로 옮겨지고 audit·seed 가 그 안에 쓰인다"},
    {label: "현재 디렉토리에서", description: "고르면 워크트리 없이 지금 위치에 쓴다 — 자료는 현재 브랜치에 남는다"}],
  multiSelect: false }] })
```

승낙 시 절차 — 순서 고정, **각 단계는 단순 명령 하나**(격리 세션의 git 가드가 복합 명령을 막는다):

1. `EnterWorktree(name=<kebab-topic>)` — native 도구 우선(superpowers `using-git-worktrees` 와 같은 원칙).
2. `git branch -m feature/<kebab-topic>` — project-init 검증기가 제안하는 바로 그 형태.
3. audit·seed 를 그 워크트리 안의 `docs/superpowers/interview/` 에 쓴다(`## 상태` 의 경로 그대로).
4. proceed 게이트에서 ①/② 를 고르면 **handoff 직전** 커밋 1회(`## 확정 — proceed 게이트` 의 절차).
5. 게이트 텍스트의 «다음 세션 첫 턴» 안내에 워크트리 **절대경로**를 함께 낸다 — 사람이 그 디렉토리에서
   새 세션을 열어 `/interview <seed 전문>` 을 친다.

거절·도구 부재·스위치 → 현재 디렉토리에서 진행하고 audit §5 에 «워크트리 없음 — <거절|EnterWorktree 부재|
DEVBREW_SPEC_DISTILL_DISABLE_WORKTREE>» 한 줄. 어느 경우도 seed 작성을 막지 않는다.

이 절은 native 도구의 동작을 단정하지 않는다 — 실측 결과는 CHANGELOG `[0.55.0]` 에 있다.
```

- [ ] **Step 4: 게이트 절** — «게이트의 네 옵션은 이 모양을 그대로 씁니다» 표 뒤에:

```markdown
**handoff 직전 커밋(①/② 에서만).** 워크트리 안이면 ①/② 를 고른 직후, `/compact` 노출(①) 또는
`/interview` 진입(②) **직전**에 한 번 커밋한다 — ③(수정)·④(멈춤)에서는 커밋하지 않는다(수정마다
커밋이 늘고 멈춤에도 커밋이 남는다). 단순 명령 셋, 메시지는 파일로:

```bash
printf 'docs(interview): <topic> interview seed + audit\n' > "$SEED_DIR/commit-msg.txt"
git add "$AUDIT" "$SEED"
git commit -q -F "$SEED_DIR/commit-msg.txt"
```

워크트리가 아니면(거절·부재·스위치) 커밋하지 않고 «미커밋 — 현재 디렉토리» 를 게이트 텍스트에 적는다.
①/② 의 «다음 세션 첫 턴» 안내에는 **워크트리 절대경로**(`pwd`)를 함께 낸다.
```
①/② 옵션 행의 문구에 «(커밋 후)» 를 덧붙인다.

- [ ] **Step 5: kill switch 목록** — `- `DEVBREW_SPEC_DISTILL_DISABLE_WORKTREE=1` — 워크트리 질문·생성을 건너뛰고 현재 디렉토리에서 진행(audit §5 에 사유).`

- [ ] **Step 6: Task 1 분기 적용** — `$SCR/v6/results.md` 의 마지막 줄대로: (e) rename 거부면 2단계를 «`EnterWorktree(name=feature/<kebab-topic>)` — 이름에 접두를 넣어 rename 을 생략한다((a) 가 이름을 그대로 쓸 때). 접두를 붙이면 사용자에게 `git branch -m` 을 수동 안내» 로; (b) 가 «c2-local-only 미포함(기본)» 이면 절 끝 문단에 «기본 base 는 origin 의 기본 브랜치라 **로컬에만 있는 main 커밋은 들어오지 않는다** — 필요하면 사용자 설정 `worktree.baseRef=head`» 한 줄; (c) 훅 미발화면 «워크트리 안에서 플러그인 훅이 해석되지 않는다는 실측 — proceed 게이트의 구조 검사는 스크립트 직접 호출이라 영향 없음» 한 줄.

- [ ] **Step 7: GREEN** — `bash plugins/spec-distill/tests/test_request_framing_command.sh | tail -1` → `Fail: 0`. `bash shared/tests/test_dispatch_disposition.sh | tail -1` (이 절에는 `Agent(` 가 없어 변화 없어야 한다). `bash plugins/spec-distill/tests/test_proceed_gate_adopters.sh | tail -1` (게이트 절 편집이 공통 계약 앵커를 깨지 않았는지).

- [ ] **Step 8: mutation** — 커밋 후 워크트리 절 통째 삭제 → RED ≥7; 커밋 메시지 리터럴을 `docs(interview): <topic> seed + audit` 로 → 1 RED; 복원.

- [ ] **Step 9: 커밋** — `feat(spec-distill): framing-requests 워크트리 질문·5단계·kill switch·handoff 직전 커밋 (AC12·AC13)`

---

### Task 14: 버전 · CHANGELOG · README · 실측 반영 · 전수 검증 (AC13·AC14·AC15, V1~V5)

**Files:**
- Modify: `plugins/spec-distill/.claude-plugin/plugin.json` · `plugins/spec-distill/CHANGELOG.md` · `plugins/spec-distill/README.md` · 이 plan 파일(«부록 A»·«부록 B»)
- Test: `bash plugins/spec-distill/tests/test_readme_sync.sh` · `bash shared/tests/test_changelog_integrity.sh` · `$SCR/run_all_locks.sh`

- [ ] **Step 1: plugin.json** — `"version": "0.54.0"` → `"0.55.0"`.

- [ ] **Step 2: CHANGELOG** — 맨 위에 새 절(기존 `[0.54.0]` 절 위에 **삽입**, 덮어쓰기 금지 — `test_changelog_integrity.sh` 가 건너뛴 버전을 잡는다):

```markdown
## [0.55.0] — 2026-09-06

### Added

- **라운드 규약 — «직전 답에서 — S<k>» 블록 + AskUserQuestion 질문 둘** (`conducting-interview`, spec
  `docs/superpowers/specs/2026-09-06-interview-depth-redesign-design.md` §1). 매 라운드는 직전 답마다
  함의·상충·확인한 사실·위험 네 줄로 시작하고, Q1 은 그 되비추기의 확인(«맞다/모르겠다», 수정은 «기타»),
  Q2 는 새 결정 하나. 넷 다 «없음»이면 Q1 은 되묻기(이유·사례·실패 조건). state 본문이 이 형식 그대로다.
- **닫힘 = 사용자 발화 앵커** — `check_brief.py` 에 `coverage_anchor_failures`(닫힌 행 evidence 의
  `S<N>` 실재, floor·derived·박제 전부)와 `budget_mapper_failures`(§2 `coverage-mapper <k>` k≥1,
  `0 (unavailable: …)` 은 advisory). **0.55.0 이전 brief 는 새 게이트를 통과하지 않는다** — 아카이브는
  재게이트 대상이 아니다. 기존 fixture 86개는 `tests/fixtures/sweep_anchor_fixtures.py` 로 정합했다
  (실행 전후 `test_check_brief.sh` ok/no 집합 동일).
- **재개방** — `closed → open`, `reopened`/`reopen_log`, 상충 줄 «→ <차원> 재개방», audit §1 접미
  `(재개방 n회 — 사유)`. 상한 없음(사용자가 시계).
- **사후 깊이 측정 세 층** — `scripts/depth_pairs.py`(짝·표본 ≤4·rc 3 측정 불가), `agents/depth-auditor.md`
  (`tools: []`, `depth-audit` 센티널), `scripts/depth_record.py`(병합·audit §2 세 줄·
  `docs/superpowers/interview/depth/<basename>.json`·판정자 조건 A 30%/B 70%/적격 5건). finishing
  Step A.7. **게이트 아님** — 어떤 결과도 종료를 막지 않는다.
- **Phase 0**: seed «(사용자 확인)» 표시·«다시 검증할 것 —» 마지막 문단(`framing-requests`·
  `compression.md`·seed 템플릿); 진입 직후 워크트리 질문 + 5단계 + `DEVBREW_SPEC_DISTILL_DISABLE_WORKTREE`
  + handoff 직전 커밋 `docs(interview): <topic> interview seed + audit`.

### Changed

- coverage-mapper dispatch: «연속 3 probe 무진전 / floor 첫 전이마다» → **R1 첫 질문 전 필수 1회 + 재개방 시
  ≤1회 (상한 2, `orchestration.coverage_mapper_dispatches`)**. 첫 사이클 실측: 정체 트리거 0회 발화,
  첫 전이 dispatch 4/9 미이행.
- state 스키마: floor/derived 에 `reopened`·`reopen_log`. migration advisory v0.55.0.
- proceed 게이트(Step B) question 에 깊이 측정 요약과 `check_brief` advisories 슬롯.

### Removed

- teach-beat 절(teach-lite/heavy — 첫 사이클 열린 질문 8/8 소실), 4-block 형식, SKILL C43 경로 (c)
  (general-purpose adversarial draft, 사용 기록 0), C51 라벨 강제, 정체 트리거와 state 필드
  `no_progress_streak`·`stall_episode`·`coverage_mapper_dispatched_episode`(`test_stale_terms.sh` V10 등재).
  SKILL.md <줄 수> 줄(0.54.0: 408).

### Verification

- V6 실측 (native 워크트리, 격리 헤드리스 2회 — 기본 baseRef / `head`): <Task 1 표를 그대로>.
  keep/remove 프롬프트 모양은 헤드리스 실측 불가 — framing-requests 는 단정하지 않는다.
- V1 mutation: 앵커 삭제/번호 +1/행 삭제/`coverage-mapper 1→0` 전부 red(`$SCR/ac3_mutation.txt`).
- V5 baseline: 착수 전 실패 <n>줄 → 완료 후 <m>줄, 새 실패 0(부록 B).
- V7 사람 e2e: <Task 15 가 채운다>.
```

- [ ] **Step 3: README** — `## Principles Instantiated` 에 두 줄:
  `- **Law 3 (Compounding) — 깊이 측정 원장 (v0.55.0)** — 인터뷰마다 «답→다음 행동» 짝을 세 층(스크립트·`depth-auditor`·사람 ≤4 라벨)으로 재어 `docs/superpowers/interview/depth/<basename>.json` 에 남긴다. `depth_record.py` 가 `depth/*.json` 을 읽어 판정자 투입 조건(적격 5건·not_dug 30%·일치 70%)을 audit 에 한 줄로 낸다 — 게이트 아님(spec C5).`
  `- **P17 (User sovereignty) — 사용자가 시계 (v0.55.0)** — 차원은 사용자 발화 `S<N>` 을 인용해야 닫히고(`check_brief.py` 앵커 게이트), 재개방에 상한이 없다 — 라운드는 사용자 답으로만 돈다.`
  그리고 `## Hooks Installed`/skill 설명에서 «4-block» 잔존을 다시 grep(Task 11 Step 5 가 했지만 재확인).

- [ ] **Step 4: 부록 A·B** — 이 plan 파일 끝 «부록 A» 에 `$SCR/v6/results.md` 표를, «부록 B» 에 `$SCR/baseline_before.txt` 요약(줄 수·PY 줄)을 옮겨 적는다(spec 은 편집하지 않는다).

- [ ] **Step 5: 전수 검증 (V1~V5)**

```bash
bash "$SCR/run_all_locks.sh" > "$SCR/baseline_after.txt" 2>&1
diff "$SCR/baseline_before.txt" "$SCR/baseline_after.txt"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s plugins/spec-distill/tests -p 'test_depth_*.py'
bash plugins/spec-distill/tests/test_readme_sync.sh | tail -1
bash shared/tests/test_changelog_integrity.sh | tail -1
bash shared/tests/test_no_new_duplication.sh | tail -1
git diff --name-only main -- plugins/spec-distill/scripts/check_seed.py plugins/spec-distill/scripts/check_verbatim_coverage.py plugins/spec-distill/scripts/section6.py plugins/spec-distill/skills/reviewing-brief plugins/spec-distill/skills/reviewing-spec plugins/spec-distill/hooks
```
Expected: diff 는 **줄이 줄어드는 방향만**(새 ✗ 0 — 선재 ✗ 가 사라진 것은 허용하되 CHANGELOG 에 적는다); `PY:` 줄의 failures 가 늘지 않음; 마지막 `git diff` 출력 없음(건드리지 않는 파일). 새 ✗ 가 있으면 그 락의 이름과 함께 원인을 고친다 — 면제 목록에 넣지 않는다.

- [ ] **Step 6: 커밋** — `chore(spec-distill): 0.55.0 — CHANGELOG·README·실측 반영 (AC13·AC15)`

---

### Task 15: V7 — 사람 e2e 1회 (AC16) · V8 리뷰

**Files:**
- Modify: `plugins/spec-distill/CHANGELOG.md` (Verification 의 V7 줄)
- 산출: `docs/superpowers/interview/depth/<basename>.json` 1개(실제 인터뷰의 것)

이 task 는 사람이 한다 — 자동화하지 않는다.

- [ ] **Step 1: 이 브랜치의 플러그인으로 새 세션** — 별 터미널에서 `claude --plugin-dir "$PWD/plugins/spec-distill"` (설치 캐시가 아니라 이 브랜치 — `--plugin-dir` 가 설치 캐시를 이긴다). 작은 실제 주제로 `/request-framing` → seed(«다시 검증할 것 —» 문단 확인, 워크트리 질문이 **audit 첫 write 전**에 뜨는지 — Task 1 이 `tool_available=no` 였다면 여기서 대화형 실측을 함께 한다) → `/interview <seed 전문>`.
- [ ] **Step 2: 관찰 항목** (각각 «예/아니오 + 한 줄»): 라운드마다 «직전 답에서» 블록이 출력과 state 본문에 남는가 / Q1·Q2 가 한 AskUserQuestion 에 뜨는가, Q1 선택지가 둘인가 / **Q2 본문이 무엇을 정하는지·용어·기술 사실·선택의 결과를 풀었는가(G5)** / 넷 다 «없음»인 라운드에서 Q1 이 되묻기였는가 / coverage-mapper 가 R1 첫 질문 전에 돌았는가 / 종료 시 라벨 질문이 `min(4, 적격)` 개인가 / audit §2 에 깊이 세 줄 + 판정자 조건 줄 / `depth/<basename>.json` 생성 / 게이트 텍스트에 깊이 요약·advisory·(워크트리면) 절대경로.
- [ ] **Step 3: 기록** — CHANGELOG `[0.55.0]` Verification 의 V7 줄에 «2026-MM-DD 인터뷰 <topic>: 관찰 9항 중 <n> 충족 — <미충족 항목과 이유>». 이것이 판정자 조건의 1건째다.
- [ ] **Step 4: V8** — 구현 리뷰는 subagent-driven-development 의 task 별 2단계 리뷰 + 브랜치 전체 whole-branch 리뷰 + codex 리뷰(실호출은 사전 승인됨 — 태운 횟수를 보고). 리뷰 findings 반영 뒤 PR(`gh pr create`, merge commit, 본문 끝 `🤖 Generated with [Claude Code](https://claude.com/claude-code)` + 세션 링크).
- [ ] **Step 5: 커밋** — `docs(spec-distill): V7 사람 e2e 결과 (AC16)`

---

## 부록 A — V6 실측 결과 (Task 1 이 채운다)

| 항목 | 기본 baseRef | baseRef=head | 근거 파일 |
|---|---|---|---|
| (a) 브랜치명 | (미실측) | | |
| (b) base ref — 로컬 전용 커밋 포함? | | | |
| (c) 훅 발화 · CLAUDE_PLUGIN_ROOT | | | |
| (d) 종료 후 워크트리/브랜치 잔존 | | | |
| (d') keep/remove 프롬프트 모양 | 헤드리스 실측 불가 | 〃 | — |
| (e) `git branch -m` / `git commit -F` | | | |
| tool_available | | | |

Task 13 분기 결정: (미기록)

## 부록 B — V5 baseline (Task 2·14 가 채운다)

- 착수 전(main merge 직후): ✗ 줄 수 <n> · `PY:` <요약>
- 완료 후: ✗ 줄 수 <m> · `PY:` <요약> · 새 실패 0 / 사라진 선재 실패 <목록>

## Self-review (writing-plans 체크리스트, 작성 시 수행)

- **Spec coverage**: G1·AC1·AC2 → Task 10 / G2·C2·AC3 → Task 3·4 / C4·AC4 → Task 5·11 / C3·AC5 → Task 5·11 / G3·C5·C6·AC6 → Task 6 / C8·AC7 → Task 7·9 / AC8·G4·§3.4 → Task 8 / AC9·AC10 → Task 9 / G7·AC14 → Task 10·11·14 / C9·AC11 → Task 12 / C10·AC12·AC13·C11 → Task 1·13·14 / C12·AC15 → Task 2·14 / AC16·V7 → Task 15 / V5 → Task 2·14 / NG7 «건드리지 않음» → Task 14 Step 5 의 `git diff` 단언. §2.4 «advisory 버전 0.55.0» → Task 11 (d). spec 의 «`depth_pairs.py` 는 `round: 0` 인 S1 만 R1 과 짝» → Task 6 test `test_non_seed_s1_round1_pairs_with_r2`.
- **Placeholder scan**: «TBD/TODO/나중에» 없음. Task 13 의 «Step 8 분기표» 는 Task 1 결과에 조건부인 세 문장으로 실제 문구를 제시했다. 부록 A·B 의 빈칸은 실측 산출물 자리이며 Task 1·2·14 가 채우는 단계가 있다.
- **Type consistency**: `depth_pairs.py` 출력 키(`pairs[].s/block/eligible`, `counts.*`, `human_sample[].s`)를 Task 8 의 `depth_record.py` 와 테스트 `PAIRS` 가 같은 이름으로 쓴다. `--human` 의 `{"skipped","labels"}` 를 Task 9 finishing 이 같은 모양으로 만든다. 센티널 `depth-audit` · 라벨 어휘 `dug|not_dug|undecidable` 은 Task 7 agent · Task 8 파서 · Task 9 프롬프트가 동일. 처분 줄 `consumer=plugins/spec-distill/scripts/depth_record.py · fail-open` 은 Task 9 finishing 과 Task 8 의 `from adjudication import Ledger` 가 짝. 커밋 메시지 리터럴 `docs(interview): <topic> interview seed + audit` 은 Task 13 락·SKILL·CHANGELOG 셋이 같은 문자열. state 키 `coverage_mapper_dispatches`·`reopen_log`·`reopened` 는 Task 11 스키마·migration·락·Task 6 fixture 가 동일.
