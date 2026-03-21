#!/bin/bash
# lint-fix.sh — Edit/Write 후 자동 린트 수정
# PostToolUse hook

TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
FILE_PATH="${CLAUDE_FILE_PATH:-}"

# Edit/Write 도구가 아니면 스킵
if [[ "$TOOL_NAME" != "Edit" && "$TOOL_NAME" != "Write" ]]; then
  exit 0
fi

# .ts/.tsx/.js/.jsx 파일이 아니면 스킵
if [[ ! "$FILE_PATH" =~ \.(ts|tsx|js|jsx)$ ]]; then
  exit 0
fi

# package.json이 없으면 스킵
if [ ! -f "package.json" ]; then
  exit 0
fi

# eslint --fix 실행 (존재하면)
if command -v npx &> /dev/null && [ -f "node_modules/.bin/eslint" ]; then
  npx eslint --fix "$FILE_PATH" 2>/dev/null
fi

exit 0
