---
name: vitest
description: Vitest 테스트 환경 설정 및 사용 규칙. vitest.config.ts, vi.* API, *.test.ts 파일 구조.
---

# Vitest 컨벤션

---

## vitest.config.ts 설정

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,           // describe, it, expect를 전역으로 사용
    environment: 'jsdom',    // 브라우저 환경 시뮬레이션
    setupFiles: ['./src/test/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: [
        'node_modules/**',
        'src/test/**',
        '**/*.config.ts',
        '**/*.d.ts',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

```typescript
// src/test/setup.ts
import '@testing-library/jest-dom';
// 전역 mock 설정 등
```

---

## 파일 구조

```
src/
├── utils/
│   ├── formatPrice.ts
│   └── __tests__/
│       └── formatPrice.test.ts
├── hooks/
│   ├── useOrderStatus.ts
│   └── __tests__/
│       └── useOrderStatus.test.ts
└── components/
    ├── OrderCard.tsx
    └── __tests__/
        └── OrderCard.test.tsx
```

---

## 기본 테스트 구조

```typescript
// utils/__tests__/formatPrice.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { formatPrice, formatPriceWithUnit } from '../formatPrice';

describe('formatPrice', () => {
  describe('정상 케이스', () => {
    it('양수 금액을 천 단위 쉼표로 포맷', () => {
      expect(formatPrice(10000)).toBe('10,000');
    });

    it('소수점 금액 처리', () => {
      expect(formatPrice(9999.99)).toBe('9,999.99');
    });
  });

  describe('경계값', () => {
    it('0원 처리', () => {
      expect(formatPrice(0)).toBe('0');
    });

    it('1원 처리', () => {
      expect(formatPrice(1)).toBe('1');
    });
  });

  describe('에러 케이스', () => {
    it('음수 처리', () => {
      expect(() => formatPrice(-1000)).toThrow();
    });

    it('NaN 처리', () => {
      expect(formatPrice(NaN)).toBe('0');
    });
  });
});
```

---

## vi.* API

### vi.fn() - Mock 함수

```typescript
import { vi, describe, it, expect } from 'vitest';

describe('useOrderActions', () => {
  it('주문 삭제 시 onSuccess 콜백 호출', async () => {
    const onSuccess = vi.fn();
    const onError = vi.fn();

    await deleteOrder('order-1', { onSuccess, onError });

    expect(onSuccess).toHaveBeenCalledOnce();
    expect(onSuccess).toHaveBeenCalledWith({ id: 'order-1' });
    expect(onError).not.toHaveBeenCalled();
  });
});
```

### vi.mock() - 모듈 모킹

```typescript
import { vi, describe, it, expect, beforeEach } from 'vitest';

// 모듈 전체 모킹
vi.mock('@/services/order', () => ({
  fetchOrders: vi.fn(),
  createOrder: vi.fn(),
}));

// 모킹된 함수 import
import { fetchOrders } from '@/services/order';

describe('OrderService', () => {
  beforeEach(() => {
    vi.clearAllMocks(); // 각 테스트 전 mock 초기화
  });

  it('주문 목록 조회 성공', async () => {
    const mockOrders = [{ id: '1', name: '주문 1' }];
    vi.mocked(fetchOrders).mockResolvedValue({ orders: mockOrders, total: 1 });

    const result = await getOrderList();

    expect(fetchOrders).toHaveBeenCalledOnce();
    expect(result.orders).toHaveLength(1);
  });

  it('조회 실패 시 에러 처리', async () => {
    vi.mocked(fetchOrders).mockRejectedValue(new Error('Network error'));

    await expect(getOrderList()).rejects.toThrow('Network error');
  });
});
```

### vi.spyOn() - 스파이

```typescript
import { vi } from 'vitest';

describe('logger', () => {
  it('오류 발생 시 console.error 호출', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    triggerError();

    expect(consoleSpy).toHaveBeenCalledWith('Error occurred');
    consoleSpy.mockRestore(); // 원래 구현 복원
  });
});
```

### vi.useFakeTimers() - 시간 제어

```typescript
import { vi, describe, it, expect, beforeAll, afterAll } from 'vitest';
import { getPeriod } from '../getPeriod';

describe('getPeriod', () => {
  beforeAll(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2025-01-15T00:00:00.000Z'));
  });

  afterAll(() => {
    vi.useRealTimers();
  });

  it('last14Days - 오늘 기준 14일 전부터 오늘까지', () => {
    expect(getPeriod('last14Days')).toEqual(['2025-01-01', '2025-01-15']);
  });

  it('thisMonth - 해당 월 1일부터 말일까지', () => {
    expect(getPeriod('thisMonth')).toEqual(['2025-01-01', '2025-01-31']);
  });
});
```

### vi.stubEnv() - 환경 변수

```typescript
import { vi } from 'vitest';

describe('config', () => {
  it('프로덕션 환경 설정', () => {
    vi.stubEnv('VITE_ENV', 'production');
    vi.stubEnv('VITE_API_URL', 'https://api.example.com');

    const config = getConfig();

    expect(config.isProd).toBe(true);
    expect(config.apiUrl).toBe('https://api.example.com');

    vi.unstubAllEnvs(); // 테스트 후 복원
  });
});
```

---

## React Testing Library 연동

```typescript
// components/__tests__/OrderCard.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { OrderCard } from '../OrderCard';

const mockOrder = {
  id: '1',
  name: '테스트 주문',
  status: 'active' as const,
};

describe('OrderCard', () => {
  it('주문명 렌더링', () => {
    render(<OrderCard order={mockOrder} onSelect={vi.fn()} />);
    expect(screen.getByText('테스트 주문')).toBeInTheDocument();
  });

  it('클릭 시 onSelect 호출', () => {
    const onSelect = vi.fn();
    render(<OrderCard order={mockOrder} onSelect={onSelect} />);

    fireEvent.click(screen.getByRole('button'));

    expect(onSelect).toHaveBeenCalledWith('1');
  });
});
```

---

## 커스텀 훅 테스트

```typescript
// hooks/__tests__/useCounter.test.ts
import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useCounter } from '../useCounter';

describe('useCounter', () => {
  it('초기값 반환', () => {
    const { result } = renderHook(() => useCounter(0));
    expect(result.current.count).toBe(0);
  });

  it('increment 호출 시 카운트 증가', () => {
    const { result } = renderHook(() => useCounter(0));

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);
  });
});
```

---

## 테스트 실행

```bash
# 전체 테스트
yarn test

# watch 모드
yarn test --watch

# 특정 파일
yarn test formatPrice.test.ts

# 커버리지
yarn test --coverage

# UI 모드
yarn test --ui
```

---

## 체크리스트

- [ ] `vitest.config.ts`에 `globals: true`, `environment: 'jsdom'` 설정?
- [ ] 날짜 의존 함수는 `vi.useFakeTimers()` + `vi.setSystemTime()` 사용?
- [ ] 각 테스트 후 `vi.clearAllMocks()` 또는 `vi.restoreAllMocks()` 사용?
- [ ] 모킹된 모듈은 `vi.mocked()` 로 타입 안전하게 접근?
- [ ] `describe` 중첩으로 시나리오 그룹화?
- [ ] 정상/경계값/에러 케이스 모두 커버?
