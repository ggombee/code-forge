# 프론트엔드 성능 최적화 체크리스트

/practice 면접관 참조 자료. 성능 관련 피드백 시 근거로 사용.

---

## 렌더링 최적화

### 불필요 리렌더링 방지

**체크 항목:**
- [ ] 부모 리렌더링 시 변하지 않는 자식이 같이 리렌더링되는가?
- [ ] Context 값 변경 시 구독하지 않는 컴포넌트까지 리렌더링되는가?
- [ ] 인라인 객체/배열/함수가 매 렌더마다 새 참조를 생성하는가?

```tsx
// Bad: 매 렌더마다 새 객체 생성 → 자식 항상 리렌더링
function Parent() {
  return <Child style={{ color: 'red' }} data={[1, 2, 3]} />;
}

// Good: 안정적 참조
const style = { color: 'red' };
const data = [1, 2, 3];

function Parent() {
  return <Child style={style} data={data} />;
}
```

```tsx
// Bad: Context 값이 매번 새 객체
function Provider({ children }) {
  const [user, setUser] = useState(null);
  return (
    <UserContext.Provider value={{ user, setUser }}>
      {children}
    </UserContext.Provider>
  );
}

// Good: useMemo로 안정화
function Provider({ children }) {
  const [user, setUser] = useState(null);
  const value = useMemo(() => ({ user, setUser }), [user]);
  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
}
```

### 가상화 (Virtualization)

100개 이상의 리스트 아이템은 가상화를 고려한다.

```tsx
// react-window 또는 @tanstack/react-virtual 사용
import { useVirtualizer } from '@tanstack/react-virtual';

function VirtualList({ items }) {
  const parentRef = useRef(null);
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  });

  return (
    <div ref={parentRef} style={{ overflow: 'auto', height: 400 }}>
      <div style={{ height: virtualizer.getTotalSize() }}>
        {virtualizer.getVirtualItems().map(virtualRow => (
          <div key={virtualRow.key} style={{
            position: 'absolute',
            top: virtualRow.start,
            height: virtualRow.size,
          }}>
            {items[virtualRow.index].name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Suspense + React.lazy

```tsx
// 라우트 단위 코드 스플리팅
const ProductPage = React.lazy(() => import('./pages/ProductPage'));
const CartPage = React.lazy(() => import('./pages/CartPage'));

function App() {
  return (
    <Suspense fallback={<Spinner />}>
      <Routes>
        <Route path="/products" element={<ProductPage />} />
        <Route path="/cart" element={<CartPage />} />
      </Routes>
    </Suspense>
  );
}
```

---

## 메모이제이션 전략

### 언제 쓰는가

| 상황 | 사용 여부 |
|------|----------|
| 비용 큰 계산 (정렬, 필터, 트리 변환) | useMemo O |
| 단순 문자열 연결, 숫자 계산 | useMemo X |
| React.memo 된 자식에 전달하는 콜백 | useCallback O |
| 이벤트 핸들러 (자식에 전달 안 함) | useCallback X |
| 의존성이 매 렌더마다 바뀜 | 메모이제이션 의미 없음 |

### 잘못된 메모이제이션

```tsx
// Bad: 의존성이 매번 바뀌어서 의미 없음
const result = useMemo(() => {
  return items.filter(i => i.type === filter);
}, [items, filter]); // items가 매번 새 배열이면 무용지물

// Bad: 비용이 거의 없는 계산에 useMemo
const fullName = useMemo(
  () => `${firstName} ${lastName}`,
  [firstName, lastName]
); // 그냥 const fullName = `${firstName} ${lastName}`이면 충분

// Bad: useCallback 안에서 상태를 직접 참조
const handleClick = useCallback(() => {
  setItems([...items, newItem]); // items가 의존성 → 매번 새 함수
}, [items, newItem]);

// Good: 함수형 업데이트로 의존성 제거
const handleClick = useCallback(() => {
  setItems(prev => [...prev, newItem]);
}, [newItem]);
```

---

## 번들 최적화

### 코드 스플리팅

- **라우트 기반**: 각 페이지를 별도 청크로
- **컴포넌트 기반**: 모달, 드로어 등 초기 렌더링에 불필요한 것
- **라이브러리 기반**: 무거운 라이브러리를 필요할 때만 로드

```tsx
// 모달을 동적 임포트
const HeavyModal = React.lazy(() => import('./HeavyModal'));

function Page() {
  const [showModal, setShowModal] = useState(false);
  return (
    <>
      <button onClick={() => setShowModal(true)}>Open</button>
      {showModal && (
        <Suspense fallback={<Spinner />}>
          <HeavyModal />
        </Suspense>
      )}
    </>
  );
}
```

### 트리 셰이킹

```tsx
// Bad: 전체 라이브러리 임포트
import _ from 'lodash';
_.debounce(fn, 300);

// Good: 필요한 함수만
import debounce from 'lodash/debounce';
debounce(fn, 300);

// 또는 lodash-es 사용 (ESM)
import { debounce } from 'lodash-es';
```

### 번들 분석

```bash
# webpack
npx webpack-bundle-analyzer stats.json

# vite
npx vite-bundle-visualizer

# next.js
ANALYZE=true next build  # @next/bundle-analyzer 설정 필요
```

---

## 네트워크 최적화

### 프리페칭

```tsx
// 링크 호버 시 프리페치 (React Router)
<Link to="/products" onMouseEnter={() => prefetchProducts()}>
  Products
</Link>

// TanStack Query 프리페칭
const queryClient = useQueryClient();
const prefetchProducts = () => {
  queryClient.prefetchQuery({
    queryKey: ['products'],
    queryFn: fetchProducts,
  });
};
```

### 이미지 최적화

- **next/image**: 자동 리사이징, WebP 변환, lazy loading
- **srcset**: 뷰포트에 맞는 이미지 제공
- **loading="lazy"**: 뷰포트에 들어올 때 로드
- **placeholder**: blur 또는 skeleton으로 CLS 방지

```tsx
// Next.js
import Image from 'next/image';
<Image src="/hero.jpg" width={800} height={400} alt="Hero" priority />

// 일반 HTML
<img
  src="photo.jpg"
  srcSet="photo-480.jpg 480w, photo-800.jpg 800w"
  sizes="(max-width: 600px) 480px, 800px"
  loading="lazy"
  alt="Photo"
/>
```

---

## 측정 도구

### React DevTools Profiler

- **렌더링 이유 확인**: 왜 리렌더링되었는지 표시
- **커밋별 렌더링 시간**: 어떤 컴포넌트가 느린지
- **하이라이트 업데이트**: 화면에서 리렌더링되는 영역 시각화

### Web Vitals (Core)

| 지표 | 목표 | 설명 |
|------|------|------|
| **LCP** (Largest Contentful Paint) | < 2.5s | 가장 큰 콘텐츠 렌더링 시간 |
| **INP** (Interaction to Next Paint) | < 200ms | 사용자 인터랙션 응답 시간 |
| **CLS** (Cumulative Layout Shift) | < 0.1 | 레이아웃 밀림 정도 |

### Lighthouse

```bash
# CLI로 실행
npx lighthouse https://example.com --view

# Chrome DevTools > Lighthouse 탭
```

---

## 안티패턴 요약

| 안티패턴 | 문제 | 대안 |
|---------|------|------|
| 모든 곳에 React.memo | 비교 비용 추가, 코드 복잡 | 프로파일링 후 필요한 곳만 |
| 불필요한 상태 (파생 가능한 값) | 동기화 이슈, 리렌더링 | 렌더 중 계산 또는 useMemo |
| 인라인 객체/함수를 memo된 자식에 전달 | memo 무효화 | 상수 추출 또는 useMemo/useCallback |
| 모든 useEffect에서 setState | 불필요한 이중 렌더 | 이벤트 핸들러 또는 렌더 중 계산 |
| 무거운 라이브러리 전체 import | 번들 비대화 | 서브패스 import 또는 동적 import |
| key에 인덱스 사용 (변경 가능한 리스트) | 비효율적 리렌더링 | 고유 id 사용 |
