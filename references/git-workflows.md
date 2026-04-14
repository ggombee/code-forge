# Git Workflows

브랜치 생성/체크아웃, 커밋 메시지 형식 (Conventional Commits), `git add` 규칙 (명시적 파일만), PR 생성 플로우.

---

## 변경 내용 분석

```bash
git status
git diff --staged
git diff
```

분석 항목:
- 변경된 파일 목록
- 주요 변경 내용 요약
- 정책 영향 여부 판단

---

## git add 규칙

```bash
# 절대 금지 - 전체 파일 add
git add .
git add -A

# 올바른 방법 - 수정한 파일만 명시적으로 add
git add apps/{앱이름}/src/{도메인}/views/{뷰이름}/components/{컴포넌트}/index.tsx
```

---

## 커밋 메시지 형식

```
[작성자] feat: [{티켓번호}] [{페이지명}] {변경 내용 요약}

- {세부 변경 1}
- {세부 변경 2}
```

예시:
```
[ggombee] feat: [QA-52372] [결제] 자동이체 노출 조건 수정

- 결제 옵션 필터링 로직 수정
- 자동이체 비노출 케이스 추가
```

---

## Push + PR 생성 플로우

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

## 최근 변경 확인 (bug-fix 시)

```bash
# 에러 키워드 검색
rg "{에러키워드}" apps/{앱이름}/src

# 최근 변경 확인
git log --oneline -10 -- {관련파일}

# git diff로 변경 내용 확인
git diff HEAD~5 -- {관련파일}
```

---

## 전체 처리 완료 후 커밋 선택

```
/done 실행할까요? (커밋 + PR + Jira 완료 처리)
  a. 전체 /done (모든 변경사항을 한 커밋 + 한 PR)
  b. 티켓별 /done (각 티켓마다 커밋 + PR 분리)
  c. 나중에 할게요
```

---

## .design-refs 정리 (완료 시)

```bash
find apps/{앱이름}/src -path "*/.design-refs/*.png" -delete
find apps/{앱이름}/src -path "*/.design-refs/*.jpg" -delete
```

---

## 코어 변경 시 Draft PR 생성

코어 모듈 변경이 포함된 경우:
- PR을 **자동으로 Draft**로 생성
- 코어 담당자를 리뷰어로 지정
- PR에 `needs-core-approval` 라벨 부착

---

## 사전 조건

커밋/PR 생성 전 품질 게이트 PASS 필수:
- lint 통과
- build 통과
- 테스트 통과 (정책 영향 시)
- 4-1 품질 검토 항목 모두 PASS
