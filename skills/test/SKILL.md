---
name: test
description: 테스트 통합 진입점. 변경 파일을 분석하여 유닛/E2E/세팅을 자동 라우팅.
---

# /test — 통합 테스트 Facade

테스트 관련 모든 작업의 **단일 진입점**. 변경 파일 패턴을 분석하여 적절한 하위 스킬로 자동 라우팅합니다.

**핵심 원칙**: 기존 스킬을 수정하지 않는 Facade 패턴. 실행은 `/generate-test`, `/e2e`, `/setup-test`, `/setup-e2e`에 위임.

---

## 사용법

```
/test                          → git diff 기반 자동 감지
/test {path}                   → 파일 패턴 자동 판단
/test {path} --unit            → 유닛/통합 강제 (/generate-test 직행)
/test {path} --e2e             → E2E 강제 (/e2e 직행)
/test --setup                  → /setup-test + /setup-e2e 순차
/test --setup-unit             → /setup-test만
/test --setup-e2e              → /setup-e2e만
/test --init                   → .policy/ 기반 전체 TC 일괄 생성
/test --all                    → 전체 테스트 실행 (yarn test && yarn playwright test)
```

---

## Step 1: 플래그 파싱

```
--setup, --setup-unit, --setup-e2e
  → 해당 setup 스킬로 위임 후 종료

--init
  → Section "─── --init 모드" 로 진입

--all
  → yarn test && yarn playwright test 실행 후 종료

--unit
  → /generate-test 워크플로우 직행

--e2e
  → /e2e 워크플로우 직행

그 외 → Step 2
```

---

## Step 2: 대상 파일 결정

```
경로 인자 있음 → 해당 파일/디렉토리
경로 인자 없음 → git diff --name-only + git diff --cached --name-only
```

---

## Step 3: 카테고리 분류

각 파일을 아래 규칙으로 분류:

| 패턴 매칭 | 카테고리 | 라우팅 |
|----------|---------|--------|
| `utils/`, `helpers/`, `lib/`, `adapters/` | 유틸 | Jest 유닛 직접 작성 (modules/testing/jest 참조) |
| `hooks/` | 훅/로직 | → `/generate-test` |
| `components/` (단일 컴포넌트) | 컴포넌트 | → `/generate-test` |
| `pages/`, `views/` (라우트 레벨) | 플로우 | → `/e2e` |
| `styled.ts`, `*.styles.ts` | 디자인 | 스냅샷 (Phase C에서 별도) |
| `types.ts`, `constants.ts`, `*.d.ts` | 타입/상수 | 스킵 |

### .policy/ 연동 (있는 경우)

```
대상 파일이 .policy/*.json의 affectedFiles에 매칭되면
  해당 매트릭스의 testFiles를 함께 실행 대상에 추가
```

---

## Step 4: 실행 계획 보고

```markdown
## /test 분석 결과

| 카테고리 | 대상 | 예정 작업 |
|---------|------|----------|
| 유틸 | formatDate.ts, period.ts | Jest 유닛 TC 생성 |
| 훅 | useCTA.tsx | testgen 에이전트 호출 |
| 플로우 | orders/list | /e2e Forge Loop |

총 예상 TC: N개
진행할까요? [Y/N]
```

---

## Step 5: 승인 후 병렬 실행

독립적인 카테고리는 병렬 실행:

```typescript
// 유틸: modules/testing/jest SKILL.md 패턴으로 직접 작성
// 훅/컴포넌트:
Task(subagent_type="testgen", prompt="targetPath: {파일}\nmode: create")

// 페이지: /e2e 워크플로우 진입
```

---

## Step 6: 결과 종합 리포트

```markdown
## /test 결과

| 카테고리 | 대상 | TC 수 | 결과 |
|---------|------|-------|------|
| 유틸 | formatDate.ts | 8 | PASS |
| 훅 | useCTA.tsx | 12 | PASS |
| 플로우 | /orders | 4 | 2 PASS, 2 FAIL |

실패 항목:
- order-list.spec.ts:42 필터 클릭 후 테이블 갱신 안 됨
- order-list.spec.ts:67 미결제 탭 DatePicker 미숨김
```

---

## ─── --init 모드 (일괄 생성) ───

### Step 1: 대상 스캔

```
.policy/*.json 있음:
  각 매트릭스의 affectedFiles + flows 추출
  카테고리별 분류

.policy/ 없음:
  src/ 전체 스캔
  파일명 패턴으로 카테고리 분류
```

### Step 2: 계획 보고

```
프로젝트 전체 스캔 결과:
  - 유틸 함수 12개 → 유닛 TC 생성 예정
  - 훅 5개 → 통합 TC 생성 예정
  - 페이지 3개 → E2E spec 생성 예정
  총 예상 TC: ~60개
진행할까요?
```

### Step 3: 병렬 실행

```typescript
// testgen 에이전트를 파일별로 spawn (Agent Teams 활용)
// E2E는 페이지별로 순차 (Phase 1~2만, Forge Loop은 개별 호출 시)
```

### Step 4: 결과 리포트

---

## 입력별 라우팅 예시

```
/test                            → git diff → 자동 판단
/test src/order/utils/period.ts  → 유틸 → Jest 유닛
/test src/order/hooks/useCTA.tsx → 훅 → testgen
/test src/order/views/list/      → 페이지 → /e2e
/test --e2e /orders              → E2E 명시
/test --unit src/utils/date.ts   → 유닛 명시
/test --setup                    → /setup-test + /setup-e2e
/test --init                     → 전체 일괄 생성
/test --all                      → yarn test && playwright test
```

---

## 기존 스킬과의 관계

| 기존 스킬 | 변경 | /test 호출 시 |
|-----------|------|--------------|
| `/generate-test` | 변경 없음 | 라우팅으로 호출 |
| `/e2e` | 변경 없음 | 라우팅으로 호출 |
| `/setup-test` | 변경 없음 | `--setup-unit` 시 호출 |
| `/setup-e2e` | 변경 없음 | `--setup-e2e` 시 호출 |

**`/test`는 Facade일 뿐**, 실제 로직은 위 스킬들에 위임. 사용자는 `/test` 하나만 기억하면 되고, 필요 시 하위 스킬 직접 호출도 가능.

---

## VERIFY와의 연동

`thinking-model.md` VERIFY 체크리스트의 "(정책 변경 시) 테스트 작성?" 항목에서 `/test {파일}` 실행을 권장. 자동 호출은 하지 않음 (비용 통제).

---

## 금지 사항

- `/test`가 직접 Jest/Playwright 실행하지 않는다 — 기존 스킬에 위임
- `/test --init` 호출 시 사용자 승인 없이 진행 금지 (비용이 크므로 반드시 확인)
- `.policy/` 없는 프로젝트에서 `--init` 호출 시 명확한 안내 출력