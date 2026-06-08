#!/usr/bin/env bash
# forge-voice — code-forge 음성 입력 진입점
#
# 단축키(Hammerspoon ⌘⇧Space)로 호출 → 마이크 녹음 → whisper.cpp 변환 → 클립보드 + 자동 paste
#
# 대장간 비유:
#   Anvil(작업대)에 명령을 외치면 → Forge Voice가 받아 → Smith/Implementor가 단조
#
# 의존성:
#   - whisper-cpp (brew install whisper-cpp)
#   - sox         (brew install sox)
#   - cliclick    (brew install cliclick — 옵션, 자동 paste용)
#
# 환경 변수:
#   WHISPER_MODEL          — 모델 경로 (기본 ~/.whisper/models/ggml-small.bin)
#   WHISPER_LANG           — 언어 코드 (기본 ko, en, ja, auto)
#   FORGE_VOICE_AUTO_PASTE — 1 시 자동 paste (기본 1, 0이면 클립보드만)
#   VOICE_POST_PROCESS     — 1 시 Claude Haiku로 후처리 (ANTHROPIC_API_KEY 필요)
#   FORGE_VOICE_STATE_DIR  — 상태 파일 위치 (기본 ~/.local/share/forge-voice)
#
# 동작 모드 (Hammerspoon이 단축키 토글로 사용):
#   forge-voice.sh start  — 녹음 시작 (백그라운드)
#   forge-voice.sh stop   — 녹음 종료 → 변환 → paste
#   forge-voice.sh toggle — 자동 (start/stop 판별)
#   forge-voice.sh status — 현재 상태 (idle / recording)
#   forge-voice.sh once   — silence detection으로 자동 녹음→종료 (한 번에)
#
# 종료 코드:
#   0 정상, 1 의존성 없음, 2 모델 없음, 3 녹음 실패

set -e

# ── 설정 ────────────────────────────────────────────────────
WHISPER_MODEL="${WHISPER_MODEL:-$HOME/.whisper/models/ggml-small.bin}"
WHISPER_LANG="${WHISPER_LANG:-ko}"
FORGE_VOICE_AUTO_PASTE="${FORGE_VOICE_AUTO_PASTE:-1}"
STATE_DIR="${FORGE_VOICE_STATE_DIR:-$HOME/.local/share/forge-voice}"
WAV_FILE="$STATE_DIR/recording.wav"
PID_FILE="$STATE_DIR/sox.pid"
LAST_TEXT_FILE="$STATE_DIR/last.txt"

mkdir -p "$STATE_DIR"

# ── 의존성 점검 ─────────────────────────────────────────────
need() {
  command -v "$1" >/dev/null 2>&1 || { echo "❌ '$1' 필요 — brew install $2"; exit 1; }
}

check_deps() {
  need sox sox
  need whisper-cpp whisper-cpp
  [ -f "$WHISPER_MODEL" ] || {
    echo "❌ Whisper 모델 없음: $WHISPER_MODEL"
    echo "   다운로드: mkdir -p ~/.whisper/models && curl -fsSL -o '$WHISPER_MODEL' \\"
    echo "     https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin"
    exit 2
  }
}

# ── notification (macOS — 사용자 피드백) ────────────────────
notify() {
  local msg="$1"
  osascript -e "display notification \"$msg\" with title \"Forge Voice\"" 2>/dev/null || true
}

# ── start: 녹음 시작 (백그라운드) ───────────────────────────
cmd_start() {
  check_deps
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    notify "이미 녹음 중 — stop으로 종료"
    return 0
  fi
  rm -f "$WAV_FILE"
  # sox: 16kHz mono, silence detection은 stop에서 처리
  sox -d -V0 -r 16000 -c 1 -b 16 "$WAV_FILE" >/dev/null 2>&1 &
  echo $! > "$PID_FILE"
  notify "🎙️ 녹음 시작 — 다시 ⌘⇧Space로 종료"
}

# ── stop: 녹음 종료 → 변환 → paste ──────────────────────────
cmd_stop() {
  if [ ! -f "$PID_FILE" ]; then
    notify "녹음 중 아님"
    return 0
  fi
  local pid
  pid=$(cat "$PID_FILE")
  rm -f "$PID_FILE"
  kill "$pid" 2>/dev/null || true
  # sox 정리 대기 (WAV 파일 finalize)
  sleep 0.3

  if [ ! -s "$WAV_FILE" ]; then
    notify "⚠️ 녹음 파일 비어있음"
    return 3
  fi

  notify "🔊 변환 중..."
  transcribe_and_paste
}

# ── once: silence detection으로 자동 녹음→종료 ──────────────
# 사용자가 말 멈추면 자동 종료 (toggle 안 쓰고 한 번에)
cmd_once() {
  check_deps
  rm -f "$WAV_FILE"
  notify "🎙️ 녹음 시작 — 1초 침묵 시 자동 종료"
  # silence: trigger when 1 burst of sound > 0.1s, end after 1 burst of silence > 1.5s at <3% threshold
  sox -d -V0 -r 16000 -c 1 -b 16 "$WAV_FILE" \
    silence 1 0.1 3% 1 1.5 3% >/dev/null 2>&1

  if [ ! -s "$WAV_FILE" ]; then
    notify "⚠️ 녹음 실패 (마이크 권한 확인)"
    return 3
  fi
  transcribe_and_paste
}

# ── toggle: 상태 보고 자동 ──────────────────────────────────
cmd_toggle() {
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    cmd_stop
  else
    cmd_start
  fi
}

cmd_status() {
  if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "recording (pid $(cat "$PID_FILE"))"
  else
    echo "idle"
  fi
}

# ── 핵심 변환 + paste ───────────────────────────────────────
transcribe_and_paste() {
  # whisper.cpp 실행 (txt 출력)
  local out="$STATE_DIR/recording"
  whisper-cpp -m "$WHISPER_MODEL" -l "$WHISPER_LANG" \
    -otxt -of "$out" -f "$WAV_FILE" \
    -np -nt >/dev/null 2>&1 || {
    notify "❌ Whisper 변환 실패"
    return 1
  }

  local text
  text=$(cat "${out}.txt" 2>/dev/null | tr -s '[:space:]' ' ' | sed 's/^ //;s/ $//')

  if [ -z "$text" ]; then
    notify "⚠️ 변환 결과 빈 문자열 — 더 명확히 말해주세요"
    return 1
  fi

  # 선택: AI 후처리 (Claude Haiku)
  if [ "${VOICE_POST_PROCESS:-0}" = "1" ] && [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    text=$(post_process "$text")
  fi

  # 클립보드에 복사
  printf '%s' "$text" | pbcopy
  echo "$text" > "$LAST_TEXT_FILE"

  # 자동 paste (옵션)
  if [ "$FORGE_VOICE_AUTO_PASTE" = "1" ]; then
    if command -v cliclick >/dev/null 2>&1; then
      # cliclick = 더 안정. 0.1s 대기 후 cmd+v
      sleep 0.1
      cliclick kp:v -m cmd >/dev/null 2>&1 || \
        osascript -e 'tell application "System Events" to keystroke "v" using command down' 2>/dev/null || true
    else
      osascript -e 'tell application "System Events" to keystroke "v" using command down' 2>/dev/null || true
    fi
  fi

  notify "✅ $(printf '%.60s' "$text")$([[ ${#text} -gt 60 ]] && echo '…')"
}

# ── AI 후처리 (옵션) ────────────────────────────────────────
# 발화 텍스트를 받아 자연스러운 prompt로 정리. punctuation, 코드 친화 표현.
post_process() {
  local raw="$1"
  local response
  response=$(curl -fsSL -X POST https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d "$(jq -n --arg t "$raw" '{
      model: "claude-haiku-4-5-20251001",
      max_tokens: 500,
      messages: [{
        role: "user",
        content: "다음 음성 dictation 결과를 자연스러운 코딩 prompt로 정리해줘. punctuation 보완. 의미 보존. 답은 정리된 텍스트만:\n\n" + $t
      }]
    }')" 2>/dev/null)

  local cleaned
  cleaned=$(echo "$response" | jq -r '.content[0].text // empty' 2>/dev/null)
  [ -n "$cleaned" ] && echo "$cleaned" || echo "$raw"
}

# ── 진입점 ──────────────────────────────────────────────────
case "${1:-toggle}" in
  start)   cmd_start ;;
  stop)    cmd_stop ;;
  toggle)  cmd_toggle ;;
  once)    cmd_once ;;
  status)  cmd_status ;;
  --help|-h|help)
    sed -n '1,30p' "$0" | sed 's/^# \{0,1\}//'
    ;;
  *)
    echo "사용: $0 {start|stop|toggle|once|status|help}"
    exit 1
    ;;
esac
