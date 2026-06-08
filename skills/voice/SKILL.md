---
name: voice
description: code-forge Forge Voice — 음성 입력 셋업 및 관리. 손목 부상/RSI 사용자가 family 워크플로우를 그대로 음성으로 쓸 수 있게. whisper.cpp + sox + Hammerspoon DIY stack. /voice setup으로 1회 셋업, /voice test로 동작 검증.
user-invocable: true
---

# /voice — Forge Voice 셋업 & 관리

> code-forge의 음성 입력 확장. 대장간 비유: **Anvil**(작업대)에 명령을 외치면 → **Forge Voice**가 받아 → **Smith/Implementor**가 단조.

---

## 서브커맨드

| 사용 | 동작 |
|---|---|
| `/voice` 또는 `/voice setup` | 1회 셋업 (의존성 + 모델 + Hammerspoon 설정) |
| `/voice test` | 동작 검증 (마이크 → STT → paste 풀 회로) |
| `/voice status` | 현재 상태 (의존성 / 모델 / hook 활성) |
| `/voice doctor` | 트러블슈팅 진단 |
| `/voice uninstall` | 셋업 되돌리기 |

---

## /voice setup — 1회 셋업

다음을 순서대로 실행 (사용자 확인 받으면서):

### 1. 의존성 점검

```bash
for cmd in sox whisper-cpp jq; do
  command -v "$cmd" >/dev/null 2>&1 || echo "  ❌ $cmd 없음"
done
command -v cliclick >/dev/null 2>&1 || echo "  ⚠️ cliclick 없음 (옵션, 자동 paste 정확도 ↑)"
brew list --cask hammerspoon >/dev/null 2>&1 || echo "  ❌ Hammerspoon 없음"
```

누락 시 사용자에게 한 줄 install 안내:

```bash
brew install whisper-cpp sox jq cliclick
brew install --cask hammerspoon
```

### 2. Whisper 모델 다운로드

`~/.whisper/models/ggml-small.bin` 없으면:

```bash
mkdir -p ~/.whisper/models
curl -fsSL -o ~/.whisper/models/ggml-small.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin
```

→ 244MB, 한국어 OK. medium 모델은 사용자에게 옵션 제안 (1.5GB, 정확도 ↑↑).

### 3. forge-voice 스크립트 + Lua 설치

```bash
mkdir -p ~/.local/bin ~/.local/share/forge-voice ~/.hammerspoon

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(claude plugin path code-forge)}"

cp "$PLUGIN_ROOT/tools/forge-voice.sh" ~/.local/bin/forge-voice.sh
chmod +x ~/.local/bin/forge-voice.sh

cp "$PLUGIN_ROOT/tools/forge-voice.lua" ~/.local/share/forge-voice/forge-voice.lua
```

### 4. Hammerspoon init.lua 등록

`~/.hammerspoon/init.lua`에 1줄 (중복 안 들어가게 grep 체크):

```bash
LINE='dofile(os.getenv("HOME") .. "/.local/share/forge-voice/forge-voice.lua")'
if ! grep -qF "forge-voice.lua" ~/.hammerspoon/init.lua 2>/dev/null; then
  echo "$LINE" >> ~/.hammerspoon/init.lua
fi
```

→ Hammerspoon 메뉴바 → Reload Config 안내.

### 5. macOS 권한 안내

사용자에게 직접 허용해야 하는 항목:
- **시스템 환경설정 → 보안 → 마이크**: Hammerspoon 허용
- **시스템 환경설정 → 보안 → 접근성**: Hammerspoon 허용 (cliclick 사용 시)

→ 본 단계는 시스템 권한이라 자동화 불가. 사용자 직접 수행 후 `/voice test`.

### 6. 사용 안내

`⌘ + Shift + Space` 단축키 3가지:
- `⌘⇧Space` — 토글 (한 번 녹음 시작, 다시 누르면 종료)
- `⌘⇧.` — silence detection (말 멈추면 자동 종료)
- `⌘⇧,` — 상태 확인

---

## /voice test — 풀 회로 검증

1. `forge-voice.sh status` → idle 확인
2. 사용자에게 "지금 ⌘⇧Space 누르고 '테스트 일이삼' 말해보세요" 안내
3. 5초 후 `~/.local/share/forge-voice/last.txt` 확인 → 결과 표시
4. (옵션) UserPromptSubmit hook 확인 — `code-forge/hooks/auto-flow-trigger.sh` 존재 + 실행 권한

---

## /voice doctor — 트러블슈팅

진단 항목:

| 증상 | 진단 | 해결 |
|---|---|---|
| ⌘⇧Space 안 먹힘 | Hammerspoon menubar 활성 | Reload Config / 재시작 |
| "마이크 안 잡힘" | macOS 권한 | 시스템 환경설정 → 보안 → 마이크 |
| 녹음은 되는데 paste 안 됨 | 접근성 권한 | 환경설정 → 접근성 → Hammerspoon |
| 한국어 인식률 낮음 | small 모델 | medium 또는 large 다운로드 |
| 영문 발음 모두 받는데 티켓 ID 안 잡힘 | hook 누락 | `ls -la code-forge/hooks/auto-flow-trigger.sh` 실행 권한 |
| 녹음이 안 끝남 | silence 임계값 | `~/.local/bin/forge-voice.sh` 의 silence 인자 조정 |

---

## /voice uninstall

되돌리기:

```bash
rm -f ~/.local/bin/forge-voice.sh
rm -rf ~/.local/share/forge-voice
# Hammerspoon init.lua 에서 dofile 라인 제거
sed -i '' '/forge-voice.lua/d' ~/.hammerspoon/init.lua
# Hammerspoon Reload Config
```

→ Whisper 모델 (~244MB)은 사용자에게 유지/삭제 선택 받음.

---

## 발화 패턴 (음성 친화 prompt 가이드)

### 1. 자연어 의도 전달 (권장)

자연어로 의도만 전달, Claude가 코드 작성:

| 발화 | 결과 |
|---|---|
| "프로젝트 일이삼 작업 시작" → Whisper → "PROJ-123 작업 시작" | G5 hook → `flow tc select PROJ-123` 자동 |
| "통합 테스트 돌려" | Claude가 `/test` 또는 `flow run report` 호출 |
| "이 버그 고쳐줘 — TypeError" | thinking-model GROUND "2-3 옵션 제시" 발화 |
| "회고 보여줘" | `flow retro` |

### 2. 자주 쓰는 단축 vocabulary

| 발화 (한국어) | Claude 해석 |
|---|---|
| "스타트 [티켓]" | /start [티켓] |
| "테스트" or "테스트 돌려" | /test |
| "정리" or "정리해" | /cleanup |
| "디베이트 [주제]" | /debate [주제] |
| "리서치 [주제]" | /research [주제] |
| "도네" or "다 했어" | /done (commit + PR) |

### 3. 코드 dictation은 한계

코드 직접 dictation (예: "open paren foo close paren")은 본 stack의 한계. RSI 영구화 우려 시 [Talon Voice](https://talonvoice.com) 학습 (1-2주, 무료) 권장.

본 Forge Voice는 **자연어 의도 → Claude 코드 작성** 패턴에 최적화. 손목 보호 + 표현 속도 우선.

---

## 통합 진입점

본 스킬은 code-forge family의 정식 일부:

- 코어 도구: `tools/forge-voice.sh` (스크립트)
- Hammerspoon hook: `tools/forge-voice.lua`
- 가이드: `docs/voice-input.md` (상세 reference)
- 자연어 → flow CLI hook: `hooks/auto-flow-trigger.sh` (G5 — 음성 입력에도 그대로 작동)
- 통합 계약: `docs/contracts/INTEGRATION.md` §11

→ 음성 입력은 별도 도구가 아니라 code-forge family의 **확장**.
