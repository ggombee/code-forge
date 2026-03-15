# Required Behaviors (필수 행동)

> 모든 작업에서 반드시 따라야 할 규칙

---

## 작업 시작

### 필수 1: 복잡도 판단

**참조**: `@../../rules/frontend/thinking-model.md`

| 복잡도 | 접근 |
|--------|------|
| LOW | 즉시 수정 |
| MEDIUM | 패턴 확인 → 구현 → 검증 |
| HIGH | planner 에이전트로 계획 수립 |

### 필수 2: 파일 읽기 후 수정

```typescript
// ✅ 필수 순서
Read({ file_path: "src/components/Button.tsx" })  // 1. 읽기
Edit({ ... })  // 2. 수정

// ❌ 금지: 읽지 않고 수정
Edit({ ... })
```

### 필수 3: 병렬 읽기

3개 이상 독립 파일은 반드시 병렬로 읽기 (단일 메시지).

---

## 코드 작성

### 필수 4: TypeScript strict 모드

```typescript
// ✅ 명시적 타입
function getItems(params: ItemParams): Promise<Item[]> {
  return itemService.getList(params);
}

// ❌ any 사용 금지
function getItems(params: any): any { ... }
```

### 필수 5: Import 순서

상세: `.claude/rules/frontend/react-nextjs-conventions.md`

외부 라이브러리 → 내부 모듈 (`@/`) → 상대 경로

---

## 검증

### 필수 6: lint/build 검증

코드 변경 후 반드시 검증:

```bash
npx tsc --noEmit    # 타입 체크
npm run lint        # 린트 체크
npm run build       # 빌드 체크
```

### 필수 7: 정책 변경 시 테스트

| 정책 유형 | 테스트 필수 |
|----------|------------|
| 날짜/기간 계산 | ✅ |
| 가격/할인 계산 | ✅ |
| 필터 조건 | ✅ |
| disabled 조건 | ✅ |

---

## 에이전트 활용

### 필수 8: 에이전트 위임

MEDIUM 이상 복잡도에서 독립적/전문적 작업은 에이전트에 위임 권장.

### 필수 9: 모델 선택

**참조**: `@../multi-agent/coordination-guide.md` (단일 진실 공급원)

LOW → haiku / MEDIUM → sonnet / HIGH → opus

---

## Git 작업

### 필수 10: 커밋 메시지 형식

SSOT: `.claude/agents/git-operator.md`

형식: `type: subject` (AI 표시/이모지 금지)

### 필수 11: 해당 파일만 커밋

```bash
# ❌ 금지
git add .

# ✅ 필수: 특정 파일만
git add src/components/Button.tsx
```

---

## 참조 문서

| 문서 | 관련 항목 |
|------|----------|
| `@forbidden-patterns.md` | 필수 4, 5 |
| `@../../rules/frontend/thinking-model.md` | 필수 1 |
| `@../multi-agent/coordination-guide.md` | 필수 9 |
