#!/bin/bash
# write-guard.sh — Write 전 민감 파일 차단
# PreToolUse hook (Write)

FILE_PATH="${TOOL_INPUT_FILE_PATH:-}"
if [ -z "$FILE_PATH" ] && [ -n "$TOOL_INPUT" ]; then
  FILE_PATH=$(echo "$TOOL_INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//' | sed 's/"$//')
fi
[ -z "$FILE_PATH" ] && exit 0

BASENAME=$(basename "$FILE_PATH")
case "$BASENAME" in
  .env|.env.local|.env.production|.env.staging)
    echo "BLOCKED: .env 파일 직접 생성 금지." && exit 2 ;;
  *.pem|*.key|*.p12|*.pfx)
    echo "BLOCKED: 인증서/키 파일 생성 금지." && exit 2 ;;
  credentials.json|secrets.json|*secret*|*credential*)
    echo "BLOCKED: 자격증명 파일 생성 금지." && exit 2 ;;
esac
exit 0
