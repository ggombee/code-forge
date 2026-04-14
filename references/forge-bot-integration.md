# forge-bot 연동 스펙

> quality-gate.sh의 JSON Lines 출력을 forge-bot이 파싱하여 Slack Block Kit으로 변환하는 인터페이스 정의.

---

## 환경변수

forge-bot이 Claude Code 실행 시 주입:
```bash
FORGE_OUTPUT=json  # quality-gate.sh가 JSON Lines 모드로 동작
```

---

## JSON Lines 출력 포맷

quality-gate.sh가 stderr로 출력하는 JSON Lines:

```json
{"type":"eslint","status":"pass","detail":""}
{"type":"tsc","status":"pass","detail":""}
{"type":"scope","status":"warn","detail":"계획에 없는 파일 수정됨: src/utils/date.ts"}
{"type":"test-trigger","status":"pass","detail":"실행: 3/3 통과"}
{"type":"test-trigger","status":"fail","detail":"실패: 1개"}
{"type":"test-trigger","status":"warn","detail":"TC 없음: src/hooks/useCTA.tsx → /test 권장"}
{"type":"policy-sync","status":"warn","detail":"order-detail: 소스 변경됨 but 문서 미갱신"}
{"type":"reflect","status":"pass","detail":"REFLECT flag 해제"}
{"type":"cleanup","status":"pass","detail":"design-refs 3개 정리"}
```

### 필드 정의

| 필드 | 타입 | 설명 |
|------|------|------|
| `type` | string | 검증 블록 ID |
| `status` | `"pass"` \| `"warn"` \| `"fail"` | 결과 |
| `detail` | string | 사람이 읽을 수 있는 상세 메시지 |

---

## Slack Block Kit 변환 예시

### 전체 통과

```json
{
  "blocks": [
    { "type": "section", "text": { "type": "mrkdwn", "text": "✅ *Quality Gate 통과*\n`eslint` OK · `tsc` OK · `test` 3/3 통과" } }
  ]
}
```

### 경고/실패 있음

```json
{
  "blocks": [
    { "type": "section", "text": { "type": "mrkdwn", "text": "⚠️ *Quality Gate 경고*" } },
    { "type": "section", "text": { "type": "mrkdwn", "text": "• `scope` 계획에 없는 파일: src/utils/date.ts\n• `test-trigger` TC 없음: src/hooks/useCTA.tsx" } },
    { "type": "section", "text": { "type": "mrkdwn", "text": "✅ `eslint` OK · `tsc` OK" } }
  ]
}
```

---

## forge-bot 구현 체크리스트

- [ ] Claude Code 실행 시 `FORGE_OUTPUT=json` 환경변수 주입
- [ ] stderr에서 JSON Lines 파싱 (줄 단위 `JSON.parse`)
- [ ] status별 이모지 매핑 (pass→✅, warn→⚠️, fail→❌)
- [ ] Slack Block Kit 메시지 조립
- [ ] DM으로 결과 전송

---

## 참고

- forge-bot 소스: `~/Desktop/forge-bot/`
- Slack 메시지 포맷: `@references/slack-message-format.md`