#!/bin/bash
# Bellows — 에이전트/스킬 사용 로깅
# PostToolUse에서 실행. Agent, Skill 도구 호출을 usage.jsonl에 기록.

TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"

# Agent 또는 Skill 호출만 기록
if [[ "$TOOL_NAME" != "Agent" && "$TOOL_NAME" != "Skill" ]]; then
  exit 0
fi

LOG_DIR="$HOME/.code-forge"
LOG_FILE="$LOG_DIR/usage.jsonl"
mkdir -p "$LOG_DIR"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
PROJECT_DIR=$(pwd)
PROJECT_NAME=$(basename "$PROJECT_DIR")

if [[ "$TOOL_NAME" == "Agent" ]]; then
  AGENT_TYPE=$(echo "$TOOL_INPUT" | grep -o '"subagent_type"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"subagent_type"[[:space:]]*:[[:space:]]*"//' | sed 's/"//')
  ENTRY="{\"ts\":\"$TIMESTAMP\",\"type\":\"agent\",\"name\":\"${AGENT_TYPE:-general-purpose}\",\"project\":\"$PROJECT_NAME\"}"
elif [[ "$TOOL_NAME" == "Skill" ]]; then
  SKILL_NAME=$(echo "$TOOL_INPUT" | grep -o '"skill"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"skill"[[:space:]]*:[[:space:]]*"//' | sed 's/"//')
  ENTRY="{\"ts\":\"$TIMESTAMP\",\"type\":\"skill\",\"name\":\"${SKILL_NAME:-unknown}\",\"project\":\"$PROJECT_NAME\"}"
fi

echo "$ENTRY" >> "$LOG_FILE"
exit 0
