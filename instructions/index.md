# Instructions Index

> Claude Code 작업 효율화를 위한 가이드 모음

---

## 개요

**목표**: 멀티 에이전트 협업, 병렬 실행, 검증 자동화를 통한 효율성 극대화

**핵심 효과**:

- 병렬 실행으로 5-10배 속도 향상
- 모델 라우팅으로 비용 최적화
- 전문 에이전트로 품질 보증

---

## 문서 구조

```
instructions/
├── index.md                          # 이 파일
├── agent-patterns/
│   ├── parallel-execution.md         # 병렬 실행 패턴
│   ├── read-parallelization.md       # 파일 읽기 병렬화
│   ├── model-routing.md              # 모델 선택 기준
│   └── agent-teams-usage.md          # Agent Teams 활용
├── multi-agent/
│   ├── coordination-guide.md         # 병렬 실행 핵심 원칙
│   ├── agent-roster.md               # 에이전트 카탈로그
│   ├── execution-patterns.md         # 실행 패턴 상세
│   ├── teammate-done-process.md      # 팀원 작업 완료 프로세스
│   └── team-evaluation.md            # 팀원 평가 템플릿
└── validation/
    └── forbidden-patterns.md         # 금지 패턴 목록
```

---

## 문서 카탈로그

### Agent Patterns

| 문서                    | 용도                                    | 사용 시점                |
| ----------------------- | --------------------------------------- | ------------------------ |
| `parallel-execution.md` | 독립 작업 동시 실행 원칙                | 병렬 실행 필요 시        |
| `read-parallelization.md` | 파일 읽기 병렬화 기준               | 여러 파일 읽기 시        |
| `model-routing.md`      | 복잡도별 모델 선택 (haiku/sonnet/opus)  | 에이전트 모델 선택 시    |
| `agent-teams-usage.md`  | Agent Teams 7단계 흐름                  | Agent Teams 사용 시      |

### Multi-Agent

| 문서                    | 용도                                    | 사용 시점                |
| ----------------------- | --------------------------------------- | ------------------------ |
| `coordination-guide.md` | 병렬 실행, 모델 라우팅, 컨텍스트 보존   | 에이전트 조합 필요 시    |
| `agent-roster.md`       | 에이전트 상세 (explore, testgen 등) | 에이전트 선택 시         |
| `execution-patterns.md` | Fan-Out, 배치, 백그라운드 패턴          | 구체적 실행 방법 필요 시 |
| `teammate-done-process.md` | 팀원 작업 완료 6단계 프로세스        | Agent Teams 팀원 완료 시 |
| `team-evaluation.md`   | 팀원 규칙 준수 평가 (100점)             | 팀원 작업 평가 시        |

### Validation

| 문서                        | 용도                                  | 사용 시점         |
| --------------------------- | ------------------------------------- | ----------------- |
| `forbidden-patterns.md`     | any 타입, 정책 임의 변경 등 금지 항목 | 코드 작성/리뷰 시 |

---

## 상황별 참조 가이드

| 상황                       | 참조 문서                                                              |
| -------------------------- | ---------------------------------------------------------------------- |
| **여러 에이전트 협업**     | `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/coordination-guide.md` |
| **어떤 에이전트 사용할지** | `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/agent-roster.md`       |
| **구체적 실행 방법**       | `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/execution-patterns.md` |
| **코드 품질 검증**         | `${CLAUDE_PLUGIN_ROOT}/instructions/validation/forbidden-patterns.md`  |
| **작업 절차/검증/복잡도**  | `${CLAUDE_PLUGIN_ROOT}/rules/thinking-model.md`                        |
| **팀원 작업 완료 절차**    | `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/teammate-done-process.md` |
| **팀원 평가**              | `${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/team-evaluation.md`    |

---

## Quick Start

### 작업 시작 시

```
1. rules/thinking-model.md → 작업 절차 (GROUND에서 S/M/L 판단)
2. agent-roster.md → 필요한 에이전트 선택
3. execution-patterns.md → 실행 패턴 결정
```

### 코드 작성 시

```
1. forbidden-patterns.md → 금지 패턴 확인
2. rules/coding-standards.md → 코딩 표준 참조
```

---

## 핵심 원칙

| 원칙                     | 설명                                   |
| ------------------------ | -------------------------------------- |
| **Parallel First**       | 독립 작업은 병렬 실행                  |
| **Model Routing**        | 복잡도별 모델 선택 (haiku/sonnet/opus) |
| **Context Preservation** | 문서 기반 컨텍스트 전달                |
| **Error Isolation**      | 에이전트 실패 격리, 재시도 3회         |
