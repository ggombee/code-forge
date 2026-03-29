#!/bin/bash
# permission-guard.sh — 읽기 전용/검증 명령 자동 허용
# PermissionRequest hook

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_name', ''))
except:
    print('')
" 2>/dev/null)

COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except:
    print('')
" 2>/dev/null)

# 안전한 읽기 전용 / 검증 명령은 자동 허용
if [[ "$TOOL_NAME" == "Bash" ]]; then
  SAFE_PATTERN='^(cat |ls |echo |pwd|git (log|status|diff|show|branch|remote)|yarn (lint|tsc|test|build)|npm run (lint|test|build))'
  if echo "$COMMAND" | grep -qE "$SAFE_PATTERN"; then
    echo '{"decision":"allow","reason":"읽기 전용 또는 검증 명령"}'
    exit 0
  fi
fi

exit 0
