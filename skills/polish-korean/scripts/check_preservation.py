#!/usr/bin/env python3
"""Check that Korean copy-editing preserved machine-verifiable anchors."""

from __future__ import annotations

import argparse
from collections import Counter
import difflib
import hashlib
from pathlib import Path
import re
import subprocess
import sys


FENCE_RE = re.compile(r"(^```[^\n]*\n.*?^```[ \t]*$)", re.MULTILINE | re.DOTALL)
INLINE_CODE_RE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
URL_RE = re.compile(r"https?://[^\s)>\]]+")
LINK_TARGET_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
SHA_RE = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{7,40}(?![0-9a-fA-F])")
NUMBER_RE = re.compile(
    r"(?<![\w])(?:#?\d+(?:[.,]\d+)*(?:%|초|분|시간|일|주|개월|년|건|개|회|줄|KB|MB|GB|Gi|Mi)?)"
)
# 체크박스는 순서 없는 목록과 번호 목록 어디에나 온다. 한 기호라도 빠지면 그 목록 전체가
# 검사 밖이 되고, 그 안에서 완료 표시가 옮겨 다녀도 통과한다.
CHECKBOX_LINE_RE = re.compile(r"^[ \t]*(?:[-*+]|\d{1,9}[.)])[ \t]+\[([ xX])\][ \t]*(.*)$")
# 닫는 `##` 는 제목 문구가 아니라 표기다. 문구에 넣으면 그것만 붙여도 다른 제목이 된다.
HEADING_LINE_RE = re.compile(r"^(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+", re.MULTILINE)
LIST_RE = re.compile(r"^\s*(?:[-*+] |\d+[.)] )", re.MULTILINE)
MODALITY = ("해야", "하여야", "필수", "금지", "가능", "수 있다", "추정", "권고", "확정")
# 윤문이 문장을 고쳐도 같은 항목으로 알아볼 만한 닮은 정도. 이 아래로 떨어진 항목은
# 짝짓지 못한 것으로 남긴다.
LABEL_MATCH_FLOOR = 0.6


def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def hashes(pattern: re.Pattern[str], text: str) -> Counter[str]:
    return Counter(hashlib.sha256(value.encode()).hexdigest() for value in pattern.findall(text))


def tokens(pattern: re.Pattern[str], text: str) -> Counter[str]:
    return Counter(pattern.findall(text))


def compare_counter(label: str, before: Counter[str], after: Counter[str], errors: list[str]) -> None:
    missing = before - after
    added = after - before
    if missing:
        errors.append(f"{label} 누락: {dict(missing)}")
    if added:
        errors.append(f"{label} 추가: {dict(added)}")


def checkboxes(text: str) -> list[tuple[str, str, str]]:
    """
    각 체크박스의 (상태, 제목 경로, 항목). 항목 글자만으로는 같은 문구가 절마다 하나씩
    있는 문서에서 어느 절의 것인지 알 수 없으므로, 그 항목을 감싼 제목들을 함께 남긴다.
    """
    found: list[tuple[str, str, str]] = []
    headings: list[tuple[int, str]] = []
    for line in text.split("\n"):
        heading = HEADING_LINE_RE.match(line)
        if heading:
            level = len(heading.group(1))
            while headings and headings[-1][0] >= level:
                headings.pop()
            headings.append((level, " ".join(heading.group(2).split())))
            continue
        box = CHECKBOX_LINE_RE.match(line)
        if box:
            found.append(
                (
                    box.group(1).lower(),
                    " > ".join(title for _, title in headings),
                    " ".join(box.group(2).split()),
                )
            )
    return found


def pair_checkboxes(
    before: list[tuple[str, str, str]], after: list[tuple[str, str, str]]
) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    """
    항목끼리 짝지어 (짝, 원문에 남은 것, 윤문본에 남은 것) 을 돌려준다. 자리 순서로
    짝지으면 항목이 자리를 바꾼 문서에서 n 번째 상태와 n 번째 상태가 같다는 이유로
    통과하는데, 그때 각 항목이 가리키는 일의 완료 여부는 이미 뒤바뀐 뒤다. 그래서 같은
    항목을 먼저 찾고 그 짝 안에서만 상태를 본다 — 항목 순서를 바꾼 것 자체는 상태가
    항목을 따라갔으면 통과한다.

    제목 경로와 항목이 모두 같은 것을 먼저 짝짓고, 남은 것은 윤문이 문장을 고쳐 글자가
    달라진 항목으로 보아 가장 닮은 것부터 짝짓는다. 바닥선은 제목 경로와 항목 중 덜 닮은
    쪽에 건다 — 항목 문구가 같아도 다른 절의 것이면 같은 항목이 아니다. 다만 그 값으로
    순서까지 정하면, 절마다 같은 문구를 쓰는 문서에서 항목 유사도가 낮은 쪽으로 모두 같은
    값이 되어 제목이 구별해 주던 것을 도로 잃는다. 그래서 순서는 (덜 닮은 쪽, 제목, 항목)
    을 차례로 본다. 바닥선에 못 미친 것은 짝짓지 않고 남긴다 — 자리 순서로 이어 붙이면
    애초의 결함이 그대로 돌아온다. 항목의 뜻을 읽는 것이 아니라 글자를 대는 것뿐이다.
    """
    pairs: list[tuple[int, int]] = []
    open_before = list(range(len(before)))
    open_after = list(range(len(after)))

    by_key: dict[tuple[str, str], list[int]] = {}
    for index in open_after:
        by_key.setdefault(after[index][1:], []).append(index)
    for index in list(open_before):
        candidates = by_key.get(before[index][1:])
        if candidates:
            matched = candidates.pop(0)
            pairs.append((index, matched))
            open_before.remove(index)
            open_after.remove(matched)

    scored = []
    for i in open_before:
        for j in open_after:
            section = difflib.SequenceMatcher(None, before[i][1], after[j][1]).ratio()
            label = difflib.SequenceMatcher(None, before[i][2], after[j][2]).ratio()
            scored.append((min(section, label), section, label, i, j))
    scored.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3], item[4]))
    for ratio, _section, _label, i, j in scored:
        if ratio < LABEL_MATCH_FLOOR:
            break
        if i in open_before and j in open_after:
            pairs.append((i, j))
            open_before.remove(i)
            open_after.remove(j)

    pairs.sort()
    return pairs, open_before, open_after


def excerpt(box: tuple[str, str, str], limit: int = 30) -> str:
    """항목을 사람이 문서에서 찾을 수 있을 만큼만. 문구가 같은 항목은 제목이 있어야 구별된다."""
    _, section, label = box
    text = f"{section} > {label}" if section else label
    return text if len(text) <= limit else f"…{text[-limit:]}"


def read_git_text(repo: str, spec: str) -> str:
    result = subprocess.run(
        ["git", "-C", repo, "show", spec],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or f"git show 실패: {spec}")
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--before", help="원문 파일")
    source.add_argument("--before-git", help="Git 원문 REV:PATH")
    parser.add_argument("--after", required=True)
    parser.add_argument("--repo", default=".", help="--before-git 저장소 경로")
    parser.add_argument("--rewrite", action="store_true", help="구조 재작성 요청: 변경률 상한만 완화")
    parser.add_argument(
        "--diff-report",
        action="store_true",
        help="내용 개정의 차이를 나열만 한다. 보존 검사가 아니며 게시 근거로 쓸 수 없다",
    )
    args = parser.parse_args()

    before = read_text(args.before) if args.before else read_git_text(args.repo, args.before_git)
    after = read_text(args.after)
    errors: list[str] = []
    warnings: list[str] = []

    # 내용 개정의 차이를 세는 것과 윤문이 사실을 흘렸는지 보는 것은 다른 일이다. 전자는
    # 나열만 하고(--diff-report), 후자만 통과/실패를 낸다. 한 실행이 둘을 겸하면 "차이를
    # 다 적었으니 통과" 가 되어 무엇을 지워도 게시가 된다.
    anchors = warnings if args.diff_report else errors

    compare_counter("코드 블록", hashes(FENCE_RE, before), hashes(FENCE_RE, after), anchors)
    for label, pattern in (
        ("인라인 코드", INLINE_CODE_RE),
        ("URL", URL_RE),
        ("링크 대상", LINK_TARGET_RE),
        ("SHA", SHA_RE),
        ("수치", NUMBER_RE),
    ):
        compare_counter(label, tokens(pattern, before), tokens(pattern, after), anchors)

    # 윤문은 진행 상태를 바꾸지 않는다 — 바꿨다면 그것은 윤문이 아니라 개정이다. 상태
    # 기호만 자리 순서로 세면 완료 표시가 항목 사이를 옮겨 다닌 문서가 그대로 통과하므로,
    # 항목과 상태의 연결을 짝지은 뒤 그 짝 안에서 상태를 본다.
    before_boxes = checkboxes(before)
    after_boxes = checkboxes(after)
    if len(before_boxes) != len(after_boxes):
        anchors.append(f"체크박스 항목 수 변경: {len(before_boxes)} -> {len(after_boxes)}")
    else:
        pairs, left_before, left_after = pair_checkboxes(before_boxes, after_boxes)
        flipped = [
            f"'{excerpt(before_boxes[i])}' [{before_boxes[i][0]}] -> [{after_boxes[j][0]}]"
            for i, j in pairs
            if before_boxes[i][0] != after_boxes[j][0]
        ]
        if flipped:
            shown = "; ".join(flipped[:5])
            more = "" if len(flipped) <= 5 else f" 외 {len(flipped) - 5}개"
            anchors.append(f"체크 상태 변경: {len(flipped)}개 항목 — {shown}{more}")

        # 짝짓지 못한 항목은 자리 순서로 이어 붙이지 않는다 — 그러면 상태가 어느 항목의
        # 것인지 모르는 채로 "그 자리의 상태는 같다" 를 통과 근거로 삼게 된다. 남은 것이
        # 모두 같은 상태일 때만 어떻게 짝지어도 결과가 같으므로 넘어간다.
        unmatched = {before_boxes[i][0] for i in left_before} | {
            after_boxes[j][0] for j in left_after
        }
        if len(unmatched) > 1:
            samples = "; ".join(f"'{excerpt(before_boxes[i])}'" for i in left_before[:5])
            more = "" if len(left_before) <= 5 else f" 외 {len(left_before) - 5}개"
            anchors.append(
                f"체크 항목을 짝지을 수 없음: {len(left_before)}개 항목의 문장이 크게 달라져 "
                f"완료 상태가 어느 항목의 것인지 확인할 수 없습니다 — {samples}{more}"
            )

    before_levels = [len(value) for value in HEADING_RE.findall(before)]
    after_levels = [len(value) for value in HEADING_RE.findall(after)]
    if before_levels != after_levels:
        anchors.append(f"제목 구조 변경: {before_levels} -> {after_levels}")

    before_lists = len(LIST_RE.findall(before))
    after_lists = len(LIST_RE.findall(after))
    if before_lists != after_lists:
        warnings.append(f"목록 항목 수 변경: {before_lists} -> {after_lists}")

    for marker in MODALITY:
        before_count = before.count(marker)
        after_count = after.count(marker)
        if before_count != after_count:
            warnings.append(f"서법 표지 '{marker}' 변화: {before_count} -> {after_count}")

    ratio = 1 - difflib.SequenceMatcher(None, before, after).ratio()
    warn_limit, error_limit = ((0.60, 0.80) if args.rewrite else (0.30, 0.50))
    if ratio >= error_limit:
        anchors.append(f"변경률 {ratio:.1%}가 상한 {error_limit:.0%} 이상")
    elif ratio >= warn_limit:
        warnings.append(f"변경률 {ratio:.1%}가 검토 기준 {warn_limit:.0%} 이상")

    print(f"change_ratio: {ratio:.1%}")
    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARN: {message}")

    if args.diff_report:
        # 통과라는 말을 쓰지 않는다. 이 실행은 무엇이 달라졌는지 세었을 뿐이고, 그 차이가
        # 옳은지는 사람이 판단한다. 여기서 "PASS" 를 찍으면 그 판단이 있었던 것처럼 보인다.
        print(f"REPORT: 내용 개정 차이 {len(warnings)}건 — 보존 검사가 아니며 게시 근거가 아닙니다")
        return 0

    if errors:
        return 1
    print("PASS: 보호 항목 유지")
    return 0


if __name__ == "__main__":
    sys.exit(main())
