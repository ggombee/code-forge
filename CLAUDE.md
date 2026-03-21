# code-forge

프로젝트 스택에 맞는 에이전트, 스킬, 규칙을 자동으로 제공하는 Claude Code 플러그인.
설치 후 `/setup` 한 번이면 프로젝트에 맞는 CLAUDE.md가 자동 생성되고, 14개 에이전트와 24개 스킬이 바로 동작한다.

## 설치

```bash
# 마켓플레이스 등록 (최초 1회) → 설치
claude plugin marketplace add https://github.com/ggombee/forge-market.git
claude plugin install code-forge
```

또는 로컬: `claude --plugin-dir /path/to/code-forge`

설치 후 `/setup` 실행 → 상세 가이드: README.md 참조

## 대장간 체계

인지적 도제이론(Cognitive Apprenticeship) 기반 대장간 메타포:

| 이름 | 역할 | 위치 |
|------|------|------|
| **Forge** (대장간) | 전체 플랫폼 | code-forge |
| **Smith** (대장장이) | 에이전트 빌드 (STATE+ACT → 컴파일) | `plugins/smith/` |
| **Anvil** (작업대) | 사용자 인터페이스 | CLI, 스킬, 커맨드 |
| **Whetstone** (숫돌) | 코딩 근육 유지 + 면접 준비 | `/practice` |
| **Assayer** (감정사) | 테스트 생성/검증 | `agents/assayer.md` |
| **Bellows** (풀무) | 사용량 로깅 + 통계 | `hooks/bellows-log.sh` |
| **Blueprint** (설계도) | 사고모델 + 규칙 | `rules/` |

## 이 플러그인의 역할

1. `/setup` 실행 → 프로젝트 스택 감지 또는 선택
2. `profile.json` + preset 기반으로 `CLAUDE.md` 자동 생성
3. 스택에 맞는 모듈(컨벤션)이 에이전트에 주입됨

## 핵심 워크플로우

```
/start feature.md       → 분석 → 구현 → 검증 → 커밋 → PR (원큐)
/done                   → 이미 구현된 코드 검증 → 커밋 → PR
/bug-fix "에러 메시지"   → 2-3 옵션 → 선택 → 수정
/practice react         → 코딩 면접 시뮬레이션
/setup                  → 스택 감지 → CLAUDE.md 생성
```

## 에이전트 (14개, 4단계 권한)

### READ-ONLY — Read/Grep/Glob만

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `analyst` | opus | 요구사항 분석, 누락 사항 발견 |
| `architect` | opus | 아키텍처 분석, 설계 자문 |
| `refactor-advisor` | sonnet | 리팩토링 전략 분석 |
| `vision` | sonnet | 이미지/PDF/다이어그램 분석 |

### SHELL-ACCESS — + Bash (Write/Edit 없음)

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `scout` | haiku | 코드베이스 빠른 탐색 |
| `code-reviewer` | sonnet | 코드 리뷰 (품질+보안) + 패턴 학습 |
| `git-operator` | sonnet | Git 커밋/브랜치 관리 |
| `researcher` | sonnet | 외부 문서/라이브러리 조사 |

### EDIT-ONLY — + Edit (Write 없음)

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `lint-fixer` | haiku | ESLint/TypeScript 오류 자동 수정 |
| `build-fixer` | sonnet | 빌드/컴파일 오류 수정 |

### READ-WRITE-FULL — Write 포함 전체

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `implementor` | sonnet | 계획 기반 즉시 구현 |
| `deep-executor` | sonnet | 자율적 심층 구현 + Ralph Loop |
| `assayer` | sonnet | 테스트 생성 (generate/tdd 모드) |
| `codex` | sonnet | Codex 페어 프로그래밍 (MCP/CLI 듀얼) |

### Smith 빌드타임 컴파일

Smith(Agent Smith System)은 STATE(지식) + ACT(행동) 조합으로 에이전트를 정의한다. `/smith-build`가 인스턴스를 정적 .md로 컴파일.

- 인스턴스 소스: `plugins/smith/agents/_agents/`
- 컴파일 출력: `agents/`
- 프로젝트 전용: `/smith-create-agent` → `.agents/agents/` 생성 → `/smith-build --project`로 컴파일

## Hooks

| 이벤트 | 훅 | 동작 |
|--------|------|------|
| PreToolUse | `guard.sh` | 위험 명령 차단 (rm -rf, --force 등 10개 패턴) |
| PostToolUse | `lint-fix.sh` | Edit/Write 후 자동 eslint --fix |
| PostToolUse | `bellows-log.sh` | Agent/Skill 사용 로깅 → ~/.code-forge/usage.jsonl |

## 스킬 (24개)

### 워크플로우

| 스킬 | 용도 |
|------|------|
| `/start` | MD 파일 또는 텍스트 → 분석 → 구현 → 검증 → 커밋 → PR (원큐) |
| `/done` | 구현 완료 후 검증 → 테스트 → 커밋 → PR |
| `/commit` | staged 분석 → 커밋 메시지 생성 → 커밋 |
| `/quality` | 포맷 → 린트 → 타입 체크 + 오류 자동 수정 |
| `/stats` | Bellows 사용량 통계 (에이전트/스킬 빈도) |

### 구현

| 스킬 | 용도 |
|------|------|
| `/bug-fix` | 버그 분석 후 2-3가지 옵션 제시 |
| `/refactor` | 리팩토링 + 정책 보호 테스트 |
| `/generate-test` | BDD 시나리오 기반 테스트 생성 |
| `/setup-test` | 테스트 환경 초기 세팅 |
| `/figma-to-code` | Figma 디자인 → 코드 변환 |

### 분석

| 스킬 | 용도 |
|------|------|
| `/debate` | 교차 모델 토론 |
| `/practice` | 코딩 근육 유지 + 면접 시뮬레이션 (4단계 힌트) |
| `/research` | 구조화된 리서치 |
| `/elon-musk` | 제1원칙 사고법 |
| `/genius-thinking` | TRIZ/SCAMPER 아이디어 발상 |
| `/startup-validator` | 스타트업 검증 |
| `/crawler` | Playwright 크롤링 설계 |

### 설정

| 스킬 | 용도 |
|------|------|
| `/setup` | 스택 감지 + CLAUDE.md 생성 + 기능 설정 |
| `/setup-notifier` | Mac 알림 설정 |
| `/setup-agent-teams` | Agent Teams 설정 |

### 유틸 + Smith

| 스킬 | 용도 |
|------|------|
| `/version-update` | 시맨틱 버전 업데이트 |
| `/docs-creator` | 문서 작성 가이드 |
| `/codex` | Codex 페어 프로그래밍 |
| `/gemini` | Gemini CLI 래퍼 |
| `/smith-build` | Smith 인스턴스 컴파일 |
| `/smith-create-agent` | 프로젝트 전용 에이전트 생성 |

## 모듈 (13개)

| 카테고리 | 모듈 |
|---------|------|
| Framework | `react-nextjs-pages`, `react-nextjs-app`, `react-spa` |
| Design System | `mui`, `ant-design` |
| State | `jotai-tanstack`, `zustand-tanstack`, `redux-rtk` |
| Styling | `emotion`, `tailwind`, `styled-components` |
| Testing | `jest`, `vitest` |

## 프리셋

| 프리셋 | 조합 |
|--------|------|
| `standard` | Pages Router + Jotai + Emotion + Jest |
| `modern-stack` | MUI + App Router + Zustand + Tailwind + Vitest |

## 상세 규칙 (alwaysApply)

코드 작업 시 아래 규칙이 자동 적용됨:

| 규칙 | 핵심 |
|------|------|
| `rules/thinking-model.md` | GROUND→APPLY→VERIFY→ADAPT 루프. S/M/L 규모 분기. 불변 제약 5가지. |
| `rules/coding-standards.md` | 코딩 표준, 네이밍, 금지 패턴, import 순서 |

## 멀티에이전트 협업

3개+ 에이전트 협업 시 Agent Teams 사용:

```
TeamCreate → 팀원 spawn → 병렬 작업 → shutdown → TeamDelete
```

가이드: `instructions/multi-agent/coordination-guide.md`
