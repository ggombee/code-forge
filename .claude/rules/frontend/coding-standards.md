---
globs:
  - "**/*.{ts,tsx,js,jsx}"
alwaysApply: false
---

# 코딩 표준 & 모범 사례

> CLAUDE.md, forbidden-patterns.md 보완 규칙

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
// ✅ 좋은 예: 동사+명사 패턴
async function fetchOrderData(orderId: string) {}
function calculateDiscountPrice(price: number, rate: number) {}
function isValidOrderStatus(status: string): boolean {}

// ❌ 나쁜 예: 불명확하거나 명사만
async function order(id: string) {}
function discount(a, b) {}
function status(s) {}
```

### Immutability (필수)

```typescript
// ✅ 항상 spread 연산자 사용
const updatedOrder = {
  ...order,
  status: 'completed',
};
const updatedItems = [...items, newItem];

// ❌ 직접 변형 금지
order.status = 'completed'; // 금지
items.push(newItem); // 금지
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

// ❌ 나쁜 예: 에러 처리 없음
async function fetchOrderDetail(orderId: string) {
  const response = await api.get(`/api/orders/${orderId}`);
  return response.data;
}
```

### Async/Await

```typescript
// ✅ 좋은 예: 병렬 실행
const [orders, users, stats] = await Promise.all([
  fetchOrders(),
  fetchUsers(),
  fetchStats()
]);

// ❌ 나쁜 예: 불필요한 순차 실행
const orders = await fetchOrders();
const users = await fetchUsers();
const stats = await fetchStats();
```

---

## 타입 안전성

### 명시적 타입 정의

```typescript
// ✅ 좋은 예: 적절한 타입
interface Order {
  id: string;
  status: 'pending' | 'active' | 'completed' | 'cancelled';
  createdAt: Date;
  items: OrderItem[];
}

function getOrder(id: string): Promise<Order> {
  // 구현
}

// ❌ 나쁜 예: any 사용
function getOrder(id: any): Promise<any> {
  // 구현
}
```

### null/undefined 처리

```typescript
// ✅ 좋은 예: Optional chaining
const userName = user?.profile?.name ?? '알 수 없음';

// ❌ 나쁜 예: 체크 없이 접근
const userName = user.profile.name; // 런타임 에러 가능
```

---

## React 패턴

### 상태 업데이트

```typescript
// ✅ 좋은 예: 함수형 업데이트
const [count, setCount] = useState(0);
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
{isLoading ? <Loading /> : error ? <ErrorMessage error={error} /> : data ? <DataDisplay data={data} /> : null}
```

### Early Return

```typescript
// ✅ 좋은 예: Early return
function OrderCard({ order }: Props) {
  if (!order) return null;
  if (order.status === 'cancelled') return <CancelledBadge />;
  return <ActiveOrderCard order={order} />;
}

// ❌ 나쁜 예: 깊은 중첩
function OrderCard({ order }: Props) {
  if (order) {
    if (order.status !== 'cancelled') {
      return <ActiveOrderCard order={order} />;
    } else {
      return <CancelledBadge />;
    }
  }
  return null;
}
```

---

## Code Smell 감지

| Smell          | 기준           | 해결               |
| -------------- | -------------- | ------------------ |
| **긴 함수**    | 50줄 이상      | 작은 함수로 분할   |
| **긴 파일**    | 300줄 이상     | 컴포넌트/로직 분리 |
| **깊은 중첩**  | 4레벨 이상     | Early return       |
| **매직 넘버**  | 설명 없는 숫자 | 상수로 추출        |
| **중복 코드**  | 3회 이상 반복  | 함수로 추출        |

---

## 매직 넘버 처리

```typescript
// ❌ 나쁜 예: 설명 없는 숫자
if (retryCount > 3) {}
setTimeout(callback, 500);

// ✅ 좋은 예: 명명된 상수
const MAX_RETRIES = 3;
const DEBOUNCE_DELAY_MS = 500;

if (retryCount > MAX_RETRIES) {}
setTimeout(callback, DEBOUNCE_DELAY_MS);
```

---

## 참조

| 문서                      | 용도             |
| ------------------------- | ---------------- |
| `forbidden-patterns.md`   | 금지 패턴        |
| `thinking-model.md`       | 사고 모델        |
