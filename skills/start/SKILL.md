---
name: start
description: 티켓 기반 작업 시작. 프로파일 확정 → 코드 분석 → 작업 계획 → 품질 게이트 → 구현 확인.
---

**[즉시 실행]** 이 메시지를 받으면 아래 단계를 바로 실행하세요. 설명하지 말고 도구를 호출하세요.

**티켓**: $ARGUMENTS

**참조 규칙**:

- `@${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/coordination-guide.md` (병렬 실행)
- `@${CLAUDE_PLUGIN_ROOT}/rules/thinking-model.md` (작업 절차 — GROUND/APPLY/VERIFY 루프)

---

## 0단계: Figma MCP 연결 확인 (필수)

**Figma MCP 사용 규칙:**

- Figma 관련 정보가 필요하면 **반드시 figma MCP를 호출**한다
- PAT(Personal Access Token) 방식이므로 OAuth 재인증 시도하지 않는다
- MCP 호출 에러 발생 시 `/mcp` 슬래시 커맨드로 재연결 안내

**MCP 연결 테스트:**

```
mcp__figma__whoami 호출하여 연결 상태 확인
```

> 성공: 다음 단계 진행
> 실패 시 안내: "Figma MCP 연결이 필요합니다. `/mcp` 실행 후 다시 진행해주세요."

---

## 1단계: 이슈 트래커 조회 + 상태 변경

프로젝트의 이슈 트래커에서 티켓 정보를 조회합니다.

**Jira (Atlassian MCP 사용 시):**

```
mcp atlassian: jira_get_issue(issueKey: "$ARGUMENTS")
```

**GitHub Issues (gh CLI 사용 시):**

```bash
gh issue view {이슈번호}
```

→ 제목, 설명, Figma 링크, API 문서 링크 추출
→ 가능하면 티켓 상태를 "진행 중"으로 변경

---

## 2단계: 작업 환경 준비

### 2-0. .design-refs 폴더 생성 (없으면)

```bash
mkdir -p {대상뷰경로}/.design-refs
```

---

## 3단계: Figma 디자인 분석 (MCP 우선)

### Figma MCP 사용 규칙

1. **MCP 호출 우선순위:**
   - `get_metadata` -> 구조/스타일/컴포넌트 파악 (최우선)
   - `get_screenshot` -> 시각적 확인 필요 시
   - `get_design_context` -> 코드 변환 시

2. **URL에서 fileKey/nodeId 추출:**

   ```
   https://www.figma.com/design/{fileKey}/{fileName}?node-id={nodeId}
   -> nodeId의 하이픈(-)을 콜론(:)으로 변환
   ```

### 3-1. Figma 메타데이터 조회 (MCP)

```
mcp__figma__get_metadata({
  fileKey: "{fileKey}",
  nodeId: "{nodeId}"
})
```

### 3-2. 스크린샷 조회 (MCP)

```
mcp__figma__get_screenshot({
  fileKey: "{fileKey}",
  nodeId: "{nodeId}"
})
```

---

## 4단계: 코드 분석 및 Figma 일치 검증 (병렬 탐색)

### 4-0. 병렬 탐색 (explore 에이전트 활용)

```typescript
// 독립적인 탐색 작업은 병렬 실행
Task((subagent_type = 'scout'), (model = 'haiku'), (prompt = '변경 대상 컴포넌트 구조 분석'));
Task((subagent_type = 'scout'), (model = 'haiku'), (prompt = '기존 패턴 분석'));
Task((subagent_type = 'scout'), (model = 'haiku'), (prompt = '관련 쿼리/서비스 파악'));
```

---

## 5단계: 작업 계획 출력

```markdown
## 티켓: $ARGUMENTS - {제목}

### Figma

{전체 URL - 클릭 가능한 링크}

### 작업 내용

1. {작업 1}
2. {작업 2}

### 변경 파일

- {파일 목록}

### 검증 방법

- Figma 스크린샷과 로컬 화면 비교
- {추가 테스트 전략}
```

---

## 6단계: @see 태그 추가 제안 (testgen 연동)

```typescript
/**
 * {컴포넌트 설명}
 * @see {Figma URL}  <- 디자인 시안
 * @see {티켓 URL}   <- 티켓 링크
 */
```

---

## 7단계: 복잡도 판단 및 구현 전략

| 복잡도     | 기준                         | 전략               |
| ---------- | ---------------------------- | ------------------ |
| **LOW**    | 1개 파일, 스타일/텍스트 변경 | 바로 구현          |
| **MEDIUM** | 2-5개 파일, 기존 패턴        | 패턴 확인 후 구현  |
| **HIGH**   | 5개+ 파일, 새 아키텍처       | Plan 에이전트 호출 |

---

## 8단계: 계획 품질 검토 (필수)

작업 절차(Working Protocol)의 VERIFY 기준으로 계획을 검증:

- 계획 수립/검토/재검토가 완료됐는가?
- 과도한 구현 요소가 제거됐는가?
- 불명확한 항목은 사용자 질문으로 확정했는가?

하나라도 FAIL이면 구현 시작 금지, 계획부터 재작성.

---

## 9단계: 구현 시작 여부 확인

"작업을 시작할까요?" 라고 물어보기
