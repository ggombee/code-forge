#!/usr/bin/env bash
# UserPromptSubmit hook — 자연어 → flow CLI 강제 호출
#
# 목적: 모델이 자율 추론으로 flow CLI를 부르길 기대하는 구조 제거.
#       사용자 발화에 티켓 ID(PROJ-123, ABC-4567 등) 정규식 매칭되면
#       hook 단계에서 직접 flow tc select 강제 호출.
#
# INTEGRATION.md §4 자연어 매핑 회로 구현.
# (2026-05-19 redesign G5)
#
# 종료 코드:
#   0 — 항상 0 (hook이 사용자 입력 자체를 막지 않음)
# stdout — Claude에게 추가 컨텍스트로 주입

set -e

# flow CLI 미설치 시 silent exit (graceful)
command -v flow >/dev/null 2>&1 || exit 0

# stdin에서 prompt 읽기 (Claude Code 표준: JSON { "prompt": "..." })
INPUT=$(cat 2>/dev/null || echo "")
[ -z "$INPUT" ] && exit 0

# prompt 필드 추출 (jq 있으면 우선, 없으면 grep)
if command -v jq >/dev/null 2>&1; then
  PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty' 2>/dev/null || echo "")
else
  PROMPT=$(echo "$INPUT" | grep -o '"prompt":[[:space:]]*"[^"]*"' \
    | sed 's/.*"prompt":[[:space:]]*"\(.*\)"/\1/' | head -1)
fi
[ -z "$PROMPT" ] && exit 0

# 티켓 ID 정규식 (대문자 알파벳 + 하이픈 + 숫자 1자리 이상)
# 음성 친화 (2026-06-08 G9c): case-insensitive + 공백 fallback
#   예: PROJ-123, proj-123, PROJ 123, Proj 123 (Whisper dictation 결과 변동 흡수)
TICKET_RAW=$(echo "$PROMPT" | grep -oiE '\b[A-Z]{2,}[[:space:]-][0-9]+\b' | head -1)
[ -z "$TICKET_RAW" ] && exit 0

# normalize: 공백 → 하이픈, 소문자 → 대문자
TICKET=$(echo "$TICKET_RAW" | tr ' ' '-' | tr 'a-z' 'A-Z')

# 영향 TC 자동 조회 (실패해도 사용자 작업은 방해하지 않음)
echo "[code-forge auto-flow-trigger] 티켓 '$TICKET' 감지 → flow tc select 자동 호출"
if flow tc select "$TICKET" --json 2>/dev/null; then
  :
else
  echo "[code-forge auto-flow-trigger] flow tc select '$TICKET' 실패 또는 미적용 프로젝트 — skip"
fi

exit 0
