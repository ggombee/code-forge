# Agent Teams 활용 가이드

> Agent Teams를 기본으로 사용한다. 토큰 비용(5-7x)은 Model Routing으로 최적화.

---

## 사용 기준

| 조건 | 실행 방식 |
|------|----------|
| 3개+ 에이전트 병렬 협업 | **Agent Teams** (TeamCreate) |
| 에이전트 간 통신 필요 | **Agent Teams** (SendMessage) |
| 2개 이하 독립 작업 | Task 병렬 호출 (팀 불필요) |
| Agent Teams 미가용 (플랜) | Task 병렬 호출 (폴백) |
| 단순 질문/단일 파일 | 직접 처리 |

---

## 7단계 기본 흐름

| 단계 | 도구 | 작업 |
|------|------|------|
| 1 | `TeamCreate` | 팀 생성 |
| 2 | `TaskCreate` | 작업 생성 |
| 3 | `Task` | 팀원 spawn (team_name 지정) |
| 4 | `TaskUpdate` | 작업 할당 (owner 지정) |
| 5 | `SendMessage` | 팀원 간 통신 |
| 6 | `SendMessage` | shutdown_request |
| 7 | `TeamDelete` | 팀 해산 |

---

## 비용 절감 전략 (우선순위순)

| 순위 | 전략 | 절감 효과 |
|------|------|----------|
| 1 | **Model Routing** - Lead는 opus, 팀원은 sonnet/haiku | 40% |
| 2 | **계획 우선** - 실행 전 계획 수립 및 승인 | 불필요 작업 방지 |
| 3 | **즉시 정리** - 완료 후 shutdown → TeamDelete | 유휴 비용 제거 |
| 4 | **직접 메시지** - broadcast 대신 message 사용 | N배 절감 |
| 5 | **간결한 프롬프트** - 문서 자동 로드 활용 | 토큰 절약 |

---

## 팀 구성 가이드

| 원칙 | 방법 |
|------|------|
| **팀원당 5-6개 작업** | 명확한 작업 분할 |
| **한 파일 = 한 팀원** | 충돌 방지 |
| **역할별 3-4명** | 리서치, 구현, 리뷰 등 |
| **general-purpose 기본** | 구현 필요 → general-purpose + 스킬 파일 읽기 |

---

## 코드 예시

### 팀 생성 + 팀원 spawn

```typescript
// 1. 팀 생성
TeamCreate({ team_name: 'sprint-team', description: '스프린트 작업' });

// 2. 작업 생성
TaskCreate({ subject: '퍼블리싱', description: '...' });
TaskCreate({ subject: 'API 연동', description: '...' });

// 3. 팀원 spawn (병렬)
Task(subagent_type='general-purpose', team_name='sprint-team', name='designer', model='sonnet',
  prompt='퍼블리싱 담당. skills/figma-to-code/SKILL.md를 먼저 읽어');
Task(subagent_type='general-purpose', team_name='sprint-team', name='api-dev', model='sonnet',
  prompt='API 연동 담당. rules/coding-standards.md를 먼저 읽어');
```

### Codex Team Lead 모드

```typescript
// Codex를 Team Lead로 사용
TeamCreate({ team_name: 'codex-project', agent_type: 'codex' });

// 팀원 spawn
Task(subagent_type='implementation-executor', team_name='codex-project', name='impl', prompt='...');

// Codex가 품질 검증
mcp__codex__codex_review({ uncommitted: true });

// 정리
SendMessage({ type: 'shutdown_request', recipient: 'impl' });
TeamDelete();
```

---

## 수명주기 관리 (필수)

| 단계 | 작업 | 주의 |
|------|------|------|
| **생성** | TeamCreate → TaskCreate → Task(team_name=...) | - |
| **협업** | SendMessage로 팀원 간 통신 | broadcast 최소화 |
| **완료** | 팀원 태스크 완료 확인 | teammate-done-process.md 6단계 |
| **종료** | shutdown_request → 응답 대기 | 팀원 컨텍스트 소실 주의 |
| **정리** | TeamDelete | 모든 팀원 종료 확인 후 |

---

## 주의사항

| 항목 | 내용 |
|------|------|
| **세션 재개** | in-progress 팀원 복원 불가 |
| **세션당 팀** | 한 세션에 한 팀만 생성 가능 |
| **토큰 한도** | 팀원당 약 200k 토큰, 그 전에 완료 권장 |
| **shutdown 순서** | done 프로세스 확인 → shutdown → TeamDelete |

---

## 참조 문서

| 문서 | 용도 |
|------|------|
| `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/coordination-guide.md` | 역할 템플릿, 모델 라우팅 |
| `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/teammate-done-process.md` | 팀원 완료 프로세스 |
| `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/team-evaluation.md` | 팀원 평가 기준 |
| `${CLAUDE_PLUGIN_ROOT}/instructions/agent-patterns/model-routing.md` | 모델 선택 기준 |
| `${CLAUDE_PLUGIN_ROOT}/instructions/agent-patterns/parallel-execution.md` | 병렬 실행 패턴 |
