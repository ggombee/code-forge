# Forge Voice — code-forge 음성 입력 확장

> code-forge의 일부. 손목 부상/RSI 사용자가 family 워크플로우를 그대로 음성으로 쓸 수 있게.
> 무료 오픈소스 도구만 조합 (whisper.cpp + sox + Hammerspoon). 유료 STT 도구 불필요.
> (2026-06-08 redesign G9 — Hermes voice memo 정신 부분 차용)

대장간 비유에서: **Anvil**(작업대)에 명령을 외치면 **Forge Voice**가 받아 그대로 **Smith/Implementor**가 단조한다.

---

## 0. code-forge 내장 진입점

```bash
# 셋업 (1회)
/voice                    # 또는 claude plugin install 후 자동

# 사용 (어디서든)
⌘ + Shift + Space         # 토글 → 말하기 → 자동 paste
```

→ 본 문서는 셋업 + 트러블슈팅 reference. 실제 사용은 `/voice` 스킬이 안내.

---

## 1. 왜

- 손목 부상/수술 회복 중 타이핑 부담
- RSI 영구화 예방
- 침대/회복 환경에서도 작업 가능

→ Claude Code prompt 창은 일반 텍스트 입력. 즉 **macOS 시스템 전역으로 음성 → 텍스트** 변환되면 자동으로 동작. STT 도구만 셋업하면 끝.

→ G5에서 만든 `UserPromptSubmit hook`(auto-flow-trigger.sh)이 음성 입력 텍스트에도 동일 작동. 티켓 ID 정규식 매칭 → flow CLI 자동 호출.

---

## 2. Voice Stack (code-forge 내장, 무료 오픈소스만)

| 도구 | 역할 | 설치 |
|---|---|---|
| **whisper.cpp** | STT 엔진. Apple Silicon Metal 가속. local 실행 (오프라인) | `brew install whisper-cpp` |
| **sox** | 마이크 녹음 (silence detection 내장) | `brew install sox` |
| **Hammerspoon** | macOS Lua 자동화. 단축키 매크로 + 스크립트 실행 | `brew install --cask hammerspoon` |
| **cliclick** | 커서 위치 자동 paste (옵션 — pbpaste만으로도 OK) | `brew install cliclick` |
| **jq** | JSON 처리 (이미 forge-glow 요구사항) | `brew install jq` |

→ 총 디스크 ~500MB (whisper 모델 포함). 토큰 비용 0 (local).

---

## 3. 빠른 셋업 (15분)

### 3-1. 도구 설치

```bash
brew install whisper-cpp sox jq
brew install --cask hammerspoon
brew install cliclick   # 옵션
```

### 3-2. Whisper 모델 다운로드

```bash
mkdir -p ~/.whisper/models
cd ~/.whisper/models
# small: 빠름 + 한국어 OK (244MB)
curl -fsSL -o ggml-small.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin
# medium: 정확도 ↑ (한국어 권장, 1.5GB) — 선택
# curl -fsSL -o ggml-medium.bin \
#   https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin
```

> 한국어 정확도: small 80% / medium 90%+ / large 95%+. 손목 보호용으로 small도 충분.

### 3-3. forge-voice 스크립트 설치

```bash
# code-forge 내장 스크립트 활용 — /voice 스킬이 자동 처리
/voice setup

# 또는 수동:
cp $(claude plugin path code-forge)/tools/forge-voice.sh ~/.local/bin/
chmod +x ~/.local/bin/forge-voice.sh
```

### 3-4. Hammerspoon 설정 (단축키 hook)

`~/.hammerspoon/init.lua`에 1줄 추가 (또는 `/voice setup`이 자동 처리):

```lua
-- code-forge Forge Voice 진입점
dofile(os.getenv("HOME") .. "/.local/share/forge-voice/forge-voice.lua")
```

또는 본 repo의 [`tools/forge-voice.lua`](../tools/forge-voice.lua) 내용을 직접 복사.

Hammerspoon 메뉴바 아이콘 → **Reload Config**.

### 3-5. 권한 부여 (macOS)

처음 실행 시 macOS가 다음 권한 요청:
- **마이크** (Hammerspoon, sox)
- **접근성** (Hammerspoon — cliclick 사용 시)

→ 시스템 환경설정 → 보안 및 개인 정보 보호 → 마이크 / 접근성에서 허용.

---

## 4. 사용법

1. Claude Code 또는 어떤 입력창 활성화
2. `⌘ + Shift + Space` 누르고 말하기
3. 1초 침묵하면 자동 녹음 종료 (sox silence detection)
4. ~1-3초 후 텍스트가 자동 paste

### 예시 발화

| 발화 | 결과 |
|---|---|
| "프로젝트 일이삼 작업 시작" | (영문 발음 강제 필요 — 한국어 숫자 인식 한계. 아래 §6 참조) |
| "PROJ dash 123 작업 시작" | "PROJ-123 작업 시작" → G5 hook이 `flow tc select PROJ-123` 자동 |
| "통합 테스트 돌려" | → `flow run report` 자동 호출 |
| "회고 보여줘" | → `flow retro` |
| "API 응답 한 번 봐줘 http://..." | → `flow spec capture` |

---

## 5. AI 후처리 (옵션 — SuperWhisper Pro 효과)

기본 Whisper 출력은 가끔 punctuation 누락 / 코드 친화 X. Claude Haiku API로 후처리하면 정확도 대폭 향상:

`voice-to-claude.sh`의 `POST_PROCESS=1` 모드 (Claude API key 필요):

```bash
export ANTHROPIC_API_KEY=sk-ant-...
export VOICE_POST_PROCESS=1
```

후처리는 Claude Haiku가 처리 — **$0.0001/회** 수준 (1분 발화당). 월 $1 미만.

---

## 6. 한국어 + 코드 발화 팁

Whisper는 한국어 일반 텍스트는 잘 받지만, 코드 친화 패턴은 약함:

| 어려운 발화 | 권장 발화 |
|---|---|
| "프로젝트 일이삼" → "PROJ-123" 변환 어려움 | "**프롭 대시 일이삼**" 또는 영문 "**proj dash one two three**" |
| "캐멀 케이스" → camelCase 변환 X | 평이하게 발화 후 paste 후 직접 수정 |
| "오픈 파렌" → `(` 변환 X | (Talon Voice 같은 grammar 도구 필요 — 본 stack 한계) |

→ **자연어 발화는 100% OK**. 코드 직접 dictation은 한계. 다음 두 패턴 권장:
1. **자연어로 의도 전달** → Claude가 코드 작성 (`/start`, `/done`, "이 버그 고쳐줘" 같은 prompt)
2. **티켓 ID + 동사** → G5 hook이 자동 처리

→ 즉 사용자는 **"무엇을 해라"** 말하고, Claude가 **코드 작성**. 손목 보호 + 의도 표현은 음성이 자연스러움.

---

## 7. 트러블슈팅

### "마이크 안 잡힘"
- 시스템 환경설정 → 보안 → 마이크 → Hammerspoon 허용
- `sox -d -n stat` 직접 테스트

### "Whisper 모델 못 찾음"
- `~/.whisper/models/ggml-small.bin` 존재 확인
- 또는 `WHISPER_MODEL=/custom/path` 환경변수

### "녹음이 안 끝남"
- sox silence detection 임계값 조정 (`silence 1 0.1 3%` → `3%`를 `1%`로 낮춤)
- 또는 단축키 다시 눌러 강제 종료 (Hammerspoon 토글 모드)

### "한국어 인식률 낮음"
- small → medium 모델 업그레이드 (1.5GB, 정확도 ↑↑)
- `WHISPER_LANG=ko` 명시

### "code-forge family와 연동 안 됨"
- G5 UserPromptSubmit hook 확인 — `code-forge/hooks/auto-flow-trigger.sh` 존재 + 실행 권한
- `claude plugin list` 에 code-forge 활성 확인

---

## 8. 보안

- whisper.cpp **local 실행** — 발화 내용 외부 전송 X
- AI 후처리 옵션 활성 시에만 Claude API에 전송 — 코드/시크릿 발화 주의
- macOS 마이크 권한은 Hammerspoon에만 — 본 도구 비활성 시 권한 자동 해제

→ 회사 노트북 사용 시 AI 후처리 OFF + local Whisper만 권장.

---

## 9. 장기 옵션 — Talon Voice (RSI 영구화 우려 시)

본 DIY stack은 손목 보호 + 자연어 발화 OK. 단:
- 코드 직접 dictation (변수명 / 기호 / 명령) 한계
- "open paren foo close paren" 같은 음성 명령 grammar 없음

→ RSI 영구화 우려 시 [Talon Voice](https://talonvoice.com) 학습 권장 (무료, 1-2주 투자, Python custom grammar).

본 DIY stack은 일상 80%, Talon은 코드 dictation 100% 커버. 둘 다 같이 써도 무방.

---

## 10. 변경 이력

| 일자 | 변경 |
|---|---|
| 2026-06-08 | G9a 신설 — DIY voice input 셋업 가이드 |
