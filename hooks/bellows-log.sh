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
PROJECT_DIR="${CLAUDE_CWD:-$(pwd)}"
PROJECT_NAME=$(basename "$PROJECT_DIR")

# 소스 판별: 에이전트 이름에 프로젝트 접두사가 있으면 local
SOURCE="plugin"
if [[ "$TOOL_NAME" == "Agent" ]]; then
  _AGENT_NAME=$(echo "$TOOL_INPUT" | grep -o '"subagent_type"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"//')
  _PROJECT_NAME=$(basename "$PROJECT_DIR")
  if [[ "$_AGENT_NAME" == "${_PROJECT_NAME}-"* ]]; then
    SOURCE="local"
  fi
fi

# 세션 시작 시간으로 duration 근사치 계산
SESSION_MARKER="$LOG_DIR/.session-start"
DURATION_MS=""
if [[ -f "$SESSION_MARKER" ]]; then
  SESSION_START=$(cat "$SESSION_MARKER" 2>/dev/null || echo "")
  if [[ -n "$SESSION_START" ]]; then
    NOW_SEC=$(date +%s)
    DURATION_MS=$(( (NOW_SEC - SESSION_START) * 1000 ))
  fi
fi
# 다음 호출을 위해 현재 시간 기록
date +%s > "$SESSION_MARKER"

if [[ "$TOOL_NAME" == "Agent" ]]; then
  AGENT_TYPE=$(echo "$TOOL_INPUT" | grep -o '"subagent_type"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"subagent_type"[[:space:]]*:[[:space:]]*"//' | sed 's/"//')
  AGENT_DESC=$(echo "$TOOL_INPUT" | grep -o '"description"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"description"[[:space:]]*:[[:space:]]*"//' | sed 's/"//')
  ENTRY="{\"ts\":\"$TIMESTAMP\",\"type\":\"agent\",\"name\":\"${AGENT_TYPE:-general-purpose}\",\"desc\":\"${AGENT_DESC:-}\",\"source\":\"$SOURCE\",\"project\":\"$PROJECT_NAME\"}"
elif [[ "$TOOL_NAME" == "Skill" ]]; then
  SKILL_NAME=$(echo "$TOOL_INPUT" | grep -o '"skill"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"skill"[[:space:]]*:[[:space:]]*"//' | sed 's/"//')
  ENTRY="{\"ts\":\"$TIMESTAMP\",\"type\":\"skill\",\"name\":\"${SKILL_NAME:-unknown}\",\"source\":\"$SOURCE\",\"project\":\"$PROJECT_NAME\"}"
fi

echo "$ENTRY" >> "$LOG_FILE"
exit 0
