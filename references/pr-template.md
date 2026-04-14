# PR Template

PR 본문 템플릿 (## Summary, ## Changes, ## Test plan), 코드 리뷰 컨벤션.

---

## PR 생성 명령

```bash
git push -u origin {현재브랜치}
gh pr create \
  --base {대상브랜치} \
  --title "[작성자] {type}: [{티켓번호}] {제목}" \
  --body "$(cat <<'EOF'
### 작업 내용

- {변경 내용 bullet points}

### 이슈 트래커 및 디자인 주소 (optional)

{이슈 트래커 티켓 URL}

### 특이사항 (optional)

-

### 코드 리뷰 컨벤션

- 칭찬 (코드 수정 필수 X)
- 수정 요청 (코드 수정 필수 O)
- 궁금증 (코드 수정 필수 X)
- 제안 (코드 수정 필수 X)
- 여담 (코드 수정 필수 X)
EOF
)"
```

---

## PR 제목 형식

```
[작성자] {type}: [{티켓번호}] {제목}
```

type 예시: feat, fix, refactor, chore, docs, style, test

---

## 코드 리뷰 컨벤션

| 종류 | 코드 수정 필수 여부 |
|------|------------------|
| 칭찬 | X |
| 수정 요청 | O |
| 궁금증 | X |
| 제안 | X |
| 여담 | X |

---

## Draft PR 생성 (옵션)

```bash
gh pr create --draft \
  --base {대상브랜치} \
  --title "[작성자] {type}: [{티켓번호}] {제목}" \
  --body "..."
```

Draft PR 사용 케이스:
- `/done TICKET-123 --draft` 옵션 사용 시
- 코어 모듈 변경이 포함된 경우 (자동 Draft)

---

## 최종 요약 출력 형식 (/done 완료 시)

```markdown
## 작업 완료

### 티켓: {티켓번호} - {제목}

### 검증 결과

- [x] lint 통과
- [x] build 통과
- [x] 테스트 {통과/스킵}

### 커밋

- {커밋 해시}: {커밋 메시지}

### PR

- URL: {PR URL}
- 상태: Open

### Jira

- 상태: {완료 / 수동 변경 필요}
```

---

## /done 완료 조건 체크리스트

- [ ] 변경 내용 분석 완료
- [ ] 테스트 전략 판단됨
- [ ] 테스트 실행/스킵 완료 (사유 명시)
- [ ] lint/build 검증 통과
- [ ] 커밋 생성됨
- [ ] PR 생성됨 (URL 출력)
- [ ] .design-refs 스크린샷 정리됨
- [ ] 최종 요약 출력됨

---

## /done 옵션

| 옵션 | 설명 | 사용 예시 |
|------|------|---------|
| `--skip-test` | 테스트 스킵 (정책 무관 확인 후) | `/done TICKET-123 --skip-test` |
| `--force-test` | 정책 무관이어도 테스트 강제 실행 | `/done TICKET-123 --force-test` |
| `--draft` | Draft PR로 생성 | `/done TICKET-123 --draft` |
