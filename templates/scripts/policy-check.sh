#!/bin/bash
# Policy Check — 수정된 파일이 정책 매트릭스에 매칭되면 관련 TC 파일 실행
#
# 사용법:
#   ./policy-check.sh <파일경로>           매칭 + TC 자동 실행
#   ./policy-check.sh --report-only <파일> 매칭 경고만
#   ./policy-check.sh --run-all           전체 TC 실행
#
# 다른 레포 이식 시:
#   POLICY_DIR=/path/to/.policy PROJECT_ROOT=/path/to/project ./policy-check.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
export POLICY_DIR="${POLICY_DIR:-$PROJECT_DIR/.policy}"

MODE="check-and-run"
CHANGED_FILE=""

case "${1:-}" in
  --report-only) MODE="report-only"; CHANGED_FILE="${2:-}" ;;
  --run-all)     MODE="run-all" ;;
  *)             CHANGED_FILE="${1:-}" ;;
esac

# ── 전체 실행 모드 ──
if [ "$MODE" = "run-all" ]; then
  echo "🔄 전체 TC 실행 중..."
  FAIL=0

  echo "=== 유닛 테스트 ==="
  cd "$PROJECT_DIR"
  yarn test 2>&1 | tail -10 || FAIL=1

  echo ""
  echo "=== E2E 테스트 ==="
  if [ -f "$PROJECT_DIR/playwright.config.ts" ]; then
    npx playwright test 2>&1 | tail -10 || FAIL=1
  else
    echo "  playwright.config.ts 없음 — 스킵"
  fi

  echo ""
  [ $FAIL -eq 0 ] && echo "✅ 전체 TC 통과" || echo "❌ 실패 발생"
  exit $FAIL
fi

# ── 파일 매칭 모드 ──
[ -z "$CHANGED_FILE" ] && exit 0

# Python으로 매칭
RESULT=$(python3 "$SCRIPT_DIR/policy-check.py" --match "$CHANGED_FILE" 2>/dev/null) || exit 0

PAGE=$(echo "$RESULT" | grep "^PAGE=" | head -1 | cut -d= -f2)
FLOWS=$(echo "$RESULT" | grep "^FLOWS=" | head -1 | cut -d= -f2-)
TEST_FILES=$(echo "$RESULT" | grep "^TEST_FILES=" | sed 's/^TEST_FILES=//' | tr ' ' '\n' | sort -u | tr '\n' ' ')

echo "⚠️  정책 매칭: $PAGE — $FLOWS"

# TC 실행
if [ "$MODE" = "check-and-run" ] && [ -n "$TEST_FILES" ]; then
  echo ""
  echo "🔄 관련 TC 실행: $TEST_FILES"
  cd "$PROJECT_DIR"
  FAIL=0

  for tf in $TEST_FILES; do
    if [[ "$tf" == e2e/* ]]; then
      echo "  → E2E: $tf"
      npx playwright test "$tf" --reporter=line 2>&1 | tail -3 || FAIL=1
    elif [[ "$tf" == src/* ]]; then
      echo "  → 유닛: $tf"
      BASENAME=$(basename "$tf" | sed 's/\.test\.\(ts\|tsx\)$//')
      yarn test -- --testPathPattern="$BASENAME" --silent 2>&1 | tail -3 || FAIL=1
    fi
  done

  echo ""
  [ $FAIL -eq 0 ] && echo "✅ 관련 TC 통과" || echo "❌ TC 실패!"
  exit $FAIL
fi
