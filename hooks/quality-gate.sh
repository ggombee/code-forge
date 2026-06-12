#!/bin/bash
# quality-gate.sh — Stop 훅. 비차단(항상 exit 0).
#
# 블록 구성 (범용):
#   1. ESLint + tsc (Node 프로젝트)
#   2. scope 체크 (.claude/temp/plan.md 있을 때)
#   3. test-trigger (변경 파일 → 단위 TC 자동 실행)
#   4. policy-sync-check (.policy/ 있을 때)
#   5. REFLECT flag 생성/삭제 (.claude/state/reflect.flag)
#   6. scope-type-check (opt-in [type:tag] 태그 기반)
#   7. design-refs 조건부 정리 (git clean 시)
#
# 출력:
#   - FORGE_OUTPUT=json → JSON Lines (stderr)
#   - 기본 → 사람 읽는 포맷
#   - quality.jsonl → .claude/state/quality.jsonl (append)

set -uo pipefail

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
STATE_DIR="$PROJECT_ROOT/.claude/state"
FLAG_FILE="$STATE_DIR/reflect.flag"
JSONL_FILE="$STATE_DIR/quality.jsonl"
SESSION_ID="${CLAUDE_SESSION_ID:-$(date -u +%s)}"

mkdir -p "$STATE_DIR" 2>/dev/null || true

# route.json에 최근 게이트 결과 기록 (HUD "이번 턴 검증" 표시용 — event-schema.md §1)
# emit-event는 deep-merge라 다른 producer(/start complexity 등) 필드를 지우지 않음.
FORGE_BIN="${CLAUDE_PLUGIN_ROOT:-$(dirname "$0")/..}/bin/forge"
emit_route() {
  local status="$1" blocks="$2"
  [ -x "$FORGE_BIN" ] || return 0
  printf '{"last_gate":{"status":"%s","blocks":"%s"},"producer":"quality-gate"}' "$status" "$blocks" \
    | "$FORGE_BIN" emit-event >/dev/null 2>&1 || true
}

# 변경 파일 (JS/TS 계열, staged+unstaged)
CHANGED_FILES=$(git diff --name-only HEAD 2>/dev/null | grep -E '\.(ts|tsx|js|jsx|vue|svelte)$' | head -20)
if [ -z "$CHANGED_FILES" ]; then
  # 침묵 스킵이던 경로 — "검증 탔는가"에 항상 답하기 위해 skipped 기록 (quality.jsonl에는 미기록, 스팸 방지)
  emit_route "skipped" ""
  exit 0
fi

HAS_FAILURE=false
FAILED_BLOCKS=""

# 출력 함수 (stderr + JSONL 동시)
emit() {
  local type="$1" status="$2" detail="$3"
  local ts
  ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  # JSONL append (관찰 가능성)
  # 간단한 JSON 이스케이프 (backslash, quote, newline)
  local esc_detail
  esc_detail=$(printf '%s' "$detail" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr -d '\n')
  printf '{"ts":"%s","sid":"%s","type":"%s","status":"%s","detail":"%s"}\n' \
    "$ts" "$SESSION_ID" "$type" "$status" "$esc_detail" >> "$JSONL_FILE"

  # stderr 출력
  if [ "${FORGE_OUTPUT:-}" = "json" ]; then
    printf '{"type":"%s","status":"%s","detail":"%s"}\n' "$type" "$status" "$esc_detail" >&2
  else
    case "$status" in
      pass) echo "[quality-gate:$type] OK" >&2 ;;
      warn) echo "[quality-gate:$type] ⚠️ $detail" >&2 ;;
      fail) echo "[quality-gate:$type] ❌ $detail" >&2 ;;
    esac
  fi
}

# 동일 detail이 최근 기록에 있으면 재기록 안 함 (동일 파일 27회 반복 경고 스팸 방지 — 2026-06-12)
emit_once() {
  local type="$1" status="$2" detail="$3"
  local esc
  esc=$(printf '%s' "$detail" | sed 's/\\/\\\\/g; s/"/\\"/g' | tr -d '\n')
  if [ -f "$JSONL_FILE" ] && tail -200 "$JSONL_FILE" 2>/dev/null | grep -qF "\"detail\":\"$esc\""; then
    return 0
  fi
  emit "$type" "$status" "$detail"
}

# ── 1. ESLint + tsc ──
# 2026-06-12 수리: 두 검사 모두 모노레포에서 구조적 always-fail이었음 (실측: pass 0/384)
#  - eslint: "출력 존재=fail" 판정이라 설정 오류 메시지에도 fail → exit code 판정으로
#  - tsc: 루트에서 실행 → 루트 tsconfig 없는 모노레포는 help+exit 1 → 변경 파일의 워크스페이스 스코프로
if [ -x "$PROJECT_ROOT/node_modules/.bin/eslint" ]; then
  # shellcheck disable=SC2086
  LINT_OUT=$("$PROJECT_ROOT/node_modules/.bin/eslint" --quiet $CHANGED_FILES 2>&1 | head -30)
  LINT_EXIT=$?
  if [ "$LINT_EXIT" -eq 0 ]; then
    emit "eslint" "pass" ""
  elif [ "$LINT_EXIT" -eq 1 ]; then
    emit "eslint" "fail" "린트 오류"
    echo "$LINT_OUT" | head -20 >&2
    HAS_FAILURE=true
    FAILED_BLOCKS="${FAILED_BLOCKS}eslint "
  else
    # exit 2+ = 설정/내부 오류 — 코드 문제가 아니므로 차단하지 않음 (graceful)
    emit "eslint" "warn" "eslint 설정 오류(exit ${LINT_EXIT}) — 판정 스킵"
  fi
fi

if [ -x "$PROJECT_ROOT/node_modules/.bin/tsc" ]; then
  # 변경 파일별 가장 가까운 tsconfig.json 워크스페이스 수집 (최대 3개)
  TS_PROJECTS=$(while IFS= read -r f; do
    d=$(dirname "$f")
    while :; do
      if [ -f "$PROJECT_ROOT/$d/tsconfig.json" ]; then echo "$d"; break; fi
      [ "$d" = "." ] && break
      d=$(dirname "$d")
    done
  done <<< "$CHANGED_FILES" | sort -u | head -3)

  if [ -z "$TS_PROJECTS" ]; then
    emit "tsc" "warn" "tsconfig 미발견 — tsc 스킵 (변경 파일 기준 워크스페이스 없음)"
  else
    TSC_FAIL_PROJ=""
    while IFS= read -r proj; do
      [ -z "$proj" ] && continue
      TSC_OUT=$("$PROJECT_ROOT/node_modules/.bin/tsc" -p "$PROJECT_ROOT/$proj" --noEmit --pretty false 2>&1 | head -20)
      if [ $? -ne 0 ]; then
        TSC_FAIL_PROJ="${TSC_FAIL_PROJ}${proj} "
        echo "$TSC_OUT" >&2
      fi
    done <<< "$TS_PROJECTS"
    if [ -n "$TSC_FAIL_PROJ" ]; then
      emit "tsc" "fail" "타입 에러: ${TSC_FAIL_PROJ% }"
      HAS_FAILURE=true
      FAILED_BLOCKS="${FAILED_BLOCKS}tsc "
    else
      emit "tsc" "pass" ""
    fi
  fi
fi

# ── 2. scope 체크 ──
PLAN_FILE="$PROJECT_ROOT/.claude/temp/plan.md"
if [ -f "$PLAN_FILE" ]; then
  PLAN_FILES=$(grep "^- " "$PLAN_FILE" 2>/dev/null | sed 's/^- //' | sed 's/ \[.*$//')
  if [ -n "$PLAN_FILES" ]; then
    OUT_OF_SCOPE=""
    for f in $CHANGED_FILES; do
      if ! echo "$PLAN_FILES" | grep -q "$f"; then
        OUT_OF_SCOPE="${OUT_OF_SCOPE} $f"
      fi
    done
    if [ -n "$OUT_OF_SCOPE" ]; then
      emit "scope" "warn" "계획에 없는 파일 수정됨:$OUT_OF_SCOPE"
    fi
  fi
fi

# ── 3. test-trigger (범용: .policy/ 자동 탐색) ──
# ad-center 하드코딩 제거. .policy/ 디렉토리를 프로젝트 트리에서 찾음.
POLICY_DIRS=$(find "$PROJECT_ROOT" -maxdepth 4 -type d -name ".policy" 2>/dev/null | head -3)

TC_RUN=0
TC_FAIL=0
TC_MISSING=0

for f in $CHANGED_FILES; do
  BASENAME=$(basename "$f")

  # 스킵: 스타일/타입/상수
  case "$BASENAME" in
    styled.*|*.styles.*|types.*|constants.*|*.d.ts) continue ;;
  esac

  # 페이지/화면은 스킵 (E2E에서 커버)
  case "$f" in
    */pages/*|*/views/*/index.tsx) continue ;;
  esac

  # policy 매칭 시도 (.policy/ 와 policy-check.py가 같은 앱 루트에 있을 때)
  POLICY_MATCHED=false
  for pdir in $POLICY_DIRS; do
    APP_DIR=$(dirname "$pdir")
    [ -x "$APP_DIR/scripts/policy-check.py" ] || continue
    if echo "$f" | grep -q "${APP_DIR##$PROJECT_ROOT/}"; then
      PC_OUT=$(POLICY_DIR="$pdir" python3 "$APP_DIR/scripts/policy-check.py" --match "$f" 2>/dev/null)
      if [ $? -eq 0 ] && [ -n "$PC_OUT" ]; then
        TEST_FILES=$(echo "$PC_OUT" | grep "^TEST_FILES=" | sed 's/^TEST_FILES=//' | tr ' ' '\n' | sort -u)
        for tf in $TEST_FILES; do
          case "$tf" in
            e2e/*|*.spec.*)
              emit "test-trigger" "warn" "E2E TC: $tf (머지 전 실행 권장)"
              ;;
            *)
              TC_RUN=$((TC_RUN + 1))
              TF_BASE=$(basename "$tf" | sed 's/\.test\..*$//;s/\.spec\..*$//')
              (cd "$APP_DIR" && yarn test -- --testPathPattern="$TF_BASE" --silent 2>&1 | tail -3) >/dev/null
              [ $? -ne 0 ] && TC_FAIL=$((TC_FAIL + 1))
              ;;
          esac
        done
        POLICY_MATCHED=true
        break
      fi
    fi
  done
  $POLICY_MATCHED && continue

  # policy 없으면 __tests__ 탐색
  SRC_BASE=$(echo "$BASENAME" | sed 's/\.\(ts\|tsx\|js\|jsx\|vue\)$//')
  DIRNAME=$(dirname "$PROJECT_ROOT/$f")
  TEST_FOUND=""
  for test_dir in "$DIRNAME/__tests__" "$DIRNAME/../__tests__"; do
    if [ -d "$test_dir" ]; then
      TEST_FOUND=$(find "$test_dir" -name "${SRC_BASE}.test.*" -o -name "${SRC_BASE}.spec.*" 2>/dev/null | head -1)
      [ -n "$TEST_FOUND" ] && break
    fi
  done

  if [ -z "$TEST_FOUND" ]; then
    TC_MISSING=$((TC_MISSING + 1))
    case "$f" in
      */utils/*|*/helpers/*|*/lib/*|*/adapters/*)
        emit_once "test-trigger" "warn" "유틸 TC 없음: $f (/test $f 권장)" ;;
      */hooks/*|*/components/*)
        emit_once "test-trigger" "warn" "TC 없음: $f (/test $f 권장)" ;;
    esac
  fi
done

if [ $TC_RUN -gt 0 ]; then
  emit "test-trigger" "pass" "실행: ${TC_RUN}개 TC"
fi
if [ $TC_FAIL -gt 0 ]; then
  emit "test-trigger" "fail" "실패: ${TC_FAIL}개"
  HAS_FAILURE=true
  FAILED_BLOCKS="${FAILED_BLOCKS}test-trigger "
fi

# ── 4. policy-sync-check (범용: 발견된 모든 .policy/) ──
for pdir in $POLICY_DIRS; do
  for policy_json in "$pdir"/*.json; do
    [ -f "$policy_json" ] || continue
    PBASE=$(basename "$policy_json" .json)
    case "$PBASE" in *schema*|config) continue ;; esac

    AFFECTED=$(python3 -c "
import json,sys
try:
  d=json.load(open('$policy_json'))
  for f in d.get('affectedFiles',[]):
    print(f)
except: pass
" 2>/dev/null)

    SOURCE_CHANGED=false
    for af in $AFFECTED; do
      if echo "$CHANGED_FILES" | grep -q "$af"; then
        SOURCE_CHANGED=true; break
      fi
    done

    if $SOURCE_CHANGED; then
      SOURCE_DOC=$(python3 -c "import json; d=json.load(open('$policy_json')); print(d.get('sourceDoc',''))" 2>/dev/null)
      if [ -n "$SOURCE_DOC" ] && ! echo "$CHANGED_FILES" | grep -q "$SOURCE_DOC"; then
        emit "policy-sync" "warn" "$PBASE: 소스 변경됨 but 문서($SOURCE_DOC) 미갱신"
      fi
    fi
  done
done

# ── 5. REFLECT flag 생성/삭제 ──
if $HAS_FAILURE; then
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  {
    echo "# REFLECT REQUIRED — 이전 턴 품질 검증 실패"
    echo "# 삭제하려면: rm $FLAG_FILE"
    echo "# 의도적 우회: 본문에 'ack: <이유>' 추가"
    echo "---"
    echo "timestamp: $TIMESTAMP"
    echo "session_id: $SESSION_ID"
    echo "failed_blocks:"
    echo "$FAILED_BLOCKS" | tr ' ' '\n' | grep -v '^$' | sed 's/^/  - /'
    echo "failed_files:"
    echo "$CHANGED_FILES" | sed 's/^/  - /'
    echo "---"
  } > "$FLAG_FILE"
else
  if [ -f "$FLAG_FILE" ]; then
    rm -f "$FLAG_FILE"
    emit "reflect" "pass" "REFLECT flag 해제 — 품질 검증 통과"
  fi
fi

# ── 6. scope-type-check (opt-in) ──
SCOPE_TYPE_SCRIPT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$0")/..}/hooks/scope-type-check.sh"
if [ -f "$SCOPE_TYPE_SCRIPT" ]; then
  # shellcheck disable=SC1090
  source "$SCOPE_TYPE_SCRIPT"
  scope_type_check "$PLAN_FILE" "$CHANGED_FILES" 2>/dev/null || true
fi

# ── 7. design-refs 조건부 정리 ──
if git diff --quiet HEAD 2>/dev/null && git diff --cached --quiet 2>/dev/null; then
  CLEANED=$(find "$PROJECT_ROOT" -path "*/.design-refs/*.png" -delete -print 2>/dev/null | wc -l | tr -d ' ')
  CLEANED=$((CLEANED + $(find "$PROJECT_ROOT" -path "*/.design-refs/*.jpg" -delete -print 2>/dev/null | wc -l | tr -d ' ')))
  if [ "$CLEANED" -gt 0 ]; then
    emit "cleanup" "pass" "design-refs ${CLEANED}개 정리"
  fi
fi

# ── 최근 게이트 결과 → route.json (HUD "이번 턴 검증" 표시) ──
if [ "$HAS_FAILURE" = true ]; then
  emit_route "fail" "${FAILED_BLOCKS% }"
else
  emit_route "pass" ""
fi

exit 0
