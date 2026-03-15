---
name: mui
description: MUI(Material UI) 컴포넌트 라이브러리 사용 규칙. import 패턴, sx prop, styled(), ThemeProvider.
---

# MUI (Material UI) 컨벤션

---

## Import 패턴

```typescript
// ✅ 좋은 예: 트리 쉐이킹이 가능한 named import
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import Box from '@mui/material/Box';

// ✅ 아이콘 import
import SearchIcon from '@mui/icons-material/Search';
import CloseIcon from '@mui/icons-material/Close';

// ❌ 나쁜 예: 배럴 import (번들 크기 증가 가능)
import { Button, TextField, Box } from '@mui/material';
```

---

## sx prop 사용

`sx` prop은 MUI 컴포넌트에 인라인 스타일을 적용하는 방법이다.

```typescript
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

// ✅ 간단한 스타일: sx prop 사용
function OrderCard() {
  return (
    <Box
      sx={{
        padding: 2,           // theme.spacing(2) = 16px
        marginBottom: 1,
        backgroundColor: 'background.paper',
        borderRadius: 1,
        boxShadow: 1,
        '&:hover': {
          boxShadow: 3,
        },
      }}
    >
      <Typography
        variant="h6"
        sx={{
          color: 'text.primary',
          fontWeight: 'bold',
        }}
      >
        주문 제목
      </Typography>
    </Box>
  );
}
```

```typescript
// 반응형 스타일 (breakpoints)
<Box
  sx={{
    width: {
      xs: '100%',   // mobile
      sm: '50%',    // tablet
      md: '33%',    // desktop
    },
    fontSize: { xs: 14, md: 16 },
  }}
/>
```

---

## styled() API

복잡한 스타일이나 재사용 컴포넌트에는 `styled()`를 사용한다.

```typescript
import { styled } from '@mui/material/styles';
import Button from '@mui/material/Button';
import Box from '@mui/material/Box';

// ✅ styled()로 커스텀 컴포넌트 생성
const StyledButton = styled(Button)(({ theme }) => ({
  borderRadius: theme.spacing(3),
  padding: theme.spacing(1, 3),
  textTransform: 'none',
  '&:hover': {
    backgroundColor: theme.palette.primary.dark,
  },
}));

const CardContainer = styled(Box)(({ theme }) => ({
  padding: theme.spacing(2),
  borderRadius: theme.shape.borderRadius,
  backgroundColor: theme.palette.background.paper,
  [theme.breakpoints.down('sm')]: {
    padding: theme.spacing(1),
  },
}));
```

```typescript
// Props를 받는 styled 컴포넌트
interface StatusBadgeProps {
  status: 'active' | 'inactive' | 'pending';
}

const StatusBadge = styled(Box, {
  shouldForwardProp: (prop) => prop !== 'status', // DOM에 전달하지 않을 prop
})<StatusBadgeProps>(({ theme, status }) => ({
  display: 'inline-flex',
  borderRadius: theme.spacing(1),
  padding: theme.spacing(0.5, 1),
  backgroundColor:
    status === 'active' ? theme.palette.success.light
    : status === 'inactive' ? theme.palette.error.light
    : theme.palette.warning.light,
}));
```

---

## ThemeProvider & createTheme

```typescript
// src/theme/index.ts
import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Pretendard", "Roboto", sans-serif',
    h1: {
      fontSize: '2rem',
      fontWeight: 700,
    },
  },
  shape: {
    borderRadius: 8,
  },
  spacing: 8, // 기본 spacing 단위 (px)
});
```

```typescript
// src/main.tsx
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { theme } from '@/theme';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline /> {/* 브라우저 기본 스타일 초기화 */}
      <AppRoutes />
    </ThemeProvider>
  );
}
```

---

## 주요 컴포넌트 패턴

### Grid 레이아웃

```typescript
import Grid from '@mui/material/Grid';

function OrderList() {
  return (
    <Grid container spacing={2}>
      {orders.map((order) => (
        <Grid item xs={12} sm={6} md={4} key={order.id}>
          <OrderCard order={order} />
        </Grid>
      ))}
    </Grid>
  );
}
```

### Form 패턴

```typescript
import TextField from '@mui/material/TextField';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';

function OrderForm() {
  return (
    <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <TextField
        label="주문명"
        variant="outlined"
        required
        error={!!errors.name}
        helperText={errors.name?.message}
        {...register('name')}
      />
      <FormControl fullWidth>
        <InputLabel>상태</InputLabel>
        <Select label="상태" value={status} onChange={handleChange}>
          <MenuItem value="pending">대기중</MenuItem>
          <MenuItem value="active">진행중</MenuItem>
        </Select>
      </FormControl>
    </Box>
  );
}
```

---

## useTheme 훅

```typescript
import { useTheme } from '@mui/material/styles';
import useMediaQuery from '@mui/material/useMediaQuery';

function ResponsiveComponent() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <div style={{ padding: isMobile ? theme.spacing(1) : theme.spacing(3) }}>
      {isMobile ? '모바일 뷰' : '데스크탑 뷰'}
    </div>
  );
}
```

---

## 체크리스트

- [ ] 컴포넌트 import는 개별 경로 사용? (`@mui/material/Button`)
- [ ] 간단한 스타일은 `sx` prop 사용?
- [ ] 재사용 컴포넌트는 `styled()` 사용?
- [ ] `ThemeProvider`로 theme 전역 제공?
- [ ] `CssBaseline` 포함?
- [ ] Props를 DOM에 전달하지 않으려면 `shouldForwardProp` 사용?
