---
name: debate
description: 교차 모델 토론. Agent Teams / Codex CLI / self-debate 모드 선택. 설계 결정, 아키텍처 선택 시 활용.
category: analysis
metadata:
  version: '2.0.0'
---

# Debate Skill

> 중요 기술 결정 시 다각도 검증을 위한 교차 모델 토론 스킬.
> 3가지 모드 중 환경에 맞는 방식을 자동 선택하여 최대 3라운드 진행 후 합의 도출.

---

## 목적

| 목적 | 설명 |
|------|------|
| **다각도 검증** | 단일 관점의 맹점 제거 |
| **설계 결정 강화** | 아키텍처 선택의 근거 명확화 |
| **리스크 사전 발견** | 반론을 통한 잠재 문제 탐지 |
| **팀 합의 촉진** | 토론 요약으로 의사결정 공유 |

---

## 모드 (3가지)

### Mode 1: agent-teams (최상위)

Agent Teams로 팀원을 spawn하여 **실시간 병렬 토론**. Claude Max + `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 필요.

```text
TeamCreate("debate-team")
  → Agent("advocate", team_name="debate-team")   # 찬성
  → Agent("critic", team_name="debate-team")     # 반대/비평
  → codex exec (Bash)                             # Codex 외부 관점
  ↓
라운드 1~3: SendMessage로 팀원 간 공방
  ↓
팀 리더(Claude)가 합의 도출
  ↓
TeamDelete("debate-team")
```

**팀 구성:**

| 팀원 | 역할 | 모델 | subagent_type |
|------|------|------|---------------|
| advocate | 입장 A 지지, 근거 제시 | sonnet | `general-purpose` 또는 `ggombee-agents:architect` |
| critic | 입장 B 반론, 가혹한 비평 | sonnet | `ggombee-agents:critic` |
| codex | 외부 모델 관점 (Bash로 실행) | gpt-5.4 | Codex CLI |

**팀 리더 역할 (Claude 본체):**
- 주제 정의 및 입장 배분
- 각 라운드 SendMessage로 상대 주장 전달
- 3라운드 후 합의 도출 및 최종 판정

---

### Mode 2: cross-model (Codex CLI)

Agent Teams 없이 Claude + Codex CLI headless 토론.

```text
Claude (입장 A) ↔ Codex CLI (입장 B)
  ↓
라운드 1: 초기 주장
  ↓
라운드 2: 반론
  ↓
라운드 3: 재반론 + 합의 탐색
  ↓
합의 도출
```

**Codex CLI 실행:**

```bash
codex exec -s read-only "{프롬프트}"
```

---

### Mode 3: self-debate (폴백)

Codex 미설정 시 Claude 내부 찬반 토론.

```text
Claude (입장 A: 지지) ↔ Claude (입장 B: 반론)
  ↓
라운드 진행 (최대 3)
  ↓
메타 분석: 어떤 주장이 더 강한가?
  ↓
합의 도출
```

---

## 모드 선택

**사용자에게 먼저 묻는다.** 자동 선택하지 않는다.

```text
"토론 모드를 선택해주세요:

1. agent-teams — Agent Teams로 팀원 병렬 토론 (Claude Max + 환경변수 필요)
2. cross-model — Codex CLI와 1:1 토론 (Codex 설치 필요)
3. self-debate — Claude 내부 찬반 토론 (별도 설정 불필요)

또는 /debate --mode {모드명}으로 바로 시작할 수 있습니다."
```

**--mode 옵션이 있으면** 질문 없이 해당 모드로 즉시 진행.

```text
/debate --mode agent-teams  → Mode 1 즉시
/debate --mode cross-model  → Mode 2 즉시
/debate --mode self-debate  → Mode 3 즉시
```

**선택된 모드의 사전 조건 미충족 시** 안내 후 다른 모드 제안.

---

## 트리거 조건

| 트리거 | 반응 |
|--------|------|
| "debate", "토론", "검토" | 스킬 활성화 |
| 아키텍처 선택이 2개 이상 | 자동 제안 |
| thinking-model GROUND (복잡도 L) | 자동 호출 |
| thinking-model ADAPT (2회 실패) | 대안 탐색용 호출 |

---

## ARGUMENT 확인

```
$ARGUMENTS 없음 → 즉시 질문:

"어떤 기술적 결정을 토론할까요?

예시:
- 아키텍처 선택 (예: REST vs GraphQL)
- 상태 관리 전략 (예: Jotai vs Zustand)
- 설계 패턴 (예: 컨테이너/뷰 vs hooks 전용)
- 라이브러리 선택"

$ARGUMENTS 있음 → 모드 선택 후 진행
```

---

## 동작 흐름

### Phase 1: 주제 정의

```markdown
## 토론 주제

**결정 사항:** {기술적 결정 내용}
**맥락:** {현재 프로젝트 상황, 제약 조건}
**평가 기준:** {성능, 유지보수성, 팀 역량, 일정 등}

**입장 A:** {옵션 1 지지}
**입장 B:** {옵션 2 지지 / 반론}
```

---

### Phase 2: 라운드 진행

각 라운드는 **주장 → 반론 → 재반론** 구조로 진행.

#### Agent Teams 모드 라운드 흐름

```text
라운드 N:
  1. 팀 리더 → SendMessage(to="advocate", "라운드 N 주장을 제시해줘: {주제}")
  2. advocate 응답 수신
  3. 팀 리더 → SendMessage(to="critic", "다음 주장에 반론해줘: {advocate 주장}")
  4. critic 응답 수신
  5. 팀 리더 → codex exec (Bash)로 Codex 외부 관점 수집
  6. 다음 라운드에 이전 결과 전달
```

#### 라운드 1: 초기 주장

```markdown
### [입장 A] 주장

**핵심 주장:** {주요 근거}
**기술적 이점:** {구체적 장점}
**위험 완화:** {예상 단점 대응}

---

### [입장 B] 주장

**핵심 주장:** {주요 근거}
**기술적 이점:** {구체적 장점}
**위험 완화:** {예상 단점 대응}
```

#### 라운드 2: 반론

```markdown
### [입장 A] 반론

**[입장 B] 주장의 약점:** {구체적 지적}
**추가 근거:** {새로운 데이터/사례}

---

### [입장 B] 반론

**[입장 A] 주장의 약점:** {구체적 지적}
**추가 근거:** {새로운 데이터/사례}
```

#### 라운드 3: 재반론 + 합의 탐색

```markdown
### [입장 A] 재반론

**인정하는 부분:** {상대 주장 중 수용 가능한 부분}
**유지하는 핵심:** {양보 불가 근거}
**합의 가능 지점:** {절충안 제안}

---

### [입장 B] 재반론

**인정하는 부분:** {상대 주장 중 수용 가능한 부분}
**유지하는 핵심:** {양보 불가 근거}
**합의 가능 지점:** {절충안 제안}
```

---

### Phase 3: 합의 도출

```markdown
## 토론 결과

### 합의점

{양측이 동의한 핵심 사항}

### 미해결 논점

| 논점 | 입장 A | 입장 B | 해결 방법 |
|------|--------|--------|-----------|
| {논점 1} | {A 견해} | {B 견해} | {후속 조치} |

### 권장 결정

**결정:** {선택된 옵션}
**근거:** {주요 이유}
**조건:** {이 결정이 유효한 전제 조건}
**후속 조치:** {모니터링, 재검토 시점}
```

---

## thinking-model 연계

| 상황 | 연계 방식 |
|------|----------|
| **GROUND (복잡도 L)** | 단순 분석으로 결론이 나지 않을 때 debate 호출 |
| **ADAPT (2회 실패)** | 기존 접근 실패 시 debate로 대안 탐색 |
| **설계 분기점** | 2개 이상 동등한 옵션 존재 시 자동 제안 |

---

## 출력 형식

토론 완료 후 반드시 아래 형식으로 요약 출력:

```markdown
## Debate Summary

**주제:** {토론 주제}
**모드:** agent-teams / cross-model / self-debate
**라운드:** {실행된 라운드 수}/3
**참가자:** {참가 모델/에이전트 목록}

### 토론 요약

| 항목 | 입장 A | 입장 B |
|------|--------|--------|
| 핵심 주장 | ... | ... |
| 주요 근거 | ... | ... |
| 양보한 부분 | ... | ... |

### 합의점

- {합의 1}
- {합의 2}

### 미해결 논점

- {논점 1}: {간략 설명}

### 권장 결정

**{선택된 옵션}** - {핵심 근거 1-2문장}
```

---

## 금지 패턴

| 금지 | 이유 |
|------|------|
| **3라운드 초과** | 무한 토론 방지 |
| **합의 없이 종료** | 반드시 권장 결정 도출 |
| **Codex 미설정 상태에서 cross-model 시도** | 폴백(self-debate) 사용 |
| **편향된 입장 A 우대** | 공정한 토론 원칙 |
| **주제 없이 시작** | Phase 1 완료 후 진행 |

---

## 참조 문서

| 문서 | 용도 |
|------|------|
| `rules/thinking-model.md` | GROUND/ADAPT 연계 |
| `instructions/multi-agent/coordination-guide.md` | 멀티에이전트 협업 |
| `instructions/validation/forbidden-patterns.md` | 금지 패턴 |
| `skills/codex/SKILL.md` | Codex CLI 설정 |
| `skills/setup-agent-teams/SKILL.md` | Agent Teams 환경 설정 |
