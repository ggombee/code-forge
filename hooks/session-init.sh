#!/bin/bash
# session-init.sh — 세션 시작 시 플러그인 자동 업데이트
# SessionStart 훅에서 실행됨

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
PLUGIN_JSON="$PLUGIN_ROOT/.claude-plugin/plugin.json"
CACHE_FILE="$PLUGIN_ROOT/.plugin-cache-version"

# 현재 로컬 버전
LOCAL_VERSION=$(grep -o '"version": *"[^"]*"' "$PLUGIN_JSON" | head -1 | grep -o '[0-9][0-9.]*')

# git repo가 아니면 스킵
if [ ! -d "$PLUGIN_ROOT/.git" ]; then
  exit 0
fi

cd "$PLUGIN_ROOT"

# remote 확인 (타임아웃 5초, 실패 시 무시)
if ! git fetch origin --quiet 2>/dev/null; then
  exit 0
fi

# 로컬과 리모트 비교
LOCAL_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "")
REMOTE_HEAD=$(git rev-parse origin/main 2>/dev/null || echo "")

if [ -z "$LOCAL_HEAD" ] || [ -z "$REMOTE_HEAD" ]; then
  exit 0
fi

# 이미 최신이면 스킵
if [ "$LOCAL_HEAD" = "$REMOTE_HEAD" ]; then
  # 캐시 버전 파일 갱신
  echo "$LOCAL_VERSION" > "$CACHE_FILE"
  exit 0
fi

# 로컬 변경사항이 있으면 업데이트 스킵 (사용자가 수정 중일 수 있음)
if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
  exit 0
fi

# 자동 업데이트 실행
if ! git pull origin main --ff-only --quiet 2>/dev/null; then
  # ff-only 실패 (conflict) → 강제 업데이트하지 않고 스킵
  exit 0
fi

# 업데이트 후 새 버전 확인
NEW_VERSION=$(grep -o '"version": *"[^"]*"' "$PLUGIN_JSON" | head -1 | grep -o '[0-9][0-9.]*')
PREV_VERSION="${LOCAL_VERSION}"

# 캐시 파일에 이전 버전이 있으면 그걸 사용
if [ -f "$CACHE_FILE" ]; then
  PREV_VERSION=$(cat "$CACHE_FILE" 2>/dev/null || echo "$LOCAL_VERSION")
fi

# 버전 변경 시 알림
if [ "$PREV_VERSION" != "$NEW_VERSION" ]; then
  echo "⚡ code-forge updated: v${PREV_VERSION} → v${NEW_VERSION}"

  # 최근 변경 요약 (버전 변경 커밋들)
  CHANGES=$(git log --oneline "${LOCAL_HEAD}..HEAD" --no-decorate 2>/dev/null | head -5)
  if [ -n "$CHANGES" ]; then
    echo ""
    echo "Changes:"
    echo "$CHANGES"
  fi
fi

# 캐시 버전 갱신
echo "$NEW_VERSION" > "$CACHE_FILE"
