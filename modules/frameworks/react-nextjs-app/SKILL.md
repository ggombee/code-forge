---
name: react-nextjs-app
description: Next.js App Router 프로젝트 컨벤션. Server/Client Components, metadata API, 특수 파일 패턴, Route Groups.
---

# React & Next.js App Router 컨벤션

이 프로젝트는 **Next.js App Router**를 사용한다. `app/` 디렉토리 기반의 파일 시스템 라우팅을 따른다.

---

## 디렉토리 구조

```
app/
├── layout.tsx          # 루트 레이아웃 (필수)
├── page.tsx            # 루트 페이지
├── loading.tsx         # 로딩 UI
├── error.tsx           # 에러 UI
├── not-found.tsx       # 404 UI
├── (auth)/             # Route Group (URL에 포함되지 않음)
│   ├── login/
│   │   └── page.tsx
│   └── register/
│       └── page.tsx
├── dashboard/
│   ├── layout.tsx      # 중첩 레이아웃
│   ├── page.tsx
│   └── @analytics/     # Parallel Route
│       └── page.tsx
└── api/                # Route Handlers
    └── users/
        └── route.ts
```

---

## Server vs Client Components

### Server Component (기본값)

```typescript
// app/orders/page.tsx - 서버 컴포넌트 (기본값)
import { db } from '@/lib/db';

// async 함수 사용 가능
export default async function OrdersPage() {
  const orders = await db.orders.findMany();

  return (
    <ul>
      {orders.map((order) => (
        <li key={order.id}>{order.name}</li>
      ))}
    </ul>
  );
}
```

### Client Component

```typescript
// app/orders/OrderFilters.tsx
'use client'; // 반드시 파일 최상단에 선언

import { useState } from 'react';

export function OrderFilters() {
  const [filter, setFilter] = useState('all');

  return (
    <select value={filter} onChange={(e) => setFilter(e.target.value)}>
      <option value="all">전체</option>
      <option value="pending">대기중</option>
    </select>
  );
}
```

```typescript
// ✅ 좋은 예: Server Component가 Client Component를 children으로 받음
// app/orders/layout.tsx (Server Component)
import { OrderFilters } from './OrderFilters'; // Client Component

export default function OrdersLayout({ children }: { children: React.ReactNode }) {
  return (
    <div>
      <OrderFilters />
      {children}
    </div>
  );
}

// ❌ 나쁜 예: 불필요하게 'use client' 추가
'use client';
// useState, useEffect 없이 'use client' 선언
export default function StaticCard({ title }: { title: string }) {
  return <div>{title}</div>;
}
```

---

## metadata API

```typescript
// app/orders/page.tsx - 정적 메타데이터
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: '주문 목록',
  description: '전체 주문 내역을 확인합니다.',
};

export default function OrdersPage() { ... }
```

```typescript
// app/orders/[id]/page.tsx - 동적 메타데이터
import type { Metadata } from 'next';

interface Props {
  params: { id: string };
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const order = await fetchOrder(params.id);
  return {
    title: `주문 #${order.id}`,
    description: `${order.status} 상태의 주문입니다.`,
  };
}

export default async function OrderDetailPage({ params }: Props) { ... }
```

---

## 특수 파일 패턴

### loading.tsx

```typescript
// app/orders/loading.tsx
// Suspense 경계를 자동으로 생성
export default function OrdersLoading() {
  return <div className="skeleton">로딩 중...</div>;
}
```

### error.tsx

```typescript
// app/orders/error.tsx
'use client'; // 에러 컴포넌트는 반드시 Client Component

import { useEffect } from 'react';

interface Props {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function OrdersError({ error, reset }: Props) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div>
      <p>주문을 불러오는 중 오류가 발생했습니다.</p>
      <button onClick={reset}>다시 시도</button>
    </div>
  );
}
```

### layout.tsx

```typescript
// app/dashboard/layout.tsx - 중첩 레이아웃
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div>
      <nav>대시보드 네비게이션</nav>
      <main>{children}</main>
    </div>
  );
}
```

---

## Route Groups

```typescript
// app/(marketing)/about/page.tsx
// URL: /about (그룹명 (marketing)은 URL에 포함되지 않음)

// app/(marketing)/layout.tsx - 마케팅 페이지 전용 레이아웃
export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return <div className="marketing-layout">{children}</div>;
}
```

---

## Parallel Routes

```typescript
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
  analytics,
  team,
}: {
  children: React.ReactNode;
  analytics: React.ReactNode; // @analytics 슬롯
  team: React.ReactNode;      // @team 슬롯
}) {
  return (
    <div>
      {children}
      {analytics}
      {team}
    </div>
  );
}

// app/dashboard/@analytics/page.tsx - analytics 슬롯
export default function AnalyticsPage() {
  return <div>분석 데이터</div>;
}
```

---

## Route Handlers

```typescript
// app/api/orders/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const status = searchParams.get('status');

  const orders = await fetchOrders(status);
  return NextResponse.json(orders);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const order = await createOrder(body);
  return NextResponse.json(order, { status: 201 });
}
```

---

## 데이터 페칭 패턴

```typescript
// ✅ Server Component에서 직접 fetch
export default async function Page() {
  // Next.js가 자동으로 캐싱/중복 제거
  const data = await fetch('https://api.example.com/data', {
    next: { revalidate: 3600 }, // 1시간마다 재검증
  });
  const json = await data.json();
  return <div>{json.title}</div>;
}

// ✅ 병렬 데이터 페칭
export default async function Page() {
  const [orders, users] = await Promise.all([
    fetchOrders(),
    fetchUsers(),
  ]);
  return <Dashboard orders={orders} users={users} />;
}
```

---

## 체크리스트

- [ ] 인터랙션 없는 컴포넌트는 Server Component(기본값) 사용?
- [ ] useState/useEffect 사용 시 'use client' 선언?
- [ ] error.tsx에 'use client' 선언?
- [ ] metadata export로 SEO 설정?
- [ ] loading.tsx로 Suspense UI 제공?
