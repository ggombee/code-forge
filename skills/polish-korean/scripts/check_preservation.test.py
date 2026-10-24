#!/usr/bin/env python3
"""
Regression cases for the checkbox item/state link in check_preservation.py.

Run: python3 check_preservation.test.py

Covers what the positional comparison used to miss (a completion mark moving between
items) and what must keep passing (items reordered with each item's own state intact).
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile


CHECKER = Path(__file__).with_name("check_preservation.py")

# 체크박스 몇 줄만 있는 문서는 줄 하나만 옮겨도 변경률 상한에 걸려, 체크박스 판정이 아니라
# 변경률 때문에 막힌다. 어느 사례든 체크박스 판정만 남기려고 같은 본문을 앞에 붙인다.
PREAMBLE = (
    "# 배포 준비 상황\n\n"
    "이번 배포에 필요한 준비를 항목별로 적어 둔다. 각 항목은 담당자가 직접 확인한 뒤\n"
    "완료 표시를 옮긴다. 표시를 옮기는 일은 진행 상황을 바꾸는 일이므로 문장을 다듬는\n"
    "작업과 섞지 않는다.\n\n"
)


def run(before: str, after: str) -> subprocess.CompletedProcess[str]:
    before = PREAMBLE + before
    after = PREAMBLE + after
    with tempfile.TemporaryDirectory(prefix="check-preservation-test-") as workspace:
        before_path = Path(workspace) / "before.md"
        after_path = Path(workspace) / "after.md"
        before_path.write_text(before, encoding="utf-8")
        after_path.write_text(after, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(CHECKER), "--before", str(before_path), "--after", str(after_path)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )


FAILURES: list[str] = []
CASES = 0


def expect_fail(name: str, before: str, after: str, contains: str) -> None:
    global CASES
    CASES += 1
    result = run(before, after)
    if result.returncode == 0:
        FAILURES.append(f"{name}: 통과하면 안 되는 입력이 exit 0 으로 통과했다\n{result.stdout}")
    elif contains not in result.stdout:
        FAILURES.append(f"{name}: 출력에 '{contains}' 가 없다\n{result.stdout}")


def expect_pass(name: str, before: str, after: str) -> None:
    global CASES
    CASES += 1
    result = run(before, after)
    if result.returncode != 0:
        FAILURES.append(f"{name}: 통과해야 하는 입력이 exit {result.returncode} 로 막혔다\n{result.stdout}")


# 검토가 보고한 누락. 항목별 완료 상태가 서로 바뀌었는데 자리별 상태 배열은 그대로다.
expect_fail(
    "완료 표시가 항목 사이를 옮겨 갔다",
    "- [x] 작업 가 완료\n- [ ] 작업 나 완료\n",
    "- [x] 작업 나 완료\n- [ ] 작업 가 완료\n",
    "체크 상태 변경",
)

# 항목 순서만 바꾼 것은 상태가 항목을 따라갔으므로 통과한다.
expect_pass(
    "항목 순서만 바뀌고 각 항목의 상태는 그대로다",
    "- [x] 작업 가 완료\n- [ ] 작업 나 완료\n",
    "- [ ] 작업 나 완료\n- [x] 작업 가 완료\n",
)

# 윤문이 문장을 고쳐도 같은 항목으로 알아보고, 상태가 그대로면 통과한다.
expect_pass(
    "문장을 고쳤지만 상태는 그대로다",
    "- [x] 작업 가를 완료하였음\n- [ ] 작업 나를 완료하였음\n",
    "- [x] 작업 가를 마쳤다\n- [ ] 작업 나를 마쳤다\n",
)

# 문장을 고치면서 상태까지 바꾼 것은 윤문이 아니라 개정이므로 막는다.
expect_fail(
    "문장을 고치면서 상태도 바꿨다",
    "- [x] 작업 가를 완료하였음\n- [ ] 작업 나를 완료하였음\n",
    "- [ ] 작업 가를 마쳤다\n- [x] 작업 나를 마쳤다\n",
    "체크 상태 변경",
)

# 항목 자체가 줄거나 늘면 짝지을 수 없으므로 개수에서 먼저 막는다.
expect_fail(
    "체크박스 항목이 사라졌다",
    "- [x] 작업 가 완료\n- [ ] 작업 나 완료\n",
    "- [x] 작업 가 완료\n",
    "체크박스 항목 수 변경",
)

# 문구가 같은 항목이 절마다 있으면 글자만으로는 구별되지 않는다. 절 제목까지 봐야 한다.
expect_fail(
    "문구가 같은 항목의 완료 표시가 절 사이를 옮겨 갔다",
    "## 서비스 가\n\n- [x] 배포 완료\n\n## 서비스 나\n\n- [ ] 배포 완료\n",
    "## 서비스 나\n\n- [x] 배포 완료\n\n## 서비스 가\n\n- [ ] 배포 완료\n",
    "체크 상태 변경",
)

# 같은 절 구성에서 절 순서만 바꾼 것은 각 절의 상태가 그대로이므로 통과한다.
expect_pass(
    "문구가 같은 항목인데 절 순서만 바뀌었다",
    "## 서비스 가\n\n- [x] 배포 완료\n\n## 서비스 나\n\n- [ ] 배포 완료\n",
    "## 서비스 나\n\n- [ ] 배포 완료\n\n## 서비스 가\n\n- [x] 배포 완료\n",
)

# 절마다 같은 문구를 쓰면 항목 유사도가 후보마다 같아진다. 그 값으로 순서까지 정하면
# 제목이 구별해 주던 것을 도로 잃고 등장 순서대로 짝지어진다.
expect_fail(
    "절마다 문구가 같고 그 문구를 함께 고쳐 쓰면서 완료 표시가 절 사이를 옮겨 갔다",
    "## 서비스 가\n\n- [x] 배포 준비를 완료하였음\n\n## 서비스 나\n\n- [ ] 배포 준비를 완료하였음\n",
    "## 서비스 나\n\n- [x] 배포 준비를 마쳤다\n\n## 서비스 가\n\n- [ ] 배포 준비를 마쳤다\n",
    "체크 상태 변경",
)

expect_pass(
    "절마다 문구가 같고 그 문구를 함께 고쳐 썼지만 각 절의 상태는 그대로다",
    "## 서비스 가\n\n- [x] 배포 준비를 완료하였음\n\n## 서비스 나\n\n- [ ] 배포 준비를 완료하였음\n",
    "## 서비스 나\n\n- [ ] 배포 준비를 마쳤다\n\n## 서비스 가\n\n- [x] 배포 준비를 마쳤다\n",
)

# 체크박스는 -, *, + 목록과 번호 목록 어디에나 온다. 한 기호라도 빠지면 그 목록 전체가
# 검사 밖이 되고, 그 안에서 완료 표시가 옮겨 다녀도 통과한다.
expect_fail(
    "+ 목록의 완료 표시가 항목 사이를 옮겨 갔다",
    "+ [x] 서비스 가 배포\n+ [ ] 서비스 나 배포\n",
    "+ [ ] 서비스 가 배포\n+ [x] 서비스 나 배포\n",
    "체크 상태 변경",
)

expect_fail(
    "번호 목록의 완료 표시가 항목 사이를 옮겨 갔다",
    "1. [x] 서비스 가 배포\n2. [ ] 서비스 나 배포\n",
    "1. [ ] 서비스 가 배포\n2. [x] 서비스 나 배포\n",
    "체크 상태 변경",
)

# 닫는 `##` 는 제목 문구가 아니라 표기다. 문구에 넣으면 그것만 붙여도 다른 제목이 되어,
# 상태를 건드리지 않은 윤문이 짝짓기에 실패한다.
expect_pass(
    "제목에 닫는 ## 만 붙였다",
    "## 배포\n\n- [x] 준비 확인\n\n## 검증\n\n- [ ] 결과 확인\n",
    "## 배포 ##\n\n- [x] 준비 확인\n\n## 검증 ##\n\n- [ ] 결과 확인\n",
)

# 어느 항목과도 닮지 않게 고쳐 쓰면 상태가 누구 것인지 알 수 없다. 자리 순서로 이어 붙여
# 통과시키면 애초에 막으려던 결함이 그대로 돌아온다.
expect_fail(
    "짝지을 수 없게 고쳐 쓰면서 상태도 섞였다",
    "- [x] 작업 가를 완료하였음\n- [ ] 작업 나를 완료하였음\n",
    "- [x] 나 작업을 마쳤다\n- [ ] 가 작업을 마쳤다\n",
    "짝지을 수 없음",
)

# 짝짓지 못했어도 남은 항목의 상태가 모두 같으면 어떻게 짝지어도 결과가 같다.
expect_pass(
    "짝지을 수 없게 고쳐 썼지만 남은 항목의 상태가 모두 같다",
    "- [ ] 작업 가를 완료하였음\n- [ ] 작업 나를 완료하였음\n",
    "- [ ] 나 작업을 마쳤다\n- [ ] 가 작업을 마쳤다\n",
)

# 순서도 문장도 그대로인 보통의 윤문은 그대로 통과한다.
expect_pass(
    "체크박스를 건드리지 않은 윤문",
    "# 제목\n\n- [x] 작업 가 완료\n- [ ] 작업 나 완료\n\n본문을 조금 다듬는다.\n",
    "# 제목\n\n- [x] 작업 가 완료\n- [ ] 작업 나 완료\n\n본문을 조금 다듬었다.\n",
)

if FAILURES:
    for failure in FAILURES:
        print(f"FAIL: {failure}")
    raise SystemExit(1)
print(f"PASS: 체크박스 항목-상태 연결 회귀 {CASES}건")
