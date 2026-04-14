---
paths:
  - '**/*.{ts,tsx,js,jsx}'
---

# 코딩 표준 & 모범 사례

> TypeScript/JavaScript 범용 코딩 표준. 스택 종속 상세(스타일링, 파일 네이밍, API/쿼리 컨벤션, 커밋/환경 파일)는 `@${CLAUDE_PLUGIN_ROOT}/references/coding-conventions-detail.md`로 분리.

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

// ❌ 나쁜 예: 불명확한 이름
const q = 'election';
const flag = true;
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

## 타입 안전성

### 금지 패턴 (범용 TS 규칙)

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
interface Order {
  id: string;
  status: 'pending' | 'active' | 'completed' | 'cancelled';
  createdAt: Date;
  items: OrderItem[];
}

function getOrder(id: string): Promise<Order> { /* */ }
```

### null/undefined 처리

```typescript
// ✅ Optional chaining
const userName = user?.profile?.name ?? '알 수 없음';

// ❌ 체크 없이 접근
const userName = user.profile.name;
```

---

## 에러 처리

### API 호출

```typescript
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
// ✅ 병렬 실행
const [orders, stats] = await Promise.all([fetchOrders(), fetchStats()]);

// ❌ 불필요한 순차 실행
const orders = await fetchOrders();
const stats = await fetchStats();
```

---

## React 패턴

### 상태 업데이트

```typescript
// ✅ 함수형 업데이트
setCount((prev) => prev + 1);

// ❌ 직접 참조 (stale 가능)
setCount(count + 1);
```

### 조건부 렌더링

```typescript
// ✅ 명확한 조건
{isLoading && <Loading />}
{error && <ErrorMessage error={error} />}
{data && <DataDisplay data={data} />}

// ❌ 삼항 지옥
{isLoading ? <Loading /> : error ? <ErrorMessage /> : data ? <DataDisplay /> : null}
```

### Early Return

```typescript
function OrderCard({ order }: Props) {
  if (!order) return null;
  if (order.status === 'cancelled') return <CancelledBadge />;
  return <ActiveOrderCard order={order} />;
}
```

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

## Import 순서 (ESLint import/order)

```typescript
// 1. external - 외부 라이브러리
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';

// 2. hooks - 커스텀 훅 (프로젝트 내부)
import { useOrderFilter } from '@/order/hooks/useOrderFilter';

// 3. shared packages - 모노레포 공유 패키지
import { Button } from '@repo/shared/components';

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

## 상세 컨벤션 참조

스택 종속 또는 프로젝트별 컨벤션은 필요 시 `@참조`로 로드:

`@${CLAUDE_PLUGIN_ROOT}/references/coding-conventions-detail.md` — Prettier 설정, 파일 네이밍, API 메서드 네이밍, 쿼리 훅/키 팩토리, 커밋 메시지, 환경 파일, Emotion 스타일링, Context/Provider 의존성
