# Multi-Agent Coordination Guide

> 멀티 에이전트 병렬 실행으로 작업 효율 극대화

---

## 핵심 원칙

| 원칙           | 방법                                  | 효과               |
| -------------- | ------------------------------------- | ------------------ |
| **TEAM FIRST** | 복잡한 병렬 작업은 Agent Teams 우선   | 협업 + 수명주기    |
| **PARALLEL**   | 독립 작업은 단일 메시지에서 동시 호출 | 5-10배 속도 향상   |
| **BACKGROUND** | 긴 작업은 백그라운드로 실행           | 메인 컨텍스트 보호 |
| **DELEGATE**   | 전문 에이전트에 즉시 위임             | 품질 향상          |

```typescript
// 순차 실행 (120초)
Task((subagent_type = 'explore'), (prompt = '파일 구조 분석')); // 60초
Task((subagent_type = 'explore'), (prompt = 'API 패턴 분석')); // 60초

// 병렬 실행 (60초) - 단일 메시지에서 호출
Task((subagent_type = 'explore'), (model = 'haiku'), (prompt = '파일 구조 분석'));
Task((subagent_type = 'explore'), (model = 'haiku'), (prompt = 'API 패턴 분석'));
```

---

## Agent Teams 우선 원칙

> **Claude Max 전용** - Agent Teams(TeamCreate, SendMessage, shutdown)는 Claude Max에서만 사용 가능
> 일반 플랜에서는 기존 Task 병렬 호출로 자동 폴백

### 적용 기준

| 조건                       | 실행 방식                              |
| -------------------------- | -------------------------------------- |
| 3개+ 에이전트 병렬 협업    | **Agent Teams** (TeamCreate)           |
| 에이전트 간 통신 필요      | **Agent Teams** (SendMessage)          |
| 2개 이하 독립 작업         | Task 병렬 호출 (팀 불필요)             |
| Agent Teams 미가용 (플랜)  | Task 병렬 호출 (폴백)                  |

### Agent Teams 모드 (기본)

```typescript
// 1. 팀 생성
TeamCreate({ team_name: 'analysis-team', description: '코드 분석 및 리뷰' });

// 2. 팀원 spawn (병렬)
Task(subagent_type='explore', team_name='analysis-team', name='code-analyzer', model='haiku', prompt='코드 구조 분석');
Task(subagent_type='explore', team_name='analysis-team', name='pattern-checker', model='haiku', prompt='패턴 분석');
Task(subagent_type='code-reviewer', team_name='analysis-team', name='reviewer', model='sonnet', prompt='코드 리뷰');
```

### 수명주기 관리 (필수)

| 단계     | 작업                                           |
| -------- | ---------------------------------------------- |
| **생성** | TeamCreate → TaskCreate → Task(team_name=...)   |
| **협업** | SendMessage로 팀원 간 통신                      |
| **완료** | 팀원 태스크 완료 → shutdown_request 전송        |
| **정리** | 모든 팀원 종료 확인 → TeamDelete로 팀 해산      |

### 폴백 모드 (Agent Teams 미가용 시)

```typescript
// Agent Teams 없이 병렬 실행
Task(subagent_type='explore', model='haiku', prompt='코드 구조 분석');
Task(subagent_type='explore', model='haiku', prompt='패턴 분석');
Task(subagent_type='code-reviewer', model='sonnet', prompt='코드 리뷰');
```

### 규칙/스킬 참조 범위

팀원(서브에이전트)은 spawn 시 자동으로 프로젝트 규칙을 로드한다:

| 항목                 | 자동 로드 | 비고                             |
| -------------------- | :-------: | -------------------------------- |
| CLAUDE.md            |     O     | 프로젝트 전체 규칙               |
| .claude/rules/       |     O     | 코딩 표준, 컨벤션 등             |
| .claude/agents/*.md  |     O     | 해당 subagent_type 정의만 적용   |
| Skill 도구 (/start)  |     X     | 메인 에이전트 전용                |
| MCP 도구 (Figma)     |     X     | 메인 에이전트 전용                |

**제약**: Skill 도구(/start, /done 등)와 MCP 도구(Figma)는 메인 에이전트에서만 사용 가능.
커스텀 에이전트(explore, lint-fixer 등)는 도구가 제한됨.

---

## 역할 기반 서브에이전트 원칙 (공용)

> Agent Teams / 일반 Task 병렬 **모두에 적용**되는 공통 원칙

### general-purpose + 역할 프롬프트

구현이 필요한 서브에이전트는 **항상 `general-purpose`로 spawn**한다.
역할별 전문 지식은 **프롬프트에서 스킬/규칙 파일 읽기를 지시**하여 주입한다.

```
general-purpose + "figma-to-code 스킬 읽어" = 디자이너 역할 + 전체 도구
general-purpose + "refactor 스킬 읽어"      = 리팩토러 역할 + 전체 도구
general-purpose + "bug-fix 스킬 읽어"       = 버그 수정 역할 + 전체 도구
```

**이유:**
- `explore`, `lint-fixer` 등은 Read/Grep만 가능 → 구현 불가
- `general-purpose`는 Read, Write, Edit, Bash, Grep, Glob 모두 가능
- 프롬프트에서 스킬 파일을 읽게 하면 전문 지식 + 전체 도구를 동시에 확보

### 에이전트 타입 선택 기준

| 작업 유형          | 에이전트 타입       | 이유                        |
| ------------------ | ------------------- | --------------------------- |
| 읽기 전용 탐색     | `explore`           | 빠르고 가볍다               |
| 린트/타입 수정만   | `lint-fixer`        | 규칙 기반 단순 수정         |
| 구현이 필요한 작업 | **general-purpose** | Write/Edit/Bash 필요        |
| 스킬 지식 필요     | **general-purpose** | 스킬 파일 읽기 + 구현 동시  |

### 역할별 필수 참조 파일

| 역할         | 스킬 파일                                              | 규칙 파일                                   |
| ------------ | ------------------------------------------------------ | ------------------------------------------- |
| 퍼블리싱     | `${CLAUDE_PLUGIN_ROOT}/skills/figma-to-code/SKILL.md`  | 프로젝트 react-nextjs-conventions.md        |
| API 연동     | -                                                      | `${CLAUDE_PLUGIN_ROOT}/rules/coding-standards.md` |
| 리팩토링     | `${CLAUDE_PLUGIN_ROOT}/skills/refactor/SKILL.md`       | 프로젝트 unit-test-conventions.md           |
| 버그 수정    | `${CLAUDE_PLUGIN_ROOT}/skills/bug-fix/SKILL.md`        | -                                           |
| Codex 협업   | `${CLAUDE_PLUGIN_ROOT}/skills/codex/SKILL.md`          | MCP 설정 필수 (opt-in)                      |

---

## Agent Teams 역할 템플릿

> 각 팀원이 **독립적으로 서브태스크를 처리**하는 모드
> 팀원은 Skill/MCP 사용 불가 → 이슈 트래커는 Bash, Figma는 curl로 직접 접근

**퍼블리싱 (디자이너):**
```
Task(subagent_type='general-purpose', team_name='sprint-team', name='designer', model='sonnet',
  prompt=`
  ## 역할: 퍼블리싱 담당
  ## 담당 티켓: {티켓번호}

  ### 사전 준비 (필수)
  1. ${CLAUDE_PLUGIN_ROOT}/skills/figma-to-code/SKILL.md를 읽고 규칙을 숙지해

  ### 작업 흐름
  1. 이슈 트래커에서 티켓 조회
  2. Figma 분석: curl로 Figma REST API 호출
  3. 코드 분석 → Figma 기반 컴포넌트 구현
  4. 검증: figma-to-code 스킬의 Phase 4 체크리스트

  ### 완료 시 (필수)
  1. '${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/teammate-done-process.md'를 읽고 6단계 프로세스 수행
`);
```

**API 연동:**
```
Task(subagent_type='general-purpose', team_name='sprint-team', name='api-integrator', model='sonnet',
  prompt=`
  ## 역할: API 연동 담당
  ## 담당 티켓: {티켓번호}

  ### 사전 준비 (필수)
  1. ${CLAUDE_PLUGIN_ROOT}/rules/coding-standards.md를 읽어

  ### 작업 흐름
  1. 이슈 트래커에서 티켓 조회
  2. 기존 서비스/쿼리 패턴 분석
  3. V1 API 서비스 + TanStack Query 훅 구현
  4. 빌드 검증: Bash로 PROFILE=dev yarn build

  ### 완료 시 (필수)
  1. '${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/teammate-done-process.md'를 읽고 6단계 프로세스 수행
`);
```

**리팩토링:**
```
Task(subagent_type='general-purpose', team_name='sprint-team', name='refactorer', model='opus',
  prompt=`
  ## 역할: 리팩토링 담당
  ## 담당 티켓: {티켓번호}

  ### 사전 준비 (필수)
  1. ${CLAUDE_PLUGIN_ROOT}/skills/refactor/SKILL.md를 읽고 정책 보호 원칙 숙지

  ### 작업 흐름
  1. 이슈 트래커에서 티켓 조회
  2. refactor 스킬의 Phase 1~5 따라 진행
  3. 정책 보호 테스트 먼저 작성 → 리팩토링 → 테스트 통과 확인

  ### 완료 시 (필수)
  1. '${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/teammate-done-process.md'를 읽고 6단계 프로세스 수행
`);
```

### Agent Teams 워크플로우

```
1. 메인(팀 리드): /start {parent-ticket} 실행
   → 이슈 트래커 조회, Figma 분석 (MCP), 서브태스크 생성

2. 팀 생성 + 역할별 팀원 spawn:
   TeamCreate({ team_name: 'sprint-team', description: '서브태스크 병렬 처리' });
   Task(... name='designer' ...);       // 퍼블리싱
   Task(... name='api-integrator' ...);  // API 연동
   Task(... name='refactorer' ...);      // 리팩토링

3. 팀원 작업 (병렬):
   각 팀원: 스킬/규칙 읽기 → 이슈 조회 → Figma(curl) → 코드 분석 → 구현 → 보고

4. 팀 리드: 결과 취합, 충돌 해결, 빌드 검증

5. 평가: team-evaluation.md 기준으로 각 팀원 평가 (90+ A등급 목표)

6. 정리: 팀원별 shutdown_request → TeamDelete
```

### 팀 리드 완료 체크리스트 (필수)

> **shutdown 전에 반드시 이 체크리스트를 확인한다.**

```
□ 1. 각 팀원이 teammate-done-process.md 6단계를 수행했는지 확인
□ 2. 각 팀원 커밋 검증 (git log로 커밋 존재 + git diff로 범위 확인)
□ 3. 통합 린트/빌드 검증 (yarn lint)
□ 3.5 작업 절차 VERIFY 기준 최종 PASS 확인
□ 4. team-evaluation.md 기준 각 팀원 평가 작성 → 사용자에게 공유
□ 5. 평가 완료 후 → shutdown_request → TeamDelete
```

### Agent Teams 도구 매핑

| 기능             | 메인 에이전트       | 팀원 (general-purpose)           |
| ---------------- | ------------------- | -------------------------------- |
| 스킬 지식        | Skill 도구로 로드   | Read로 스킬 파일 직접 읽기       |
| 이슈 조회        | Skill → Bash        | Bash (이슈 트래커 CLI 직접)      |
| Figma 분석       | mcp__figma__* (MCP) | Bash (curl + Figma REST API)     |
| 코드 분석        | Read, Grep, Glob    | Read, Grep, Glob (동일)          |
| 구현             | Edit, Write         | Edit, Write (동일)               |
| 팀 보고          | -                   | SendMessage                      |

---

## 일반 Task 병렬 역할 템플릿

> 메인이 `/start`로 Figma MCP 분석을 완료한 후, **분석 결과를 프롬프트에 전달**하여 병렬 실행

**퍼블리싱:**
```
Task(subagent_type='general-purpose', model='sonnet',
  prompt=`
  ## 역할: 퍼블리싱 담당

  ### 사전 준비 (필수)
  1. ${CLAUDE_PLUGIN_ROOT}/skills/figma-to-code/SKILL.md를 읽고 규칙을 숙지해

  ### Figma 분석 결과 (메인에서 MCP로 분석 완료)
  {레이아웃, 색상, 타이포그래피, 컴포넌트 구조 등 MCP 분석 결과}

  ### 작업 내용
  {구체적 구현 지시}
`);
```

**API 연동:**
```
Task(subagent_type='general-purpose', model='sonnet',
  prompt=`
  ## 역할: API 연동 담당

  ### 사전 준비 (필수)
  1. ${CLAUDE_PLUGIN_ROOT}/rules/coding-standards.md를 읽어

  ### 작업 내용
  {API 스펙, 엔드포인트, 타입 정보 등 구체적 지시}
`);
```

**리팩토링:**
```
Task(subagent_type='general-purpose', model='opus',
  prompt=`
  ## 역할: 리팩토링 담당

  ### 사전 준비 (필수)
  1. ${CLAUDE_PLUGIN_ROOT}/skills/refactor/SKILL.md를 읽고 정책 보호 원칙 숙지

  ### 작업 내용
  {리팩토링 대상, 목표, 제약 조건}
`);
```

**버그 수정:**
```
Task(subagent_type='general-purpose', model='sonnet',
  prompt=`
  ## 역할: 버그 수정 담당

  ### 사전 준비 (필수)
  1. ${CLAUDE_PLUGIN_ROOT}/skills/bug-fix/SKILL.md를 읽고 분석 → 옵션 → 수정 흐름 숙지

  ### 작업 내용
  {에러 증상, 발생 조건, 관련 파일}
`);
```

---

## 모델 라우팅 전략

### 기본 복잡도 기준

| 복잡도     | 모델   | 사용 케이스                               | 비용   |
| ---------- | ------ | ----------------------------------------- | ------ |
| **LOW**    | haiku  | 파일 탐색, 단순 검색, 린트 수정           | $      |
| **MEDIUM** | sonnet | 코드 리뷰, 테스트 생성, 구현              | $$     |
| **HIGH**   | opus   | 아키텍처 설계, 복잡한 버그, 리팩토링 분석 | $$$    |

### 비즈니스 정책 관련 = 상향 조정

| 정책 키워드                       | 최소 모델  | 이유               |
| --------------------------------- | ---------- | ------------------ |
| `getPeriod`, `addDate`, 날짜 계산 | **opus**   | 비즈니스 규칙 복잡 |
| `disabled`, `readonly` 조건       | **sonnet** | 상태 의존성        |
| `filterState`, 필터 조건          | **sonnet** | 연쇄 영향          |
| 가격, 할인, 계산 로직             | **opus**   | 정확성 중요        |
| 주문 상태 전이                    | **opus**   | 상태 머신 이해     |

---

## 컨텍스트 보존 전략

### 1. 문서 기반 핸드오프

에이전트 간 컨텍스트는 파일로 전달:

```typescript
// Agent 1: 분석 결과를 파일에 저장
Task((subagent_type = 'explore'), (prompt = '분석 후 .claude/temp/analysis.md에 저장'));

// Agent 2: 파일 읽어서 작업 수행
Task((subagent_type = 'implementor'), (prompt = '.claude/temp/analysis.md 읽고 구현'));
```

### 2. 프롬프트 내 컨텍스트 명시

```typescript
Task(
  (subagent_type = 'testgen'),
  (prompt = `
  대상: apps/{앱이름}/src/{도메인}/views/listV2/useOrderListV2.ts
  기존 패턴: packages/shared/queries 참조
  테스트 위치: __tests__/useOrderListV2.test.ts
`)
);
```

---

## 에러 핸들링

| 전략              | 설명                        | 적용         |
| ----------------- | --------------------------- | ------------ |
| **실패 격리**     | 에이전트 실패가 전체 영향 X | 병렬 실행 시 |
| **재시도**        | 최대 3회, 지수 백오프       | 일시적 실패  |
| **서킷 브레이커** | 연속 실패 시 중단           | API 호출     |

---

## 참조 문서

| 문서              | 경로                                                               |
| ----------------- | ------------------------------------------------------------------ |
| 에이전트 목록     | `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/agent-roster.md`        |
| 실행 패턴         | `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/execution-patterns.md`  |
| 팀원 완료 프로세스 | `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/teammate-done-process.md` |
| 팀원 평가 템플릿  | `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/team-evaluation.md`     |
| 금지 패턴         | `${CLAUDE_PLUGIN_ROOT}/instructions/validation/forbidden-patterns.md`   |
| 작업 절차         | `${CLAUDE_PLUGIN_ROOT}/rules/thinking-model.md`                         |
