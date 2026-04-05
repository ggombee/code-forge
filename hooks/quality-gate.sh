#!/bin/bash
# quality-gate.sh — 응답 완료 시 변경 파일 품질 검증
# Stop hook

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null | grep -E '\.(ts|tsx|js|jsx|vue)$' | head -20)
[ -z "$CHANGED_FILES" ] && exit 0

ERRORS=""

if [ -f "$PROJECT_ROOT/node_modules/.bin/eslint" ]; then
  LINT_OUT=$(echo "$CHANGED_FILES" | xargs "$PROJECT_ROOT/node_modules/.bin/eslint" --quiet 2>&1)
  [ -n "$LINT_OUT" ] && ERRORS="${ERRORS}\n[ESLint]\n${LINT_OUT}"
fi

if [ -f "$PROJECT_ROOT/node_modules/.bin/tsc" ]; then
  TSC_OUT=$("$PROJECT_ROOT/node_modules/.bin/tsc" --noEmit --pretty false 2>&1)
  TSC_EXIT=$?
  TSC_OUT=$(echo "$TSC_OUT" | head -20)
  [ $TSC_EXIT -ne 0 ] && ERRORS="${ERRORS}\n[TypeScript]\n${TSC_OUT}"
fi

# 관련 테스트 파일 탐지 및 실행
JEST_BIN=""
[ -f "$PROJECT_ROOT/node_modules/.bin/jest" ] && JEST_BIN="$PROJECT_ROOT/node_modules/.bin/jest"
[ -f "$PROJECT_ROOT/node_modules/.bin/vitest" ] && JEST_BIN="$PROJECT_ROOT/node_modules/.bin/vitest"

if [ -n "$JEST_BIN" ] && [ -n "$CHANGED_FILES" ]; then
  TEST_PATTERNS=""
  for f in $CHANGED_FILES; do
    BASENAME=$(basename "$f" | sed 's/\.\(ts\|tsx\|js\|jsx\)$//')
    TEST_PATTERNS="$TEST_PATTERNS $BASENAME"
  done

  if [ -n "$TEST_PATTERNS" ]; then
    TEST_OUT=$(timeout 30 $JEST_BIN --passWithNoTests --no-coverage \
      --testPathPattern="$(echo $TEST_PATTERNS | tr ' ' '|')" 2>&1 | tail -15)
    echo "$TEST_OUT" | grep -qE "^(FAIL|Tests:.*failed)" && \
      ERRORS="${ERRORS}\n[Tests]\n$TEST_OUT"
  fi
fi

[ -n "$ERRORS" ] && echo -e "[quality-gate] 오류:${ERRORS}" | head -30 >&2
exit 0
