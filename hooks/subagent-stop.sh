#!/bin/bash
# subagent-stop.sh — 서브에이전트 완료 후 품질 검증
# SubagentStop hook: implementor/deep-executor/build-fixer 완료 시 tsc 검증

INPUT=$(cat)
AGENT_TYPE=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('agent_type', ''))
except:
    print('')
" 2>/dev/null)

# 구현 에이전트 완료 시에만 검증
if [[ "$AGENT_TYPE" =~ ^(implementor|deep-executor|build-fixer)$ ]]; then
  PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  CHANGED=$(git diff --name-only HEAD 2>/dev/null | grep -E '\.(ts|tsx|js|jsx)$' | head -10)

  if [ -n "$CHANGED" ] && [ -f "$PROJECT_ROOT/node_modules/.bin/tsc" ]; then
    TSC_OUT=$("$PROJECT_ROOT/node_modules/.bin/tsc" --noEmit --pretty false 2>&1 | head -10)
    if [ $? -ne 0 ]; then
      echo "SubagentStop [${AGENT_TYPE}] TypeScript 오류:"
      echo "$TSC_OUT"
    fi
  fi
fi

exit 0
