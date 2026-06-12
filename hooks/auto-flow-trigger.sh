#!/usr/bin/env bash
# UserPromptSubmit hook — Foreman(작업 길안내) + 자연어 → flow CLI 강제 호출
#
# 블록 구성:
#   C0. 직전 턴 마무리 제안 백스톱 — quality-gate가 route.json에 남긴 wrapup_hint를
#       다음 프롬프트에서 1회 전달 (Stop 훅 stdout은 모델에 미도달 — 2026-06-12 판정)
#   C1. Foreman — 작업성 발화 감지 시 /start·복잡도·effort 선택지 안내 (세션당 1회, 강제 아님)
#   C2. 티켓 ID(PROJ-123 등) → flow tc select 강제 호출 (flow CLI 설치 시에만)
#
# INTEGRATION.md §4 자연어 매핑 회로 + FORGE_MASTERPLAN 2단계 (2026-06-12).
# (2026-05-19 redesign G5 → 2026-06-12 Foreman 확장 — 전역 flow 가드를 C2로 강등,
#  flow 미설치 환경에서도 C0/C1은 동작)
#
# 종료 코드:
#   0 — 항상 0 (hook이 사용자 입력 자체를 막지 않음)
# stdout — Claude에게 추가 컨텍스트로 주입
#
# set -e 주의 (must_fix 7): 분류용 grep/정규식은 매칭 실패가 정상 경로이므로
# 전부 `|| true`/`|| echo ""` 가드 — 훅 침묵 사망 방지.

set -e

# stdin에서 prompt 읽기 (Claude Code 표준: JSON { "prompt": "...", "session_id": "..." })
INPUT=$(cat 2>/dev/null || echo "")
[ -z "$INPUT" ] && exit 0

# prompt/session_id 추출 (jq 있으면 우선, 없으면 grep)
if command -v jq >/dev/null 2>&1; then
  PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty' 2>/dev/null || echo "")
  SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null || echo "")
else
  PROMPT=$(echo "$INPUT" | grep -o '"prompt":[[:space:]]*"[^"]*"' 2>/dev/null \
    | sed 's/.*"prompt":[[:space:]]*"\(.*\)"/\1/' | head -1 || echo "")
  SESSION_ID=""
fi
[ -z "$PROMPT" ] && exit 0

MARKER_DIR="$HOME/.code-forge"
mkdir -p "$MARKER_DIR" 2>/dev/null || true
TODAY=$(date +%Y%m%d)
SID="${SESSION_ID:-nosid}"
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

# ── C0. 직전 턴 마무리 제안 백스톱 (F3a 수신측) ──
# quality-gate.sh(Stop)가 남긴 wrapup_hint는 모델에 직접 도달하지 않으므로
# 다음 프롬프트에서 여기로 1회 전달. 2시간 지난 힌트는 무시 (세션 경계 오염 방지).
WRAP_MARKER="$MARKER_DIR/foreman-$TODAY-$SID-f3a"
ROUTE_FILE="$PROJECT_ROOT/.claude/state/route.json"
if command -v jq >/dev/null 2>&1 && [ ! -f "$WRAP_MARKER" ] && [ -f "$ROUTE_FILE" ]; then
  HINT_TS=$(jq -r '.wrapup_hint.ts // empty' "$ROUTE_FILE" 2>/dev/null || echo "")
  if [ -n "$HINT_TS" ]; then
    HINT_EPOCH=$(date -j -u -f "%Y-%m-%dT%H:%M:%SZ" "$HINT_TS" +%s 2>/dev/null || echo 0)
    NOW_EPOCH=$(date -u +%s)
    if [ "$HINT_EPOCH" -gt 0 ] && [ $((NOW_EPOCH - HINT_EPOCH)) -lt 7200 ]; then
      touch "$WRAP_MARKER" 2>/dev/null || true
      echo "[code-forge foreman] 직전 턴: 변경 파일 있음 + progress.md 미갱신. 작업이 일단락된 상태면 progress 정리 또는 /handoff를 한 줄로 제안할 것 (세션당 1회 안내, 강제 아님)."
    fi
  fi
fi

# ── C1. Foreman — 작업성 발화 → /start·복잡도·effort 선택지 (세션당 1회) ──
C1_MARKER="$MARKER_DIR/foreman-$TODAY-$SID-c1"
case "$PROMPT" in
  /*) C1_ELIGIBLE=0 ;;  # 슬래시 명령 — 이미 레일 위
  *)  C1_ELIGIBLE=1 ;;
esac
if [ "$C1_ELIGIBLE" -eq 1 ] && [ ! -f "$C1_MARKER" ] && [ "${#PROMPT}" -ge 10 ]; then
  if echo "$PROMPT" | grep -qiE '(만들|구현|추가|수정해|수정하|고쳐|고치|리팩토|개선해|개선하|작성해|작성하|생성해|연동|적용해|마이그레|구축|개발해|시작하|시작해|진행해|붙여|implement|build|create|add|refactor|fix)' 2>/dev/null; then
    touch "$C1_MARKER" 2>/dev/null || true
    cat <<'FOREMAN_EOF'
[code-forge foreman] 작업성 발화 감지 (세션당 1회 안내, 강제 아님)
이 발화가 실제 코드 작업 요청이면, 착수 전에 사용자에게 다음 선택지를 한 번 제시할 것:
  ① /start로 정식 진행 (분석→구현→검증→커밋, progress 기록)
  ② 그냥 진행 — 단, 복잡도 판단(LOW/MED/HIGH)과 권장 effort(low/medium/high/xhigh)를 한 줄로 명시
질문/단답/논의성 발화로 판단되면 제안을 생략하고 평소대로 답할 것.
FOREMAN_EOF
  fi
fi

# ── C2. 티켓 ID → flow tc select (flow CLI 설치 시에만 — 기존 G5 회로, 동작 무변경) ──
command -v flow >/dev/null 2>&1 || exit 0

# 티켓 ID 정규식 (대문자 알파벳 + 하이픈 + 숫자 1자리 이상)
# 음성 친화 (2026-06-08 G9c): case-insensitive + 공백 fallback
#   예: PROJ-123, proj-123, PROJ 123, Proj 123 (Whisper dictation 결과 변동 흡수)
TICKET_RAW=$(echo "$PROMPT" | grep -oiE '\b[A-Z]{2,}[[:space:]-][0-9]+\b' 2>/dev/null | head -1 || echo "")
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
