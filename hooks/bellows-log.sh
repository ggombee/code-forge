#!/bin/bash
# Bellows — 에이전트/스킬 사용 로깅
# PostToolUse에서 실행. Agent, Skill 도구 호출을 usage.jsonl에 기록.
# v2: session_id + model + duration_ms + success 필드 추가 (forge-glow L3 연동)

TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
TOOL_INPUT="${CLAUDE_TOOL_INPUT:-}"
TOOL_RESPONSE="${CLAUDE_TOOL_RESPONSE:-}"

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
SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
MODEL="${CLAUDE_MODEL:-unknown}"

# 소스 판별
SOURCE="plugin"
if [[ "$TOOL_NAME" == "Agent" ]]; then
  _AGENT_NAME=$(echo "$TOOL_INPUT" | grep -o '"subagent_type"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"//')
  if [[ "$_AGENT_NAME" == "${PROJECT_NAME}-"* ]]; then
    SOURCE="local"
  fi
fi

# duration 근사 (이전 Bellows 호출과의 간격)
SESSION_MARKER="$LOG_DIR/.session-start-${SESSION_ID}"
DURATION_MS=0
if [[ -f "$SESSION_MARKER" ]]; then
  LAST=$(cat "$SESSION_MARKER" 2>/dev/null || echo "")
  if [[ -n "$LAST" ]]; then
    NOW_SEC=$(date +%s)
    DURATION_MS=$(( (NOW_SEC - LAST) * 1000 ))
  fi
fi
date +%s > "$SESSION_MARKER"

# success 판단 (TOOL_RESPONSE에 "error"가 없으면 true로 가정)
SUCCESS="true"
if [[ -n "$TOOL_RESPONSE" ]] && echo "$TOOL_RESPONSE" | grep -qiE '"(is_?error|error)"[[:space:]]*:[[:space:]]*true'; then
  SUCCESS="false"
fi

# JSON 이스케이프 헬퍼
esc() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr -d '\n'
}

if [[ "$TOOL_NAME" == "Agent" ]]; then
  AGENT_TYPE=$(echo "$TOOL_INPUT" | grep -o '"subagent_type"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"subagent_type"[[:space:]]*:[[:space:]]*"//' | sed 's/"//')
  AGENT_DESC=$(echo "$TOOL_INPUT" | grep -o '"description"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"description"[[:space:]]*:[[:space:]]*"//' | sed 's/"//')
  ENTRY="{\"ts\":\"$TIMESTAMP\",\"sid\":\"$(esc "$SESSION_ID")\",\"type\":\"agent\",\"name\":\"$(esc "${AGENT_TYPE:-general-purpose}")\",\"desc\":\"$(esc "${AGENT_DESC:-}")\",\"model\":\"$(esc "$MODEL")\",\"duration_ms\":$DURATION_MS,\"success\":$SUCCESS,\"source\":\"$SOURCE\",\"project\":\"$(esc "$PROJECT_NAME")\"}"
elif [[ "$TOOL_NAME" == "Skill" ]]; then
  SKILL_NAME=$(echo "$TOOL_INPUT" | grep -o '"skill"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"skill"[[:space:]]*:[[:space:]]*"//' | sed 's/"//')
  ENTRY="{\"ts\":\"$TIMESTAMP\",\"sid\":\"$(esc "$SESSION_ID")\",\"type\":\"skill\",\"name\":\"$(esc "${SKILL_NAME:-unknown}")\",\"model\":\"$(esc "$MODEL")\",\"duration_ms\":$DURATION_MS,\"success\":$SUCCESS,\"source\":\"$SOURCE\",\"project\":\"$(esc "$PROJECT_NAME")\"}"
fi

echo "$ENTRY" >> "$LOG_FILE"

# usage.jsonl 30일 GC (성능상 매 호출 아닌 확률적 — 100회 중 1회)
if [ $(( RANDOM % 100 )) -eq 0 ]; then
  CUTOFF=$(date -u -v-30d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d '30 days ago' +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null)
  if [ -n "$CUTOFF" ]; then
    awk -v c="$CUTOFF" 'match($0, /"ts":"([^"]+)"/, a) { if (a[1] >= c) print }' "$LOG_FILE" > "$LOG_FILE.tmp" 2>/dev/null && mv "$LOG_FILE.tmp" "$LOG_FILE"
  fi
fi

exit 0
