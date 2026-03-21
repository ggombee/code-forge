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

전역 설치(기본)면 모든 프로젝트에서 사용 가능. 특정 프로젝트에만 쓰려면:

```bash
claude plugin install code-forge --scope project
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

### 방법 3: Claude에게 시키기

Claude Code 세션에서 이 README URL을 주면 됩니다:

```
이 플러그인 설치해줘: https://github.com/ggombee/code-forge
```

Claude가 알아서 `claude plugin marketplace add` → `install` → `/setup`까지 처리합니다.

### 설치 확인

```bash
claude plugin list
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

### `/practice` — 코딩 근육을 유지하세요

AI가 코드를 대신 써주는 시대. Copilot 켜놓고 Tab만 누르다 보면 어느새 직접 코드를 치는 감각이 무뎌집니다.
근육도 매일 같은 무게만 들면 늘지 않는 것처럼, 코딩도 점점 더 어려운 문제를 풀어야 실력이 유지됩니다.

Whetstone(숫돌)은 그 코딩 근육을 갈고닦는 도구입니다.

```
/practice react              # 의도적으로 문제 있는 코드를 받고 직접 수정
/practice react --senior     # 시니어 난이도
```

면접관 페르소나가 코드를 주고, 분석하고, 수정하라고 합니다. 답을 알려주지 않습니다.
막히면 힌트를 요청할 수 있는데, 4단계로 점진적으로 줍니다 — 방향만 알려주다가, 정말 막히면 뼈대 코드까지.

난이도는 junior → mid → senior로 올라가고, 같은 난이도 안에서도 점점 더 복잡한 문제가 나옵니다.
면접 준비에도 쓸 수 있고, 그냥 감각 유지용으로 하루 한 문제씩 풀어도 됩니다.

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
