# Figma MCP Integration

Figma MCP 메서드, URL에서 fileKey/nodeId 추출 규칙, PAT 방식 주의사항, MCP 에러 핸들링, curl fallback.

---

## MCP 사용 규칙

- Figma 관련 정보가 필요하면 **반드시 figma MCP를 호출**한다
- PAT(Personal Access Token) 방식이므로 OAuth 재인증 시도하지 않는다
- MCP 호출 에러 발생 시 `/mcp` 슬래시 커맨드로 재연결 안내

---

## 연결 테스트

```
mcp__figma__whoami 호출하여 연결 상태 확인
```

→ 성공: 다음 단계 진행
→ 실패 시 안내: "Figma MCP 연결이 필요합니다. `/mcp` 실행 후 다시 진행해주세요."

---

## MCP 메서드

### 1. get_metadata (최우선)

구조/스타일/컴포넌트 파악용.

```
mcp__figma__get_metadata({
  fileKey: "{fileKey}",
  nodeId: "{nodeId}"
})
```

→ 노드 구조, 레이아웃, 컴포넌트 정보 확인
→ 결과 받은 후에만 분석 진행 (추측 금지)

### 2. get_screenshot (시각적 확인)

시각적 확인이 필요한 경우.

```
mcp__figma__get_screenshot({
  fileKey: "{fileKey}",
  nodeId: "{nodeId}"
})
```

→ 스크린샷 이미지 확인하여 디자인 파악
→ `.design-refs/` 폴더에 저장 (필요 시)

### 3. get_design_context (코드 변환)

코드 변환이 필요한 경우.

```
mcp__figma__get_design_context({
  fileKey: "{file_key}",
  nodeId: "{node_id}",
  clientLanguages: "typescript",
  clientFrameworks: "react"
})
```

---

## 호출 우선순위 결정표

| 상황 | MCP 호출 |
|------|:--------:|
| 구조/레이아웃 파악 | get_metadata |
| 시각적 디자인 확인 | get_screenshot |
| 코드 변환 필요 | get_design_context |
| 기존 색상만 확인 | 스킵 |

---

## URL에서 fileKey/nodeId 추출 규칙

```
https://www.figma.com/design/{fileKey}/{fileName}?node-id={nodeId}
예: https://figma.com/design/BXiGIhNq64fq3rllWWqZN0/...?node-id=2040-47609
→ fileKey: BXiGIhNq64fq3rllWWqZN0
→ nodeId: 2040:47609 (하이픈을 콜론으로 변환)
```

서브태스크 Figma 링크 형식 (전체 URL 필수):
```
https://www.figma.com/design/{file_key}?node-id={node-id}&m=dev
```
※ node-id만 저장하지 않음 - 클릭해서 바로 이동 가능해야 함

---

## MCP 에러 핸들링

- "re-authorization", "token expired" 에러 발생 시
- OAuth 재인증 시도하지 않음 (PAT 방식)
- 안내: "Figma MCP 재연결이 필요합니다. `/mcp` 실행해주세요."

---

## curl Fallback (MCP 연결 실패 시에만 사용)

```bash
# 이미지 URL 조회
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/{fileKey}?ids={node-id}&format=png&scale=2"

# 노드 정보 조회
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/{fileKey}/nodes?ids={node-id}&depth=5"
```
