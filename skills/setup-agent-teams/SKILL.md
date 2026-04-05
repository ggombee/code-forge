---
name: setup-agent-teams
description: Agent Teams 환경 설정. Claude Max 전용. TeamCreate/SendMessage/TeamDelete 도구 활성화.
category: setup
user-invocable: false
---

# /setup-agent-teams

Claude Code Agent Teams 기능을 활성화한다. Claude Max 구독 필수.

## 사전 조건

| 조건 | 확인 방법 |
|------|----------|
| Claude Max 구독 | `claude --version` + 플랜 확인 |
| Claude Code v2.1.32+ | `claude --version` |

---

## 실행 워크플로우

아래 단계를 순서대로 즉시 실행한다.

### Step 1. 환경변수 설정

`~/.claude/settings.json`에 `env` 블록을 추가한다.

```bash
# 현재 설정 확인
cat ~/.claude/settings.json
```

`env` 블록이 없으면 추가:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

이미 `env` 블록이 있으면 해당 키만 추가한다.

### Step 2. 세션 재시작 안내

환경변수 설정 후 **현재 세션을 종료하고 새 세션을 시작**해야 Agent Teams 도구가 로드된다.

```
설정 완료! Agent Teams를 사용하려면 새 세션을 시작하세요.

활성화되는 도구:
- TeamCreate  — 팀 생성
- TeamDelete  — 팀 삭제
- SendMessage — 팀원 간 메시지
- TaskCreate  — 작업 생성 (팀원에게 할당)
- TaskUpdate  — 작업 상태 변경
- TaskList    — 작업 목록 조회
```

### Step 3. 검증 (새 세션에서)

새 세션 시작 후 아래를 실행하여 정상 활성화 확인:

```
"Agent Teams 테스트: 2명의 팀원으로 간단한 코드 리뷰를 진행해줘"
```

TeamCreate가 호출되면 정상.

---

## Agent Teams 사용 패턴

### 기본 흐름

```text
TeamCreate("team-name")
  → Agent(name="member-1", team_name="team-name", prompt="...")
  → Agent(name="member-2", team_name="team-name", prompt="...")
  → SendMessage(to="member-1", message="...")
  → 작업 완료 대기
  → TeamDelete("team-name")
```

### 추천 팀 구성

| 시나리오 | 팀원 | 모델 |
|---------|------|------|
| **코드 리뷰** | reviewer-1 (품질), reviewer-2 (보안) | sonnet, sonnet |
| **기능 구현** | architect (설계), implementor (구현) | opus, sonnet |
| **토론** | advocate (찬성), critic (반대), judge (판정) | sonnet, sonnet, opus |
| **리서치** | researcher-1 (공식문서), researcher-2 (커뮤니티) | sonnet, haiku |

### Codex 팀원 참여

Codex를 팀원처럼 활용하려면 Bash 도구로 `codex exec` 실행:

```bash
codex exec -s read-only "{프롬프트}"
```

Agent Teams 팀원이 Codex를 호출하는 구조로 cross-model 협업 가능.

---

## 주의사항

| 주의 | 설명 |
|------|------|
| **토큰 사용량 증가** | 팀원마다 독립 컨텍스트 → 토큰 N배 |
| **순차 작업 부적합** | 병렬 가능한 독립 작업에만 사용 |
| **Claude Max 전용** | 일반 플랜에서는 Agent 병렬 spawn으로 폴백 |
| **세션 재시작 필수** | settings.json 수정 후 현재 세션에서는 미반영 |

---

## 참조

| 문서 | 용도 |
|------|------|
| `instructions/multi-agent/coordination-guide.md` | 멀티에이전트 협업 패턴 |
| `instructions/multi-agent/execution-patterns.md` | 작업별 실행 패턴 |
| `skills/debate/SKILL.md` | Agent Teams 기반 토론 |
