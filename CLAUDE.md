# Claude Code Multi-Agent System

> 모든 프로젝트에서 재사용 가능한 범용 멀티 에이전트 시스템

설치/사용법: `README.md` 참조 | 초기화: `bash init.sh`

---

## 핵심 규칙

### 코드 품질

- No `any` → `unknown` + 타입 가드
- 모든 함수에 반환 타입 명시
- No `@ts-ignore`, No `eslint-disable` 남발
- 상태 업데이트는 immutability 유지
- Import 순서: 외부 라이브러리 → 내부 모듈 (`@/`) → 상대 경로

### 금지 패턴

상세: `.claude/instructions/validation/forbidden-patterns.md`

---

## 규칙 우선순위

| 우선순위 | 소스 | 적용 시점 |
|---------|------|-----------|
| 1 | `agents/*.md` | 해당 에이전트 실행 시 |
| 2 | `rules/` | 코드 작업 시 (frontmatter globs 기반) |
| 3 | `instructions/` | 워크플로우/검증 시 |
| 4 | `CLAUDE.md` | 항상 (요약/네비게이션) |

---

## 에이전트 운영 방식

### 기본팀 (대부분 작업에 사용)

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| explore | haiku | 코드베이스 탐색 |
| implementation-executor | sonnet | 코드 구현 |
| code-reviewer | sonnet | 코드 리뷰 |
| deployment-validator | sonnet | 배포 전 검증 |
| git-operator | haiku | Git 커밋/푸시 |

### 필요시 투입

designer, vision, researcher, security-reviewer, qa-tester, document-writer, lint-fixer, build-fixer, architect, planner

### general-purpose 에이전트

구현이 필요한 서브에이전트는 `general-purpose`로 spawn하고, 역할별 전문 지식은 프롬프트에서 스킬/규칙 파일 읽기를 지시하여 주입한다.

전체 에이전트 목록: `.claude/instructions/multi-agent/agent-roster.md`

### 모델 라우팅

SSOT: `.claude/instructions/multi-agent/coordination-guide.md`

LOW → haiku / MEDIUM → sonnet / HIGH → opus

### 병렬 실행

상세: `.claude/instructions/multi-agent/coordination-guide.md`

---

## 인지 모델

모든 코드 작업에 적용되는 사고 흐름. 상세: `.claude/rules/frontend/thinking-model.md`

초기 아이디어는 Chain-of-Thought(CoT) 기반 단계적 추론이며, 이를 프로젝트 실행 맥락(탐색/구조화/검증)까지 확장해 현재 통합 인지 모델로 발전시켰다.
참고: https://www.ibm.com/kr-ko/think/topics/chain-of-thoughts

```
READ → REACT → ANALYZE → RESTRUCTURE → STRUCTURE → REFLECT
```

| 복잡도 | 단계 | 접근 |
|--------|------|------|
| LOW | READ → REACT → VERIFY | 즉시 수정 (tsc만) |
| MEDIUM | READ → ANALYZE → STRUCTURE → REFLECT | 패턴 확인 후 구현 (tsc + lint) |
| HIGH | 전체 6단계 + planner 에이전트 | 계획 수립 후 구현 (tsc + lint + build) |

---

## 스킬 시스템

`.claude/skills/` 폴더에 작업별 전문 스킬 정의.
`UserPromptSubmit` 후크로 강제 평가하여 발동률 확보.

| 스킬 | 트리거 | 역할 |
|------|--------|------|
| bug-fix | 버그, 오류, 에러, 동작 안함 | 버그 분석, 옵션 제시 후 수정 |
| refactor | 리팩토링, 구조 개선, 중복 제거 | 정책 보호 기반 코드 구조 개선 |
| figma-to-code | 이미지 첨부 + 구현, 시안대로 | 디자인 시안 → 컴포넌트 코드 변환 |
| docs-creator | 새 프로젝트, 문서 작성/업데이트 | CLAUDE.md, SKILL.md 등 문서 작성 |

---

## 멀티 에이전트

> **Agent Teams 우선** (Claude Max 전용): 3개+ 에이전트 협업 시 TeamCreate → 팀원 spawn → 병렬 협업 → shutdown → TeamDelete
> Agent Teams 미가용 시 Task 병렬 호출로 폴백

| 문서 | 용도 |
|------|------|
| `.claude/instructions/multi-agent/coordination-guide.md` | 병렬 실행, 모델 라우팅 (SSOT) |
| `.claude/instructions/multi-agent/execution-patterns.md` | 작업별 실행 패턴 |
| `.claude/instructions/multi-agent/agent-roster.md` | 에이전트 목록/상세 |
| `.claude/instructions/multi-agent/team-evaluation.md` | Agent Teams 평가 |

---

## 상세 규칙

프론트엔드 개발 시 아래 규칙 파일들을 참조:

| 규칙 | 경로 |
|------|------|
| 통합 사고 모델 | `.claude/rules/frontend/thinking-model.md` |
| React/Next.js 컨벤션 | `.claude/rules/frontend/react-nextjs-conventions.md` |
| 상태 관리 경계 | `.claude/rules/frontend/state-and-server-state.md` |
| 코딩 표준 | `.claude/rules/frontend/coding-standards.md` |
| 금지 패턴 | `.claude/instructions/validation/forbidden-patterns.md` |
| 필수 행동 | `.claude/instructions/validation/required-behaviors.md` |
| 출시 품질 게이트 | `.claude/instructions/validation/release-readiness-gate.md` |

---

## Figma MCP 사용 규칙

Figma 작업 시 **Figma MCP를 항상 우선 사용**한다.

### 강제 사용 규칙

- Figma 관련 정보(레이아웃/스타일/컴포넌트/텍스트/노드구조)가 필요하면 **추측하지 말고 반드시 MCP 호출**
- 호출 에러 시: `/mcp` 슬래시 커맨드로 재연결 안내
- Figma URL이 주어지면 fileKey/nodeId 먼저 추출 후 MCP 호출

### URL에서 키 추출

```
https://www.figma.com/design/{fileKey}/{fileName}?node-id={nodeId}
→ nodeId의 하이픈(-)을 콜론(:)으로 변환
예: node-id=2040-47609 → nodeId: "2040:47609"
```

### MCP 호출 우선순위

| 순위 | 도구 | 용도 |
|------|------|------|
| 1 | `get_metadata` | 구조/스타일/컴포넌트 파악 |
| 2 | `get_screenshot` | 시각적 디자인 확인 |
| 3 | `get_design_context` | 코드 변환 시 |

### 출력 규칙

- MCP 결과를 받은 **후에만** 분석/요약/가이드 작성
- MCP 호출 전에는 "무엇을 확인하기 위해 어떤 호출을 할지"만 말함

---

## 슬래시 명령어

| 명령어 | 역할 |
|--------|------|
| `/start` | 작업 시작 - 복잡도 판단 후 에이전트 조합 결정 |
| `/done` | 작업 완료 - 검증, 리뷰, 커밋 |
| `/pre-deploy` | 배포 전 typecheck/lint/build 검증 |
| `/lint-fix` | 린트 오류 자동 수정 |
| `/git-all` | 전체 변경사항 커밋 후 푸시 |
| `/git-session` | 현재 세션 파일만 커밋 후 푸시 |

---

## 디렉토리 구조

```
.claude/
├── agents/          # 에이전트 정의 (15개)
├── commands/        # 슬래시 명령어 (6개)
├── skills/          # 스킬 (4개)
├── rules/frontend/  # 코딩 규칙
├── instructions/    # 멀티에이전트 협업, 검증 규칙
├── hooks/           # UserPromptSubmit 훅
├── settings.json    # 훅 설정
├── plans/           # 작업 계획 (자동 생성, gitignored)
└── temp/            # 임시 파일 (자동 생성, gitignored)
```
