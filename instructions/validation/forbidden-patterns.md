# Forbidden Patterns

> 프로젝트에서 금지된 패턴 목록

---

## 언어 표현

| 금지                 | 대안                |
| -------------------- | ------------------- |
| "~할 것 같습니다"    | "~합니다"           |
| "아마도", "추측컨대" | 확인 후 명시적 진술 |
| "~일 수 있습니다"    | 조건 명시하여 단정  |

---

## 코드 품질

> TypeScript 타입 안전성 규칙은 `rules/coding-standards.md` → **타입 안전성 > 금지 패턴** 참조

---

## 상태 관리

| 금지                    | 대안                  |
| ----------------------- | --------------------- |
| 서버 상태에 useState    | TanStack Query        |
| 과도한 전역 상태        | 로컬 상태 우선        |
| Query 내 직접 상태 변경 | mutation + invalidate |

```typescript
// ❌ 금지: 서버 데이터를 useState로 관리
const [orders, setOrders] = useState([]);
useEffect(() => {
  fetchOrders().then(setOrders);
}, []);

// ✅ 허용: TanStack Query 사용
const { data: orders } = useOrderListQuery(params);
```

---

## Import 순서

| 순서               | 예시                                               |
| ------------------ | -------------------------------------------------- |
| 1. 외부 라이브러리 | `import { useQuery } from '@tanstack/react-query'` |
| 2. @repo/shared    | `import { Button } from '@repo/shared/components'` |
| 3. @/ alias        | `import { useOrder } from '@/order/hooks'`         |
| 4. 상대 경로       | `import { Table } from './components'`             |

**ESLint 강제**: `@typescript-eslint/consistent-type-imports`

---

## Git/PR

| 금지                  | 이유          |
| --------------------- | ------------- |
| 커밋 메시지에 AI 표시 | 불필요한 노출 |
| 커밋 메시지에 이모지  | 일관성        |
| force push to master  | 히스토리 파괴 |
| --no-verify           | 검증 우회     |

```bash
# ❌ 금지
git commit -m "🚀 feat: add feature"
git commit -m "feat: add feature (by Claude)"
git push --force origin master

# ✅ 허용
git commit -m "feat: [{티켓번호}] add feature"
```

---

## 워크플로우

| 금지                | 대안                |
| ------------------- | ------------------- |
| 읽지 않은 파일 수정 | Read → Edit         |
| 테스트 없이 PR      | testgen 실행        |
| 린트 오류 무시      | lint-fixer 실행     |
| 기존 정책 임의 변경 | 사용자 확인 후 변경 |

---

## Context/Provider 의존성

> `rules/coding-standards.md` → **React 패턴 > Context/Provider 의존성** 참조

---

## API/서비스

| 금지             | 대안                             |
| ---------------- | -------------------------------- |
| 수동 axios 호출  | 앱별 api 래퍼 사용               |
| 직접 에러 핸들링 | Query의 onError                  |
| 하드코딩된 URL   | 환경 변수                        |

```typescript
// ❌ 금지
const res = await axios.get('https://api.example.com/orders');

// ✅ 허용: 앱별 api 래퍼 사용
const res = await api.get('/api/sales/orders');
```

---

## 테스트

| 금지             | 대안                   |
| ---------------- | ---------------------- |
| 테스트 삭제      | 테스트 수정            |
| 하드코딩된 날짜  | `jest.useFakeTimers()` |
| 구현 상세 테스트 | 동작 중심 테스트       |

---

## 스타일링

> `rules/coding-standards.md` → **스타일링** 섹션 참조 (inline style, !important, px 하드코딩, transient props)

---

## 체크리스트

PR 전 확인:

- [ ] `any` 타입 없음
- [ ] return type 명시
- [ ] Import 순서 준수
- [ ] TanStack Query로 서버 상태 관리
- [ ] 테스트 작성/실행
- [ ] 린트 오류 없음

---

## 참조 문서

| 문서                                                       | 관련 금지 항목 |
| ---------------------------------------------------------- | -------------- |
| `@${CLAUDE_PLUGIN_ROOT}/rules/coding-standards.md`         | 코딩 표준      |
| `@${CLAUDE_PLUGIN_ROOT}/rules/thinking-model.md`           | 작업 절차      |
