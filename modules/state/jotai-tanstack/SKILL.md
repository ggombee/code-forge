---
name: jotai-tanstack
description: Jotai + TanStack Query v5 상태관리 패턴. atoms/, queries/, queryKeys 구조.
---

# Jotai + TanStack Query v5 상태관리

## 상태 유형별 도구

| 상태 유형              | 도구                | 위치                     |
| ---------------------- | ------------------- | ------------------------ |
| 서버 상태 (API 데이터) | TanStack Query v5   | `packages/shared/queries/` |
| 전역 UI/세션 상태      | Jotai               | `packages/shared/atoms/` |
| 폼 상태                | React Hook Form     | 컴포넌트 내부            |
| 로컬 UI 상태           | useState/useReducer | 컴포넌트 내부            |

### 판단 기준

- **서버에서 온 데이터인가?** → React Query
- **여러 컴포넌트가 공유해야 하는 UI 상태인가?** → Jotai
- **폼 입력값인가?** → React Hook Form
- **이 컴포넌트에서만 쓰는 상태인가?** → useState

---

## TanStack Query 구조

### 디렉토리 구조

```
packages/shared/
├── queries/
│   └── {도메인}/
│       ├── index.ts       # useXxxQuery, useXxxMutation 훅
│       └── queryKeys.ts   # 쿼리 키 정의
├── services/
│   └── {도메인}/
│       ├── index.ts       # API 호출 함수
│       └── types.ts       # 요청/응답 타입
```

### 쿼리 키 패턴 (queryKeys 팩토리)

```typescript
// packages/shared/queries/{도메인}/queryKeys.ts
export const orderKeys = {
  all: ['order'] as const,
  lists: () => [...orderKeys.all, 'list'] as const,
  list: (filters: OrderFilters) => [...orderKeys.lists(), filters] as const,
  details: () => [...orderKeys.all, 'detail'] as const,
  detail: (id: string) => [...orderKeys.details(), id] as const,
};
```

### 쿼리 훅 작성 규칙

```typescript
// packages/shared/queries/{도메인}/index.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { orderKeys } from './queryKeys';
import { orderService } from '@repo/shared/services/order';

export const useOrderQuery = (orderId: string) => {
  return useQuery({
    queryKey: orderKeys.detail(orderId),
    queryFn: () => orderService.getOrder(orderId),
  });
};

export const useUpdateOrderMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: orderService.updateOrder,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: orderKeys.detail(variables.orderId),
      });
    },
  });
};
```

### Query Client 기본 설정 (변경 금지)

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      staleTime: 0,
      refetchOnWindowFocus: false,
    },
  },
});
```

---

## Jotai 사용 규칙

### 적합한 사용 사례

- 모달/사이드바 열림 상태
- 현재 선택된 탭/필터
- 사용자 세션 정보 (인증 후)
- 다크모드 등 UI 설정

### Atom 정의 위치

```typescript
// packages/shared/atoms/uiAtoms.ts
import { atom } from 'jotai';

export const sidebarOpenAtom = atom(false);
export const selectedTabAtom = atom<TabType>('all');
```

### 관련 상태 그룹화 (안티패턴 방지)

```typescript
// ❌ 안티패턴: 관련 상태를 개별 atom으로
export const filterTypeAtom = atom('all');
export const filterStartDateAtom = atom(null);
export const filterEndDateAtom = atom(null);

// ✅ 대안: 관련 상태를 하나의 atom으로 그룹화
export const filterAtom = atom<FilterState>({
  type: 'all',
  startDate: null,
  endDate: null,
  status: [],
});
```

### 금지 사항

- 서버 데이터를 atom에 저장하지 않는다
- atom에서 API 호출을 직접 하지 않는다

---

## 캐시 무효화 패턴

```typescript
// ✅ 좋은 예: 도메인 훅 사용
import { useClearOrderListCache } from '@repo/shared/queries/order';

const Component = () => {
  const clearCache = useClearOrderListCache();
  const handleRefresh = () => { clearCache(); };
};

// ❌ 나쁜 예: queryClient 직접 조작
const Component = () => {
  const queryClient = useQueryClient();
  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ['order', 'list'] });
  };
};
```

---

## 안티패턴과 대안

### useEffect로 데이터 페칭 금지

```typescript
// ❌ 안티패턴
const [data, setData] = useState(null);
useEffect(() => { fetchData().then(setData); }, []);

// ✅ 대안
const { data, isLoading } = useQuery({ queryKey: ['data'], queryFn: fetchData });
```

### 파생 상태를 위한 useEffect 금지

```typescript
// ❌ 안티패턴
const [filteredItems, setFilteredItems] = useState([]);
useEffect(() => { setFilteredItems(items.filter(item => item.active)); }, [items]);

// ✅ 대안
const filteredItems = useMemo(() => items.filter(item => item.active), [items]);
```

### 서버 상태와 클라이언트 상태 혼합 금지

```typescript
// ❌ 안티패턴: 서버 데이터를 atom에 동기화
const { data } = useOrderListQuery();
useEffect(() => { if (data) setOrders(data); }, [data]);

// ✅ 대안: React Query를 단일 진실 공급원으로
const { data: orders } = useOrderListQuery();
const activeOrders = useMemo(() => orders?.filter(o => o.status === 'active'), [orders]);
```

### 불안정한 쿼리 키 금지

```typescript
// ❌ 안티패턴: 인라인 객체
useQuery({ queryKey: ['order', { id: orderId, options: { includeDetails: true } }] });

// ✅ 대안: queryKeys 팩토리 함수
useQuery({ queryKey: orderKeys.detail(orderId) });
```

---

## 체크리스트

새로운 상태를 추가할 때 확인:

- [ ] 이 데이터는 서버에서 오는가? → React Query
- [ ] 여러 컴포넌트에서 공유되는가?
  - 서버 데이터 → React Query (이미 전역)
  - UI 상태 → Jotai
- [ ] 폼 입력인가? → React Hook Form
- [ ] 이 컴포넌트에서만 쓰이는가? → useState
- [ ] 쿼리 키가 queryKeys 파일에 정의되어 있는가?
- [ ] 캐시 무효화 로직이 도메인 훅으로 캡슐화되어 있는가?
