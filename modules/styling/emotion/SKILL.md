---
name: emotion
description: Emotion 스타일링 규칙. @emotion/styled, css prop 사용, 스타일 파일 분리 기준.
---

# Emotion 스타일링 규칙

---

## 기본 규칙

- `@emotion/styled` 또는 `css` prop을 사용한다
- 전역 스타일은 `packages/shared/styles/globalStyles`에만 정의한다

---

## 스타일 컴포넌트 위치 기준

### 간단한 스타일: 컴포넌트 파일 하단

```typescript
// components/OrderCard/index.tsx
const OrderCard = () => {
  return <Container>...</Container>;
};

export default OrderCard;

// 파일 하단에 스타일 정의
const Container = styled.div`
  padding: 16px;
`;
```

### 복잡한 스타일: `*.styled.ts` 파일로 분리

```typescript
// components/OrderCard/styled.ts
export const Container = styled.div`...`;
export const Header = styled.div`...`;
export const Footer = styled.div`...`;

// components/OrderCard/index.tsx - named import 사용
import { Container, Header, Footer } from './styled';
```

---

## 색상 토큰 사용

직접 색상값을 쓰지 않고 semanticColor 토큰을 사용한다:

```typescript
// ✅ 좋은 예
import { semanticColor } from '@repo/shared/styles/foundation/semanticColor';

const StyledDiv = styled.div`
  color: ${semanticColor.text.primary};
  background: ${semanticColor.bg.surface};
`;

// ❌ 나쁜 예
const StyledDiv = styled.div`
  color: #333333;
  background: #ffffff;
`;
```

---

## 파일 명명 규칙

| 유형           | 규칙                    | 예시                       |
| -------------- | ----------------------- | -------------------------- |
| 스타일 파일    | 컴포넌트명.styles       | `OrderCard.styles.ts`      |
| 분리된 스타일  | styled.ts 또는 styled.tsx | `styled.ts`              |

---

## 체크리스트

스타일 작성 전:

- [ ] 스타일 양이 간단한가? → 컴포넌트 파일 하단
- [ ] 스타일이 복잡한가? → `styled.ts`로 분리
- [ ] 직접 색상값(hex, rgb) 없이 semanticColor 토큰 사용?
- [ ] 전역 스타일을 임의로 추가하지 않는가?
