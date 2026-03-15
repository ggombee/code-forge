---
name: styled-components
description: styled-components 스타일링 규칙. styled() API, ThemeProvider, createGlobalStyle, *.styled.ts 파일 분리.
---

# styled-components 컨벤션

---

## 기본 규칙

- `styled-components`의 `styled()` API로 스타일 컴포넌트를 작성한다
- 간단한 스타일은 컴포넌트 파일 하단에 정의한다
- 복잡하거나 많은 스타일은 `*.styled.ts` 파일로 분리한다
- 직접 색상값(hex, rgb) 대신 theme 토큰을 사용한다

---

## styled() API

```typescript
// ✅ 좋은 예: 기본 HTML 요소 스타일링
import styled from 'styled-components';

const Container = styled.div`
  padding: 16px;
  margin-bottom: 8px;
  border-radius: 8px;
  background-color: ${({ theme }) => theme.colors.surface};
`;

const Title = styled.h2`
  font-size: 1.25rem;
  font-weight: 700;
  color: ${({ theme }) => theme.colors.text.primary};
`;

const Button = styled.button<{ variant?: 'primary' | 'secondary' }>`
  display: inline-flex;
  align-items: center;
  padding: 8px 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;

  background-color: ${({ variant, theme }) =>
    variant === 'secondary' ? theme.colors.secondary : theme.colors.primary};
  color: #ffffff;

  &:hover {
    opacity: 0.9;
  }

  &:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }
`;
```

```typescript
// ✅ 기존 컴포넌트 확장
import { Link } from 'react-router-dom';

const StyledLink = styled(Link)`
  color: ${({ theme }) => theme.colors.primary};
  text-decoration: none;

  &:hover {
    text-decoration: underline;
  }
`;
```

---

## Props를 받는 스타일 컴포넌트

```typescript
interface StatusBadgeProps {
  status: 'active' | 'inactive' | 'pending';
}

const StatusBadge = styled.span<StatusBadgeProps>`
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;

  background-color: ${({ status, theme }) => {
    switch (status) {
      case 'active': return theme.colors.success.light;
      case 'inactive': return theme.colors.error.light;
      case 'pending': return theme.colors.warning.light;
    }
  }};

  color: ${({ status, theme }) => {
    switch (status) {
      case 'active': return theme.colors.success.dark;
      case 'inactive': return theme.colors.error.dark;
      case 'pending': return theme.colors.warning.dark;
    }
  }};
`;
```

---

## 스타일 파일 분리 기준

### 간단한 스타일: 컴포넌트 파일 하단

```typescript
// components/OrderCard/index.tsx
function OrderCard({ order }: { order: Order }) {
  return (
    <Container>
      <Title>{order.name}</Title>
      <StatusBadge status={order.status}>{order.status}</StatusBadge>
    </Container>
  );
}

export default OrderCard;

// 파일 하단에 스타일 정의
const Container = styled.div`
  padding: 16px;
  border: 1px solid ${({ theme }) => theme.colors.border};
  border-radius: 8px;
`;

const Title = styled.h3`
  font-size: 1rem;
  font-weight: 600;
`;
```

### 복잡한 스타일: `*.styled.ts` 파일로 분리

```typescript
// components/OrderTable/styled.ts
import styled from 'styled-components';

export const TableContainer = styled.div`
  width: 100%;
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid ${({ theme }) => theme.colors.border};
`;

export const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
`;

export const TableHeader = styled.thead`
  background-color: ${({ theme }) => theme.colors.surfaceVariant};
`;

export const TableRow = styled.tr<{ isSelected?: boolean }>`
  border-bottom: 1px solid ${({ theme }) => theme.colors.divider};
  background-color: ${({ isSelected, theme }) =>
    isSelected ? theme.colors.primary + '20' : 'transparent'};

  &:hover {
    background-color: ${({ theme }) => theme.colors.surfaceVariant};
  }
`;

export const TableCell = styled.td`
  padding: 12px 16px;
  font-size: 0.875rem;
  color: ${({ theme }) => theme.colors.text.primary};
`;
```

```typescript
// components/OrderTable/index.tsx - named import 사용
import { TableContainer, Table, TableHeader, TableRow, TableCell } from './styled';
```

---

## ThemeProvider & createGlobalStyle

### 테마 정의

```typescript
// styles/theme.ts
export const theme = {
  colors: {
    primary: '#1677ff',
    secondary: '#6b7280',
    surface: '#ffffff',
    surfaceVariant: '#f9fafb',
    border: '#e5e7eb',
    divider: '#f3f4f6',
    text: {
      primary: '#111827',
      secondary: '#6b7280',
      disabled: '#9ca3af',
    },
    success: { light: '#dcfce7', dark: '#166534' },
    error: { light: '#fee2e2', dark: '#991b1b' },
    warning: { light: '#fef9c3', dark: '#854d0e' },
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
  },
  borderRadius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    full: '9999px',
  },
  typography: {
    fontFamily: '"Pretendard", system-ui, sans-serif',
  },
};

export type Theme = typeof theme;
```

### TypeScript 타입 확장

```typescript
// styles/styled.d.ts
import 'styled-components';
import { Theme } from './theme';

declare module 'styled-components' {
  export interface DefaultTheme extends Theme {}
}
```

### GlobalStyle

```typescript
// styles/GlobalStyle.ts
import { createGlobalStyle } from 'styled-components';

export const GlobalStyle = createGlobalStyle`
  *, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  html {
    font-size: 16px;
  }

  body {
    font-family: ${({ theme }) => theme.typography.fontFamily};
    color: ${({ theme }) => theme.colors.text.primary};
    background-color: ${({ theme }) => theme.colors.surface};
    -webkit-font-smoothing: antialiased;
  }

  a {
    color: inherit;
    text-decoration: none;
  }
`;
```

### Provider 설정

```typescript
// src/main.tsx
import { ThemeProvider } from 'styled-components';
import { GlobalStyle } from '@/styles/GlobalStyle';
import { theme } from '@/styles/theme';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <GlobalStyle />
      <AppRoutes />
    </ThemeProvider>
  );
}
```

---

## css 헬퍼 (재사용 스타일)

```typescript
import styled, { css } from 'styled-components';

// ✅ 재사용 가능한 스타일 조각
const flexCenter = css`
  display: flex;
  align-items: center;
  justify-content: center;
`;

const truncate = css`
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

// 사용
const CenteredBox = styled.div`
  ${flexCenter}
  padding: 16px;
`;

const EllipsisText = styled.p`
  ${truncate}
  max-width: 200px;
`;
```

---

## 체크리스트

- [ ] 간단한 스타일은 컴포넌트 하단, 복잡한 스타일은 `*.styled.ts` 분리?
- [ ] `ThemeProvider`로 theme 전역 제공?
- [ ] `styled.d.ts`로 DefaultTheme 타입 확장?
- [ ] `GlobalStyle`로 전역 스타일 초기화?
- [ ] theme 토큰으로 색상/간격 참조?
- [ ] Props를 받는 styled 컴포넌트는 타입 파라미터 지정?
