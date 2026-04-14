---
name: setup-channels
description: Claude Channels(텔레그램/디스코드) 자동 셋업. 폰에서 메시지로 Claude Code에 작업 지시 가능. --auto 플래그와 FORGE_OUTPUT=json 프로토콜 공유.
---

# /setup-channels

Claude Channels를 통해 **텔레그램/디스코드에서 Claude Code 세션에 원격 접근**합니다.
폰에서 메시지만으로 `/start`, `/test` 같은 명령을 실행할 수 있고,
`--auto` 플래그와 결합하면 블로킹 없이 자동 완료됩니다.

**[즉시 실행]** 아래 흐름을 바로 시작하세요.

---

## 사용법

```
/setup-channels                  → AskUserQuestion으로 플랫폼 선택
/setup-channels telegram         → 텔레그램 직행
/setup-channels discord          → 디스코드 직행
/setup-channels --status         → 현재 연결 상태 확인
/setup-channels --uninstall      → 연결 제거
```

---

## Step 1: 플랫폼 선택

`$ARGUMENTS`에 `telegram`/`discord`가 포함되면 Step 2로. 아니면 `AskUserQuestion`으로 질문:

```
AskUserQuestion({
  questions: [{
    question: "어떤 채널을 연결할까요?",
    header: "채널 플랫폼",
    options: [
      { label: "Telegram", description: "BotFather로 봇 생성 → 다이렉트 메시지로 명령 실행" },
      { label: "Discord", description: "Discord Developer Portal로 봇 생성 → 서버/DM으로 명령 실행" },
      { label: "둘 다", description: "순차적으로 둘 다 셋업" }
    ],
    multiSelect: false
  }]
})
```

---

## Step 2: 전제 조건 확인

```bash
# Claude Code 버전 (Channels는 v2.1.80+ 필요)
claude --version

# Channels 플러그인 설치 여부
claude plugin list | grep -i channel
```

미설치면 마켓플레이스에서 설치:
```bash
claude plugin install claude-channels  # 이름은 실제 배포명에 맞춰 확인
```

---

## Step 3-A: Telegram 셋업

### 3A-1. 봇 토큰 발급 안내

사용자에게 다음을 안내:

```
1. 텔레그램에서 @BotFather 찾기
2. /newbot 명령 입력
3. 봇 이름 지정 (예: "ggombee-forge-bot")
4. 봇 유저네임 지정 (예: "ggombee_forge_bot" — _bot으로 끝나야 함)
5. 받은 API 토큰(형식: 123456789:ABC-DEF...) 복사
```

AskUserQuestion으로 토큰 입력 요청:

```
AskUserQuestion({
  questions: [{
    question: "BotFather에서 받은 토큰을 붙여넣어주세요",
    header: "Telegram Bot Token",
    options: [
      { label: "직접 입력", description: "토큰을 다음 입력에 붙여넣기 (123456789:ABC...)" },
      { label: "취소", description: "셋업 중단" }
    ],
    multiSelect: false
  }]
})
```

### 3A-2. 토큰 저장

```bash
# ~/.claude/channels/telegram.env 에 저장 (권한 600)
mkdir -p ~/.claude/channels
cat > ~/.claude/channels/telegram.env <<EOF
TELEGRAM_BOT_TOKEN=$TOKEN
TELEGRAM_AUTHORIZED_USER=  # 채팅에서 /whoami 후 채워넣기
EOF
chmod 600 ~/.claude/channels/telegram.env
```

### 3A-3. 설정 파일 생성

```json
// ~/.claude/channels/telegram.json
{
  "platform": "telegram",
  "envFile": "~/.claude/channels/telegram.env",
  "allowedCommands": ["/start", "/test", "/cleanup", "/stats"],
  "defaultFlags": "--auto",
  "responseFormat": "FORGE_OUTPUT=json"
}
```

`defaultFlags: --auto`로 블로킹 방지. `FORGE_OUTPUT=json`으로 quality-gate JSON 출력 → 봇이 Telegram Markdown으로 변환.

### 3A-4. 첫 연결 테스트

```bash
# 봇 프로세스 시작
source ~/.claude/channels/telegram.env
claude channels start --platform telegram &

# 사용자 안내:
# 1. 텔레그램에서 방금 만든 봇을 찾아 /start 메시지 전송
# 2. 봇이 응답하면 /whoami 입력 → 나온 user_id를 TELEGRAM_AUTHORIZED_USER에 저장
```

---

## Step 3-B: Discord 셋업

### 3B-1. 봇 생성 안내

```
1. https://discord.com/developers/applications 접속
2. "New Application" → 이름 입력
3. 좌측 "Bot" 탭 → "Add Bot"
4. "Reset Token" → 토큰 복사
5. "OAuth2 > URL Generator":
   - Scopes: bot, applications.commands
   - Bot Permissions: Send Messages, Read Message History
6. 생성된 URL로 봇을 서버에 초대
```

### 3B-2. 토큰 저장 + 설정

Telegram 3A-2, 3A-3과 동일한 패턴. 파일명만 `discord.{env,json}`.

---

## Step 4: 로컬 데몬 자동 시작 (옵션)

macOS `launchd` 또는 `pm2`로 봇 프로세스를 백그라운드 실행:

### launchd (추천 — macOS 네이티브)

```xml
<!-- ~/Library/LaunchAgents/com.ggombee.claude-channels.plist -->
<plist>
  <dict>
    <key>Label</key><string>com.ggombee.claude-channels</string>
    <key>ProgramArguments</key>
    <array>
      <string>/bin/bash</string>
      <string>-c</string>
      <string>source ~/.claude/channels/telegram.env && claude channels start --platform telegram</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardErrorPath</key><string>~/Library/Logs/claude-channels.err</string>
  </dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.ggombee.claude-channels.plist
```

### pm2 (Node 개발자 선호)

```bash
pm2 start "claude channels start --platform telegram" --name forge-channels
pm2 save
pm2 startup
```

---

## Step 5: 검증

```bash
/setup-channels --status
```

기대 출력:
```
✅ telegram  연결됨  (인증: @ggombee)  최근 메시지: 2분 전
⏸ discord   미설정
```

텔레그램에서 `/start TICKET-123 --auto` 메시지 전송 → 봇이 작업 분석/구현/커밋까지 자동 완료 후 결과 리포트.

---

## Step 6: 사용 팁

### 원격 시나리오

| 상황 | 폰에서 할 일 |
|-----|-----------|
| 아이디어 떠오름 | `/notepad-add 이 부분 리팩토링 필요` → .claude/state/notepad.md |
| 버그 리포트 | `/start "에러: XXX" --auto` — 2-3 옵션 받고 선택 |
| 긴 빌드 감시 | `ScheduleWakeup` 훅이 완료 알림 (Phase K) |
| 상태 확인 | `/forge-status` (Phase H) |

### 보안

- 토큰 파일 권한 **반드시 600**
- `TELEGRAM_AUTHORIZED_USER` 화이트리스트로 **본인 user_id만** 허용
- `allowedCommands`에 위험 명령(`--no-verify`, `rm -rf`) 금지
- 원격에서 오는 명령도 `hooks/guard.sh` + `write-guard.sh` 전부 거침

---

## Step 7: 문제 해결

| 증상 | 원인 | 해결 |
|-----|-----|-----|
| 봇이 응답 안 함 | 프로세스 중단 | `pm2 restart` 또는 launchd reload |
| "unauthorized" | user_id 미등록 | telegram.env의 `TELEGRAM_AUTHORIZED_USER` 갱신 |
| 블로킹으로 멈춤 | `--auto` 미포함 | `defaultFlags: "--auto"` 확인 |
| 메시지 못 읽음 | Discord 권한 부족 | "Read Message History" intent 활성화 |

---

## 관련 문서

- `@../../references/forge-bot-integration.md` — FORGE_OUTPUT=json 프로토콜 스펙
- `@../../docs/contracts/state-schema.md` — 세션 간 상태 파일 계약
- `@../../plans/mossy-marinating-sun.md` (로컬) — 원격 개발 환경 전체 계획

---

## 금지 사항

- 토큰/인증정보 커밋 금지 (`.gitignore`에 `.claude/channels/` 추가 권장)
- 공개 Discord 서버에 봇 추가 금지 — 누구나 명령 실행 가능해짐
- Channels 플러그인 미설치 상태로 이 스킬 완료 처리 금지 — Step 2에서 중단
