# ggombee-agents

범용 멀티 에이전트 Claude Code 플러그인. 프로젝트 스택에 맞는 에이전트와 스킬을 자동으로 제공한다.

---

## 설치

```bash
# GitHub에서 직접 설치
claude plugin install ggombee/ggombee-agents

# 로컬 개발
claude --plugin-dir ./ggombee-agents
```

---

## 빠른 시작

1. `.claude/profile.json` 생성 (또는 `/setup` 실행 시 대화형 선택)
2. `/setup` 스킬 실행 → 스택에 맞는 `CLAUDE.md` 자동 생성
3. 에이전트와 스킬 사용 시작

```jsonc
// .claude/profile.json
{
  "preset": "partner-standard",
  "project": {
    "name": "광고센터",
    "dev": "yarn dev:ad-web",
    "build": "yarn build",
    "lint": "yarn lint",
    "test": "yarn test"
  }
}
```

`profile.json`을 수정한 후 `/setup`을 재실행하면 `CLAUDE.md`가 갱신된다.

---

## 구조

```
ggombee-agents/
├── agents/           # 14개 에이전트
├── skills/           # 11개 스킬
├── modules/          # 14개 스택 모듈
├── hooks/            # 이벤트 훅
├── commands/         # 슬래시 커맨드
├── presets/          # 프리셋 (partner-standard, modern-stack)
├── rules/            # 핵심 규칙
├── instructions/     # 멀티에이전트 가이드
└── docs/             # 사용자 가이드
```

---

## 프리셋

| 프리셋 | 스택 |
|--------|------|
| `partner-standard` | PDS + Pages Router + Jotai + Emotion + Jest |
| `modern-stack` | MUI + App Router + Zustand + Tailwind + Vitest |

---

## 모듈 시스템

스택별 규칙을 모듈 단위로 조합한다. `/setup`이 `profile.json`을 읽어 해당 모듈의 `SKILL.md`를 `CLAUDE.md`에 참조로 주입한다.

| 카테고리 | 모듈 |
|---------|------|
| Frameworks | `react-nextjs-pages`, `react-nextjs-app`, `react-spa` |
| Design Systems | `pds`, `mui`, `ant-design` |
| State | `jotai-tanstack`, `zustand-tanstack`, `redux-rtk` |
| Styling | `emotion`, `tailwind`, `styled-components` |
| Testing | `jest`, `vitest` |

---

## 스킬 (11개)

| 스킬 | 설명 |
|------|------|
| `start` | 작업 시작 절차 (브랜치 확인, 컨텍스트 파악) |
| `done` | 작업 완료 절차 (린트, 빌드, 커밋 준비) |
| `setup` | `profile.json` → `CLAUDE.md` 자동 생성 |
| `debate` | 구현 방향 논쟁 및 결정 |
| `generate-test` | 테스트 코드 생성 |
| `setup-test` | 테스트 환경 초기 세팅 |
| `docs-creator` | 문서 작성 가이드 |
| `figma-to-code` | Figma 디자인 → 코드 변환 |
| `bug-fix` | 버그 분석 후 2-3가지 수정 옵션 제시 |
| `refactor` | 리팩토링 + 정책 보호 테스트 |
| `codex` | Codex 페어 프로그래밍 (MCP opt-in) |

---

## 에이전트 (14개)

### 분석 전용 (READ-ONLY)

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `explore` | haiku | 코드베이스 탐색 |
| `analyst` | opus | 요구사항 분석, 갭 식별 |
| `architect` | opus | 아키텍처 분석, 설계 자문 |
| `researcher` | sonnet | 외부 문서/라이브러리 조사 |
| `code-reviewer` | sonnet | 코드 리뷰 (보안, 품질) |
| `refactor-advisor` | sonnet | 리팩토링 분석, 개선 전략 |
| `vision` | sonnet | 미디어 파일 분석, 정보 추출 |

### 수정 전문 (READ-WRITE)

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `lint-fixer` | haiku | 린트/타입 오류 수정 |
| `build-fixer` | sonnet | 빌드/컴파일 오류 수정 |
| `testgen` | sonnet | BDD 테스트 코드 생성 |
| `implementation-executor` | sonnet | 계획 기반 즉시 구현 |
| `deep-executor` | sonnet | 자율적 심층 구현 |

### 전문 에이전트

| 에이전트 | 모델 | 용도 |
|---------|------|------|
| `codex` | sonnet | Codex 페어 프로그래밍, Team Lead (MCP 필요) |
| `git-operator` | sonnet | Git 커밋/브랜치 관리 |

---

## 이벤트 훅

| 훅 | 동작 |
|----|------|
| `PostToolUse` (Edit/Write) | 린트 자동 수정 |
| `PreToolUse` (Bash) | 위험 명령어 가드 |
| `Stop` | 세션 종료 시 lint + tsc 검증 |
| `SubagentStart/Stop` | 에이전트 메트릭 수집 |
| `SessionStart/End` | 세션 로깅 |

---

## 라이센스

MIT
