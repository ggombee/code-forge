#!/bin/bash
# subagent-stop.sh — 서브에이전트 완료 훅
#   1. 구현 에이전트(implementor/deep-executor/build-fixer) 완료 시 tsc 검증
#   2. bellows v2.5 agent_end 이벤트 기록 — agent_transcript의 첫/마지막 ts 차이로 duration 계산
#
# SubagentStop 페이로드에 duration_ms는 없지만 agent_transcript_path가 제공되므로
# transcript의 타임스탬프 범위로 자체 계산 (훅 간 상태 공유 불필요).

INPUT=$(cat)

# ── 1. 필드 추출 ──────────────────────────────────────────────
parse_field() {
  local key="$1"
  echo "$INPUT" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('$key', ''))
except:
    print('')
" 2>/dev/null
}

AGENT_TYPE=$(parse_field "agent_type")
AGENT_ID=$(parse_field "agent_id")
SESSION_ID=$(parse_field "session_id")
AGENT_TRANSCRIPT=$(parse_field "agent_transcript_path")

# ── 2. bellows v2.5 — agent_end 이벤트 ────────────────────────
LOG_DIR="$HOME/.code-forge"
LOG_FILE="$LOG_DIR/usage.jsonl"
mkdir -p "$LOG_DIR" 2>/dev/null

if [ -n "$AGENT_ID" ] && [ -n "$SESSION_ID" ]; then
  # agent_transcript의 첫/마지막 메시지 타임스탬프로 duration 계산
  DURATION_MS=0
  if [ -n "$AGENT_TRANSCRIPT" ] && [ -f "$AGENT_TRANSCRIPT" ]; then
    DURATION_MS=$(python3 <<PYEOF 2>/dev/null
import json, sys
try:
    first_ts = last_ts = None
    with open("$AGENT_TRANSCRIPT") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            # timestamp 후보 필드들 (Claude Code transcript 표준)
            ts = obj.get("timestamp") or obj.get("ts")
            if not ts:
                continue
            if first_ts is None:
                first_ts = ts
            last_ts = ts
    if first_ts and last_ts and first_ts != last_ts:
        import datetime
        def to_ms(s):
            s = s.replace("Z", "+00:00")
            return int(datetime.datetime.fromisoformat(s).timestamp() * 1000)
        print(to_ms(last_ts) - to_ms(first_ts))
    else:
        print(0)
except Exception:
    print(0)
PYEOF
)
    DURATION_MS="${DURATION_MS:-0}"
  fi

  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  PROJECT_NAME=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")

  ESCAPED_TYPE=$(printf '%s' "${AGENT_TYPE:-unknown}" | sed 's/\\/\\\\/g; s/"/\\"/g')
  ESCAPED_PROJECT=$(printf '%s' "$PROJECT_NAME" | sed 's/\\/\\\\/g; s/"/\\"/g')

  echo "{\"ts\":\"$TIMESTAMP\",\"sid\":\"$SESSION_ID\",\"type\":\"agent_end\",\"name\":\"$ESCAPED_TYPE\",\"agent_id\":\"$AGENT_ID\",\"duration_ms\":$DURATION_MS,\"project\":\"$ESCAPED_PROJECT\"}" >> "$LOG_FILE"
fi

# ── 3. 구현 에이전트 tsc 검증 (기존 로직 보존) ─────────────────
if [[ "$AGENT_TYPE" =~ ^(implementor|deep-executor|build-fixer)$ ]]; then
  PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
  CHANGED=$(git diff --name-only HEAD 2>/dev/null | grep -E '\.(ts|tsx|js|jsx)$' | head -10)

  if [ -n "$CHANGED" ] && [ -f "$PROJECT_ROOT/node_modules/.bin/tsc" ]; then
    if ! TSC_OUT=$("$PROJECT_ROOT/node_modules/.bin/tsc" --noEmit --pretty false 2>&1 | head -10); then
      echo "SubagentStop [${AGENT_TYPE}] TypeScript 오류:"
      echo "$TSC_OUT"
    fi
  fi
fi

exit 0
