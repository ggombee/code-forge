# Agent Roster

> 프로젝트에 최적화된 전문 에이전트 카탈로그

**모델 선택 기준**: `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/coordination-guide.md` 참조 (단일 진실 공급원)

---

## 에이전트 전체 목록

| 에이전트 | 기본 모델 | 도구 | 차단 도구 | 병렬 | 용도 |
|----------|-----------|------|----------|------|------|
| **explore** | haiku | Read, Glob, Grep, Bash | Write, Edit | O | 코드베이스 탐색, 패턴 분석 |
| **analyst** | opus | Read, Grep, Glob | Write, Edit, Bash | O | 요구사항 분석, 갭 식별 |
| **architect** | opus | Read, Grep, Glob | Write, Edit, Bash | O | 아키텍처 분석, 설계 자문 |
| **researcher** | sonnet | Read, Grep, Glob, Bash | Write, Edit | O | 외부 문서/라이브러리 조사 |
| **code-reviewer** | sonnet | Read, Grep, Glob, Bash | Write, Edit | O | 코드 리뷰 (품질+보안, mode: quality/security/both) |
| **refactor-advisor** | sonnet | Read, Grep, Glob | Write, Edit, Bash | O | 리팩토링 분석, 개선 전략 |
| **vision** | sonnet | Read | Write, Edit, Bash | O | 미디어 파일 분석, 정보 추출 |
| **lint-fixer** | haiku | Read, Edit, Bash | Write, Glob, Grep | O | 린트/타입 오류 수정 |
| **build-fixer** | sonnet | Read, Edit, Bash, Glob | Write | O | 빌드/컴파일 오류 수정 |
| **assayer** | sonnet | Read, Write, Edit, Bash, Grep, Glob | - | O | 테스트 생성 (mode: generate/tdd) |
| **implementor** | sonnet | Read, Write, Edit, Grep, Glob, Bash | - | ! | 계획 기반 즉시 구현 |
| **deep-executor** | sonnet | Read, Write, Edit, Bash, Grep, Glob | - | ! | 자율적 심층 구현 |
| **codex** | sonnet | Read, Write, Edit, Grep, Glob, Bash + MCP | - | ! | Codex 페어 프로그래밍 (MCP opt-in) |
| **git-operator** | sonnet | Read, Grep, Glob, Bash | Write, Edit | X | Git 커밋/브랜치 관리 |
| **Plan** | opus | (내장) | (내장) | X | 아키텍처 설계, 구현 계획 |

> 병렬: O = 가능, ! = 같은 파일 수정 시 순차 필수, X = 순차 전용
> 정책 키워드(날짜 계산, disabled 조건, 가격 등) 포함 시 모델 상향 - coordination-guide.md 참조

---

## 에이전트 분류

### 분석 전용 (READ-ONLY)

코드를 수정하지 않고 분석/리포트만 제공하는 에이전트.

| 에이전트 | 목적 | 출력 |
|----------|------|------|
| **explore** | 코드베이스 탐색 | 파일 목록, 패턴 분석 |
| **analyst** | 요구사항 갭 분석 | 7섹션 분석 리포트 |
| **architect** | 아키텍처 분석 | 진단, 권장사항, 트레이드오프 |
| **researcher** | 외부 문서 조사 | 출처 URL 포함 리서치 리포트 |
| **code-reviewer** | 코드 리뷰 (품질+보안) | 심각도별 피드백, OWASP 취약점 리포트 |
| **refactor-advisor** | 리팩토링 분석 | Before/After + 우선순위 |
| **vision** | 미디어 파일 분석 | 구조화된 정보 추출 |

### 수정 전문 (READ-WRITE)

코드를 직접 수정하는 에이전트.

| 에이전트 | 목적 | 수정 범위 |
|----------|------|----------|
| **lint-fixer** | 린트/타입 오류 수정 | 오류 라인만 |
| **build-fixer** | 빌드 오류 수정 | 최소 diff |
| **assayer** | 테스트 생성 + TDD | 테스트 파일 (+ TDD 시 구현) |
| **implementor** | 계획 기반 구현 | 대상 파일 |
| **deep-executor** | 자율적 심층 구현 | 대상 파일 (넓은 범위) |

### Codex 협업 (MCP opt-in)

MCP 서버 설정 시에만 사용 가능. 미설정 환경에서는 무시.

| 에이전트 | 목적 | 전제 조건 |
|----------|------|----------|
| **codex** | Codex 페어 프로그래밍, Team Lead | codex-mcp MCP 서버 |

### Git 전용

| 에이전트 | 목적 |
|----------|------|
| **git-operator** | 커밋, 브랜치, 스테이징 |

---

## 에이전트 상세

### explore

**목적**: 코드베이스 빠른 탐색, 파일 구조 파악

```typescript
Task(subagent_type='explore', model='haiku', prompt='apps/{앱이름}/src/{도메인} 폴더 구조 파악');
Task(subagent_type='explore', model='sonnet', prompt='필터 disabled 조건 분석');
```

---

### analyst

**목적**: 계획 전 요구사항 심층 분석, 놓친 질문/가정/엣지 케이스 발견

```typescript
Task(subagent_type='analyst', model='opus', prompt='결제 시스템 리팩토링 요구사항 분석');
```

---

### architect

**목적**: 아키텍처 분석 및 설계 자문 (READ-ONLY)

```typescript
Task(subagent_type='architect', model='opus', prompt='현재 상태 관리 아키텍처 분석 및 개선 방향');
```

---

### researcher

**목적**: 외부 문서/라이브러리 조사, 출처 URL 필수

```typescript
Task(subagent_type='researcher', model='sonnet', prompt='TanStack Query v5 migration guide 조사');
```

---

### code-reviewer

**목적**: PR 전 코드 품질 검증

```typescript
// mode: quality (기본), security, both
Task(subagent_type='code-reviewer', model='sonnet', prompt='apps/{앱이름}/src/{도메인}/ 코드 리뷰 (mode: both)');
```

---

### refactor-advisor

**목적**: 리팩토링 분석, 우선순위별 개선 전략 (READ-ONLY)

```typescript
Task(subagent_type='refactor-advisor', model='sonnet', prompt='주문 목록 컴포넌트 리팩토링 분석');
```

---

### vision

**목적**: 미디어 파일(이미지, PDF, 다이어그램) 분석 및 정보 추출 (READ-ONLY)

```typescript
Task(subagent_type='vision', model='sonnet', prompt='파일: /path/to/document.pdf\n추출: API 엔드포인트 목록과 필수 파라미터');
```

---

### lint-fixer

**목적**: ESLint/TypeScript 오류 자동 수정

```typescript
Task(subagent_type='lint-fixer', model='haiku', prompt='apps/{앱이름}/src/{도메인}/ 린트 오류 수정');
```

---

### build-fixer

**목적**: 빌드/타입/컴파일 오류 수정

```typescript
Task(subagent_type='build-fixer', model='sonnet', prompt='yarn build 실패 오류 수정');
```

---

### assayer

**목적**: 테스트 생성 (mode: generate/tdd)

```typescript
// generate 모드 (기본) — BDD 시나리오 기반 테스트 생성
Task(subagent_type='assayer', prompt='apps/{앱이름}/src/{도메인}/views/list/components/Table 테스트');

// tdd 모드 — Red-Green-Refactor 사이클
Task(subagent_type='assayer', prompt='calculateDiscount 함수 TDD로 구현 (mode: tdd)');
```

**주의**: 순수 함수(utils, helpers)는 Claude가 직접 작성, 컴포넌트/훅은 assayer 사용

---

### implementor

**목적**: 계획된 코드 구현 실행

```typescript
Task(subagent_type='implementor', model='sonnet', prompt='계획: .claude/temp/plan.md 참조');
```

**! 병렬 제한**: 같은 파일 수정 시 순차 실행 필수

---

### deep-executor

**목적**: 복잡한 작업을 자율적으로 탐색→계획→실행

```typescript
Task(subagent_type='deep-executor', model='sonnet', prompt='주문 상세 페이지 전체 구현');
```

**! 병렬 제한**: 같은 파일 수정 시 순차 실행 필수

---

### codex

**목적**: OpenAI Codex와 페어 프로그래밍 (MCP 설정 시에만 사용 가능)

```typescript
// Solo+Review: Claude 구현 후 Codex 리뷰
mcp__codex__codex_review({ uncommitted: true });

// Team Lead: 팀 생성 → 팀원 spawn → 품질 검증
TeamCreate({ team_name: 'project', agent_type: 'codex' });
Task({ subagent_type: 'implementor', team_name: 'project', name: 'impl', prompt: '...' });
mcp__codex__codex_review({ uncommitted: true });
```

**전제 조건**: codex-mcp MCP 서버 설정 필수. 미설정 시 완전 무시.
**! 병렬 제한**: 동일 파일 동시 수정 금지 (Claude/Codex 충돌 방지)

---

### git-operator

**목적**: 프로젝트 커밋 규칙에 맞는 안전한 Git 작업

```typescript
Task(subagent_type='git-operator', model='sonnet', prompt='현재 변경사항 커밋');
```

---

## 조합 패턴

### 분석 → 구현

```typescript
// 1. 요구사항 분석 (opus)
Task(subagent_type='analyst', model='opus', prompt='요구사항 분석');

// 2. 아키텍처 분석 (opus)
Task(subagent_type='architect', model='opus', prompt='아키텍처 분석');

// 3. 구현 (sonnet)
Task(subagent_type='deep-executor', model='sonnet', prompt='분석 기반 구현');
```

### 구현 → 검증 (병렬)

```typescript
Task(subagent_type='lint-fixer', model='haiku', prompt='린트 수정');
Task(subagent_type='assayer', model='sonnet', prompt='테스트 생성');
Task(subagent_type='code-reviewer', model='sonnet', prompt='코드 리뷰 (mode: both)');
```

### 리팩토링 흐름

```typescript
// 1. 리팩토링 분석 (sonnet)
Task(subagent_type='refactor-advisor', model='sonnet', prompt='리팩토링 분석');

// 2. TDD로 보호 테스트 (sonnet) — assayer의 tdd 모드 사용
Task(subagent_type='assayer', model='sonnet', prompt='정책 보호 테스트 (mode: tdd)');

// 3. 리팩토링 구현 (sonnet)
Task(subagent_type='implementor', model='sonnet', prompt='리팩토링 실행');
```

---

## 에이전트 선택 의사결정 트리

```
작업이 들어옴
  │
  ├─ 분석/리뷰만 필요? (코드 수정 없음)
  │   ├─ 아키텍처/설계 판단 → architect (opus)
  │   ├─ PR/코드 품질 검증 → code-reviewer (sonnet)
  │   ├─ "이 코드 어떻게 개선?" → refactor-advisor (sonnet)
  │   ├─ 외부 라이브러리 조사 → researcher (sonnet)
  │   ├─ 요구사항 갭 분석 → analyst (opus)
  │   └─ 파일/패턴 탐색 → explore (haiku)
  │
  ├─ 오류 수정만 필요?
  │   ├─ ESLint/tsc 오류 → lint-fixer (haiku, 저비용)
  │   └─ 빌드/컴파일 실패 → build-fixer (sonnet)
  │
  ├─ 구현 필요?
  │   ├─ 계획/명세가 이미 있음 → implementor (sonnet)
  │   ├─ 탐색부터 자율 수행 → deep-executor (sonnet)
  │   └─ Codex 리뷰 포함 → codex (sonnet, MCP 필요)
  │
  └─ 테스트 필요?
      ├─ 기존 코드에 테스트 추가 → assayer (generate 모드)
      └─ 새 기능 TDD 개발 → assayer (tdd 모드)
```

## 스킬 ↔ 에이전트 매핑

스킬이 내부적으로 어떤 에이전트를 호출하는지:

| 스킬 | 사용 에이전트 | 비고 |
|------|-------------|------|
| `/start` | analyst → implementor → code-reviewer → git-operator | 전체 파이프라인 |
| `/done` | code-reviewer → git-operator | 검증+커밋 |
| `/bug-fix` | (직접 구현, 에이전트 없음) | 2-3 옵션 제시 후 직접 수정 |
| `/quality` | lint-fixer → (tsc 직접 실행) | 자동 수정 파이프라인 |
| `/refactor` | refactor-advisor → assayer → implementor | 분석→보호테스트→구현 |
| `/generate-test` | assayer (generate 모드) | 스킬이 에이전트의 인터페이스 |
| `/debate` | (멀티모델 직접 호출) | Agent Teams 사용 시 병렬 |
| `/research` | researcher | 스킬이 에이전트의 인터페이스 |
| `/codex` | codex | MCP opt-in |

---

## 참조 문서

| 문서 | 용도 |
|------|------|
| `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/coordination-guide.md` | 병렬 실행 원칙, 모델 라우팅 |
| `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/execution-patterns.md` | 실행 패턴 상세 |
| `${CLAUDE_PLUGIN_ROOT}/instructions/validation/forbidden-patterns.md` | 금지 패턴 |
| `${CLAUDE_PLUGIN_ROOT}/rules/thinking-model.md` | 작업 절차 |
