# code-forge

프로젝트 스택에 맞는 에이전트, 스킬, 규칙을 자동으로 제공하는 Claude Code 플러그인.
설치 후 `/setup` 한 번이면 프로젝트에 맞는 CLAUDE.md + AGENTS.md가 자동 생성된다.
(에이전트/스킬 개수는 디스크가 진실 — `ls agents/*.md | wc -l`, `ls skills/*/SKILL.md | wc -l`)

## 설치

```bash
claude plugin marketplace add https://github.com/ggombee/forge-market.git
claude plugin install code-forge
```

로컬: `claude --plugin-dir /path/to/code-forge` · 설치 후 `/setup` → 상세: README.md

## 역할

1. `/setup` → 스택 감지 → CLAUDE.md + AGENTS.md 자동 생성, 스택 모듈(컨벤션) 주입
2. `/setup --profile` → 코딩 스타일 분석 → `.candidate/profile.md` 생성
3. Smith: 프로젝트 전용 에이전트 빌드 (STATE+ACT 컴파일, setup이 자동 호출)

## 핵심 워크플로우

```
/start feature.md   → 분석 → 구현 → 검증 → 커밋 → PR (원큐; 완료 검증/버그 옵션 제시는 규칙·훅에 흡수 — docs/CATALOG.md)
/handoff            → 세션 핸드오프 (중요 맥락 → progress.md + 킥오프 프롬프트 클립보드)
/test               → 테스트 통합 진입점 (유닛/E2E/세팅 자동 라우팅)
/setup              → 스택 감지 → CLAUDE.md + AGENTS.md 생성
```

## 자동 적재 규칙 (매 세션/파일별 — 실제 frontmatter가 진실)

| 규칙 | 적재 시점 |
|------|---|
| `rules/thinking-model.md` | **alwaysApply** — GROUND→APPLY→VERIFY→ADAPT |
| `rules/candidate-profile.md` | **alwaysApply** — 프로필 참조 + 소통 보장선 + 커밋 컨벤션 |
| `rules/coding-standards.md` `review-guide.md` | path-scoped `*.{ts,tsx,js,jsx}` |
| `rules/build-guide.md` | path-scoped `*.{tsx,jsx}` |

## 카탈로그 (단일 소스 — 여기 표를 복제하지 말 것)

| 찾는 것 | 위치 |
|---------|------|
| 에이전트 전체 (4단계 권한) · 스킬 전체 · 훅 · quality-gate · State Layer · 멀티에이전트 · 대장간 체계 | [`docs/REFERENCE.md`](docs/REFERENCE.md) |
| 폐지 스킬(/done /bug-fix /refactor /quality → 대체 매핑) · 모듈 · 프리셋 | [`docs/CATALOG.md`](docs/CATALOG.md) |
| 상태/이벤트/통합 계약 | `docs/contracts/` (state-schema · event-schema · INTEGRATION) |
| 외부 도구의 상태 접근 | `bin/forge status --json` (파일 직독 금지) |

## 수정 규칙

이 저장소를 수정할 때의 규칙·금지 작업은 [`AGENTS.md`](AGENTS.md) 참조.
