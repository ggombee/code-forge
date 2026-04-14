#!/bin/bash
# session-init.sh — 세션 시작 시 플러그인 자동 업데이트
# SessionStart 훅에서 실행됨

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
PLUGIN_JSON="$PLUGIN_ROOT/.claude-plugin/plugin.json"
CACHE_FILE="$PLUGIN_ROOT/.plugin-cache-version"

# 현재 로컬 버전
LOCAL_VERSION=$(grep -o '"version": *"[^"]*"' "$PLUGIN_JSON" | head -1 | grep -o '[0-9][0-9.]*')

# git repo가 아니면 스킵
if [ ! -d "$PLUGIN_ROOT/.git" ]; then
  exit 0
fi

cd "$PLUGIN_ROOT"

# remote 확인 (타임아웃 5초, 실패 시 무시)
if ! git fetch origin --quiet 2>/dev/null; then
  exit 0
fi

# 로컬과 리모트 비교
LOCAL_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "")
REMOTE_HEAD=$(git rev-parse origin/main 2>/dev/null || echo "")

if [ -z "$LOCAL_HEAD" ] || [ -z "$REMOTE_HEAD" ]; then
  exit 0
fi

# 이미 최신이면 스킵
if [ "$LOCAL_HEAD" = "$REMOTE_HEAD" ]; then
  # 캐시 버전 파일 갱신
  echo "$LOCAL_VERSION" > "$CACHE_FILE"
  exit 0
fi

# 로컬 변경사항이 있으면 업데이트 스킵 (사용자가 수정 중일 수 있음)
if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
  exit 0
fi

# 자동 업데이트 실행
if ! git pull origin main --ff-only --quiet 2>/dev/null; then
  # ff-only 실패 (conflict) → 강제 업데이트하지 않고 스킵
  exit 0
fi

# 업데이트 후 새 버전 확인
NEW_VERSION=$(grep -o '"version": *"[^"]*"' "$PLUGIN_JSON" | head -1 | grep -o '[0-9][0-9.]*')
PREV_VERSION="${LOCAL_VERSION}"

# 캐시 파일에 이전 버전이 있으면 그걸 사용
if [ -f "$CACHE_FILE" ]; then
  PREV_VERSION=$(cat "$CACHE_FILE" 2>/dev/null || echo "$LOCAL_VERSION")
fi

# 버전 변경 시 알림
if [ "$PREV_VERSION" != "$NEW_VERSION" ]; then
  echo "⚡ code-forge updated: v${PREV_VERSION} → v${NEW_VERSION}"

  # 최근 변경 요약 (버전 변경 커밋들)
  CHANGES=$(git log --oneline "${LOCAL_HEAD}..HEAD" --no-decorate 2>/dev/null | head -5)
  if [ -n "$CHANGES" ]; then
    echo ""
    echo "Changes:"
    echo "$CHANGES"
  fi
fi

# 캐시 버전 갱신
echo "$NEW_VERSION" > "$CACHE_FILE"

# ─────────────────────────────────────────────
# 프로젝트 에이전트 재컴파일 알림
# ─────────────────────────────────────────────

WORK_DIR_CHECK="${CLAUDE_CWD:-$(pwd)}"
LOCAL_MD="$WORK_DIR_CHECK/.claude/code-forge.local.md"

if [ -f "$LOCAL_MD" ]; then
  PROJECT_CF_VERSION=$(grep -o 'version: *[0-9][0-9.]*' "$LOCAL_MD" | head -1 | grep -o '[0-9][0-9.]*' 2>/dev/null || echo "")
  CURRENT_CF_VERSION=$(grep -o '"version": *"[^"]*"' "$PLUGIN_JSON" | head -1 | grep -o '[0-9][0-9.]*')

  if [ -n "$PROJECT_CF_VERSION" ] && [ "$PROJECT_CF_VERSION" != "$CURRENT_CF_VERSION" ]; then
    echo ""
    echo "--- code-forge updated: v${PROJECT_CF_VERSION} → v${CURRENT_CF_VERSION} ---"
    echo ""
    echo "CLAUDE.md와 AGENTS.md를 최신 버전에 맞게 업데이트합니다."
    echo "사용자에게 알리고 /setup을 실행하세요."

    # Smith 프로젝트 에이전트가 있으면 재컴파일도 안내
    if [ -d "$WORK_DIR_CHECK/.agents/agents" ]; then
      echo "프로젝트 에이전트도 재컴파일이 필요합니다: /smith-build --project"
    fi

    echo "---"
  fi
fi

# ─────────────────────────────────────────────
# 프로젝트 컨텍스트 주입 (Claude additionalContext)
# ─────────────────────────────────────────────

# 작업 디렉토리 (플러그인이 아닌 사용자 프로젝트 기준)
WORK_DIR="${CLAUDE_CWD:-$(pwd)}"

echo ""
echo "=== Project Context ==="

# Git 프로젝트 정보
if [ -d "$WORK_DIR/.git" ]; then
  PROJECT_NAME=$(basename "$WORK_DIR")
  BRANCH=$(git -C "$WORK_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
  UNCOMMITTED_COUNT=$(git -C "$WORK_DIR" status --porcelain 2>/dev/null | wc -l | tr -d ' ')

  echo "Project: $PROJECT_NAME"
  echo "Branch: $BRANCH"
  echo "Uncommitted files: $UNCOMMITTED_COUNT"

  if [ "$UNCOMMITTED_COUNT" -gt 0 ]; then
    echo "Changed files (max 10):"
    git -C "$WORK_DIR" status --porcelain 2>/dev/null | head -10 | while read -r line; do
      echo "  $line"
    done
    if [ "$UNCOMMITTED_COUNT" -gt 10 ]; then
      echo "  ... and $((UNCOMMITTED_COUNT - 10)) more"
    fi
  fi
else
  echo "Project: $(basename "$WORK_DIR") (not a git repo)"
fi

# profile.json 스택 정보
PROFILE_JSON="$WORK_DIR/.claude/profile.json"
if [ ! -f "$PROFILE_JSON" ]; then
  # .agents/ 하위도 탐색
  PROFILE_JSON="$WORK_DIR/.agents/profile.json"
fi

if [ -f "$PROFILE_JSON" ]; then
  echo ""
  echo "Stack (from profile.json):"
  # framework, styling, state 필드 파싱 (외부 도구 없이 grep 사용)
  FRAMEWORK=$(grep -o '"framework": *"[^"]*"' "$PROFILE_JSON" | grep -o '"[^"]*"$' | tr -d '"' 2>/dev/null || echo "")
  STYLING=$(grep -o '"styling": *"[^"]*"' "$PROFILE_JSON" | grep -o '"[^"]*"$' | tr -d '"' 2>/dev/null || echo "")
  STATE=$(grep -o '"state": *"[^"]*"' "$PROFILE_JSON" | grep -o '"[^"]*"$' | tr -d '"' 2>/dev/null || echo "")
  TESTING=$(grep -o '"testing": *"[^"]*"' "$PROFILE_JSON" | grep -o '"[^"]*"$' | tr -d '"' 2>/dev/null || echo "")

  [ -n "$FRAMEWORK" ] && echo "  framework: $FRAMEWORK"
  [ -n "$STYLING" ]   && echo "  styling: $STYLING"
  [ -n "$STATE" ]     && echo "  state: $STATE"
  [ -n "$TESTING" ]   && echo "  testing: $TESTING"
fi

echo "======================="

# ─────────────────────────────────────────────
# notepad.md 주입 (세션 간 작업 메모, 옵션)
# 계약: docs/contracts/state-schema.md §3
# ─────────────────────────────────────────────

NOTEPAD_FILE="$WORK_DIR/.claude/state/notepad.md"
if [ -f "$NOTEPAD_FILE" ]; then
  NOTEPAD_SIZE=$(wc -l < "$NOTEPAD_FILE" 2>/dev/null || echo 0)
  if [ "$NOTEPAD_SIZE" -gt 0 ] && [ "$NOTEPAD_SIZE" -le 100 ]; then
    echo ""
    echo "=== Session Notepad (.claude/state/notepad.md) ==="
    cat "$NOTEPAD_FILE"
    echo "=== /Notepad ==="
  elif [ "$NOTEPAD_SIZE" -gt 100 ]; then
    echo ""
    echo "[code-forge] notepad.md ${NOTEPAD_SIZE}줄 초과 — 앞 100줄만 주입"
    echo "=== Session Notepad (truncated) ==="
    head -100 "$NOTEPAD_FILE"
    echo "=== /Notepad ==="
  fi
fi

# ─────────────────────────────────────────────
# REFLECT flag 감지 (quality-gate.sh 실패 연동)
# 계약: docs/contracts/state-schema.md §1
# ─────────────────────────────────────────────

FLAG_FILE="$WORK_DIR/.claude/state/reflect.flag"

# 구버전 경로 migration (.claude/temp/reflect-required.flag → .claude/state/reflect.flag)
LEGACY_FLAG="$WORK_DIR/.claude/temp/reflect-required.flag"
if [ -f "$LEGACY_FLAG" ] && [ ! -f "$FLAG_FILE" ]; then
  mkdir -p "$WORK_DIR/.claude/state" 2>/dev/null
  mv "$LEGACY_FLAG" "$FLAG_FILE" 2>/dev/null
fi

if [ -f "$FLAG_FILE" ]; then
  # 사용자 ack 확인 — 있으면 주입 스킵
  if grep -q "^ack:" "$FLAG_FILE" 2>/dev/null; then
    ACK_REASON=$(grep "^ack:" "$FLAG_FILE" | head -1 | sed 's/^ack: *//')
    echo ""
    echo "[code-forge] REFLECT flag ack됨: $ACK_REASON"
  else
    FLAG_SUMMARY=$(head -15 "$FLAG_FILE" 2>/dev/null || echo "[flag read error]")
    cat <<REFLECT_EOF

================================================
[REFLECT REQUIRED] 이전 턴 품질 검증 실패
thinking-model.md ADAPT 단계를 우선 실행:
  1. 실패한 파일 Read → 증상 파악
  2. 근인 분석 → 교정안 수립
  3. 수정 → quality-gate 재실행
  4. 통과 시 flag 자동 삭제

우회: rm $FLAG_FILE
또는 본문에 'ack: <이유>' 추가

--- flag 요약 ---
$FLAG_SUMMARY
================================================
REFLECT_EOF
  fi
fi

# quality.jsonl GC (7일 경과 엔트리 정리, 10MB 초과 시 트리밍)
# 계약: docs/contracts/state-schema.md §2
JSONL_FILE="$WORK_DIR/.claude/state/quality.jsonl"
if [ -f "$JSONL_FILE" ]; then
  SIZE=$(wc -c < "$JSONL_FILE" 2>/dev/null || echo 0)
  # 10MB = 10485760
  if [ "$SIZE" -gt 10485760 ]; then
    # 뒤쪽 절반 유지
    TOTAL=$(wc -l < "$JSONL_FILE")
    HALF=$((TOTAL / 2))
    tail -n "$HALF" "$JSONL_FILE" > "$JSONL_FILE.tmp" && mv "$JSONL_FILE.tmp" "$JSONL_FILE"
  fi
  # 7일 경과 GC (best-effort, 포맷 가정)
  CUTOFF=$(date -u -v-7d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d '7 days ago' +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null)
  if [ -n "$CUTOFF" ]; then
    awk -v cutoff="$CUTOFF" 'match($0, /"ts":"([^"]+)"/, a) { if (a[1] >= cutoff) print }' "$JSONL_FILE" > "$JSONL_FILE.tmp" 2>/dev/null && mv "$JSONL_FILE.tmp" "$JSONL_FILE"
  fi
fi
