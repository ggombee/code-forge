---
globs:
  - "**/*.{ts,tsx,js,jsx}"
alwaysApply: false
---

# React & Next.js 컨벤션

> 프로젝트의 React/Next.js 코딩 규칙

---

## Import 순서

아래 순서를 반드시 지킨다. ESLint 규칙으로도 강제된다.

```typescript
// 1. 외부 라이브러리
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';

// 2. 내부 모듈 (@/ alias)
import { Button } from '@/components/Button';
import { useOrderQuery } from '@/queries/order';

// 3. 상대 경로 (현재 모듈 내부)
import { OrderHeader } from './components/OrderHeader';
import { formatPrice } from '../utils/format';
```

---

## 컴포넌트 작성 규칙

### 함수 선언 방식

- 페이지 컴포넌트: 프로젝트 컨벤션에 따름
- 일반 컴포넌트: `const ComponentName = () => {}` 또는 `function ComponentName() {}`

### Props 타입 정의

컴포넌트와 동일 파일에 정의한다. 별도 types 파일 분리는 복잡한 경우에만.

```typescript
// 좋은 예
interface OrderCardProps {
  order: Order;
  onSelect: (id: string) => void;
}

const OrderCard = ({ order, onSelect }: OrderCardProps) => { ... };
```

---

## 스타일링

### 프로젝트 감지 기준

- `tailwindcss`가 package.json에 있으면 → Tailwind CSS 사용
- `@emotion`이 package.json에 있으면 → Emotion (CSS-in-JS) 사용
- 둘 다 없으면 → 기존 코드의 스타일링 패턴을 따름

### 기본 규칙

- 프로젝트 스타일링 도구(Tailwind 또는 CSS-in-JS) 사용
- 전역 스타일은 공유 패키지에만 정의
- 디자인 시스템 컴포넌트를 우선 사용

### 스타일 컴포넌트 위치

- 간단한 스타일: 컴포넌트 파일 하단에 정의
- 복잡한 스타일: `styled.ts` 파일로 분리

```typescript
// 좋은 예: 컴포넌트 파일 하단
const Container = styled.div`
  padding: 16px;
`;

// 복잡한 경우: 별도 파일 (styled.ts)
// components/OrderCard/styled.ts
export const Container = styled.div`...`;
export const Header = styled.div`...`;

// 사용 (index.tsx) - named import 사용
import { Container, Header } from './styled';
```

---

## 디자인 시스템 사용 규칙

### 필수: 디자인 시스템 컴포넌트 우선 사용

새 UI를 만들기 전에 반드시 디자인 시스템 컴포넌트 존재 여부를 확인한다.

### 디자인 시스템 래핑 패턴

디자인 시스템 컴포넌트를 확장해야 할 때는 styled로 래핑한다:

```typescript
// ✅ 좋은 예: 디자인 시스템 컴포넌트 래핑
import { Table } from '@/components/Table';

const StyledTable = styled(Table)`
  margin-top: 16px;
`;

// ❌ 나쁜 예: 디자인 시스템 있는데 직접 구현
const CustomTable = styled.table`
  border-collapse: collapse;
`;
```

### 색상/스타일 상수 사용

직접 색상값을 쓰지 않고 디자인 시스템 상수를 사용한다:

```typescript
// ✅ 좋은 예
import { semanticColor } from '@/styles/semanticColor';

const StyledButton = styled.button`
  color: ${semanticColor.text.primary};
`;

// ❌ 나쁜 예
const StyledButton = styled.button`
  color: #333333;
`;
```

---

## 기존 코드 패턴 참조 규칙

### 필수: 유사 구현 탐색

새로운 기능을 구현하기 전에 반드시 기존 코드에서 유사 패턴을 찾는다:

```bash
# 유사 컴포넌트 검색
rg "FilterDropdown|DropSelect" src/ --type tsx

# 유사 훅 검색
rg "useFilter|useSearch" src/ --type tsx

# 유사 타입 검색
rg "FilterState|SearchParams" src/ --type ts
```

### 타입 재사용

기존에 정의된 타입이 있으면 재사용한다:

```typescript
// ✅ 좋은 예: 기존 타입 재사용
import { OrderStatus, OrderItem } from '@/types/order';

// ❌ 나쁜 예: 중복 타입 정의
interface MyOrderStatus {
  code: string;
  label: string;
}
```

### 패턴 참조 체크리스트

새 코드 작성 전:
- 디자인 시스템에 해당 컴포넌트가 있는가?
- 유사한 컴포넌트/훅이 기존에 있는가?
- 재사용 가능한 타입이 있는가?
- 색상/스타일 상수가 정의되어 있는가?

---

## 금지/권장 예시

### 예시 1: 페이지 컴포넌트 구조

```typescript
// ❌ 나쁜 예: 페이지에 로직이 모두 포함됨
const OrderPage = () => {
  const { orderId } = useRouter().query;
  const { data } = useQuery(...);
  const [state, setState] = useState(...);
  return (
    <div>
      {/* 수백 줄의 JSX */}
    </div>
  );
};
```

```typescript
// ✅ 좋은 예: 페이지는 얇게, 로직은 분리
const OrderPage = () => {
  return <OrderContainer />;
};
```

### 예시 2: Import 순서

```typescript
// ❌ 나쁜 예: 순서가 뒤섞임
import { OrderHeader } from './OrderHeader';
import { useState } from 'react';
import { Button } from '@/components/Button';
import axios from 'axios';
```

```typescript
// ✅ 좋은 예: 외부 → 내부(@/) → 상대경로
import { useState } from 'react';
import axios from 'axios';

import { Button } from '@/components/Button';

import { OrderHeader } from './OrderHeader';
```

### 예시 3: 컴포넌트 Props 처리

```typescript
// ❌ 나쁜 예: any 사용, 타입 정의 없음
const OrderCard = (props: any) => {
  return <div>{props.data.title}</div>;
};
```

```typescript
// ✅ 좋은 예: 명시적 타입 정의
interface OrderCardProps {
  order: Order;
  isSelected?: boolean;
}

const OrderCard = ({ order, isSelected = false }: OrderCardProps) => {
  return (
    <Container $isSelected={isSelected}>
      {order.title}
    </Container>
  );
};
```

### 예시 4: API 호출

```typescript
// ❌ 나쁜 예: 프론트엔드에서 직접 외부 API 호출
const data = await axios.get('https://api.example.com/orders');
```

```typescript
// ✅ 좋은 예: 프로젝트 api 래퍼 사용
const data = await api.get('/api/orders');
```

---

## 파일 명명 규칙

| 유형     | 규칙                   | 예시                            |
| -------- | ---------------------- | ------------------------------- |
| 페이지   | kebab-case 또는 [param] | `order-list.tsx`, `[orderId].tsx` |
| 컴포넌트 | PascalCase             | `OrderCard.tsx`                 |
| 훅       | camelCase, use 접두사  | `useOrderStatus.ts`             |
| 유틸리티 | camelCase              | `formatDate.ts`                 |
| 타입     | PascalCase             | `order.types.ts`                |
| 스타일   | styled                 | `styled.ts`                     |

---

## Portal 사용

오버레이 UI는 반드시 지정된 Portal을 사용한다.
새로운 Portal을 임의로 추가하지 않는다.
