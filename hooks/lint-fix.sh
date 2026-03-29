#!/bin/bash
# lint-fix.sh — Edit/Write/MultiEdit 후 자동 ESLint --fix + Prettier
# PostToolUse hook (Edit|Write|MultiEdit)

FILE_PATH="${TOOL_INPUT_FILE_PATH:-}"
if [ -z "$FILE_PATH" ] && [ -n "$TOOL_INPUT" ]; then
  FILE_PATH=$(echo "$TOOL_INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//' | sed 's/"$//')
fi
[ -z "$FILE_PATH" ] && exit 0

case "$FILE_PATH" in
  *.js|*.ts|*.jsx|*.tsx|*.vue|*.css|*.scss|*.json) ;;
  *) exit 0 ;;
esac

[ -f "$FILE_PATH" ] || exit 0

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

ESLINT_BIN=""
if [ -f "$PROJECT_ROOT/node_modules/.bin/eslint" ]; then
  ESLINT_BIN="$PROJECT_ROOT/node_modules/.bin/eslint"
elif command -v npx &>/dev/null; then
  for cfg in .eslintrc.js .eslintrc.json .eslintrc.cjs .eslintrc.yml .eslintrc.yaml eslint.config.js eslint.config.mjs eslint.config.ts; do
    [ -f "$PROJECT_ROOT/$cfg" ] && ESLINT_BIN="npx eslint" && break
  done
fi

if [ -n "$ESLINT_BIN" ]; then
  $ESLINT_BIN --fix --quiet "$FILE_PATH" 2>/dev/null
  REMAINING=$($ESLINT_BIN --quiet "$FILE_PATH" 2>&1)
  [ -n "$REMAINING" ] && echo "$REMAINING" | head -10 >&2
fi

PRETTIER_BIN=""
if [ -f "$PROJECT_ROOT/node_modules/.bin/prettier" ]; then
  PRETTIER_BIN="$PROJECT_ROOT/node_modules/.bin/prettier"
elif command -v npx &>/dev/null; then
  for cfg in .prettierrc .prettierrc.js .prettierrc.json .prettierrc.yml prettier.config.js prettier.config.cjs; do
    [ -f "$PROJECT_ROOT/$cfg" ] && PRETTIER_BIN="npx prettier" && break
  done
fi

[ -n "$PRETTIER_BIN" ] && $PRETTIER_BIN --write --log-level=silent "$FILE_PATH" 2>/dev/null

exit 0
