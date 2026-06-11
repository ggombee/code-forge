#!/bin/bash
# write-guard.sh — Write 전 민감 파일 차단
# PreToolUse hook (Write)

# stdin JSON 파싱 (Claude Code hooks는 stdin으로 JSON 전달 — guard.sh와 동일 패턴)
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('file_path', ''))
except:
    print('')
" 2>/dev/null)

# 폴백: 환경변수 방식 (구버전 호환)
if [ -z "$FILE_PATH" ]; then
  FILE_PATH="${TOOL_INPUT_FILE_PATH:-}"
fi
if [ -z "$FILE_PATH" ] && [ -n "${TOOL_INPUT:-}" ]; then
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
