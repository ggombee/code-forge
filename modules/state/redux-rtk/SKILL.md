---
name: redux-rtk
description: Redux Toolkit(RTK) 상태 관리 패턴. createSlice, configureStore, RTK Query(createApi), slices 디렉토리 구조.
---

# Redux Toolkit (RTK) 컨벤션

---

## 디렉토리 구조

```
store/
├── index.ts              # configureStore, RootState, AppDispatch
├── slices/
│   ├── authSlice.ts      # 인증 상태
│   ├── uiSlice.ts        # UI 전역 상태
│   └── filterSlice.ts    # 필터 상태
└── api/
    ├── orderApi.ts       # RTK Query API 슬라이스
    └── userApi.ts
```

---

## configureStore

```typescript
// store/index.ts
import { configureStore } from '@reduxjs/toolkit';
import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';
import authReducer from './slices/authSlice';
import uiReducer from './slices/uiSlice';
import { orderApi } from './api/orderApi';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    ui: uiReducer,
    [orderApi.reducerPath]: orderApi.reducer, // RTK Query
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(orderApi.middleware), // RTK Query 미들웨어
});

// TypeScript 타입 추출
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// 타입이 적용된 훅 (컴포넌트에서 사용)
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
```

---

## createSlice

```typescript
// store/slices/authSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface User {
  id: string;
  name: string;
  email: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  token: string | null;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  token: null,
};

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    login: (state, action: PayloadAction<{ user: User; token: string }>) => {
      state.user = action.payload.user;
      state.token = action.payload.token;
      state.isAuthenticated = true;
    },
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
    },
    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload };
      }
    },
  },
});

export const { login, logout, updateUser } = authSlice.actions;
export default authSlice.reducer;

// Selectors
export const selectUser = (state: RootState) => state.auth.user;
export const selectIsAuthenticated = (state: RootState) => state.auth.isAuthenticated;
```

```typescript
// store/slices/uiSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface UIState {
  isSidebarOpen: boolean;
  activeTab: string;
  theme: 'light' | 'dark';
}

const initialState: UIState = {
  isSidebarOpen: true,
  activeTab: 'overview',
  theme: 'light',
};

export const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.isSidebarOpen = !state.isSidebarOpen;
    },
    setActiveTab: (state, action: PayloadAction<string>) => {
      state.activeTab = action.payload;
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
    },
  },
});

export const { toggleSidebar, setActiveTab, setTheme } = uiSlice.actions;
export default uiSlice.reducer;
```

---

## RTK Query (createApi)

```typescript
// store/api/orderApi.ts
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../index';

interface Order {
  id: string;
  name: string;
  status: string;
}

interface OrderFilters {
  status?: string;
  page?: number;
}

export const orderApi = createApi({
  reducerPath: 'orderApi',
  baseQuery: fetchBaseQuery({
    baseUrl: '/api',
    prepareHeaders: (headers, { getState }) => {
      // 인증 토큰 자동 첨부
      const token = (getState() as RootState).auth.token;
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['Order'], // 캐시 무효화 태그
  endpoints: (builder) => ({
    getOrders: builder.query<{ orders: Order[]; total: number }, OrderFilters>({
      query: (filters) => ({
        url: '/orders',
        params: filters,
      }),
      providesTags: ['Order'],
    }),
    getOrder: builder.query<Order, string>({
      query: (id) => `/orders/${id}`,
      providesTags: (result, error, id) => [{ type: 'Order', id }],
    }),
    createOrder: builder.mutation<Order, Omit<Order, 'id'>>({
      query: (body) => ({
        url: '/orders',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Order'], // 생성 후 목록 캐시 무효화
    }),
    updateOrder: builder.mutation<Order, Partial<Order> & { id: string }>({
      query: ({ id, ...body }) => ({
        url: `/orders/${id}`,
        method: 'PATCH',
        body,
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Order', id }],
    }),
    deleteOrder: builder.mutation<void, string>({
      query: (id) => ({
        url: `/orders/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['Order'],
    }),
  }),
});

// 자동 생성된 훅 export
export const {
  useGetOrdersQuery,
  useGetOrderQuery,
  useCreateOrderMutation,
  useUpdateOrderMutation,
  useDeleteOrderMutation,
} = orderApi;
```

---

## 컴포넌트에서 사용

```typescript
// ✅ 좋은 예: 타입 적용된 훅 사용
import { useAppDispatch, useAppSelector } from '@/store';
import { login, logout, selectUser } from '@/store/slices/authSlice';
import { useGetOrdersQuery, useCreateOrderMutation } from '@/store/api/orderApi';

function OrderListPage() {
  const user = useAppSelector(selectUser);
  const dispatch = useAppDispatch();

  const { data, isLoading, error } = useGetOrdersQuery({ status: 'active' });
  const [createOrder, { isLoading: isCreating }] = useCreateOrderMutation();

  const handleCreate = async (orderData: NewOrder) => {
    try {
      await createOrder(orderData).unwrap(); // unwrap으로 에러 처리
    } catch (err) {
      console.error('생성 실패:', err);
    }
  };

  return (
    <div>
      <p>사용자: {user?.name}</p>
      {isLoading && <div>로딩 중...</div>}
      {error && <div>오류 발생</div>}
      {data?.orders.map((order) => (
        <OrderCard key={order.id} order={order} />
      ))}
    </div>
  );
}
```

---

## Provider 설정

```typescript
// src/main.tsx
import { Provider } from 'react-redux';
import { store } from '@/store';

function Root() {
  return (
    <Provider store={store}>
      <App />
    </Provider>
  );
}
```

---

## 체크리스트

- [ ] `useAppDispatch`, `useAppSelector` 사용 (기본 훅 대신)?
- [ ] `createSlice`로 reducer + actions 함께 정의?
- [ ] RTK Query API에 `tagTypes` 설정?
- [ ] mutation 후 `invalidatesTags`로 캐시 무효화?
- [ ] RTK Query 미들웨어 `configureStore`에 추가?
- [ ] selector 함수를 slice 파일에 함께 정의?
