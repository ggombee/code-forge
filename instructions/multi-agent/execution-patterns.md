# Execution Patterns

> 작업 유형별 최적 실행 패턴

**모델 선택 기준**: `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/coordination-guide.md` 참조 (단일 진실 공급원)

---

## 패턴 개요

| 패턴                        | 사용 시점               | 토큰 절감     |
| --------------------------- | ----------------------- | ------------- |
| **Agent Teams**             | 3개+ 에이전트 협업 필요 | 팀 기반 협업  |
| **Single-Message Parallel** | 독립 작업 동시 실행     | 50-70%        |
| **Fan-Out/Fan-In**          | 분할 → 병합             | 60-80%        |
| **Sequential Pipeline**     | 의존성 있는 작업        | -             |
| **Batching**                | 대량 파일 처리          | 70-90%        |
| **Background**              | 긴 작업 분리            | 컨텍스트 보호 |

---

## 0. Agent Teams (Claude Max 전용)

> 3개 이상 에이전트가 협업하거나 에이전트 간 통신이 필요한 경우 사용
> Agent Teams 미가용 시 패턴 1(Single-Message Parallel)로 폴백

```typescript
// 팀 생성
TeamCreate({ team_name: 'commit-analysis', description: '커밋 분석 및 계획' });

// 팀원 spawn (병렬) - 모두 general-purpose + 역할 프롬프트
Task(subagent_type='general-purpose', team_name='commit-analysis', name='lint-analyzer', model='sonnet',
  prompt='린트/타입 에러 분석');
Task(subagent_type='general-purpose', team_name='commit-analysis', name='commit-planner', model='opus',
  prompt='커밋 분리 계획 수립');
Task(subagent_type='general-purpose', team_name='commit-analysis', name='risk-checker', model='sonnet',
  prompt='시크릿/위험 파일 검출');

// 수명주기: 완료 → shutdown → TeamDelete
```

**적용 케이스:**

| 케이스           | 팀 이름            | 팀원 구성                                |
| ---------------- | ------------------ | ---------------------------------------- |
| 커밋 분석/계획   | `commit-analysis`  | lint-analyzer, commit-planner, risk-checker |
| 대규모 리팩토링  | `refactor-team`    | analyzer, planner, implementor            |
| 코드 리뷰        | `review-team`      | structure-reviewer, logic-reviewer        |
| Figma → 코드     | `figma-team`       | designer, implementor, reviewer           |
| 테스트 생성      | `test-team`        | analyzer, test-writer, validator          |
| Codex 페어 리뷰  | `codex-review-team`| implementor (Claude), codex-reviewer (MCP opt-in) |

---

## 1. Single-Message Parallel

**독립 작업을 단일 메시지에서 동시 호출.**

```typescript
// 단순 구조 탐색: haiku
Task((subagent_type = 'scout'), (model = 'haiku'), (prompt = 'apps/{앱이름}/src/{도메인} 폴더 구조 파악'));
Task((subagent_type = 'scout'), (model = 'haiku'), (prompt = 'packages/shared/queries 파일 목록'));

// 정책/로직 분석: sonnet
Task((subagent_type = 'scout'), (model = 'sonnet'), (prompt = '주문 필터 조건 분석 - disabled, 기본값'));
Task((subagent_type = 'scout'), (model = 'sonnet'), (prompt = '기간 계산 로직 분석 - getPeriod 구현'));
```

---

## 2. Fan-Out/Fan-In

**하나의 작업을 여러 에이전트로 분할 후 결과 병합.**

```typescript
// Fan-Out: 도메인별 분석 (sonnet - 정책 이해 필요)
Task((subagent_type = 'scout'), (model = 'sonnet'), (prompt = 'order 도메인 정책 분석 → .claude/temp/order.md'));
Task((subagent_type = 'scout'), (model = 'sonnet'), (prompt = 'payment 도메인 정책 분석 → .claude/temp/payment.md'));

// Fan-In: 결과 수집
Read('.claude/temp/order.md');
Read('.claude/temp/payment.md');

// 통합 분석 (opus - 복잡한 관계 파악)
Task((subagent_type = 'Plan'), (model = 'opus'), (prompt = '도메인 간 정책 관계 분석'));
```

---

## 3. Sequential Pipeline

**의존성이 있는 작업의 순차 실행.**

```typescript
// 1단계: 구조 탐색 (haiku)
Task((subagent_type = 'scout'), (model = 'haiku'), (prompt = '파일 구조 파악'));

// 2단계: 정책 분석 (sonnet/opus)
Task((subagent_type = 'scout'), (model = 'sonnet'), (prompt = '비즈니스 로직 분석'));

// 3단계: 계획 수립 (opus)
Task((subagent_type = 'Plan'), (model = 'opus'), (prompt = '분석 결과 기반 구현 계획'));

// 4단계: 구현 (sonnet)
Task((subagent_type = 'implementor'), (model = 'sonnet'), (prompt = '계획대로 구현'));

// 5단계: 검증 (sonnet)
Task((subagent_type = 'testgen'), (model = 'sonnet'), (prompt = '정책 보호 테스트 생성'));
```

---

## 4. Batching

**대량 파일을 청크로 분할하여 처리.**

```typescript
// 린트 수정: haiku (단순 수정)
Task((subagent_type = 'lint-fixer'), (model = 'haiku'), (prompt = '파일 처리: file1.ts, file2.ts, file3.ts'));

// 타입 수정: sonnet (타입 이해 필요)
Task((subagent_type = 'lint-fixer'), (model = 'sonnet'), (prompt = '복잡한 타입 오류 수정: file4.ts, file5.ts'));
```

---

## 5. Background

**긴 작업을 백그라운드로 분리.**

```typescript
// 테스트 생성: sonnet (BDD 시나리오 이해)
Task((subagent_type = 'testgen'), (model = 'sonnet'), (run_in_background = true), (prompt = '전체 order 도메인 테스트 생성'));
```

---

## /start 커맨드 패턴

### 단계별 모델 선택

```typescript
// 1단계: 복잡도 판단 (haiku - 빠른 초기 파악)
Task(
  (subagent_type = 'scout'),
  (model = 'haiku'),
  (prompt = `
  티켓: {티켓번호}
  복잡도 판단:
  - 영향 파일 수
  - 정책 키워드 포함 여부 (getPeriod, disabled, filter 등)
  결과: LOW / MEDIUM / HIGH
`)
);

// 2단계: 복잡도별 분석
// LOW → haiku
// MEDIUM → sonnet
// HIGH → opus

// 3단계: Figma 분석 (sonnet - 디자인 의도 파악)
Task((subagent_type = 'scout'), (model = 'sonnet'), (prompt = 'Figma 디자인 분석 - 상태별 스타일, 인터랙션'));

// 4단계: 정책 분석 (HIGH일 때 opus)
Task(
  (subagent_type = 'Plan'),
  (model = 'opus'),
  (prompt = `
  정책 분석:
  - 기존 비즈니스 로직
  - 변경 영향 범위
  - 정책 보호 테스트 필요 여부
`)
);
```

---

## /done 커맨드 패턴

```typescript
// 병렬 검증
Task((subagent_type = 'lint-fixer'), (model = 'haiku'), (prompt = '린트 오류 수정'));
Task((subagent_type = 'testgen'), (model = 'sonnet'), (prompt = '정책 보호 테스트 생성'));
Task((subagent_type = 'code-reviewer'), (model = 'sonnet'), (prompt = '코드 리뷰 - 정책 준수 확인'));
// Codex MCP 설정 시 선택 추가: codex_review로 변경사항 더블체크

// 결과 확인 후 PR 생성
Bash('gh pr create ...');
```

---

## 작업별 권장 모델

| 작업                | 모델        | 이유              |
| ------------------- | ----------- | ----------------- |
| 파일/폴더 구조 탐색 | haiku       | 단순 탐색         |
| 린트/포맷 수정      | haiku       | 규칙 기반 수정    |
| UI 컴포넌트 분석    | sonnet      | 디자인 의도 파악  |
| 비즈니스 로직 분석  | sonnet/opus | 정책 이해 필수    |
| 정책 변경 계획      | opus        | 영향 범위 판단    |
| 테스트 생성         | sonnet      | BDD 시나리오 도출 |
| 아키텍처 설계       | opus        | 전체 구조 파악    |

---

## 참조 문서

| 문서                      | 용도          |
| ------------------------- | ------------- |
| `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/coordination-guide.md` | 핵심 원칙     |
| `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/agent-roster.md`       | 에이전트 상세 |
