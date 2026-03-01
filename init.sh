#!/bin/bash
# ggombee-agents 초기화 스크립트
# 사용법: bash init.sh /path/to/my-project
#    또는: bash <(curl -s https://raw.githubusercontent.com/ggombee/ggombee-agents/main/init.sh) /path/to/my-project

set -e

TARGET="${1:-.}"
REPO="https://github.com/ggombee/ggombee-agents.git"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_DIR=$(mktemp -d)

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

# 대상 경로 확인
if [ ! -d "$TARGET" ]; then
  echo "경로가 존재하지 않습니다: $TARGET"
  exit 1
fi

TARGET="$(cd "$TARGET" && pwd)"

# 이미 있으면 확인
if [ -d "$TARGET/.claude" ]; then
  read -p ".claude/ 폴더가 이미 있습니다. 덮어쓸까요? (y/n) " -n 1 -r
  echo
  [[ ! $REPLY =~ ^[Yy]$ ]] && echo "취소됨." && exit 0
fi

# 로컬 실행인지 원격 실행인지 판단
if [ -d "$SCRIPT_DIR/.claude" ]; then
  SRC="$SCRIPT_DIR"
else
  echo "가져오는 중..."
  git clone --depth 1 --quiet "$REPO" "$TMP_DIR"
  SRC="$TMP_DIR"
fi

# 복사
cp -r "$SRC/.claude" "$TARGET/"
cp "$SRC/CLAUDE.md" "$TARGET/"

# .gitignore는 이미 있으면 병합, 없으면 복사
if [ -f "$TARGET/.gitignore" ]; then
  while IFS= read -r line; do
    grep -qxF "$line" "$TARGET/.gitignore" 2>/dev/null || echo "$line" >> "$TARGET/.gitignore"
  done < "$SRC/.gitignore"
  echo ".gitignore  - 누락 항목만 추가됨"
else
  cp "$SRC/.gitignore" "$TARGET/"
  echo ".gitignore  - 새로 생성됨"
fi

echo ""
echo "설치 완료: $TARGET"
echo "  .claude/     - 에이전트, 규칙, 스킬, 명령어"
echo "  CLAUDE.md    - 진입점"
echo ""
echo "이제 해당 폴더에서 claude 실행하면 됩니다."
