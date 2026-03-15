---
name: done
description: 작업 완료 후 검증 → 테스트 → 커밋 → PR 생성까지 전체 플로우 수행.
---

# /done - 작업 완료 및 PR 생성

구현 완료 후 사용합니다. 검증 → 테스트 → 커밋 → PR 생성 → 정리까지 전체 플로우를 수행합니다.

**참조 규칙**:

- `@${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/coordination-guide.md` (병렬 실행)
- `@${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/agent-roster.md` (에이전트 선택)
- `@${CLAUDE_PLUGIN_ROOT}/instructions/validation/forbidden-patterns.md` (금지 패턴)
- `@${CLAUDE_PLUGIN_ROOT}/rules/thinking-model.md` (작업 절차 — VERIFY 기준으로 검증)

## 사용법

```
/done TICKET-123
/done                # 현재 브랜치의 티켓 번호 자동 감지
```

---

## 수행 작업

### 1. 변경 내용 분석

```bash
git status
git diff --staged
git diff
```

**분석 항목:**

- 변경된 파일 목록
- 주요 변경 내용 요약
- **정책 영향 여부 판단** (아래 기준표 참조)

---

### 2. 테스트 전략 판단

> 코드 = 문서. **의도치 않은 정책 변경**을 방지하기 위한 테스트 전략

#### 2-1. 변경 파일 분류

| 경로 패턴                                 | 분류        | 테스트 도구          |
| ----------------------------------------- | ----------- | -------------------- |
| `components/`, `views/`, `hooks/`         | 컴포넌트/훅 | **testgen 에이전트** |
| `utils/`, `helpers/`, `lib/`, `adapters/` | 순수 함수   | **Claude 직접 작성** |
| `styled.ts`, `constants.ts`, `types.ts`   | UI/타입     | 스킵                 |

#### 2-2. 정책 영향 판단 기준

| 변경 내용            | 대상 유형 | 테스트 전략  | 도구               |
| -------------------- | --------- | ------------ | ------------------ |
| 필터 UI 변경         | 컴포넌트  | 통합 테스트  | **testgen**        |
| disabled 조건 변경   | 컴포넌트  | 통합 테스트  | **testgen**        |
| 새 UI 상태 추가      | 컴포넌트  | BDD 시나리오 | **testgen + @see** |
| 날짜/기간 계산 변경  | 순수 함수 | 유닛 테스트  | **Claude 직접**    |
| 가격/할인 계산 변경  | 순수 함수 | 유닛 테스트  | **Claude 직접**    |
| 상태 전이 로직 변경  | 순수 함수 | 유닛 테스트  | **Claude 직접**    |
| 텍스트/라벨 변경     | UI only   | 스킵         | -                  |
| 스타일/레이아웃 변경 | UI only   | 스킵         | -                  |

---

### 3. 테스트 자동 실행

#### Case A: 컴포넌트/훅 + 정책 영향 -> testgen 자동 호출

```
컴포넌트/훅 변경이 감지되었습니다. testgen 에이전트를 호출합니다.

실행:
Task(subagent_type: "testgen", prompt: "
  targetPath: {대상 파일}
  mode: create (또는 update)
")
```

#### Case B: 순수 함수 + 정책 영향 -> Claude 직접 유닛 테스트 작성

```
순수 함수 변경이 감지되었습니다. 유닛 테스트를 작성합니다.

실행:
1. 대상 파일 분석
2. unit-test-conventions.md 규칙 참조
3. __tests__/{파일명}.test.ts 생성
4. yarn test 실행
```

#### Case C: 기존 테스트 있음 -> 실행만

```bash
yarn test --filter={해당앱} -- --testPathPattern="{관련 테스트}"
```

#### Case D: UI only (정책 무관) -> 스킵

---

### 4. 코드 검증 (병렬 실행)

```typescript
// 병렬 검증 (단일 메시지에서 동시 호출)
Task((subagent_type = 'lint-fixer'), (model = 'haiku'), (prompt = '린트 오류 수정'));
Bash('yarn build --filter={해당앱}'); // 타입 체크
```

---

### 4-1. 품질 검토 (필수)

작업 절차(Working Protocol)의 VERIFY 기준으로 아래 항목을 반드시 점검:

- 계획 검토/재검토가 타당한가?
- 구현이 목적과 정확히 맞는가?
- 잠재 버그/크리티컬/보안 이슈는 없는가?
- 개선 내용에 회귀나 사이드 이펙트는 없는가?
- 큰 함수/파일은 분리됐는가?
- 재사용/통합 가능한 기존 코드를 활용했는가?
- 불필요 코드가 정리됐는가?
- "지금 배포 가능한가?" 질문에 근거로 답할 수 있는가?

**원칙**: 하나라도 FAIL이면 커밋/PR 진행 금지.

---

### 5. 커밋 생성

**사전 조건**: 4-1 출시 품질 게이트 PASS

```bash
# 절대 금지 - 전체 파일 add
git add .
git add -A

# 올바른 방법 - 수정한 파일만 명시적으로 add
git add apps/{앱이름}/src/{도메인}/views/{뷰이름}/components/{컴포넌트}/index.tsx
```

**커밋 메시지 형식:**

```
[작성자] feat: [{티켓번호}] [{페이지명}] {변경 내용 요약}

- {세부 변경 1}
- {세부 변경 2}
```

---

### 6. PR 생성 (GitHub)

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

### 7. 정리

```bash
find apps/{앱이름}/src -path "*/.design-refs/*.png" -delete
find apps/{앱이름}/src -path "*/.design-refs/*.jpg" -delete
```

---

### 8. 최종 요약 출력

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
```

---

## 옵션

| 옵션           | 설명                             | 사용 예시                           |
| -------------- | -------------------------------- | ----------------------------------- |
| `--skip-test`  | 테스트 스킵 (정책 무관 확인 후)  | `/done TICKET-123 --skip-test`      |
| `--force-test` | 정책 무관이어도 테스트 강제 실행 | `/done TICKET-123 --force-test`     |
| `--draft`      | Draft PR로 생성                  | `/done TICKET-123 --draft`          |

---

## 완료 조건

- [ ] 변경 내용 분석 완료
- [ ] 테스트 전략 판단됨
- [ ] 테스트 실행/스킵 완료 (사유 명시)
- [ ] lint/build 검증 통과
- [ ] 커밋 생성됨
- [ ] PR 생성됨 (URL 출력)
- [ ] .design-refs 스크린샷 정리됨
- [ ] 최종 요약 출력됨
