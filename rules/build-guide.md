---
paths:
  - '**/*.{tsx,jsx}'
---

<!-- React/TypeScript 프로젝트용 가이드 — React 컴포넌트 파일(tsx, jsx)에만 적용됨 -->

# 구현 가이드

Phase 1(구현) 시 참조하는 기본 컨벤션, 패턴, 삽질 기록.
리팩토링 과제에서 코드를 읽을 때도 참조.

---

## React 패턴

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

---

## TypeScript 패턴

## 제네릭 패턴

### 기본 제약 조건 (extends)

```typescript
// Bad: any를 받는 함수
function getProperty(obj: any, key: string) {
  return obj[key];
}

// Good: 타입 안전한 제네릭
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

const user = { name: 'Kim', age: 30 };
getProperty(user, 'name');  // string
getProperty(user, 'foo');   // Error: 'foo'는 keyof User에 없음
```

### 조건부 타입 (Conditional Types)

```typescript
type IsString<T> = T extends string ? true : false;

type A = IsString<string>;  // true
type B = IsString<number>;  // false

// 실용 예: API 응답 타입 추출
type ApiResponse<T> = T extends { data: infer D } ? D : never;

type UserResponse = ApiResponse<{ data: User; meta: Meta }>;  // User
```

### infer 키워드

```typescript
// 함수 반환 타입 추출
type ReturnOf<T> = T extends (...args: any[]) => infer R ? R : never;

// Promise 내부 타입 추출
type Unwrap<T> = T extends Promise<infer U> ? U : T;

type A = Unwrap<Promise<string>>;  // string
type B = Unwrap<number>;           // number
```

### 맵드 타입 (Mapped Types)

```typescript
// 모든 프로퍼티를 optional로
type MyPartial<T> = {
  [K in keyof T]?: T[K];
};

// 모든 프로퍼티를 읽기 전용으로
type MyReadonly<T> = {
  readonly [K in keyof T]: T[K];
};

// 키 리매핑 (4.1+)
type Getters<T> = {
  [K in keyof T as `get${Capitalize<string & K>}`]: () => T[K];
};

type UserGetters = Getters<{ name: string; age: number }>;
// { getName: () => string; getAge: () => number }
```

---

## 유틸리티 타입 활용

### 기본 유틸리티

| 타입 | 용도 | 예시 |
|------|------|------|
| `Partial<T>` | 모든 프로퍼티 optional | 폼 초기값, 업데이트 payload |
| `Required<T>` | 모든 프로퍼티 필수 | 설정 객체 완성 |
| `Pick<T, K>` | 특정 키만 선택 | API 응답에서 필요한 필드만 |
| `Omit<T, K>` | 특정 키 제외 | 민감 정보 제거 |
| `Record<K, V>` | 키-값 매핑 | 룩업 테이블, enum 매핑 |
| `Extract<T, U>` | 유니온에서 추출 | 특정 이벤트 타입만 |
| `Exclude<T, U>` | 유니온에서 제거 | null/undefined 제거 |
| `NonNullable<T>` | null/undefined 제거 | API 응답 보장 |

### 커스텀 유틸리티 타입

```typescript
// 깊은 Partial
type DeepPartial<T> = {
  [K in keyof T]?: T[K] extends object ? DeepPartial<T[K]> : T[K];
};

// 특정 키만 Required
type RequireKeys<T, K extends keyof T> = T & Required<Pick<T, K>>;

type User = { name?: string; email?: string; age?: number };
type UserWithEmail = RequireKeys<User, 'email'>;
// email은 필수, 나머지는 optional

// Nullable
type Nullable<T> = { [K in keyof T]: T[K] | null };
```

---

## 타입 가드와 타입 좁히기

### is 타입 가드 (사용자 정의)

```typescript
interface Cat { meow(): void; }
interface Dog { bark(): void; }

function isCat(animal: Cat | Dog): animal is Cat {
  return 'meow' in animal;
}

function handleAnimal(animal: Cat | Dog) {
  if (isCat(animal)) {
    animal.meow();  // Cat으로 좁혀짐
  } else {
    animal.bark();  // Dog으로 좁혀짐
  }
}
```

### 판별 유니온 (Discriminated Union)

```typescript
type Success = { status: 'success'; data: User };
type Error = { status: 'error'; message: string };
type Loading = { status: 'loading' };

type State = Success | Error | Loading;

function render(state: State) {
  switch (state.status) {
    case 'success':
      return state.data;    // Success로 좁혀짐
    case 'error':
      return state.message; // Error로 좁혀짐
    case 'loading':
      return 'Loading...';
  }
}
```

### exhaustive check

```typescript
function assertNever(x: never): never {
  throw new Error(`Unexpected value: ${x}`);
}

function handle(state: State) {
  switch (state.status) {
    case 'success': return;
    case 'error': return;
    case 'loading': return;
    default: assertNever(state); // 새 상태 추가 시 컴파일 에러
  }
}
```

---

## 타입 안전한 이벤트 핸들링

```typescript
// Bad
const handleChange = (e: any) => { ... };

// Good
const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  const value = e.target.value; // string으로 타입 추론
};

const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
  e.preventDefault();
};

// 이벤트 핸들러 타입
type ButtonProps = {
  onClick: React.MouseEventHandler<HTMLButtonElement>;
  onChange: React.ChangeEventHandler<HTMLInputElement>;
};
```

---

## 제네릭 컴포넌트 패턴

```typescript
// 제네릭 리스트 컴포넌트
interface ListProps<T> {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
  keyExtractor: (item: T) => string;
}

function List<T>({ items, renderItem, keyExtractor }: ListProps<T>) {
  return (
    <ul>
      {items.map(item => (
        <li key={keyExtractor(item)}>{renderItem(item)}</li>
      ))}
    </ul>
  );
}

// 사용: T가 자동 추론됨
<List
  items={users}
  renderItem={(user) => <span>{user.name}</span>}
  keyExtractor={(user) => user.id}
/>
```

```typescript
// 제네릭 테이블
interface Column<T> {
  key: keyof T;
  header: string;
  render?: (value: T[keyof T], row: T) => React.ReactNode;
}

interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
}

function Table<T extends Record<string, unknown>>({ data, columns }: TableProps<T>) {
  // ...
}
```

---

## 타입 레벨 프로그래밍 기초

### Template Literal Types

```typescript
type EventName = 'click' | 'focus' | 'blur';
type Handler = `on${Capitalize<EventName>}`;
// 'onClick' | 'onFocus' | 'onBlur'

type CSSProperty = 'margin' | 'padding';
type Direction = 'Top' | 'Right' | 'Bottom' | 'Left';
type CSSKey = `${CSSProperty}${Direction}`;
// 'marginTop' | 'marginRight' | ... | 'paddingLeft'
```

### Recursive Types

```typescript
// JSON 타입 정의
type Json = string | number | boolean | null | Json[] | { [key: string]: Json };

// 깊은 Readonly
type DeepReadonly<T> = {
  readonly [K in keyof T]: T[K] extends object ? DeepReadonly<T[K]> : T[K];
};
```

---

## 면접 빈출

### any vs unknown

| | `any` | `unknown` |
|---|-------|-----------|
| 할당 | 모든 타입에 할당 가능 | 모든 타입에 할당 가능 |
| 사용 | 아무 연산 가능 (위험) | 타입 좁히기 전까지 연산 불가 |
| 원칙 | **쓰지 마라** | 타입을 모를 때 사용 |

```typescript
// any: 타입 체크를 포기
const x: any = 'hello';
x.foo.bar; // 런타임 에러, 컴파일 통과

// unknown: 안전한 미지의 타입
const y: unknown = 'hello';
if (typeof y === 'string') {
  y.toUpperCase(); // OK, 좁혀진 후에만 사용 가능
}
```

### type vs interface

| | `type` | `interface` |
|---|--------|------------|
| 유니온/인터섹션 | O | X |
| extends | 인터섹션으로 | O (다중 상속) |
| 선언 병합 | X | O |
| 원시/튜플/유틸리티 | O | X |
| 권장 | 유니온, 유틸리티 타입 | 객체 형태, API 계약 |

### 공변 / 반변 (Covariance / Contravariance)

```typescript
// 공변 (Covariant): 출력 위치 — 하위 타입 OK
type Producer<T> = () => T;
// Dog extends Animal이면 Producer<Dog>은 Producer<Animal>에 할당 가능

// 반변 (Contravariant): 입력 위치 — 상위 타입 OK
type Consumer<T> = (value: T) => void;
// Dog extends Animal이면 Consumer<Animal>은 Consumer<Dog>에 할당 가능

// strictFunctionTypes: true에서만 함수 파라미터가 반변적으로 검사됨
```

---

## 실전 삽질 기록


---

## React + React Router

### setSearchParams는 내부적으로 navigate를 호출한다
- 렌더 중 직접 호출하면 React Router 경고 발생
- useEffect로 감싸면 동작하지만 location.state가 날아감
- 해결: Navigate 컴포넌트로 redirect, 또는 라우트 레벨 가드

### location.state는 URL 변경 시 유실된다
- navigate('/', { state: { message } }) 후 setSearchParams하면 state 소멸
- 해결: Navigate에 state={location.state} 전달하여 보존

### useEffect로 URL 동기화하면 동기화 누락 버그
- useState 7개 + useEffect → 의존성 배열 누락 시 URL과 상태 불일치
- 해결: URL 자체를 SSOT로 삼는 useUrlFilter 훅

---

## React Query

### useQuery 2개 연속 → waterfall
- suspense: true인 useQuery를 연속 호출하면 첫 번째가 throw
- Suspense catch → 컴포넌트 언마운트 → 두 번째 useQuery 실행 안 됨
- 해결: useSuspenseQueries로 병렬 fetch

### invalidateQueries 키 범위 주의
- `invalidateQueries(['reservations'])`는 prefix match
- `['reservations', date]`도 포함하여 모든 날짜 캐시를 날림
- 의도된 건지 확인 필요. queryKeys 팩토리로 명시적 관리 권장

### react-query v4 → v5 API 변경
- `useQuery(['key'], fn)` 배열 오버로드는 v5에서 제거
- `useQuery({ queryKey, queryFn })` 객체 형태로 전환 필요
- useSuspenseQuery에서는 조건부 쿼리에 skipToken 사용 (v5)

### staleTime 미설정 → 매 마운트마다 refetch
- 정적 데이터(rooms 등)에 staleTime 미설정 시 불필요한 요청
- staleTime: 5 * 60 * 1000 또는 Infinity 설정 고려

---

## Testing

### userEvent.clear() + URL controlled input
- userEvent.clear()가 onChange로 빈 문자열 전달
- URL에 빈 문자열을 담을 수 없으면 value가 복원됨
- 이후 userEvent.type()이 제대로 동작 안 함
- 해결: useState를 버퍼로 두어 빈 문자열 중간 상태 허용

### window.confirm mock과 커스텀 다이얼로그
- 테스트가 vi.spyOn(window, 'confirm')에 의존
- 커스텀 다이얼로그로 교체하면 테스트도 리라이트 필요
- 시간 대비 효과 판단 필요

### MSW가 클라이언트 버그를 숨기는 패턴
- 클라이언트가 잘못된 형태로 보내도 MSW에서 방어 코드로 보정
- 테스트는 통과하지만 실제 백엔드에서는 실패
- 함정 탐지: 서버 핸들러에 fallback/방어 코드가 있으면 "왜 필요한지" 역추적

---

## Emotion / CSS-in-JS

### 인라인 css`` 는 매 렌더마다 새 객체 생성
- 같은 스타일이 반복되면 모듈 상수로 추출
- 또는 styled 컴포넌트로 분리

---

## TypeScript

### axios 0.27의 isAxiosError는 제네릭 미지원
- `axios.isAxiosError<ServerError>(err)` → 타입 에러
- 해결: axios 1.x 업그레이드 또는 런타임 타입 가드

### string[] vs 유니온 리터럴 타입 불일치
- 서버 타입: `equipment: ('tv' | 'whiteboard')[]`
- 클라이언트 인라인: `equipment: string[]`
- 컴파일 에러 없이 런타임 불일치 발생 가능

---

## 컴포넌트 분리

### key prop으로 상태 초기화 vs useEffect
- useEffect: 의존성 배열에 배열/객체 넣으면 참조 비교 → 매 렌더 실행
- JSON.stringify로 우회 가능하지만 anti-pattern
- key prop: 컴포넌트 리마운트로 자연스러운 초기화. 주석으로 의도 명시

### 필터 변경 시 선택 상태 초기화
- 필터 조건이 바뀌면 선택된 회의실 + 에러 메시지 초기화 필요
- 방법 A: useEffect → anti-pattern
- 방법 B: key prop → 암시적이지만 깔끔
- 방법 C: 선택 상태를 URL에 넣기 → 요구사항에 없으면 과도

---

## 축적 규칙

이 파일은 실제 과제/프로젝트를 진행하면서 발견한 gotcha를 누적한다.
- 리팩토링 Step 3에서 실패한 시도가 있으면 여기에 추가
- 다른 사람의 PR에서 발견한 삽질 기록도 추가
- 다음 과제에서 같은 실수를 반복하지 않기 위한 목적
