#!/bin/bash
# guard.sh — Bash 실행 전 위험 명령 차단
# PreToolUse hook

COMMAND="$@"

DANGEROUS_PATTERNS=(
  "git push.*--force"
  "git reset.*--hard"
  "rm -rf /"
  "rm -rf \.\."
  "DROP TABLE"
  "DELETE FROM.*WHERE 1"
  "--no-verify"
  "dangerouslyDisableSandbox"
  "curl.*|.*sh"
  "wget.*|.*sh"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qEi "$pattern"; then
    echo "BLOCKED: 위험한 명령이 감지되었습니다: $COMMAND"
    echo "패턴: $pattern"
    exit 1
  fi
done

exit 0
