#!/usr/bin/env bash
# docreview 케이스 락들이 **실제로 읽는** 픽스처 코퍼스를 낸다 — `--emit-scanned` 의 정본.
# 테스트가 아니다(`test_*.sh` 글롭 밖이고 `# guards:` 선언도 없다) — 도출기다.
#
# ── 왜 도출이 한 곳인가 ───────────────────────────────────────────────────
# 이 목록은 여섯 락이 각자 `git ls-files -- 'shared/tests/fixtures/docreview/*'` 로
# **열거**하고 있었다. Task 8b 가 그 디렉토리에 `golden/` 과 `capture_finalize_golden.sh`
# 를 넣자, 여섯이 **한꺼번에** 「안 읽은 파일 일곱을 읽었다」고 선언하게 됐고
# `test_guards_coverage_bidirectional.sh` 가 그 거짓 주장을 축복했다. 한 락만 고치면
# 같은 결함이 대상만 옮겨 재발한다 — 열거를 도출로 바꾼다.
#
# ── 무엇을 빼는가 ─────────────────────────────────────────────────────────
# `golden/**` 과 `capture_finalize_golden.sh`. 그 일곱은 케이스의 «입력»이 아니라
# 형제 락 `test_docreview_golden.sh` 의 «기대 출력»이자 그 러너다. 그것을 실제로 읽는
# 유일한 락이 자기 emit 에 따로 더한다 — 그래서 두 emit 을 합치면 코퍼스 전체가 되고,
# 어느 쪽도 안 읽은 것을 선언하지 않는다.
set -u
cd "$(dirname "$0")/../.." || exit 1
git ls-files -- 'shared/tests/fixtures/docreview/*' \
  | grep -v -e '^shared/tests/fixtures/docreview/golden/' \
            -e '^shared/tests/fixtures/docreview/capture_finalize_golden\.sh$'
