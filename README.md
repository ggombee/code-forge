# ggombee-agents

모든 프로젝트에서 재사용 가능한 Claude Code 멀티 에이전트 시스템.

에이전트 정의, 코딩 규칙, 스킬, 슬래시 명령어를 한 세트로 관리하고, 어떤 프로젝트에든 한 줄로 적용한다.

---

## 설치

### 새 프로젝트에 적용

```bash
# 어디서든 프로젝트 경로만 넘기면 됨
bash ~/Desktop/ggombee-agents/init.sh /path/to/my-project
```

GitHub에서 직접:

```bash
bash <(curl -s https://raw.githubusercontent.com/ggombee/ggombee-agents/main/init.sh) /path/to/my-project
```

경로 생략 시 현재 디렉토리에 설치된다.

설치되는 파일:

| 파일 | 역할 |
|------|------|
| `.claude/` | 에이전트, 규칙, 스킬, 명령어, 훅 |
| `CLAUDE.md` | Claude Code 진입점 (AI가 읽는 메인 문서) |
| `.gitignore` | 기본 제외 규칙 |

### 규칙 업데이트

중앙 레포에서 규칙을 수정한 뒤, 같은 스크립트를 다시 실행하면 최신으로 덮어쓴다.

```bash
# 기존 .claude/가 있으면 덮어쓸지 물어봄
bash ~/Desktop/ggombee-agents/init.sh /path/to/my-project
```

---

## 구조

```
.claude/
├── agents/          # 15개 에이전트 정의 (explore, code-reviewer, ...)
├── commands/        # 슬래시 명령어 (/start, /done, /git-all, ...)
├── skills/          # 스킬 (bug-fix, refactor, figma-to-code, docs-creator)
├── rules/
│   └── frontend/    # 코딩 표준, React 컨벤션, 상태 관리, 사고 모델
├── instructions/
│   ├── multi-agent/ # 에이전트 협업, 모델 라우팅, 실행 패턴
│   └── validation/  # 금지 패턴, 필수 행동, 출시 게이트
├── hooks/           # UserPromptSubmit 훅 (스킬 자동 평가)
├── settings.json    # 훅 설정
├── plans/           # 작업 계획 (자동 생성, gitignored)
└── temp/            # 임시 분석 파일 (자동 생성, gitignored)
```

---

## 사용법

### 슬래시 명령어

| 명령어 | 역할 |
|--------|------|
| `/start` | 작업 시작 — 복잡도 판단 후 에이전트 조합 결정 |
| `/done` | 작업 완료 — 검증, 리뷰, 커밋/PR |
| `/pre-deploy` | 배포 전 typecheck/lint/build 검증 |
| `/lint-fix` | 린트 오류 자동 수정 |
| `/git-all` | 전체 변경사항 커밋 후 푸시 |
| `/git-session` | 현재 세션 파일만 커밋 후 푸시 |

### 스킬 (자동 발동)

| 스킬 | 트리거 키워드 |
|------|---------------|
| bug-fix | 버그, 오류, 에러, 동작 안함 |
| refactor | 리팩토링, 구조 개선, 중복 제거 |
| figma-to-code | 이미지 첨부 + 구현, 시안대로 |
| docs-creator | 새 프로젝트, 문서 작성/업데이트 |

### 에이전트

기본팀 (대부분 작업):

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| explore | haiku | 코드베이스 탐색 |
| implementation-executor | sonnet | 코드 구현 |
| code-reviewer | sonnet | 코드 리뷰 |
| deployment-validator | sonnet | 배포 전 검증 |
| git-operator | haiku | Git 커밋/푸시 |

필요시 투입: designer, vision, researcher, security-reviewer, qa-tester, document-writer, lint-fixer, build-fixer, architect, planner

---

## 핵심 규칙 요약

- **사고 모델**: READ → REACT → ANALYZE → RESTRUCTURE → STRUCTURE → REFLECT
- **모델 라우팅**: LOW → haiku / MEDIUM → sonnet / HIGH → opus
- **코드 품질**: No `any`, 반환 타입 명시, immutability, import 순서
- **상태 관리**: 서버 상태는 TanStack Query, 전역 UI는 Jotai/Zustand, 폼은 React Hook Form

상세 규칙은 `CLAUDE.md`와 `.claude/rules/`, `.claude/instructions/`를 참조.

---

## 프로젝트별 커스터마이즈

규칙을 프로젝트에 맞게 조정하려면 해당 파일을 직접 수정한다. 모든 규칙 파일은 범용으로 작성되어 있어 대부분 수정 없이 사용 가능하다.

프로젝트 특화 설정이 필요하면 `CLAUDE.md` 하단에 프로젝트 섹션을 추가하는 것을 권장한다.

```markdown
## 프로젝트 설정

- 패키지 매니저: pnpm
- 모노레포: turborepo
- API: /api/v2 prefix
```
