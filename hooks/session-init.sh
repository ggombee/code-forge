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

# ─────────────────────────────────────────────
# 프로젝트 에이전트 재컴파일 알림
# ─────────────────────────────────────────────

WORK_DIR_CHECK="${CLAUDE_CWD:-$(pwd)}"
LOCAL_MD="$WORK_DIR_CHECK/.claude/code-forge.local.md"

if [ -f "$LOCAL_MD" ]; then
  PROJECT_CF_VERSION=$(grep -o 'version: *[0-9][0-9.]*' "$LOCAL_MD" | head -1 | grep -o '[0-9][0-9.]*' 2>/dev/null || echo "")
  CURRENT_CF_VERSION=$(grep -o '"version": *"[^"]*"' "$PLUGIN_JSON" | head -1 | grep -o '[0-9][0-9.]*')

  if [ -n "$PROJECT_CF_VERSION" ] && [ "$PROJECT_CF_VERSION" != "$CURRENT_CF_VERSION" ]; then
    echo ""
    echo "--- code-forge version mismatch ---"
    echo "Plugin: v${CURRENT_CF_VERSION} | Project: v${PROJECT_CF_VERSION}"

    # Smith 프로젝트 에이전트가 있으면 재컴파일 권장
    if [ -d "$WORK_DIR_CHECK/.agents/agents" ]; then
      echo "Project agents may use outdated thinking model."
      echo "Run: /smith-build --project"
    fi

    echo "Run: /setup (to update CLAUDE.md + AGENTS.md)"
    echo "---"
  fi
fi

# ─────────────────────────────────────────────
# 프로젝트 컨텍스트 주입 (Claude additionalContext)
# ─────────────────────────────────────────────

# 작업 디렉토리 (플러그인이 아닌 사용자 프로젝트 기준)
WORK_DIR="${CLAUDE_CWD:-$(pwd)}"

echo ""
echo "=== Project Context ==="

# Git 프로젝트 정보
if [ -d "$WORK_DIR/.git" ]; then
  PROJECT_NAME=$(basename "$WORK_DIR")
  BRANCH=$(git -C "$WORK_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
  UNCOMMITTED_COUNT=$(git -C "$WORK_DIR" status --porcelain 2>/dev/null | wc -l | tr -d ' ')

  echo "Project: $PROJECT_NAME"
  echo "Branch: $BRANCH"
  echo "Uncommitted files: $UNCOMMITTED_COUNT"

  if [ "$UNCOMMITTED_COUNT" -gt 0 ]; then
    echo "Changed files (max 10):"
    git -C "$WORK_DIR" status --porcelain 2>/dev/null | head -10 | while read -r line; do
      echo "  $line"
    done
    if [ "$UNCOMMITTED_COUNT" -gt 10 ]; then
      echo "  ... and $((UNCOMMITTED_COUNT - 10)) more"
    fi
  fi
else
  echo "Project: $(basename "$WORK_DIR") (not a git repo)"
fi

# profile.json 스택 정보
PROFILE_JSON="$WORK_DIR/.claude/profile.json"
if [ ! -f "$PROFILE_JSON" ]; then
  # .agents/ 하위도 탐색
  PROFILE_JSON="$WORK_DIR/.agents/profile.json"
fi

if [ -f "$PROFILE_JSON" ]; then
  echo ""
  echo "Stack (from profile.json):"
  # framework, styling, state 필드 파싱 (외부 도구 없이 grep 사용)
  FRAMEWORK=$(grep -o '"framework": *"[^"]*"' "$PROFILE_JSON" | grep -o '"[^"]*"$' | tr -d '"' 2>/dev/null || echo "")
  STYLING=$(grep -o '"styling": *"[^"]*"' "$PROFILE_JSON" | grep -o '"[^"]*"$' | tr -d '"' 2>/dev/null || echo "")
  STATE=$(grep -o '"state": *"[^"]*"' "$PROFILE_JSON" | grep -o '"[^"]*"$' | tr -d '"' 2>/dev/null || echo "")
  TESTING=$(grep -o '"testing": *"[^"]*"' "$PROFILE_JSON" | grep -o '"[^"]*"$' | tr -d '"' 2>/dev/null || echo "")

  [ -n "$FRAMEWORK" ] && echo "  framework: $FRAMEWORK"
  [ -n "$STYLING" ]   && echo "  styling: $STYLING"
  [ -n "$STATE" ]     && echo "  state: $STATE"
  [ -n "$TESTING" ]   && echo "  testing: $TESTING"
fi

echo "======================="
