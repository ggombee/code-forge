#!/bin/bash
# skill-dedup.sh — 새 SKILL.md 생성 시 기존 스킬과 중복 검사
# PreToolUse (Write) 훅에서 실행. SKILL.md 파일에만 반응.

FILE_PATH="${TOOL_INPUT_FILE_PATH:-}"
if [ -z "$FILE_PATH" ] && [ -n "${TOOL_INPUT:-}" ]; then
  FILE_PATH=$(echo "$TOOL_INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"//' | sed 's/"$//')
fi

# SKILL.md 파일이 아니면 스킵
if [[ "$FILE_PATH" != *"/SKILL.md" && "$FILE_PATH" != *"/skills/"* ]]; then
  exit 0
fi

# 플러그인 스킬 디렉토리가 아니고, 프로젝트 로컬 스킬도 아니면 스킵
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
WORK_DIR="${CLAUDE_CWD:-$(pwd)}"

# 기존 스킬 목록 수집 (이름 + 설명)
EXISTING_SKILLS=""

# 플러그인 스킬
if [ -d "$PLUGIN_ROOT/skills" ]; then
  for skill_file in "$PLUGIN_ROOT"/skills/*/SKILL.md; do
    if [ -f "$skill_file" ]; then
      SKILL_NAME=$(grep -m1 'name:' "$skill_file" | sed 's/name:[[:space:]]*//')
      SKILL_DESC=$(grep -m1 'description:' "$skill_file" | sed 's/description:[[:space:]]*//' | head -c 100)
      EXISTING_SKILLS="${EXISTING_SKILLS}${SKILL_NAME}: ${SKILL_DESC}\n"
    fi
  done
fi

# 프로젝트 로컬 스킬
if [ -d "$WORK_DIR/.claude/skills" ]; then
  for skill_file in "$WORK_DIR"/.claude/skills/*/SKILL.md; do
    if [ -f "$skill_file" ]; then
      SKILL_NAME=$(grep -m1 'name:' "$skill_file" | sed 's/name:[[:space:]]*//')
      SKILL_DESC=$(grep -m1 'description:' "$skill_file" | sed 's/description:[[:space:]]*//' | head -c 100)
      EXISTING_SKILLS="${EXISTING_SKILLS}${SKILL_NAME}: ${SKILL_DESC}\n"
    fi
  done
fi

# 기존 스킬이 없으면 스킵 (첫 스킬)
if [ -z "$EXISTING_SKILLS" ]; then
  exit 0
fi

# 기존 스킬 목록을 환경변수로 전달 (prompt 훅에서 참조)
echo "$EXISTING_SKILLS" > "$HOME/.code-forge/.existing-skills-cache"
exit 0
