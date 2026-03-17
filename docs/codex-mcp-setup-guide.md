# Codex MCP 설정 가이드

> Claude Code에서 OpenAI Codex를 MCP 서버로 연결하여 페어 프로그래밍하는 방법
> 완전 opt-in -- 설정하지 않아도 다른 기능에 영향 없음

---

## 전제 조건

| 항목 | 설명 |
|------|------|
| **OpenAI 계정** | Codex 접근 가능한 플랜 (Pro / Team / Enterprise) |
| **Codex CLI** | `codex` 명령어 사용 가능 |
| **Claude Code** | v1.0.33 이상 |

---

## Step 1: Codex CLI 설치

```bash
# Homebrew (macOS)
brew install openai-codex

# 또는 직접 설치
# https://github.com/openai/codex 참조
```

설치 확인:

```bash
codex --version
# codex-cli 0.104.0 (또는 그 이상)
```

---

## Step 2: OpenAI 인증 (OAuth)

```bash
codex login
```

브라우저가 열리고 OpenAI 계정으로 로그인하면 인증 완료.
인증 정보는 `~/.codex/auth.json`에 저장됩니다.

확인:

```bash
ls ~/.codex/auth.json
# 파일이 있으면 인증 완료
```

---

## Step 3: Claude Code에 MCP 서버 등록

아래 두 가지 중 선택:

### 방법 A: 전역 설정 (모든 프로젝트에서 사용)

`~/.claude/.mcp.json` 생성:

```json
{
  "mcpServers": {
    "codex": {
      "command": "codex",
      "args": ["mcp-server"]
    }
  }
}
```

### 방법 B: 프로젝트 전용 설정

프로젝트 루트에 `.mcp.json` 생성:

```json
{
  "mcpServers": {
    "codex": {
      "command": "codex",
      "args": ["mcp-server"]
    }
  }
}
```

> 방법 B는 `.gitignore`에 `.mcp.json` 추가를 권장합니다 (개인 인증 정보 보호).

---

## Step 4: Claude Code 재시작

```bash
# Claude Code 종료 후 다시 시작
claude
```

시작 시 "codex MCP server connected" 같은 메시지가 나오면 연결 성공.

---

## Step 5: 연결 확인

Claude Code에서:

```
codex mcp 상태 확인해줘
```

또는 `/code-forge:codex` 스킬을 호출하면 자동으로 ping 확인 후 사용 가능 여부를 알려줍니다.

---

## 사용 가능한 MCP 도구

| 도구 | 용도 | 예시 |
|------|------|------|
| `codex` | 새 작업 시작 (세션 생성) | "이 함수 구현해줘" |
| `codex_reply` | 기존 세션 이어서 작업 | "테스트도 추가해줘" |
| `codex_review` | 코드 리뷰 | uncommitted 변경사항 리뷰 |

---

## 모델 선택

`codex mcp-server` 실행 시 기본 모델은 `~/.codex/config.toml`의 설정을 따릅니다.

특정 모델을 강제하려면:

```json
{
  "mcpServers": {
    "codex": {
      "command": "codex",
      "args": ["mcp-server", "-c", "model=\"gpt-4.1\""]
    }
  }
}
```

사용 가능한 모델: `o3`, `o4-mini`, `gpt-4.1`, `gpt-4.1-mini` 등

---

## 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| MCP 도구가 안 보임 | `.mcp.json` 미생성 또는 위치 잘못 | 파일 경로 확인 |
| 401 Unauthorized | OAuth 인증 만료 | `codex login` 재실행 |
| "codex: command not found" | PATH에 없음 | `which codex`로 경로 확인 후 full path 사용 |
| 세션 에러 | 세션 손상 | 새 세션으로 시작 |

### full path 사용 예시

`which codex`가 `/opt/homebrew/bin/codex`를 반환하면:

```json
{
  "mcpServers": {
    "codex": {
      "command": "/opt/homebrew/bin/codex",
      "args": ["mcp-server"]
    }
  }
}
```

---

## 참고

- 이 설정은 **완전 opt-in**입니다. 설정하지 않아도 다른 에이전트/스킬에 영향 없음
- 팀원에게 설치를 강요하지 않음
- 관련 스킬: `skills/codex/SKILL.md`
- 관련 에이전트: `agents/codex.md`

---

# 기타 MCP 서버 설정

## Atlassian (Jira + Confluence)

프로젝트 루트 `.mcp.json`에 추가:

```json
{
  "mcpServers": {
    "Atlassian": {
      "command": "uvx",
      "args": ["mcp-atlassian"],
      "env": {
        "JIRA_URL": "https://{회사}.atlassian.net",
        "JIRA_USERNAME": "{이메일}",
        "JIRA_API_TOKEN": "{API 토큰}",
        "CONFLUENCE_URL": "https://{회사}.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "{이메일}",
        "CONFLUENCE_API_TOKEN": "{API 토큰}"
      }
    }
  }
}
```

API 토큰 발급: https://id.atlassian.com/manage-profile/security/api-tokens

## Figma

```json
{
  "mcpServers": {
    "Figma": {
      "command": "npx",
      "args": [
        "-y",
        "figma-developer-mcp",
        "--figma-api-key={Figma PAT}",
        "--stdio"
      ]
    }
  }
}
```

Figma PAT 발급: Figma → Settings → Personal Access Tokens

> `.mcp.json`에 토큰이 포함되므로 반드시 `.gitignore`에 추가할 것.
