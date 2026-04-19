#!/bin/bash
# scope-type-check.sh — 변경 유형 체크 (opt-in, [type:tag] 태그 기반)
#
# plan.md에 [type:tag] 태그가 명시된 파일에 대해서만 동작.
# 태그가 없으면 아무 작업도 하지 않음 (false positive zero).
#
# 사용법:
#   quality-gate.sh에서 호출:
#     source "$PLUGIN_ROOT/hooks/scope-type-check.sh"
#     scope_type_check "$PLAN_FILE" "$CHANGED_FILES"
#
# 태그 스펙:
#   [refactor:no-style]   — variant/color/padding/margin 변경 금지
#   [bug-fix:no-new-deps] — 새 import 추가 금지
#   [qa:ui-only]          — 로직 변경 금지 (if/else/switch/return 변경)
#
# MEMORY 교훈 기반 정규식 (2026-02-10 에이전트 리팩토링):
#   variant|fontSize|color|padding|margin

scope_type_check() {
  local PLAN_FILE="$1"
  local CHANGED_FILES="$2"
  local PROJECT_ROOT
  PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

  [ ! -f "$PLAN_FILE" ] && return 0

  # [type:tag] 패턴이 있는 줄만 추출
  local TAGGED_FILES
  TAGGED_FILES=$(grep -E '\[.+:.+\]' "$PLAN_FILE" 2>/dev/null)
  [ -z "$TAGGED_FILES" ] && return 0

  local VIOLATIONS=""

  while IFS= read -r line; do
    # "- src/order/components/OrderCard.tsx [refactor:no-style]" 형식 파싱
    local FILE
    local TAG
    FILE=$(echo "$line" | sed 's/^- //' | sed 's/ \[.*$//')
    TAG=$(echo "$line" | grep -oE '\[[^]]+\]' | tr -d '[]')

    [ -z "$FILE" ] || [ -z "$TAG" ] && continue

    # 변경 파일에 포함되어 있는지 확인
    echo "$CHANGED_FILES" | grep -q "$FILE" || continue

    # 태그별 검증
    local DIFF
    DIFF=$(git diff HEAD -- "$PROJECT_ROOT/$FILE" 2>/dev/null | grep '^+' | grep -v '^+++')

    case "$TAG" in
      refactor:no-style|*:no-style)
        # variant, fontSize, color, padding, margin 변경 감지
        local STYLE_CHANGES
        STYLE_CHANGES=$(echo "$DIFF" | grep -iE '(variant|fontSize|fontWeight|color|padding|margin|gap|size)[=:"\x27]' | head -5)
        if [ -n "$STYLE_CHANGES" ]; then
          VIOLATIONS="${VIOLATIONS}\n  [$TAG] $FILE: 스타일 값 변경 감지"
          VIOLATIONS="${VIOLATIONS}\n    $(echo "$STYLE_CHANGES" | head -3 | sed 's/^/    /')"
        fi
        ;;

      *:no-new-deps)
        # 새 import 추가 감지
        local NEW_IMPORTS
        NEW_IMPORTS=$(echo "$DIFF" | grep -E '^\+import ' | head -5)
        if [ -n "$NEW_IMPORTS" ]; then
          VIOLATIONS="${VIOLATIONS}\n  [$TAG] $FILE: 새 import 추가 감지"
          VIOLATIONS="${VIOLATIONS}\n    $(echo "$NEW_IMPORTS" | head -3 | sed 's/^/    /')"
        fi
        ;;

      *:ui-only)
        # 로직 변경 감지 (if/else/switch/return/throw/await)
        local LOGIC_CHANGES
        LOGIC_CHANGES=$(echo "$DIFF" | grep -E '^\+.*(if\s*\(|else\s|switch\s*\(|return\s|throw\s|await\s)' | head -5)
        if [ -n "$LOGIC_CHANGES" ]; then
          VIOLATIONS="${VIOLATIONS}\n  [$TAG] $FILE: 로직 변경 감지 (ui-only 위반)"
          VIOLATIONS="${VIOLATIONS}\n    $(echo "$LOGIC_CHANGES" | head -3 | sed 's/^/    /')"
        fi
        ;;
    esac
  done <<< "$TAGGED_FILES"

  if [ -n "$VIOLATIONS" ]; then
    if [ "$FORGE_OUTPUT" = "json" ]; then
      echo "{\"type\":\"scope-type\",\"status\":\"warn\",\"detail\":\"변경 유형 위반 감지\"}" >&2
    else
      echo -e "[scope-type-check] ⚠️ 변경 유형 위반:${VIOLATIONS}" >&2
    fi
  fi

  return 0
}