#!/bin/bash
# ggombee-agents 초기화 스크립트
# 사용법: bash <(curl -s https://raw.githubusercontent.com/you/ggombee-agents/main/init.sh)
#    또는: bash init.sh

set -e

REPO="https://github.com/ggombee/ggombee-agents.git"
TMP_DIR=$(mktemp -d)

cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

# 이미 있으면 확인
if [ -d ".claude" ]; then
  read -p "⚠ .claude/ 폴더가 이미 있습니다. 덮어쓸까요? (y/n) " -n 1 -r
  echo
  [[ ! $REPLY =~ ^[Yy]$ ]] && echo "취소됨." && exit 0
fi

echo "가져오는 중..."
git clone --depth 1 --quiet "$REPO" "$TMP_DIR"

# 복사
cp -r "$TMP_DIR/.claude" .
cp "$TMP_DIR/CLAUDE.md" .
cp "$TMP_DIR/.gitignore" .

echo ""
echo "설치 완료:"
echo "  .claude/     - 에이전트, 규칙, 스킬, 명령어"
echo "  CLAUDE.md    - 진입점"
echo "  .gitignore   - 기본 제외 규칙"
echo ""
echo "이제 claude 실행하면 됩니다."
