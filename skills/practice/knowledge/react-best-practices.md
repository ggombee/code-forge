# React 베스트 프랙티스

/practice 면접관 참조 자료. "이건 React 베스트 프랙티스 위반입니다" 같은 피드백 시 근거로 사용.

---

## 컴포넌트 설계 원칙

### 단일 책임 원칙 (SRP)

하나의 컴포넌트는 하나의 역할만 담당한다.

```tsx
// Bad: 데이터 페칭 + 렌더링 + 비즈니스 로직이 한 곳에
function ProductPage() {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);

  useEffect(() => { fetch('/api/products').then(...) }, []);

  const addToCart = (id) => { /* 카트 로직 */ };
  const calculateTotal = () => { /* 계산 로직 */ };

  return (
    <div>
      {products.map(p => <div onClick={() => addToCart(p.id)}>{p.name}</div>)}
      <div>Total: {calculateTotal()}</div>
    </div>
  );
}

// Good: 관심사 분리
function ProductPage() {
  const { products } = useProducts();
  const { cart, addToCart, total } = useCart();

  return (
    <div>
      <ProductList products={products} onAddToCart={addToCart} />
      <CartSummary total={total} />
    </div>
  );
}
```

### 합성 패턴 (Composition)

상속보다 합성을 선호한다. children과 render props로 유연한 구조를 만든다.

```tsx
// Bad: 조건부 렌더링이 컴포넌트 내부에 하드코딩
function Card({ type, title, content }) {
  return (
    <div className="card">
      {type === 'image' && <img src={content} />}
      {type === 'text' && <p>{content}</p>}
      {type === 'video' && <video src={content} />}
    </div>
  );
}

// Good: 합성으로 유연하게
function Card({ children }) {
  return <div className="card">{children}</div>;
}

<Card><img src={url} /></Card>
<Card><p>{text}</p></Card>
```

### 제어 역전 (Inversion of Control)

컴포넌트가 "어떻게 렌더링할지"를 외부에서 결정할 수 있게 한다.

```tsx
// Compound Component 패턴
function Select({ children, value, onChange }) {
  return (
    <SelectContext.Provider value={{ value, onChange }}>
      <div className="select">{children}</div>
    </SelectContext.Provider>
  );
}

Select.Option = function Option({ value, children }) {
  const ctx = useContext(SelectContext);
  return (
    <div
      className={ctx.value === value ? 'selected' : ''}
      onClick={() => ctx.onChange(value)}
    >
      {children}
    </div>
  );
};
```

---

## Hook 규칙과 베스트 프랙티스

### Hook 기본 규칙 (면접 필수)

1. **최상위에서만 호출** — 조건문, 반복문, 중첩 함수 안에서 호출 금지
2. **React 함수 컴포넌트 또는 커스텀 훅에서만 호출**

```tsx
// Bad: 조건부 훅 호출
function Component({ isLoggedIn }) {
  if (isLoggedIn) {
    const [user, setUser] = useState(null); // Rules of Hooks 위반
  }
}

// Good: 항상 호출하고, 조건은 내부에서
function Component({ isLoggedIn }) {
  const [user, setUser] = useState(null);
  // isLoggedIn에 따른 로직은 여기서
}
```

### 커스텀 훅 추출 기준

- **2개 이상의 컴포넌트에서 동일한 상태+로직 조합**이 반복될 때
- **컴포넌트의 로직이 렌더링과 무관한 비즈니스 로직**일 때
- **테스트하고 싶은 로직**이 컴포넌트에 묶여있을 때

```tsx
// 추출 대상: 데이터 페칭 + 로딩/에러 상태
function useProducts(category: string) {
  const [data, setData] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    setLoading(true);
    fetchProducts(category)
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false));
  }, [category]);

  return { data, loading, error };
}
```

### useEffect 올바른 사용

useEffect는 **외부 시스템과의 동기화**에 사용한다. 파생 상태 계산이나 이벤트 핸들링에 쓰지 않는다.

```tsx
// Bad: 파생 상태를 useEffect로 계산
const [items, setItems] = useState([]);
const [filteredItems, setFilteredItems] = useState([]);

useEffect(() => {
  setFilteredItems(items.filter(i => i.active));
}, [items]);

// Good: 렌더링 중 직접 계산
const [items, setItems] = useState([]);
const filteredItems = items.filter(i => i.active);
// 비용이 크면 useMemo 사용
const filteredItems = useMemo(() => items.filter(i => i.active), [items]);
```

```tsx
// Bad: 이벤트 핸들러 대신 useEffect
useEffect(() => {
  if (submitted) {
    sendAnalytics('form_submit');
  }
}, [submitted]);

// Good: 이벤트 핸들러에서 직접
const handleSubmit = () => {
  setSubmitted(true);
  sendAnalytics('form_submit');
};
```

---

## 상태 관리 원칙

### 로컬 vs 전역

| 기준 | 로컬 (useState) | 전역 (Context/Store) |
|------|----------------|---------------------|
| 사용 범위 | 단일 컴포넌트 또는 부모-자식 | 트리 전체 또는 다수 비관련 컴포넌트 |
| 예시 | 폼 입력, 토글, 모달 열림 | 인증 상태, 테마, 언어 |
| 원칙 | **가능한 한 로컬에 유지** | 정말 전역이어야 할 때만 |

### 상태 최소화

저장할 필요 없는 값은 상태로 만들지 않는다.

```tsx
// Bad: 파생 가능한 값을 상태로
const [firstName, setFirstName] = useState('');
const [lastName, setLastName] = useState('');
const [fullName, setFullName] = useState(''); // 불필요

useEffect(() => {
  setFullName(`${firstName} ${lastName}`);
}, [firstName, lastName]);

// Good: 파생 값은 계산
const [firstName, setFirstName] = useState('');
const [lastName, setLastName] = useState('');
const fullName = `${firstName} ${lastName}`;
```

### 상태 구조화

관련 상태는 하나의 객체로 묶는다.

```tsx
// Bad: 항상 같이 업데이트되는 상태가 분리
const [x, setX] = useState(0);
const [y, setY] = useState(0);

// Good: 하나로 묶기
const [position, setPosition] = useState({ x: 0, y: 0 });
```

---

## 렌더링 최적화

### React.memo — 언제 쓰는가

- 부모가 자주 리렌더링되지만 **자식의 props는 변하지 않을 때**
- 렌더링 비용이 **측정 가능하게 높을 때**
- **모든 곳에 기본으로 쓰지 않는다** — 비교 비용도 있다

### useMemo / useCallback

```tsx
// useMemo: 비용 큰 계산 결과 캐싱
const sortedList = useMemo(
  () => items.sort((a, b) => a.price - b.price),
  [items]
);

// useCallback: 자식에 전달하는 콜백 안정화
const handleClick = useCallback((id: string) => {
  setSelected(id);
}, []);
```

**쓰지 말아야 할 때:**
- 계산이 가볍고 빠른 경우
- 메모된 값을 아무도 참조 동등성으로 비교하지 않는 경우
- 의존성이 매 렌더마다 바뀌는 경우 (의미 없음)

---

## 에러 처리

### Error Boundary

```tsx
class ErrorBoundary extends React.Component {
  state = { hasError: false };

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    logErrorToService(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}
```

- Error Boundary는 **렌더링 중 에러**만 잡는다
- 이벤트 핸들러, 비동기 코드, SSR 에러는 잡지 못한다
- **페이지 단위 + 섹션 단위** 이중으로 감싸는 것이 좋다

### 비동기 에러 핸들링

```tsx
// Good: 비동기 에러를 명시적으로 처리
function useAsyncAction() {
  const [error, setError] = useState<Error | null>(null);

  const execute = async (action: () => Promise<void>) => {
    try {
      setError(null);
      await action();
    } catch (e) {
      setError(e instanceof Error ? e : new Error(String(e)));
    }
  };

  return { error, execute };
}
```

---

## 접근성

### 필수 체크리스트

- **시맨틱 HTML**: `<button>`, `<nav>`, `<main>`, `<article>` 사용. `<div onClick>` 금지
- **alt 텍스트**: 모든 `<img>`에 의미 있는 alt. 장식 이미지는 `alt=""`
- **ARIA**: 네이티브 요소로 불가능할 때만 사용. `aria-label`, `aria-describedby`, `role`
- **키보드 네비게이션**: Tab 순서, Enter/Space 활성화, Escape로 닫기
- **포커스 관리**: 모달 열릴 때 포커스 이동, 닫힐 때 복귀

```tsx
// Bad
<div onClick={handleClick}>Click me</div>

// Good
<button onClick={handleClick}>Click me</button>
```

---

## 면접 빈출 질문 패턴

### Virtual DOM과 Reconciliation

- Virtual DOM은 실제 DOM의 경량 복사본
- state/props 변경 → 새 Virtual DOM 생성 → 이전과 비교 (diffing) → 최소 변경만 실제 DOM에 적용
- **key**가 중요한 이유: 리스트에서 요소 식별. 인덱스를 key로 쓰면 순서 변경 시 비효율적 리렌더링

### React Fiber

- React 16에서 도입된 reconciliation 엔진
- 렌더링 작업을 작은 단위(fiber)로 분할하여 중단/재개 가능
- 우선순위 기반 스케줄링 (사용자 입력 > 애니메이션 > 데이터 페칭)

### Hooks 동작 원리

- 훅은 **호출 순서**에 의존하여 상태를 추적한다 (linked list)
- 그래서 조건부 호출이 금지 — 순서가 바뀌면 상태 매핑이 깨진다
- `useState`의 setter가 Object.is로 비교하여 같으면 리렌더링 스킵

### Closure 트랩

```tsx
// 문제: stale closure
function Counter() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      console.log(count); // 항상 0 (클로저에 갇힌 초기값)
      setCount(count + 1); // 항상 0 + 1 = 1
    }, 1000);
    return () => clearInterval(id);
  }, []);

  // 해결: 함수형 업데이트
  // setCount(prev => prev + 1);
}
```

### Batching

- React 18+: 모든 상태 업데이트가 자동 배칭됨 (이벤트 핸들러, setTimeout, Promise 등)
- 여러 setState 호출이 하나의 리렌더링으로 합쳐짐

### Strict Mode 동작

- 개발 모드에서 컴포넌트를 두 번 렌더링하여 부수효과 감지
- useEffect도 mount → unmount → mount로 실행하여 클린업 누락 발견
