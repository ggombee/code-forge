---
name: react-nextjs-pages
description: Next.js Pages Router 프로젝트 컨벤션. 라우팅, pageInfo, Import 순서, 컨테이너/뷰 패턴.
---

# React & Next.js Pages Router 컨벤션

이 프로젝트는 **Next.js 14 Pages Router**를 사용한다. App Router 패턴을 적용하지 않는다.

---

## 라우팅 구조

```
apps/{app}/
├── pages/          # 라우팅 진입점 (얇게 유지)
└── src/            # 도메인별 로직
```

- `pages/` 파일은 얇게 유지
- 로직은 `src/{도메인}/` 아래에 분리
- 컨테이너/뷰 패턴 사용

---

## pageInfo static 속성

페이지 컴포넌트에 `pageInfo` static 속성으로 레이아웃을 지정한다:

```typescript
const OrderPage: NextPageWithLayout = () => {
  return <OrderContainer />;
};

OrderPage.pageInfo = {
  routeKey: RouteKey.ORDER,
  layout: Layout.ORDER,
};

export default OrderPage;
```

---

## 페이지 컴포넌트 구조

```typescript
// ✅ 좋은 예: 페이지는 얇게, 로직은 src로 분리
// pages/order/[orderId].tsx
import { OrderContainer } from '@/order/containers/OrderContainer';

const OrderPage: NextPageWithLayout = () => {
  return <OrderContainer />;
};

OrderPage.pageInfo = {
  routeKey: RouteKey.ORDER,
  layout: Layout.ORDER,
};

export default OrderPage;
```

```typescript
// ❌ 나쁜 예: 페이지에 로직이 모두 포함됨
// pages/order/[orderId].tsx
const OrderPage = () => {
  const { orderId } = useRouter().query;
  const { data } = useQuery(...);
  // 수백 줄...
};
```

---

## Import 순서 (ESLint 강제)

아래 순서를 반드시 지킨다:

```typescript
// 1. 외부 라이브러리
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

// 2. @repo/shared (모노레포 공유 패키지)
import { Button } from '@repo/shared/components';
import { useOrderQuery } from '@repo/shared/queries/order';

// 3. 상대 경로 (현재 앱 내부)
import { OrderHeader } from './components/OrderHeader';
import { formatPrice } from '../utils/format';
```

```typescript
// ❌ 나쁜 예: 순서가 뒤섞임
import { OrderHeader } from './OrderHeader';
import { useState } from 'react';
import { Button } from '@repo/shared/components';
```

---

## 컴포넌트 작성 규칙

### 함수 선언 방식

- 페이지 컴포넌트: `const PageName: NextPageWithLayout = () => {}`
- 일반 컴포넌트: `const ComponentName = () => {}` 또는 `function ComponentName() {}`

### Props 타입 정의

- 컴포넌트와 동일 파일에 정의한다
- 별도 types 파일 분리는 복잡한 경우에만 한다

```typescript
interface OrderCardProps {
  order: Order;
  onSelect: (id: string) => void;
}

const OrderCard = ({ order, onSelect }: OrderCardProps) => { ... };
```

---

## 경로/별칭

- `@/`는 각 앱의 `src` 기준 (예: `apps/{app-1}/src`)
- `@repo/shared`는 모노레포 공용 패키지

---

## API 프록시

- `/api/*` → `NEXT_PUBLIC_API_URL`로 프록시

```typescript
// ❌ 나쁜 예: 프론트엔드에서 직접 외부 API 호출
const data = await axios.get('https://api.example.com/orders');

// ✅ 좋은 예: /api 프록시 경유
const data = await api.get('/api/orders');
```

---

## 파일 명명 규칙

| 유형     | 규칙                     | 예시                              |
| -------- | ------------------------ | --------------------------------- |
| 페이지   | kebab-case 또는 [param]  | `order-list.tsx`, `[orderId].tsx` |
| 컴포넌트 | PascalCase               | `OrderCard.tsx`                   |
| 훅       | camelCase, use 접두사    | `useOrderStatus.ts`               |
| 유틸리티 | camelCase                | `formatDate.ts`                   |
| 타입     | PascalCase, types 접미사 | `order.types.ts`                  |
| 스타일   | 컴포넌트명.styles        | `OrderCard.styles.ts`             |

---

## 기존 코드 패턴 참조 규칙

새로운 기능을 구현하기 전에 반드시 기존 코드에서 유사 패턴을 찾는다:

| 구현 대상         | 탐색 경로                     |
| ----------------- | ----------------------------- |
| 앱 도메인 관련    | `apps/{앱이름}/src/{도메인}/` |
| 공용 컴포넌트     | `packages/shared/components/` |
| 공용 훅           | `packages/shared/hooks/`      |
| 공용 타입         | `packages/shared/types/`      |

새 코드 작성 전 체크리스트:

- [ ] PDS에 해당 컴포넌트가 있는가?
- [ ] 유사한 컴포넌트/훅이 기존에 있는가?
- [ ] 재사용 가능한 타입이 있는가?
- [ ] 색상/스타일 상수가 정의되어 있는가?
