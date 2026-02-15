---
description: 작업 완료 - 변경 분석, 테스트 전략, 품질 게이트, 커밋/PR, 정리까지 수행
---

# /done - 작업 완료 및 PR 생성

## 사용법

```bash
/done BOWD-193
/done                # 현재 브랜치에서 티켓 번호 추론
```

## 참조 규칙

- `@../instructions/multi-agent/coordination-guide.md`
- `@../instructions/multi-agent/agent-roster.md`
- `@../instructions/validation/forbidden-patterns.md`
- `@../instructions/validation/release-readiness-gate.md`

## 1단계: 변경 내용 분석

```bash
git status
git diff --staged
git diff
```

분석 항목:
- 변경 파일 목록
- 주요 변경 요약
- 정책 영향 여부

## 2단계: 테스트 전략 판단

### 2-1. 변경 파일 분류

- `components/`, `views/`, `hooks/`: 컴포넌트/훅 (qa-tester 우선)
- `utils/`, `helpers/`, `lib/`, `adapters/`: 순수 함수 (직접 유닛 테스트)
- `styled.ts`, `constants.ts`, `types.ts`: UI/타입 (기본 스킵)

### 2-2. 정책 영향 키워드 탐지

```bash
rg "(getPeriod|addDate|startOf|endOf)" {변경파일들}
rg "(disabled|isDisabled)" {변경파일들}
rg "(filter|defaultValue|initialValue)" {변경파일들}
rg "(price|discount|amount|calculate)" {변경파일들}
```

판단:
- 정책 영향 있음: 테스트 필수
- 정책 영향 없음(UI only): 테스트 스킵 가능

## 3단계: 테스트 실행 분기

### Case A. 컴포넌트/훅 + 정책 영향

- `qa-tester` 에이전트 사용 가능 시 호출
- 정책 영향이 있으면 테스트 시나리오 생성

```typescript
Task(subagent_type="qa-tester", prompt="targetPath: {대상파일}, mode: create|update")
```

### Case B. 순수 함수 + 정책 영향

직접 유닛 테스트 작성:
1. 대상 함수 분석
2. 규칙 파일 존재 시 참조
3. `__tests__/*.test.ts` 작성
4. 테스트 스크립트 있으면 실행

### Case C. 기존 테스트 존재

관련 테스트만 실행:

```bash
find . -path "**/__tests__/*" -name "*.test.ts"
```

### Case D. UI only

테스트 스킵, 사유 명시:
- 텍스트/라벨 변경
- 스타일/레이아웃 변경

## 4단계: 코드 검증

독립 검증은 병렬 실행:

```typescript
Task(subagent_type="lint-fixer", model="haiku", prompt="린트 오류 수정: {변경파일}")
// 프로젝트 빌드 명령 실행
Task(subagent_type="qa-tester", prompt="테스트 생성: {대상파일}") // 필요 시
```

기본 순차 명령:

```bash
# 프로젝트 lint/build 명령 실행
npm run lint   # 또는 yarn lint
npm run build  # 또는 yarn build
```

## 4-1단계: 출시 품질 게이트 (필수)

`release-readiness-gate.md` Gate 1~5를 점검한다.
원칙:
- 하나라도 FAIL이면 커밋/PR 진행 금지

## 5단계: 커밋

규칙:
- 해당 티켓에서 수정한 파일만 `git add {path}`로 명시 추가
- `git add .`, `git add -A`, `git add --all` 금지

검증:

```bash
git diff --staged --name-only
```

커밋 메시지 형식:
- `[작성자] {type}: [{TICKET}] 설명`
- 상세 규칙은 `@../agents/git-operator.md`

## 6단계: PR 생성

```bash
git push -u origin {현재브랜치}
gh pr create \
  --title "type: subject" \
  --body "{템플릿 본문}"
```

주의:
- `gh` CLI 미설치/미인증이면 설치·인증 후 진행

## 7단계: 리뷰 연동

PR URL 출력 후 리뷰 요청.

## 8단계: 정리

디자인 작업 시에만 스크린샷 정리:

```bash
find . -path "*/.design-refs/*.png" -delete
find . -path "*/.design-refs/*.jpg" -delete
```

## 9단계: 최종 요약 출력

```markdown
## ✅ 작업 완료
### 티켓: {TICKET} - {제목}
### 테스트 전략
| 항목 | 결과 |
| --- | --- |
| 정책 영향 | 있음/없음 |
| 테스트 | 실행/스킵/추가 |
| 사유 | ... |
### 검증 결과
- [x] lint 통과
- [x] build 통과
- [x] 테스트 통과/스킵
### Release Readiness Gate
- Gate 1: PASS/FAIL
- Gate 2: PASS/FAIL
- Gate 3: PASS/FAIL
- Gate 4: PASS/FAIL
- Gate 5: PASS/FAIL
- 최종 판정: READY/NOT READY
### 커밋
- {hash}: {message}
### PR
- URL: {url}
- 상태: Open
### 정리
- [x] .design-refs 정리 (디자인 작업 시)
### 다음 단계
1. 자동 리뷰 확인
2. 리뷰 반영
3. 머지
```

## 옵션

- `--skip-test`: 정책 무관 변경에서 테스트 생략
- `--force-test`: 정책 무관이어도 테스트 강제
- `--skip-cleanup`: 정리 단계 생략
- `--draft`: Draft MR/PR 생성

## 완료 조건

- [ ] 변경 분석 완료
- [ ] 테스트 전략 확정
- [ ] 테스트 실행/스킵 + 사유 명시
- [ ] lint/build 검증 완료
- [ ] release-readiness-gate PASS
- [ ] 커밋 생성
- [ ] PR 생성
- [ ] `.design-refs` 정리 (디자인 작업 시)
- [ ] 최종 요약 출력
