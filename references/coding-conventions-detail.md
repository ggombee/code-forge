# Coding Conventions Detail

> coding-standards.md에서 분리된 상세 컨벤션. 필요 시 @참조로 로드.
> alwaysApply가 아님 — 토큰 효율을 위해 분리.

---

## Prettier 공통 설정

범용 Prettier 설정 예시 (프로젝트별 조정):

```json
{
  "printWidth": 200,
  "singleQuote": true,
  "semi": true,
  "tabWidth": 2
}
```

---

---

## 파일 네이밍 컨벤션

| 유형             | 규칙                   | 예시                                        |
| ---------------- | ---------------------- | ------------------------------------------- |
| 컴포넌트 폴더    | PascalCase             | `OrderCard/index.tsx`, `FilterButton/`       |
| 훅 파일          | camelCase, `use*`      | `useOrderFilter.ts`, `useGetOrderList.ts`    |
| 서비스 파일      | camelCase              | `orderService.ts`, `authService.ts`          |
| 페이지 라우팅    | kebab-case             | `order-list.tsx`, `product-detail.tsx`       |
| 유틸리티         | camelCase              | `formatDate.ts`, `calculateDiscount.ts`      |
| 타입 파일        | camelCase              | `order.types.ts`, `product.types.ts`         |
| 스타일 파일      | `styled.ts`            | `styled.ts` (컴포넌트 폴더 내)              |
| 쿼리 키 파일     | camelCase              | `queryKeys.ts`                              |

---

---

## API 서비스 메서드 네이밍

HTTP 동사 + 리소스명 패턴을 따른다:

```typescript
// services/order/index.ts

// GET 요청: get + 리소스명
export const getOrderList = (params: GetOrderListRequest): Promise<GetOrderListResponse> =>
  api.get('/api/orders', { params });

export const getOrderDetail = (orderId: string): Promise<GetOrderDetailResponse> =>
  api.get(`/api/orders/${orderId}`);

// POST 요청: post + 리소스명
export const postOrder = (body: PostOrderRequest): Promise<PostOrderResponse> =>
  api.post('/api/orders', body);

// PUT 요청: put + 리소스명
export const putOrder = (orderId: string, body: PutOrderRequest): Promise<PutOrderResponse> =>
  api.put(`/api/orders/${orderId}`, body);

// DELETE 요청: delete + 리소스명
export const deleteOrder = (orderId: string): Promise<void> =>
  api.delete(`/api/orders/${orderId}`);
```

---

---

## 쿼리 훅 네이밍

`use` + `Get/Post` + 도메인 패턴을 따른다:

```typescript
// queries/order/index.ts

// 조회: useGet + 도메인
export const useGetOrderList = (params: GetOrderListRequest) =>
  useQuery({
    queryKey: queryKeys.getOrderList(params),
    queryFn: () => getOrderList(params),
  });

export const useGetOrderDetail = (orderId: string) =>
  useQuery({
    queryKey: queryKeys.getOrderDetail(orderId),
    queryFn: () => getOrderDetail(orderId),
  });

// 변경: usePost/usePut/useDelete + 도메인
export const usePostOrder = () =>
  useMutation({
    mutationFn: postOrder,
  });
```

---

---

## 쿼리 키 팩토리

쿼리 키는 팩토리 패턴으로 관리한다:

```typescript
// queries/order/queryKeys.ts

export const queryKeys = {
  getOrderList: (params: GetOrderListRequest) => ['getOrderList', params] as const,
  getOrderDetail: (orderId: string) => ['getOrderDetail', orderId] as const,
};
```

**규칙:**
- 키 이름은 서비스 메서드명과 동일하게 맞춘다
- 파라미터를 키에 포함하여 자동 캐시 분리
- `as const`로 타입 안전성 확보

---

---

## 커밋 메시지 컨벤션

```
[작성자] type: [{티켓번호}] 설명
```

**예시:**

```bash
git commit -m "[홍길동] feat: [TICKET-123] 주문 목록 필터 추가"
git commit -m "[홍길동] fix: [TICKET-456] 날짜 필터 오프바이원 수정"
git commit -m "[홍길동] refactor: [TICKET-789] 주문 서비스 레이어 분리"
```

**type 종류:**

| type       | 용도                     |
| ---------- | ------------------------ |
| `feat`     | 새 기능                  |
| `fix`      | 버그 수정                |
| `refactor` | 리팩토링 (동작 변경 없음)|
| `style`    | 스타일/포맷팅 변경       |
| `docs`     | 문서 수정                |
| `test`     | 테스트 추가/수정         |
| `chore`    | 빌드/설정 변경           |

---

---

## 환경 파일

| 파일             | 용도                   |
| ---------------- | ---------------------- |
| `.env.local`     | 로컬 개발 (gitignore)  |
| `.env.dev`       | 개발 서버 환경         |
| `.env.stage`     | 스테이징 환경          |
| `.env.release`   | 프로덕션 환경          |

**주요 환경 변수:**

```bash
NEXT_PUBLIC_ENV=local|dev|stage|release
NEXT_PUBLIC_API_URL=https://api.example.com
```

**빌드 시 환경 지정:**

```bash
PROFILE=dev yarn build     # 개발 환경 빌드
PROFILE=stage yarn build   # 스테이징 환경 빌드
PROFILE=release yarn build # 프로덕션 환경 빌드
```

---


---

## Context/Provider 의존성 (React)

Dialog/Modal content 내부에서는 상위 Context 접근이 불가하다.

| 금지                  | 대안                         |
| --------------------- | ---------------------------- |
| `useModal` 직접 호출  | 상위에서 콜백을 props로 전달 |
| `useDialog` 직접 호출 | 상위에서 콜백을 props로 전달 |
| `useToast` 직접 호출  | 상위에서 콜백을 props로 전달 |

```typescript
// ❌ 금지: Dialog/Modal content 내부에서 context hook 사용
const Content = () => {
  const { close } = useModal();
  return <Button onClick={close} />;
};

// ✅ 허용: 상위에서 콜백 전달
const Content = ({ onClose }: { onClose: () => void }) => {
  return <Button onClick={onClose} />;
};
```

---

## 스타일링 (Emotion)

| 금지              | 대안                       |
| ----------------- | -------------------------- |
| inline style 객체 | Emotion styled/css         |
| `!important`      | `&&` specificity           |
| px 하드코딩       | 디자인 토큰                |
| 하드코딩 색상값   | semanticColor 토큰         |

```typescript
// ❌ 금지
<div style={{ marginTop: 20 }}>

// ✅ 허용: styled 컴포넌트
const Container = styled.div`
  margin-top: ${spacing.md};
`;

// ✅ 허용: Emotion css prop (inline style이 아님)
<Typography css={{ marginTop: '4px' }}>
```

### !important 대신 `&&` specificity 패턴

`&&`는 Emotion이 생성한 자기 자신의 클래스를 한번 더 참조하여 specificity를 높이는 기법이다.
`!important`는 이후 override가 불가능해지므로 금지한다.

```typescript
// ❌ 금지
background-color: ${semanticColor.backgroundSecondary} !important;

// ✅ 허용: && 사용 (specificity 0,1,0 → 0,2,0)
&& {
  background-color: ${semanticColor.backgroundSecondary};
}
```

### transient props (`$` prefix)

styled 컴포넌트에 전달하는 custom prop은 `$` prefix를 붙인다.
`$` 없이 전달하면 DOM에 unknown attribute가 전달되어 React warning이 발생한다.

```typescript
// ❌ 금지
const Chip = styled.button<{ isActive: boolean }>`...`;
<Chip isActive={true}>

// ✅ 허용
const Chip = styled.button<{ $isActive: boolean }>`...`;
<Chip $isActive={true}>
```

### inline style vs css prop 구분

| 구문                    | 판정    | 이유                                        |
| ----------------------- | ------- | ------------------------------------------- |
| `style={{ margin: 8 }}` | ❌ 금지 | React의 inline style (정적 스타일에 비효율) |
| `css={{ margin: 8 }}`   | ✅ 허용 | Emotion의 css prop (컴파일 타임 처리)       |
