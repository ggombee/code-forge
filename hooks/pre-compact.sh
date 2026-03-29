#!/bin/bash
# pre-compact.sh — 컨텍스트 압축 전 상태 스냅샷 주입
# PreCompact hook (stdout → preserveContent로 Claude에게 전달)

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

echo "=== 컨텍스트 압축 전 상태 (이 정보를 압축 후에도 유지하세요) ==="
echo "시각: $(date '+%Y-%m-%d %H:%M:%S')"

if [ -d "$PROJECT_ROOT/.git" ]; then
  BRANCH=$(git -C "$PROJECT_ROOT" branch --show-current 2>/dev/null)
  echo "브랜치: $BRANCH"

  CHANGED=$(git -C "$PROJECT_ROOT" diff --name-only HEAD 2>/dev/null)
  if [ -n "$CHANGED" ]; then
    echo "미커밋 변경 파일:"
    echo "$CHANGED" | head -20 | sed 's/^/  - /'
  fi

  STAGED=$(git -C "$PROJECT_ROOT" diff --cached --name-only 2>/dev/null)
  if [ -n "$STAGED" ]; then
    echo "스테이지된 파일:"
    echo "$STAGED" | head -10 | sed 's/^/  + /'
  fi
fi

echo "=== 끝 ==="
