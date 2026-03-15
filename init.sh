#!/bin/bash
# ggombee-agents 플러그인 설치 스크립트
# 사용법: bash init.sh
#    또는: bash <(curl -s https://raw.githubusercontent.com/ggombee/ggombee-agents/main/init.sh)

set -e

echo "ggombee-agents 플러그인 설치"
echo ""

# Claude Code CLI 확인
if ! command -v claude &> /dev/null; then
  echo "Claude Code CLI가 설치되어 있지 않습니다."
  echo "https://claude.ai/code 에서 설치 후 다시 시도하세요."
  exit 1
fi

# 플러그인 설치
echo "플러그인 설치 중..."
claude plugin install ggombee/ggombee-agents

echo ""
echo "설치 완료!"
echo "  claude 실행 후 /setup 으로 프로젝트 초기화하세요."
