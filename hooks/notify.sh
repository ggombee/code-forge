#!/bin/bash
# Claude Code - 사용자 입력 필요 시 Mac 알림
# Claude Code의 Notification 훅에서 자동 호출됨

TITLE="Claude Code"
MESSAGE="${CLAUDE_NOTIFICATION_TITLE:-확인이 필요합니다}"

# terminal-notifier를 사용한 배너 알림 (macOS 15 Sequoia 호환)
NOTIFIER=$(command -v terminal-notifier || echo "/opt/homebrew/bin/terminal-notifier")
"$NOTIFIER" -title "$TITLE" -message "$MESSAGE" -sound Glass

# 터미널 벨 소리 (터미널 포커스 없을 때 추가 알림)
echo -e "\a"
