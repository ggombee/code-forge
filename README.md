# code-forge

> 설치하면 Claude Code가 더 잘 동작합니다.

14개 전문 에이전트, 24개 워크플로우 스킬, 13개 스택 모듈.
검증된 사고모델이 모든 작업의 품질을 일관되게 유지합니다.

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
# 1. 클론
git clone https://github.com/ggombee/code-forge.git

# 2. 플러그인 디렉토리 지정하여 실행
claude --plugin-dir /path/to/code-forge

# 3. 프로젝트 세팅
> /setup
```

매번 입력하기 번거로우면 alias를 추가하세요:

```bash
alias claude-forge='claude --plugin-dir /path/to/code-forge'
```

### `/setup`이 하는 일

package.json을 읽어서 스택을 자동 감지하고, 프로젝트에 맞는 CLAUDE.md를 생성합니다.
스택 선택, 기능 설정(Smith/Whetstone/Bellows on/off)까지 대화형으로 진행됩니다.

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



### `/bug-fix` — 옵션을 제시합니다

에러 메시지를 던지면 2-3가지 해결 방안을 비교해서 보여줍니다. 선택하면 바로 수정.

```
/bug-fix "TypeError: Cannot read property of undefined"
```

### 그 외

| 스킬 | 한 줄 설명 |
|------|----------|
| `/stats` | 에이전트/스킬 사용량 통계 |
| `/done` | 이미 구현한 코드 → 검증 → 커밋 → PR |
| `/quality` | 포맷 → 린트 → 타입 체크, 에러 자동 수정 |
| `/refactor` | 리팩토링 분석 + 정책 보호 테스트 |
| `/generate-test` | BDD 시나리오 기반 테스트 코드 생성 |
| `/debate` | 서로 다른 모델끼리 토론시켜서 방향 결정 |
| `/figma-to-code` | Figma 디자인을 코드로 변환 |

---

## Bellows — 사용량 추적

에이전트와 스킬 호출을 자동으로 기록합니다. `/stats`로 확인.

```
/stats              # 전체 통계
/stats --week       # 최근 7일
/stats --project    # 현재 프로젝트만
```

---

## 에이전트 14명

코드를 수정할 수 있는 놈과 없는 놈을 확실히 나눴습니다.

| 권한 | 누구 | 할 수 있는 것 |
|------|------|-------------|
| **읽기만** | analyst, architect, refactor-advisor, vision | 분석, 설계, 리뷰 — 코드 안 건드림 |
| **Bash만** | scout, code-reviewer, git-operator, researcher | 탐색, 리뷰, git, 조사 — 파일 수정 안 함 |
| **수정만** | lint-fixer, build-fixer | 기존 파일 수정 — 새 파일 생성 안 함 |
| **전체** | implementor, deep-executor, assayer, codex | 뭐든 가능 |

간단한 탐색은 haiku가 빠르게, 복잡한 구현은 sonnet이, 아키텍처 분석은 opus가 처리합니다.

---

## Smith — 에이전트를 만드는 에이전트

에이전트를 STATE(이 에이전트가 아는 것)와 ACT(이 에이전트가 하는 것)로 나눠서 정의하고, 빌드타임에 컴파일합니다. TypeScript를 매번 해석하지 않고 .js로 컴파일하는 것과 같은 원리.

```
/smith-create-agent    # 프로젝트 분석 → 맞춤 에이전트 자동 생성
/smith-build           # 수동 빌드
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

## MCP 연동

플러그인만으로 다 됩니다. 아래는 있으면 더 좋은 것들:

| MCP | 효과 |
|-----|------|
| Figma | `/start`에서 디자인 자동 분석 |
| Pencil | `.pen` 파일 직접 분석 |
| Codex | 다른 모델과 페어 프로그래밍 |

없으면? 그냥 안 쓰입니다. 에러 안 납니다.

---

## 라이선스

MIT
