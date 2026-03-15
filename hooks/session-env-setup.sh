#!/bin/bash
# SessionStart 훅: 프로젝트 스크립트 경로 환경변수 설정
# 프로젝트 스코프 우선, 없으면 사용자 스코프로 폴백

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# 프로젝트 스코프 scripts 경로
PROJECT_SCRIPTS="${SCRIPT_DIR}/scripts"

# 사용자 스코프 scripts 경로
USER_SCRIPTS="${HOME}/.claude/scripts"

# 프로젝트 스코프 우선
if [ -d "${PROJECT_SCRIPTS}" ]; then
  SCRIPTS_ROOT="${PROJECT_SCRIPTS}"
elif [ -d "${USER_SCRIPTS}" ]; then
  SCRIPTS_ROOT="${USER_SCRIPTS}"
else
  SCRIPTS_ROOT=""
fi

# 환경변수 설정 (CLAUDE_ENV_FILE이 있으면 사용)
if [ -n "${CLAUDE_ENV_FILE}" ] && [ -n "${SCRIPTS_ROOT}" ]; then
  echo "CLAUDE_SCRIPTS_ROOT=${SCRIPTS_ROOT}" >> "${CLAUDE_ENV_FILE}"
fi
