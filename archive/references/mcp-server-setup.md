# MCP Server Setup

Codex MCP/CLI 설정 방법, Figma MCP 토큰 설정, Atlassian MCP 설정, MCP 연결 테스트 방법.

---

## Codex MCP 설정

### 자동 감지 순서

1. `mcp__codex__codex` 도구가 사용 가능한가? → **MCP 모드로 진행**
2. `which codex` 실행 가능한가? → **CLI Headless 모드로 진행**
3. 둘 다 불가 → **설정 안내 표시 후 종료**

### Codex 미설정 시 안내

```
Codex가 설정되어 있지 않습니다.

설정 방법은 docs/codex-mcp-setup-guide.md 를 참조하세요.
빠른 설정:
  1. codex CLI 설치: brew install openai-codex
  2. 인증: codex login
  3. .mcp.json에 MCP 서버 등록
  4. Claude Code 재시작
```

### Codex MCP 도구

| 도구 | 용도 | 주요 파라미터 |
|------|------|--------------|
| `codex` | 새 작업 시작 | dir, session_id, model, reasoning_effort |
| `codex_reply` | 기존 세션 이어서 작업 | session_id, 이전 컨텍스트 유지 |
| `codex_review` | 코드 리뷰 | uncommitted 변경, 브랜치, 특정 커밋 |
| `list_sessions` | 활성 세션 목록 | - |
| `ping` | 서버 상태 확인 | - |

### Codex CLI headless 모드

```bash
# 기본 실행 (read-only sandbox)
codex exec -m o4-mini -s read-only "{프롬프트}"

# 예시: 라운드 1 반론 요청
codex exec -m o4-mini -s read-only \
  "다음 아키텍처 결정에 대해 반론 입장에서 주장해줘: {주제}\n\n상대 주장: {입장 A 내용}"

# 예시: 합의 탐색
codex exec -m o4-mini -s read-only \
  "다음 토론의 합의 가능 지점을 찾아줘:\n입장 A: {A 요약}\n입장 B: {B 요약}"

# 가용 확인
codex exec -m o4-mini -s read-only "ping"
```

### Codex 연결 상태 확인

```
mcp__codex__ping 호출
```

### Codex 에러 대응

| 에러 | 원인 | 해결 |
|------|------|------|
| **401 Unauthorized** | 인증 만료 | `codex login` 재실행 |
| **세션 실패** | 세션 손상 | 새 세션으로 시작 |
| **MCP 연결 실패** | 서버 미실행 | MCP 서버 재시작 |
| **도구 미발견** | MCP 미등록 | `.claude/settings.json` 확인 |

---

## Figma MCP 설정

### 연결 테스트

```
mcp__figma__whoami 호출하여 연결 상태 확인
```

→ 성공: 다음 단계 진행
→ 실패 시 안내: "Figma MCP 연결이 필요합니다. `/mcp` 실행 후 다시 진행해주세요."

### PAT 방식 주의사항

- PAT(Personal Access Token) 방식이므로 OAuth 재인증 시도하지 않는다
- "re-authorization", "token expired" 에러 발생 시 OAuth 재인증 시도하지 않음
- 안내: "Figma MCP 재연결이 필요합니다. `/mcp` 실행해주세요."

### curl fallback (MCP 실패 시)

```bash
# 이미지 URL 조회
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/{fileKey}?ids={node-id}&format=png&scale=2"

# 노드 정보 조회
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/{fileKey}/nodes?ids={node-id}&depth=5"
```

---

## Atlassian MCP 설정

### .mcp.json 수동 설정

```json
{
  "mcpServers": {
    "Atlassian": {
      "command": "uvx",
      "args": ["mcp-atlassian"],
      "env": {
        "JIRA_URL": "https://회사도메인.atlassian.net",
        "JIRA_USERNAME": "이메일",
        "JIRA_API_TOKEN": "토큰"
      }
    }
  }
}
```

API 토큰 발급: https://id.atlassian.com/manage-profile/security/api-tokens

### 연결 테스트

```
mcp__Atlassian__jira_get_issue({ issueKey: "TEST-1" })
```

성공하면 연결 확인됨. 실패하면 아래 설치 안내.

### Atlassian MCP 미연결 시 안내

```
Atlassian MCP가 연결되지 않았습니다.

연결 방법:
1. /mcp 실행
2. Atlassian 선택 → OAuth 인증
3. 완료 후 다시 진행

또는 .mcp.json에 수동 설정 (위 예시 참조)
```

막혔을 때:
- "uvx가 없어요" → `pip install uvx` 또는 `pipx install mcp-atlassian`
- "토큰을 어디서 발급하나요" → https://id.atlassian.com/manage-profile/security/api-tokens
- "OAuth가 안 돼요" → API 토큰 방식(.mcp.json 수동 설정)으로 대안

---

## 설정 원칙

| 원칙 | 내용 |
|------|------|
| 완전 opt-in | MCP 서버가 설정되지 않으면 아무 영향 없음 |
| 설치 강요 금지 | MCP 미설정 사용자에게 설치를 강요하지 않음 |
| 연결 확인 우선 | 작업 전 연결 상태 확인 후 진행 |
| 폴백 사용 | MCP 실패 시 curl/CLI 폴백으로 동작 |
