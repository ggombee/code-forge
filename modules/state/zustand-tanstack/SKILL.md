---
name: zustand-tanstack
description: Zustand + TanStack Query 상태 관리 패턴. store 생성, devtools, 서버 상태 연동, 디렉토리 구조.
---

# Zustand + TanStack Query 상태 관리 컨벤션

---

## 상태 분리 원칙

| 상태 유형 | 도구 | 예시 |
|-----------|------|------|
| 서버 상태 | TanStack Query | 주문 목록, 사용자 정보 |
| 전역 클라이언트 상태 | Zustand | 선택된 탭, 사이드바 열림 여부 |
| 폼 상태 | React Hook Form | 입력값, 유효성 검사 |
| 로컬 UI 상태 | useState | 모달 열림/닫힘 |

---

## 디렉토리 구조

```
store/
├── useAuthStore.ts       # 인증 상태
├── useUIStore.ts         # UI 전역 상태
└── useFilterStore.ts     # 필터/검색 상태

queries/
├── order/
│   ├── index.ts          # useOrderQuery, useOrderMutation
│   └── queryKeys.ts      # 쿼리 키 팩토리
└── user/
    ├── index.ts
    └── queryKeys.ts
```

---

## Zustand Store 생성

### 기본 패턴

```typescript
// store/useAuthStore.ts
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface User {
  id: string;
  name: string;
  email: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  // Actions
  login: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set) => ({
        user: null,
        isAuthenticated: false,
        login: (user) => set({ user, isAuthenticated: true }, false, 'login'),
        logout: () => set({ user: null, isAuthenticated: false }, false, 'logout'),
      }),
      {
        name: 'auth-storage', // localStorage key
        partialize: (state) => ({ user: state.user }), // 저장할 필드만 선택
      },
    ),
    { name: 'AuthStore' }, // DevTools 이름
  ),
);
```

### UI 상태 store

```typescript
// store/useUIStore.ts
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

interface UIState {
  isSidebarOpen: boolean;
  activeTab: string;
  // Actions
  toggleSidebar: () => void;
  setActiveTab: (tab: string) => void;
}

export const useUIStore = create<UIState>()(
  devtools(
    (set) => ({
      isSidebarOpen: true,
      activeTab: 'overview',
      toggleSidebar: () =>
        set((state) => ({ isSidebarOpen: !state.isSidebarOpen }), false, 'toggleSidebar'),
      setActiveTab: (tab) =>
        set({ activeTab: tab }, false, 'setActiveTab'),
    }),
    { name: 'UIStore' },
  ),
);
```

---

## Zustand 사용 패턴

```typescript
// ✅ 좋은 예: selector로 필요한 상태만 구독
function Header() {
  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);

  return <div>{user?.name} <button onClick={logout}>로그아웃</button></div>;
}

// ❌ 나쁜 예: 전체 state 구독 (불필요한 리렌더링 발생)
function Header() {
  const { user, logout } = useAuthStore();
}
```

```typescript
// ✅ 여러 값을 한번에 구독할 때 (shallow 비교)
import { useShallow } from 'zustand/react/shallow';

function FilterPanel() {
  const { status, dateRange, setStatus } = useFilterStore(
    useShallow((state) => ({
      status: state.status,
      dateRange: state.dateRange,
      setStatus: state.setStatus,
    })),
  );
}
```

---

## TanStack Query 연동

### 쿼리 키 팩토리

```typescript
// queries/order/queryKeys.ts
export const orderKeys = {
  all: ['orders'] as const,
  lists: () => [...orderKeys.all, 'list'] as const,
  list: (filters: OrderFilters) => [...orderKeys.lists(), filters] as const,
  details: () => [...orderKeys.all, 'detail'] as const,
  detail: (id: string) => [...orderKeys.details(), id] as const,
};
```

### 쿼리/뮤테이션 훅

```typescript
// queries/order/index.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { orderKeys } from './queryKeys';
import { fetchOrders, fetchOrder, createOrder, updateOrder } from '@/services/order';

export function useOrderListQuery(filters: OrderFilters) {
  return useQuery({
    queryKey: orderKeys.list(filters),
    queryFn: () => fetchOrders(filters),
    staleTime: 5 * 60 * 1000, // 5분
  });
}

export function useOrderDetailQuery(id: string) {
  return useQuery({
    queryKey: orderKeys.detail(id),
    queryFn: () => fetchOrder(id),
    enabled: !!id, // id가 있을 때만 실행
  });
}

export function useCreateOrderMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createOrder,
    onSuccess: () => {
      // 목록 캐시 무효화
      queryClient.invalidateQueries({ queryKey: orderKeys.lists() });
    },
  });
}
```

---

## Zustand + TanStack Query 연동

```typescript
// Zustand 필터 상태 + TanStack Query 서버 상태 조합
function OrderListPage() {
  // 클라이언트 상태 (Zustand)
  const filters = useFilterStore(useShallow((s) => ({
    status: s.status,
    dateRange: s.dateRange,
  })));

  // 서버 상태 (TanStack Query)
  const { data, isLoading } = useOrderListQuery(filters);

  return <OrderList orders={data?.orders} loading={isLoading} />;
}
```

---

## QueryClient 설정

```typescript
// src/main.tsx 또는 providers/QueryProvider.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1분
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

---

## 체크리스트

- [ ] 서버 상태는 TanStack Query, 클라이언트 상태는 Zustand 사용?
- [ ] store에 `devtools` 미들웨어 적용?
- [ ] selector로 필요한 상태만 구독?
- [ ] 여러 값 구독 시 `useShallow` 사용?
- [ ] 쿼리 키는 `queryKeys` 팩토리로 관리?
- [ ] mutation 후 관련 쿼리 `invalidateQueries` 처리?
