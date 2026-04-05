---
paths:
  - '**/*.{ts,tsx,js,jsx}'
---

# 코딩 표준 & 모범 사례

> TypeScript/JavaScript 코딩 표준

---

## 핵심 원칙

| 원칙            | 설명               | 적용                   |
| --------------- | ------------------ | ---------------------- |
| **KISS**        | 가장 단순한 해결책 | 과도한 엔지니어링 지양 |
| **DRY**         | 중복 코드 금지     | 공통 로직 함수 추출    |
| **YAGNI**       | 필요할 때만 구현   | 추측성 일반화 금지     |
| **Readability** | 읽기 쉬운 코드     | 자기 설명적 변수명     |

---

## TypeScript 표준

### 변수 네이밍

```typescript
// ✅ 좋은 예: 설명적 이름
const marketSearchQuery = 'election';
const isUserAuthenticated = true;
const totalRevenue = 1000;

// ❌ 나쁜 예: 불명확한 이름
const q = 'election';
const flag = true;
const x = 1000;
```

### 함수 네이밍

```typescript
// ✅ 좋은 예: 동사-명사 패턴
async function fetchOrderData(orderId: string) {}
function calculateDiscountPrice(price: number, rate: number) {}
function isValidOrderStatus(status: string): boolean {}

// ❌ 나쁜 예: 불명확하거나 명사만
async function order(id: string) {}
function discount(a, b) {}
```

### Immutability (필수)

```typescript
// ✅ 항상 spread 연산자 사용
const updatedOrder = { ...order, status: 'completed' };
const updatedItems = [...items, newItem];

// ❌ 직접 변형 금지
order.status = 'completed';
items.push(newItem);
```

---

## 에러 처리

### API 호출

```typescript
// ✅ 좋은 예: 포괄적 에러 처리
async function fetchOrderDetail(orderId: string) {
  try {
    const response = await api.get(`/api/orders/${orderId}`);
    if (!response.data.success) {
      throw new Error(response.data.message);
    }
    return response.data;
  } catch (error) {
    console.error('Order fetch failed:', error);
    throw new Error('주문 정보를 불러올 수 없습니다');
  }
}
```

### Async/Await

```typescript
// ✅ 좋은 예: 병렬 실행
const [orders, stats] = await Promise.all([fetchOrders(), fetchStats()]);

// ❌ 나쁜 예: 불필요한 순차 실행
const orders = await fetchOrders();
const stats = await fetchStats();
```

---

## 타입 안전성

### 금지 패턴

| 금지                  | 대안                  | 예시                  |
| --------------------- | --------------------- | --------------------- |
| `any` 타입            | `unknown` + 타입 가드 | `data: unknown`       |
| `@ts-ignore`          | 타입 수정             | -                     |
| `// @ts-expect-error` | 타입 수정             | -                     |
| 암시적 `any`          | 명시적 타입           | `(item: Item) => ...` |
| return type 생략      | 명시적 반환 타입      | `: Promise<Order>`    |

```typescript
// ❌ 금지
const getData = (id) => api.get(`/orders/${id}`);

// ✅ 허용
const getData = (id: string): Promise<OrderResponse> => api.get(`/orders/${id}`);
```

### 명시적 타입 정의

```typescript
// ✅ 좋은 예
interface Order {
  id: string;
  status: 'pending' | 'active' | 'completed' | 'cancelled';
  createdAt: Date;
  items: OrderItem[];
}

function getOrder(id: string): Promise<Order> { /* */ }

// ❌ 나쁜 예: any 사용
function getOrder(id: any): Promise<any> { /* */ }
```

### null/undefined 처리

```typescript
// ✅ 좋은 예: Optional chaining
const userName = user?.profile?.name ?? '알 수 없음';

// ❌ 나쁜 예: 체크 없이 접근
const userName = user.profile.name;
```

---

## React 패턴

### 상태 업데이트

```typescript
// ✅ 좋은 예: 함수형 업데이트
setCount((prev) => prev + 1);

// ❌ 나쁜 예: 직접 참조 (stale 가능)
setCount(count + 1);
```

### 조건부 렌더링

```typescript
// ✅ 좋은 예: 명확한 조건
{isLoading && <Loading />}
{error && <ErrorMessage error={error} />}
{data && <DataDisplay data={data} />}

// ❌ 나쁜 예: 삼항 지옥
{isLoading ? <Loading /> : error ? <ErrorMessage /> : data ? <DataDisplay /> : null}
```

### Early Return

```typescript
// ✅ 좋은 예
function OrderCard({ order }: Props) {
  if (!order) return null;
  if (order.status === 'cancelled') return <CancelledBadge />;
  return <ActiveOrderCard order={order} />;
}
```

### Context/Provider 의존성

Dialog/Modal content 내부에서는 상위 Context 접근이 불가하다.

| 금지                  | 대안                         |
| --------------------- | ---------------------------- |
| `useModal` 직접 호출  | 상위에서 콜백을 props로 전달 |
| `useDialog` 직접 호출 | 상위에서 콜백을 props로 전달 |
| `useToast` 직접 호출  | 상위에서 콜백을 props로 전달 |

```typescript
// ❌ 금지: Dialog/Modal content 내부에서 context hook 사용
const Content = () => {
  const { close } = useModal();
  return <Button onClick={close} />;
};

// ✅ 허용: 상위에서 콜백 전달
const Content = ({ onClose }: { onClose: () => void }) => {
  return <Button onClick={onClose} />;
};
```

---

## 스타일링

| 금지              | 대안                       |
| ----------------- | -------------------------- |
| inline style 객체 | Emotion styled/css         |
| `!important`      | `&&` specificity           |
| px 하드코딩       | 디자인 토큰                |
| 하드코딩 색상값   | semanticColor 토큰         |

```typescript
// ❌ 금지
<div style={{ marginTop: 20 }}>

// ✅ 허용: styled 컴포넌트
const Container = styled.div`
  margin-top: ${spacing.md};
`;

// ✅ 허용: Emotion css prop (inline style이 아님)
<Typography css={{ marginTop: '4px' }}>
```

### !important 대신 `&&` specificity 패턴

`&&`는 Emotion이 생성한 자기 자신의 클래스를 한번 더 참조하여 specificity를 높이는 기법이다.
`!important`는 이후 override가 불가능해지므로 금지한다.

```typescript
// ❌ 금지
background-color: ${semanticColor.backgroundSecondary} !important;

// ✅ 허용: && 사용 (specificity 0,1,0 → 0,2,0)
&& {
  background-color: ${semanticColor.backgroundSecondary};
}
```

### transient props (`$` prefix)

styled 컴포넌트에 전달하는 custom prop은 `$` prefix를 붙인다.
`$` 없이 전달하면 DOM에 unknown attribute가 전달되어 React warning이 발생한다.

```typescript
// ❌ 금지: DOM에 isActive가 전달됨 → React warning
const Chip = styled.button<{ isActive: boolean }>`...`;
<Chip isActive={true}>

// ✅ 허용: $prefix로 DOM 전달 방지
const Chip = styled.button<{ $isActive: boolean }>`...`;
<Chip $isActive={true}>
```

### inline style vs css prop 구분

| 구문                    | 판정    | 이유                                        |
| ----------------------- | ------- | ------------------------------------------- |
| `style={{ margin: 8 }}` | ❌ 금지 | React의 inline style (정적 스타일에 비효율) |
| `css={{ margin: 8 }}`   | ✅ 허용 | Emotion의 css prop (컴파일 타임 처리)       |

---

## Code Smell 감지

| Smell         | 기준           | 해결               |
| ------------- | -------------- | ------------------ |
| **긴 함수**   | 50줄 이상      | 작은 함수로 분할   |
| **긴 파일**   | 300줄 이상     | 컴포넌트/로직 분리 |
| **깊은 중첩** | 4레벨 이상     | Early return       |
| **매직 넘버** | 설명 없는 숫자 | 상수로 추출        |
| **중복 코드** | 3회 이상 반복  | 함수로 추출        |

---

## 매직 넘버 처리

```typescript
// ❌ 나쁜 예
if (retryCount > 3) {}
setTimeout(callback, 500);

// ✅ 좋은 예
const MAX_RETRIES = 3;
const DEBOUNCE_DELAY_MS = 500;

if (retryCount > MAX_RETRIES) {}
setTimeout(callback, DEBOUNCE_DELAY_MS);
```

---

## Prettier 공통 설정

3개 레포(project, code-forge, project)에서 공통으로 사용하는 Prettier 설정:

```json
{
  "printWidth": 200,
  "singleQuote": true,
  "semi": true,
  "tabWidth": 2
}
```

---

## Import 순서 (ESLint import/order)

ESLint `import/order` 규칙으로 강제되는 상세 groups 순서:

```typescript
// 1. external - 외부 라이브러리
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

// 2. hooks - 커스텀 훅 (프로젝트 내부)
import { useOrderFilter } from '@/order/hooks/useOrderFilter';

// 3. shared packages - 모노레포 공유 패키지
import { Button } from '@repo/shared/components';
import { useGetOrderList } from '@repo/shared/queries/order';

// 4. internal - 같은 도메인 내부 모듈
import { OrderHeader } from '@/order/components/OrderHeader';

// 5. sibling - 형제 파일
import { OrderCard } from './OrderCard';

// 6. type - 타입 import (type-only)
import type { Order, OrderStatus } from '@repo/shared/types/order';

// 7. style - 스타일 파일
import { Container, Header } from './styled';
```

---

## 파일 네이밍 컨벤션

| 유형             | 규칙                   | 예시                                        |
| ---------------- | ---------------------- | ------------------------------------------- |
| 컴포넌트 폴더    | PascalCase             | `OrderCard/index.tsx`, `FilterButton/`       |
| 훅 파일          | camelCase, `use*`      | `useOrderFilter.ts`, `useGetOrderList.ts`    |
| 서비스 파일      | camelCase              | `orderService.ts`, `authService.ts`          |
| 페이지 라우팅    | kebab-case             | `order-list.tsx`, `product-detail.tsx`       |
| 유틸리티         | camelCase              | `formatDate.ts`, `calculateDiscount.ts`      |
| 타입 파일        | camelCase              | `order.types.ts`, `product.types.ts`         |
| 스타일 파일      | `styled.ts`            | `styled.ts` (컴포넌트 폴더 내)              |
| 쿼리 키 파일     | camelCase              | `queryKeys.ts`                              |

---

## API 서비스 메서드 네이밍

HTTP 동사 + 리소스명 패턴을 따른다:

```typescript
// services/order/index.ts

// GET 요청: get + 리소스명
export const getOrderList = (params: GetOrderListRequest): Promise<GetOrderListResponse> =>
  api.get('/api/orders', { params });

export const getOrderDetail = (orderId: string): Promise<GetOrderDetailResponse> =>
  api.get(`/api/orders/${orderId}`);

// POST 요청: post + 리소스명
export const postOrder = (body: PostOrderRequest): Promise<PostOrderResponse> =>
  api.post('/api/orders', body);

// PUT 요청: put + 리소스명
export const putOrder = (orderId: string, body: PutOrderRequest): Promise<PutOrderResponse> =>
  api.put(`/api/orders/${orderId}`, body);

// DELETE 요청: delete + 리소스명
export const deleteOrder = (orderId: string): Promise<void> =>
  api.delete(`/api/orders/${orderId}`);
```

---

## 쿼리 훅 네이밍

`use` + `Get/Post` + 도메인 패턴을 따른다:

```typescript
// queries/order/index.ts

// 조회: useGet + 도메인
export const useGetOrderList = (params: GetOrderListRequest) =>
  useQuery({
    queryKey: queryKeys.getOrderList(params),
    queryFn: () => getOrderList(params),
  });

export const useGetOrderDetail = (orderId: string) =>
  useQuery({
    queryKey: queryKeys.getOrderDetail(orderId),
    queryFn: () => getOrderDetail(orderId),
  });

// 변경: usePost/usePut/useDelete + 도메인
export const usePostOrder = () =>
  useMutation({
    mutationFn: postOrder,
  });
```

---

## 쿼리 키 팩토리

쿼리 키는 팩토리 패턴으로 관리한다:

```typescript
// queries/order/queryKeys.ts

export const queryKeys = {
  getOrderList: (params: GetOrderListRequest) => ['getOrderList', params] as const,
  getOrderDetail: (orderId: string) => ['getOrderDetail', orderId] as const,
};
```

**규칙:**
- 키 이름은 서비스 메서드명과 동일하게 맞춘다
- 파라미터를 키에 포함하여 자동 캐시 분리
- `as const`로 타입 안전성 확보

---

## 커밋 메시지 컨벤션

```
[작성자] type: [{티켓번호}] 설명
```

**예시:**

```bash
git commit -m "[홍길동] feat: [TICKET-123] 주문 목록 필터 추가"
git commit -m "[홍길동] fix: [TICKET-456] 날짜 필터 오프바이원 수정"
git commit -m "[홍길동] refactor: [TICKET-789] 주문 서비스 레이어 분리"
```

**type 종류:**

| type       | 용도                     |
| ---------- | ------------------------ |
| `feat`     | 새 기능                  |
| `fix`      | 버그 수정                |
| `refactor` | 리팩토링 (동작 변경 없음)|
| `style`    | 스타일/포맷팅 변경       |
| `docs`     | 문서 수정                |
| `test`     | 테스트 추가/수정         |
| `chore`    | 빌드/설정 변경           |

---

## 환경 파일

| 파일             | 용도                   |
| ---------------- | ---------------------- |
| `.env.local`     | 로컬 개발 (gitignore)  |
| `.env.dev`       | 개발 서버 환경         |
| `.env.stage`     | 스테이징 환경          |
| `.env.release`   | 프로덕션 환경          |

**주요 환경 변수:**

```bash
NEXT_PUBLIC_ENV=local|dev|stage|release
NEXT_PUBLIC_API_URL=https://api.example.com
```

**빌드 시 환경 지정:**

```bash
PROFILE=dev yarn build     # 개발 환경 빌드
PROFILE=stage yarn build   # 스테이징 환경 빌드
PROFILE=release yarn build # 프로덕션 환경 빌드
```

---

## 참조

| 문서                          | 용도               |
| ----------------------------- | ------------------ |
| `react-nextjs-conventions.md` | React/Next.js 규칙 |
| `state-and-server-state.md`   | 상태 관리 경계     |
| `forbidden-patterns.md`       | 금지 패턴          |
