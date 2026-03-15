---
name: codex
description: Claude + OpenAI Codex 협업 스킬. MCP 서버 설정 시에만 사용 가능.
---

# Codex Pair Programming

> Claude + OpenAI Codex 협업 스킬. MCP 서버 설정 시에만 사용 가능.

---

## Prerequisites (전제 조건)

이 스킬은 **codex-mcp MCP 서버가 설정된 경우에만** 사용 가능합니다.
설정되지 않은 환경에서는 이 스킬을 무시하세요.

| 항목 | 필수 |
|------|------|
| **OpenAI 계정** | Codex 접근 가능한 플랜 |
| **codex-mcp** | Rust 기반 MCP 서버 설치 (`codex login`으로 인증) |
| **MCP 설정** | `.claude/settings.json`에 codex MCP 서버 등록 |

### 설정 확인

```bash
# 인증 확인
codex login

# MCP 서버 상태 확인
ping (MCP 도구)
```

설정 미완료 시 → 이 스킬의 모든 내용을 건너뛴다.

---

## MCP 도구

| 도구 | 용도 | 주요 파라미터 |
|------|------|--------------|
| `codex` | 새 작업 시작 | dir, session_id, model, reasoning_effort |
| `codex_reply` | 기존 세션 이어서 작업 | session_id, 이전 컨텍스트 유지 |
| `codex_review` | 코드 리뷰 | uncommitted 변경, 브랜치, 특정 커밋 |
| `list_sessions` | 활성 세션 목록 | - |
| `ping` | 서버 상태 확인 | - |

---

## 협업 모드

### Mode 1: Solo+Review (기본)

Claude가 구현하고, Codex가 리뷰한다. 1-2개 파일 변경에 적합.

```text
Claude: 코드 구현
  ↓
Codex (codex_review): 코드 리뷰, 엣지케이스 검증
  ↓
Claude: 피드백 반영
```

**적합한 경우:**
- 단순 기능 추가/수정
- 빠른 피드백이 필요할 때
- 코드 품질 더블체크

---

### Mode 2: Sequential (순차 협업)

Claude가 설계하고, Codex가 구현 + 테스트한다.

```text
Claude: 아키텍처 설계, 인터페이스 정의
  ↓
Codex (codex): 구현 + 테스트 작성
  ↓
Claude: 결과 검증, 통합
```

**적합한 경우:**
- 설계와 구현이 분리 가능한 작업
- 테스트 커버리지가 중요한 작업

---

### Mode 3: Parallel (병렬 협업)

Claude와 Codex가 서로 다른 파일을 동시에 작업한다.

```text
Claude: 창의적/아키텍처 작업 (컴포넌트 설계, 상태 관리)
Codex (codex): 정밀 작업 (유틸 함수, 타입 정의, 테스트)
```

**적합한 경우:**
- 대규모 작업에서 병렬 처리
- 파일 수정 범위가 겹치지 않을 때

---

## 역할 분담

| 역할 | Claude | Codex |
|------|--------|-------|
| **아키텍처 설계** | O | - |
| **창의적 문제 해결** | O | - |
| **꼼꼼한 구현** | - | O |
| **엣지케이스 검증** | - | O |
| **코드 리뷰** | O | O |
| **테스트 작성** | O | O |

---

## 금지 사항

| 금지 | 이유 |
|------|------|
| **MCP 미설정 상태에서 사용** | 도구 없이 시뮬레이션 금지 |
| **동일 파일 동시 수정** | 충돌 방지 |
| **Codex 출력 무검증 수용** | 반드시 결과 확인 후 반영 |
| **MCP 미설정 사용자에게 설치 강요** | opt-in 원칙 |

---

## 필수 사항

| 필수 | 기준 |
|------|------|
| **MCP 상태 확인** | 작업 전 `ping`으로 연결 확인 |
| **세션 관리** | 작업 완료 시 세션 정리 |
| **결과 검증** | Codex 출력은 반드시 검토 후 반영 |
| **파일 충돌 방지** | 동시 수정 파일 명확히 분리 |

---

## 워크플로우 예시

### 기능 구현 + 리뷰 (Solo+Review)

```text
1. Claude: 컴포넌트 구현
2. codex_review: 변경사항 리뷰 요청
3. Claude: 리뷰 피드백 반영
4. 완료
```

### 설계 → 구현 (Sequential)

```text
1. Claude: 인터페이스/타입 설계, 파일 구조 결정
2. codex: "다음 인터페이스에 맞게 구현해줘" + 설계 내용 전달
3. codex_reply: 추가 요구사항 전달 (필요 시)
4. Claude: 결과 검증, lint/build 확인
5. 완료
```

---

## 에러 대응

| 에러 | 원인 | 해결 |
|------|------|------|
| **401 Unauthorized** | 인증 만료 | `codex login` 재실행 |
| **세션 실패** | 세션 손상 | 새 세션으로 시작 |
| **MCP 연결 실패** | 서버 미실행 | MCP 서버 재시작 |
| **도구 미발견** | MCP 미등록 | `.claude/settings.json` 확인 |

---

## 참고

- 이 스킬은 **완전 opt-in**입니다. MCP 서버가 설정되지 않으면 아무 영향 없음
- 팀원 중 Codex를 사용하지 않는 사람에게 설치를 강요하지 않음
- Agent Teams에서 팀원으로 사용할 경우, `general-purpose` 타입으로 spawn 후 이 스킬을 읽도록 프롬프트에 지시
- Codex 전용 에이전트도 별도 존재: `agents/codex.md` (Team Lead 역할 포함)

---

## 참조 문서

| 문서 | 용도 |
|------|------|
| `agents/codex.md` | Codex 에이전트 정의 (Team Lead 역할) |
| `@${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/coordination-guide.md` | 역할별 필수 참조 파일, 팀 템플릿 |
| `@${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/teammate-done-process.md` | Agent Teams 팀원 완료 프로세스 |
