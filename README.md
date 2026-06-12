# code-forge

[English](README.en.md)

> 설치하면 Claude Code가 더 잘 동작합니다.

전문 에이전트, 슬래시 스킬, 스택 모듈을 제공하는 Claude Code 플러그인.
검증된 사고모델(GROUND→APPLY→VERIFY→ADAPT)이 모든 작업의 품질을 일관되게 유지합니다.
(에이전트/스킬 개수는 디스크가 진실 — `ls agents/*.md | wc -l`, `ls skills/*/SKILL.md | wc -l`)

**현재 상태**: 개인 GitHub 운영 중 (마켓플레이스 배포 4.10.0). 패치노트: [CHANGELOG.md](CHANGELOG.md)

---

## 설치

### 방법 1: 마켓플레이스 (권장)

```bash
# 1. 마켓플레이스 등록 (최초 1회)
claude plugin marketplace add https://github.com/ggombee/forge-market.git

# 2. 플러그인 설치
claude plugin install code-forge

# 3. 프로젝트 세팅
claude
> /setup
```

### 방법 2: 로컬 클론

```bash
git clone https://github.com/ggombee/code-forge.git
claude --plugin-dir /path/to/code-forge
> /setup
```

매번 입력하기 번거로우면 alias를 추가하세요:

```bash
alias claude-forge='claude --plugin-dir /path/to/code-forge'
```

### `/setup`이 하는 일

package.json을 읽어서 스택을 자동 감지하고, 프로젝트에 맞는 CLAUDE.md + AGENTS.md를 생성합니다.
스택 선택, 기능 설정(Smith/Whetstone/Bellows on/off)까지 대화형으로 진행됩니다.

- CLAUDE.md — 스택 규칙 + 모듈 참조 (Claude Code용)
- AGENTS.md — 사고모델 핵심 전파 (Codex CLI 등 멀티툴 호환)

---

## 이런 걸 합니다

### `/start feature.md` — 한 줄이면 PR까지

MD 파일에 요구사항을 적으면, 분석 → 디자인 확인 → 구현 → 테스트 → 린트 → 커밋 → PR까지 한 번에.
중간에 두 번만 물어봅니다: "구현할까요?", "커밋할까요?"

```
/start feature.md              # 전체 플로우
/start feature.md --plan-only  # 분석+계획만
/start "버튼 색상 변경"         # 자유 텍스트도 가능
```

복잡도를 스스로 판단해서 LOW면 탐색을 생략하고, HIGH면 계획 에이전트를 먼저 태웁니다.
완료 검증·버그 수정 같은 후속은 별도 스킬이 아니라 규칙·훅에 흡수되어 있습니다 (대체 매핑: [docs/CATALOG.md](docs/CATALOG.md)).

### `/handoff` — 세션을 끊고 이어가기

auto-compact에 맡기지 않고, 대화에만 존재하는 맥락(결정/이유/미결질문)을 progress.md에 문서화한 뒤
다음 세션 킥오프 프롬프트를 클립보드에 복사합니다. 새 세션은 시작 시 자동 주입으로 이어받습니다.

### 그 외 주요 스킬

| 스킬 | 한 줄 설명 |
|------|----------|
| `/test` | 테스트 통합 진입점 — 유닛/E2E/세팅 자동 라우팅 |
| `/e2e` | 화면 단위 E2E 자동화 (Playwright + 자율 실행 루프) |
| `/debate` | 서로 다른 모델끼리 토론시켜서 방향 결정 |
| `/research` | 구조화된 팩트 기반 리서치 |
| `/codex` | OpenAI Codex와 페어 프로그래밍 |
| `/voice` | 음성 입력 셋업 (local Whisper, hands-free) |
| `/setup --profile` | 프로젝트 코딩 스타일 분석 → 프로필 생성 |

전체 카탈로그: [docs/REFERENCE.md](docs/REFERENCE.md)

### `bin/forge` — 상태 표면 (외부 도구 연동)

```bash
bin/forge status --json   # 품질 게이트/라우팅/REFLECT 상태 (외부 도구의 유일한 읽기 표면)
bin/forge whet --draft    # 반복 품질 이슈 3회+ → 개인 컨벤션 후보 초안 (채택은 사람)
bin/forge doctor          # 주입 회로/버전 정합/만년 적색 자가진단 (보고만)
```

[forge-glow](https://github.com/ggombee/forge-glow) HUD가 이 표면을 소비해 품질 게이트·effort 권고를 상태줄에 표시합니다.

---

## 에이전트

코드를 수정할 수 있는 놈과 없는 놈을 확실히 나눴습니다.

| 권한 | 누구 | 할 수 있는 것 |
|------|------|-------------|
| **읽기만** | analyst, architect, refactor-advisor, vision | 분석, 설계, 리뷰 — 코드 안 건드림 |
| **Bash만** | scout, code-reviewer, git-operator, researcher | 탐색, 리뷰, git, 조사 — 파일 수정 안 함 |
| **수정만** | lint-fixer, build-fixer | 기존 파일 수정 — 새 파일 생성 안 함 |
| **전체** | implementor, deep-executor, assayer, codex | 뭐든 가능 |

간단한 탐색은 haiku가 빠르게, 복잡한 구현은 sonnet이, 아키텍처 분석은 opus가 처리합니다.
라우팅 정책(티어 핀 = 비용 통제): [references/routing-policy.md](references/routing-policy.md)

---

## Smith — 에이전트를 만드는 에이전트

에이전트를 STATE(이 에이전트가 아는 것)와 ACT(이 에이전트가 하는 것)로 나눠서 정의하고, 빌드타임에 컴파일합니다.

프로젝트 에이전트는 사고모델(Blueprint)이 인라인 임베딩되어 플러그인 없이도 핵심 규칙이 동작합니다.

```
/code-forge:smith-create-agent    # 프로젝트 분석 → 맞춤 에이전트 자동 생성 (setup에서 자동 호출됨)
/code-forge:smith-build           # 수동 빌드
```

---

## 스택 모듈

`/setup`이 package.json을 읽고 자동으로 맞춰줍니다. 수동으로 고르려면:

| 카테고리 | 선택지 |
|---------|--------|
| Framework | Next.js Pages Router, App Router, React SPA |
| Design System | MUI, Ant Design |
| State | Jotai+TanStack, Zustand+TanStack, Redux RTK |
| Styling | Emotion, Tailwind, Styled Components |
| Testing | Jest, Vitest |

프리셋으로 한 번에: `standard` (Pages+Jotai+Emotion+Jest) 또는 `modern-stack` (MUI+App+Zustand+Tailwind+Vitest)

---

## 자매 도구 (5-family)

code-forge는 단독으로 완결되지만, 같은 계약 위에서 자매 도구와 결합됩니다.
계약 + 연결 상태(🟢 wired / 📐 designed)는 [docs/contracts/INTEGRATION.md](docs/contracts/INTEGRATION.md)가 단일 진실.

| 도구 | 역할 | 상태 |
|---|---|---|
| [forge-glow](https://github.com/ggombee/forge-glow) | 실시간 HUD (상태줄) | 🟢 wired — `bin/forge status --json` 소비 |
| flow-toolkit | model-agnostic 워크플로우 CLI | 📐 휴면 — 미설치 시 전부 graceful skip |
| forge-hearth | 다중 프로젝트 대시보드 | 📐 휴면 |
| coding-practice | 개인 컨벤션 원본 (`.candidate/profile.md`) | 🟢 candidate-profile 룰이 소비 |

---

## MCP 연동

플러그인만으로 다 됩니다. 아래는 있으면 더 좋은 것들:

| MCP | 효과 |
|-----|------|
| Figma | `/start`에서 디자인 자동 분석 |
| Codex | 다른 모델과 페어 프로그래밍 |

없으면? 그냥 안 쓰입니다. 에러 안 납니다.

---

## 라이선스

MIT
