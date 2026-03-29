#!/bin/bash
# guard.sh — Bash 실행 전 위험 명령 차단
# PreToolUse hook (Bash)

# stdin JSON 파싱 (Claude Code hooks는 stdin으로 JSON 전달)
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('command', ''))
except:
    print('')
" 2>/dev/null)

# 폴백: 환경변수 방식 (구버전 호환)
if [ -z "$COMMAND" ]; then
  COMMAND="${TOOL_INPUT_COMMAND:-}"
fi
if [ -z "$COMMAND" ] && [ -n "$TOOL_INPUT" ]; then
  COMMAND=$(echo "$TOOL_INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"command"[[:space:]]*:[[:space:]]*"//' | sed 's/"$//')
fi
[ -z "$COMMAND" ] && exit 0

if echo "$COMMAND" | grep -qE 'git\s+add\s+(-A|--all|\.)(\s|$)'; then
  echo "BLOCKED: 'git add .' / 'git add -A' 금지. 파일을 명시적으로 지정하세요." && exit 2
fi
if echo "$COMMAND" | grep -qE 'git\s+push\s+.*(--force|--force-with-lease|-f)(\s|$)'; then
  echo "BLOCKED: force push 금지." && exit 2
fi
if echo "$COMMAND" | grep -qE 'git\s+commit\s+.*--no-verify'; then
  echo "BLOCKED: '--no-verify' 금지." && exit 2
fi
if echo "$COMMAND" | grep -qE 'git\s+stash\s+(drop|clear)'; then
  echo "BLOCKED: 'git stash drop/clear' 금지." && exit 2
fi
if echo "$COMMAND" | grep -qE '(yarn|npm|pnpm)\s+publish'; then
  echo "BLOCKED: 패키지 배포 금지." && exit 2
fi
if echo "$COMMAND" | grep -qE 'rm\s+(-rf|-fr)\s+(/|~|\$HOME)(\s|$)'; then
  echo "BLOCKED: 루트/홈 삭제 금지." && exit 2
fi
if echo "$COMMAND" | grep -qiE 'DROP\s+(TABLE|DATABASE)'; then
  echo "BLOCKED: DROP TABLE/DATABASE 금지." && exit 2
fi
if echo "$COMMAND" | grep -qE 'git\s+reset\s+--hard'; then
  echo "BLOCKED: 'git reset --hard' 금지." && exit 2
fi
if echo "$COMMAND" | grep -qE 'git\s+(checkout|restore)\s+\.(\s|$)'; then
  echo "BLOCKED: 모든 변경사항 되돌리기 금지." && exit 2
fi
exit 0
