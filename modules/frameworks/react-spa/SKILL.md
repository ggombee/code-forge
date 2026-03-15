---
name: react-spa
description: React SPA (Vite/CRA) 프로젝트 컨벤션. react-router-dom v6 라우팅, 빌드/개발 설정.
---

# React SPA 컨벤션

이 프로젝트는 **Vite** 또는 **CRA(Create React App)** 기반의 React SPA다.

---

## 프로젝트 구조

```
src/
├── main.tsx            # 진입점
├── App.tsx             # 루트 컴포넌트
├── routes/             # 라우트 정의
│   └── index.tsx
├── pages/              # 페이지 컴포넌트
│   ├── HomePage.tsx
│   └── OrderPage.tsx
├── components/         # 공유 컴포넌트
├── hooks/              # 커스텀 훅
├── services/           # API 서비스
├── store/              # 상태 관리
├── types/              # TypeScript 타입
└── utils/              # 유틸리티 함수
```

---

## Vite 설정

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL,
        changeOrigin: true,
      },
    },
  },
});
```

---

## 진입점

```typescript
// src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './index.css';

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
```

---

## react-router-dom v6 라우팅

### 기본 라우트 설정

```typescript
// src/routes/index.tsx
import { Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';

// 코드 스플리팅
const HomePage = lazy(() => import('@/pages/HomePage'));
const OrderPage = lazy(() => import('@/pages/OrderPage'));
const OrderDetailPage = lazy(() => import('@/pages/OrderDetailPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));

export function AppRoutes() {
  return (
    <Suspense fallback={<div>로딩 중...</div>}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/orders" element={<OrderPage />} />
        <Route path="/orders/:orderId" element={<OrderDetailPage />} />
        <Route path="/404" element={<NotFoundPage />} />
        <Route path="*" element={<Navigate to="/404" replace />} />
      </Routes>
    </Suspense>
  );
}
```

### 중첩 라우트

```typescript
// src/routes/index.tsx
import { Outlet } from 'react-router-dom';

function DashboardLayout() {
  return (
    <div>
      <nav>대시보드 메뉴</nav>
      <Outlet /> {/* 자식 라우트가 렌더링되는 위치 */}
    </div>
  );
}

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/dashboard" element={<DashboardLayout />}>
        <Route index element={<DashboardHome />} />       {/* /dashboard */}
        <Route path="orders" element={<DashboardOrders />} /> {/* /dashboard/orders */}
        <Route path="settings" element={<DashboardSettings />} /> {/* /dashboard/settings */}
      </Route>
    </Routes>
  );
}
```

### 보호된 라우트

```typescript
// src/routes/ProtectedRoute.tsx
import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '@/store/auth';

export function ProtectedRoute() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
```

### 라우트 훅 사용

```typescript
import { useNavigate, useParams, useSearchParams, useLocation } from 'react-router-dom';

function OrderDetailPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();

  const handleBack = () => navigate(-1);
  const handleGoToOrders = () => navigate('/orders');

  // 쿼리 파라미터
  const page = searchParams.get('page') ?? '1';

  return <div>주문 #{orderId}</div>;
}
```

---

## 환경 변수 (Vite)

```typescript
// .env.local
VITE_API_URL=http://localhost:8080
VITE_ENV=development

// 코드에서 사용
const apiUrl = import.meta.env.VITE_API_URL;
const isDev = import.meta.env.DEV; // Vite 내장 변수
```

```typescript
// ❌ process.env는 Vite에서 동작하지 않음
const url = process.env.REACT_APP_API_URL; // CRA 방식

// ✅ Vite 방식
const url = import.meta.env.VITE_API_URL;
```

---

## 빌드 설정

```json
// package.json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext ts,tsx",
    "test": "vitest"
  }
}
```

---

## App.tsx 구조

```typescript
// src/App.tsx
import { AppRoutes } from '@/routes';

function App() {
  return <AppRoutes />;
}

export default App;
```

---

## 체크리스트

- [ ] 코드 스플리팅에 `lazy()` + `Suspense` 사용?
- [ ] 환경 변수는 `VITE_` 접두사 사용 (Vite)?
- [ ] 중첩 라우트에 `Outlet` 사용?
- [ ] 보호된 라우트에 `ProtectedRoute` 래퍼 사용?
- [ ] 존재하지 않는 경로는 404 페이지로 리다이렉트?
