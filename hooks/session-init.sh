#!/bin/bash
# session-init.sh — 세션 시작 훅 (SessionStart)
#   1) 플러그인 자동 업데이트 (dev 레포 git 설치본 한정 — 서브셸 격리)
#   2) 프로젝트 컨텍스트/notepad/progress/REFLECT 주입 (★항상 실행)
#
# 2026-06-12 수리 (FORGE_MASTERPLAN 3단계, must_fix 3):
#   마켓플레이스 설치본(캐시)엔 .git이 없는데 구버전은 .git 부재 시 3줄 만에 exit 0 —
#   아래 주입 블록 전체가 배포 환경에서 역사상 한 번도 발화하지 않았다 (이번 조사 최대 발견).
#   업데이트 로직의 어떤 실패/조기 종료도 주입을 막지 않도록 서브셸 함수로 격리.

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
PLUGIN_JSON="$PLUGIN_ROOT/.claude-plugin/plugin.json"
CACHE_FILE="$PLUGIN_ROOT/.plugin-cache-version"

# 현재 로컬 버전
LOCAL_VERSION=$(grep -o '"version": *"[^"]*"' "$PLUGIN_JSON" | head -1 | grep -o '[0-9][0-9.]*')

# SessionStart stdin 페이로드 (transcript_path 등 — tty면 수동 실행이므로 스킵)
HOOK_INPUT=""
if [ ! -t 0 ]; then
  HOOK_INPUT=$(cat 2>/dev/null || true)
fi

# ─────────────────────────────────────────────
# 1. 플러그인 자동 업데이트 — 서브셸 ( ) 격리:
#    exit는 서브셸만 끝내고, cd도 본 셸에 누출되지 않는다
# ─────────────────────────────────────────────
run_auto_update() (
  # git repo가 아니면 스킵 (마켓플레이스 캐시 설치본 — 업데이트는 plugin update가 담당)
  [ -d "$PLUGIN_ROOT/.git" ] || exit 0

  cd "$PLUGIN_ROOT"

  # remote 확인 (실패 시 무시)
  git fetch origin --quiet 2>/dev/null || exit 0

  LOCAL_HEAD=$(git rev-parse HEAD 2>/dev/null || echo "")
  REMOTE_HEAD=$(git rev-parse origin/main 2>/dev/null || echo "")
  { [ -z "$LOCAL_HEAD" ] || [ -z "$REMOTE_HEAD" ]; } && exit 0

  # 이미 최신이면 캐시 버전만 갱신
  if [ "$LOCAL_HEAD" = "$REMOTE_HEAD" ]; then
    echo "$LOCAL_VERSION" > "$CACHE_FILE"
    exit 0
  fi

  # 로컬 변경사항이 있으면 업데이트 스킵 (사용자가 수정 중일 수 있음)
  if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
    exit 0
  fi

  # ff-only 실패 (conflict) → 강제 업데이트하지 않고 스킵
  git pull origin main --ff-only --quiet 2>/dev/null || exit 0

  NEW_VERSION=$(grep -o '"version": *"[^"]*"' "$PLUGIN_JSON" | head -1 | grep -o '[0-9][0-9.]*')
  PREV_VERSION="${LOCAL_VERSION}"
  if [ -f "$CACHE_FILE" ]; then
    PREV_VERSION=$(cat "$CACHE_FILE" 2>/dev/null || echo "$LOCAL_VERSION")
  fi

  if [ "$PREV_VERSION" != "$NEW_VERSION" ]; then
    echo "⚡ code-forge updated: v${PREV_VERSION} → v${NEW_VERSION}"
    CHANGES=$(git log --oneline "${LOCAL_HEAD}..HEAD" --no-decorate 2>/dev/null | head -5)
    if [ -n "$CHANGES" ]; then
      echo ""
      echo "Changes:"
      echo "$CHANGES"
    fi
  fi

  echo "$NEW_VERSION" > "$CACHE_FILE"
)
run_auto_update || true

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
      echo "프로젝트 에이전트도 재컴파일이 필요합니다: /code-forge:smith-build --project"
    fi

    echo "---"
  fi
fi

# ─────────────────────────────────────────────
# 프로젝트 컨텍스트 주입 (Claude additionalContext)
# ─────────────────────────────────────────────
# 디폴트: full — git changed files + stack 정보까지 (현행 유지)
# brief 모드 (opt-in): FORGE_INIT_BRIEF=1 시 project + branch + uncommitted count만
# (2026-05-17 redesign G2: opt-in brief 추가, 정보 자체는 보존)

# 작업 디렉토리 (플러그인이 아닌 사용자 프로젝트 기준)
WORK_DIR="${CLAUDE_CWD:-$(pwd)}"
FORGE_BRIEF="${FORGE_INIT_BRIEF:-0}"

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

  if [ "$UNCOMMITTED_COUNT" -gt 0 ] && [ "$FORGE_BRIEF" != "1" ]; then
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

# profile.json 스택 정보 (brief 모드에서 스킵 — `/start` 진입 시 lazy load)
if [ "$FORGE_BRIEF" != "1" ]; then
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
# progress.md 주입 (작업 이어가기, brief 모드에서도 출력)
# 계약: docs/contracts/state-schema.md §4 (2026-05-17 redesign G3 신설)
# /start 스킬이 작업 시작 시 자동 write. 세션 끊겨도 다음 세션이 이어 받음.
# ─────────────────────────────────────────────

PROGRESS_FILE="$WORK_DIR/.claude/state/progress.md"
if [ -f "$PROGRESS_FILE" ]; then
  PROGRESS_SIZE=$(wc -l < "$PROGRESS_FILE" 2>/dev/null || echo 0)
  if [ "$PROGRESS_SIZE" -gt 0 ] && [ "$PROGRESS_SIZE" -le 80 ]; then
    echo ""
    echo "=== Active Progress (.claude/state/progress.md) ==="
    cat "$PROGRESS_FILE"
    echo "=== /Progress ==="
    # 미결 질문(⚠️) 카운트 — 사용자 인지 강화 (2026-05-20 G3.5)
    PENDING_Q=$(grep -c '⚠️' "$PROGRESS_FILE" 2>/dev/null || echo 0)
    [ "${PENDING_Q:-0}" -gt 0 ] && echo "[code-forge] ⚠️  미결 질문 ${PENDING_Q}개 — 답변 시 다음 작업 사이클 진입"
  elif [ "$PROGRESS_SIZE" -gt 80 ]; then
    echo ""
    echo "[code-forge] progress.md ${PROGRESS_SIZE}줄 — 마지막 80줄만 주입 (가장 최근 작업)"
    echo "=== Active Progress (tail 80) ==="
    tail -80 "$PROGRESS_FILE"
    echo "=== /Progress ==="
    PENDING_Q=$(grep -c '⚠️' "$PROGRESS_FILE" 2>/dev/null || echo 0)
    [ "${PENDING_Q:-0}" -gt 0 ] && echo "[code-forge] ⚠️  전체 progress.md에 미결 질문 ${PENDING_Q}개 — \`grep '⚠️' .claude/state/progress.md\` 로 확인"
  fi
else
  # progress.md 없음 — 정상 상태, 짧은 안내 (2026-05-20 G3.5b)
  if [ -d "$WORK_DIR/.git" ]; then
    echo ""
    echo "[code-forge] 진행 중인 작업 없음 — \`/start <ticket>\` 으로 시작 시 .claude/state/progress.md 자동 생성"
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
  elif FLAG_MTIME=$(stat -f %m "$FLAG_FILE" 2>/dev/null || stat -c %Y "$FLAG_FILE" 2>/dev/null || echo 0) \
    && [ "$FLAG_MTIME" -gt 0 ] && [ $(( $(date +%s) - FLAG_MTIME )) -gt 259200 ]; then
    # 72시간 넘게 방치된 flag — 33줄 전체 대신 1줄 축약 (자동 삭제는 하지 않음)
    FLAG_AGE_DAYS=$(( ( $(date +%s) - FLAG_MTIME ) / 86400 ))
    echo ""
    echo "[code-forge] ⚠️ REFLECT flag ${FLAG_AGE_DAYS}일째 방치 — 품질 검증 실패가 미해소 상태. 재검증(파일 수정 후 턴 종료) 또는 'ack: <이유>' / rm $FLAG_FILE 로 정리 권장"
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

# Whetstone 초안 대기 보고 (1줄 — state-schema §7, 마스터플랜 5단계. 채택은 사람이)
WHET_DIR="$WORK_DIR/.claude/state/whetstone"
if [ -d "$WHET_DIR" ]; then
  WHET_DRAFTS=$(grep -l '^status: draft' "$WHET_DIR"/*.md 2>/dev/null | wc -l | tr -d ' ')
  if [ "${WHET_DRAFTS:-0}" -gt 0 ]; then
    echo ""
    echo "[code-forge] Whetstone 규칙 초안 ${WHET_DRAFTS}건 대기 — /forge-status로 검토 (status를 accepted/rejected로)"
  fi
fi

# quality.jsonl GC (7일 경과 엔트리 → archive 이동, 10MB 초과 시 앞쪽 절반 archive)
# 계약: docs/contracts/state-schema.md §2
# 2026-06-12 수리 2건:
#   - 3-인자 match()는 gawk 전용 — macOS BSD awk에서 매번 에러로 GC가 영구 무동작이었음 → POSIX match+substr
#   - 삭제 → quality.archive.jsonl append로 변경: 반복 패턴 히스토리는 Whetstone(마스터플랜 5단계)의
#     입력 데이터라 유실 금지 (정보보존 원칙). 활성 파일만 가볍게 유지
JSONL_FILE="$WORK_DIR/.claude/state/quality.jsonl"
ARCHIVE_FILE="$WORK_DIR/.claude/state/quality.archive.jsonl"
if [ -f "$JSONL_FILE" ]; then
  SIZE=$(wc -c < "$JSONL_FILE" 2>/dev/null || echo 0)
  # 10MB = 10485760
  if [ "$SIZE" -gt 10485760 ]; then
    # 앞쪽 절반 archive, 뒤쪽 절반 유지
    TOTAL=$(wc -l < "$JSONL_FILE")
    HALF=$((TOTAL / 2))
    head -n "$((TOTAL - HALF))" "$JSONL_FILE" >> "$ARCHIVE_FILE" 2>/dev/null || true
    tail -n "$HALF" "$JSONL_FILE" > "$JSONL_FILE.tmp" && mv "$JSONL_FILE.tmp" "$JSONL_FILE"
  fi
  # 7일 경과 → archive (best-effort, 포맷 가정. ts 없는 줄도 archive로 — 유실 0)
  CUTOFF=$(date -u -v-7d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d '7 days ago' +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null)
  if [ -n "$CUTOFF" ]; then
    awk -v cutoff="$CUTOFF" -v arch="$ARCHIVE_FILE" '{
      if (match($0, /"ts":"[^"]*"/)) {
        ts = substr($0, RSTART + 6, RLENGTH - 7)
        if (ts >= cutoff) { print } else { print >> arch }
      } else { print >> arch }
    }' "$JSONL_FILE" > "$JSONL_FILE.tmp" 2>/dev/null && mv "$JSONL_FILE.tmp" "$JSONL_FILE" || rm -f "$JSONL_FILE.tmp"
  fi
fi

# ─────────────────────────────────────────────
# model_version → route.json (HUD 버전 표시의 producer — 마스터플랜 4단계 전제 배선)
# 실측(2026-06-12): SessionStart/Stop stdin 페이로드에 model 필드 없음(공식 문서) →
# transcript에서 마지막 assistant 메시지의 .message.model 추출 (resume/clear/compact 시 존재,
# 신규 세션은 transcript가 비어 있으므로 graceful skip — 다음 세션부터 채워짐)
# ─────────────────────────────────────────────
FORGE_BIN="$PLUGIN_ROOT/bin/forge"
if [ -n "$HOOK_INPUT" ] && [ -x "$FORGE_BIN" ] && command -v jq >/dev/null 2>&1; then
  TRANSCRIPT=$(echo "$HOOK_INPUT" | jq -r '.transcript_path // empty' 2>/dev/null || echo "")
  if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
    MODEL_VER=$(tail -50 "$TRANSCRIPT" 2>/dev/null \
      | jq -r 'select(.message.model? // empty != "") | .message.model' 2>/dev/null \
      | tail -1 || echo "")
    if [ -n "$MODEL_VER" ]; then
      printf '{"model_version":"%s","producer":"session-init"}' "$MODEL_VER" \
        | "$FORGE_BIN" emit-event >/dev/null 2>&1 || true
    fi
  fi
fi
