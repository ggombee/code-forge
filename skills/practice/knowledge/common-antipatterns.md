# 자주 나오는 안티패턴

/practice 면접관 참조 자료. 안티패턴 발견 시 "이 패턴은 X 안티패턴입니다" 피드백의 근거.

---

## 컴포넌트 안티패턴

### God Component

하나의 컴포넌트가 너무 많은 일을 한다.

```tsx
// Bad: 500줄짜리 컴포넌트
function Dashboard() {
  const [users, setUsers] = useState([]);
  const [orders, setOrders] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [filters, setFilters] = useState({});
  const [modal, setModal] = useState(null);

  useEffect(() => { fetchUsers() }, []);
  useEffect(() => { fetchOrders() }, [filters]);
  useEffect(() => { fetchAnalytics() }, []);

  const handleUserClick = () => { /* ... */ };
  const handleOrderFilter = () => { /* ... */ };
  const handleExport = () => { /* ... */ };
  // ... 30개 핸들러

  return (
    <div>
      {/* 500줄의 JSX */}
    </div>
  );
}

// Good: 관심사별로 분리
function Dashboard() {
  return (
    <DashboardLayout>
      <UserSection />
      <OrderSection />
      <AnalyticsSection />
    </DashboardLayout>
  );
}
```

**면접관 피드백:** "이 컴포넌트는 God Component입니다. 단일 책임 원칙에 따라 분리해보세요."

### Prop Drilling

props를 여러 레벨을 거쳐 전달한다.

```tsx
// Bad: 3단계 이상 drilling
function App() {
  const [theme, setTheme] = useState('light');
  return <Page theme={theme} setTheme={setTheme} />;
}
function Page({ theme, setTheme }) {
  return <Section theme={theme} setTheme={setTheme} />;
}
function Section({ theme, setTheme }) {
  return <Button theme={theme} onClick={() => setTheme('dark')} />;
}

// Good: Context 또는 composition
function App() {
  const [theme, setTheme] = useState('light');
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      <Page />
    </ThemeContext.Provider>
  );
}
function Button() {
  const { theme, setTheme } = useContext(ThemeContext);
  return <button onClick={() => setTheme('dark')}>{theme}</button>;
}
```

**면접관 피드백:** "Props가 3단계 이상 drilling되고 있습니다. Context나 composition 패턴을 고려해보세요."

### 불필요한 추상화 (Premature Abstraction)

한 번만 쓰이는 것을 과도하게 추상화한다.

```tsx
// Bad: 한 곳에서만 쓰이는 제네릭 버튼
function GenericActionButton<T extends ActionType>({
  action,
  payload,
  variant,
  size,
  icon,
  confirmMessage,
  onSuccess,
  onError,
  transform,
}: GenericActionButtonProps<T>) {
  // 50줄의 복잡한 로직
}

// Good: 필요할 때 구체적으로
function DeleteButton({ onDelete }: { onDelete: () => void }) {
  return <Button variant="danger" onClick={onDelete}>삭제</Button>;
}
```

**면접관 피드백:** "아직 하나의 유스케이스만 있는데 과도하게 추상화되었습니다. YAGNI 원칙을 기억하세요."

---

## 상태 안티패턴

### 불필요한 전역 상태

로컬이면 충분한 상태를 전역으로 올린다.

```tsx
// Bad: 모달 열림 상태를 전역 store에
const useStore = create((set) => ({
  isModalOpen: false,
  setModalOpen: (v) => set({ isModalOpen: v }),
  modalData: null,
  setModalData: (d) => set({ modalData: d }),
}));

// Good: 모달을 사용하는 컴포넌트에서 로컬로
function ProductCard({ product }) {
  const [showDetail, setShowDetail] = useState(false);
  return (
    <>
      <button onClick={() => setShowDetail(true)}>상세</button>
      {showDetail && <DetailModal product={product} onClose={() => setShowDetail(false)} />}
    </>
  );
}
```

**면접관 피드백:** "이 상태는 이 컴포넌트에서만 사용됩니다. 전역 store에 넣을 이유가 없어요."

### 상태 동기화 문제

동일 데이터의 복사본을 여러 곳에서 관리한다.

```tsx
// Bad: 같은 데이터를 두 곳에서 관리
const [users, setUsers] = useState([]); // 원본
const [selectedUser, setSelectedUser] = useState(null); // 복사본

const handleUpdate = (id, newName) => {
  setUsers(users.map(u => u.id === id ? { ...u, name: newName } : u));
  // selectedUser도 업데이트해야 함 → 잊기 쉬움
  if (selectedUser?.id === id) {
    setSelectedUser({ ...selectedUser, name: newName }); // 동기화 누락 위험
  }
};

// Good: ID만 저장하고 파생
const [users, setUsers] = useState([]);
const [selectedUserId, setSelectedUserId] = useState(null);
const selectedUser = users.find(u => u.id === selectedUserId);
```

**면접관 피드백:** "상태의 단일 소스 원칙(Single Source of Truth)을 위반하고 있습니다."

### Redux 남용

모든 상태를 Redux에 넣는다.

```tsx
// Bad: 폼 입력값을 Redux로
dispatch(updateFormField('email', e.target.value));

// Good: 서버 상태는 TanStack Query, 로컬 UI 상태는 useState
const [email, setEmail] = useState('');
const { data: user } = useQuery({ queryKey: ['user'], queryFn: fetchUser });
```

---

## Effect 안티패턴

### 불필요한 useEffect

useEffect가 필요 없는 곳에 사용한다.

```tsx
// Bad: props/state 변환에 useEffect
function ProductList({ products, category }) {
  const [filtered, setFiltered] = useState([]);

  useEffect(() => {
    setFiltered(products.filter(p => p.category === category));
  }, [products, category]);

  return <List items={filtered} />;
}

// Good: 렌더링 중 계산
function ProductList({ products, category }) {
  const filtered = products.filter(p => p.category === category);
  return <List items={filtered} />;
}
```

```tsx
// Bad: 이벤트 응답에 useEffect 체인
const [query, setQuery] = useState('');
const [results, setResults] = useState([]);

useEffect(() => {
  if (query) {
    search(query).then(setResults);
  }
}, [query]);

const handleSearch = (e) => setQuery(e.target.value);

// Good: 이벤트 핸들러에서 직접
const handleSearch = async (e) => {
  const q = e.target.value;
  setQuery(q);
  if (q) {
    const results = await search(q);
    setResults(results);
  }
};
```

**면접관 피드백:** "이 useEffect는 불필요합니다. React 공식 문서의 'You Might Not Need an Effect'를 참고하세요."

### 누락된 의존성

ESLint 규칙을 무시하고 의존성을 빠뜨린다.

```tsx
// Bad: 의존성 누락 → stale closure
useEffect(() => {
  const id = setInterval(() => {
    setCount(count + 1); // count는 항상 초기값
  }, 1000);
  return () => clearInterval(id);
}, []); // count가 의존성에 없음

// Good: 함수형 업데이트
useEffect(() => {
  const id = setInterval(() => {
    setCount(prev => prev + 1);
  }, 1000);
  return () => clearInterval(id);
}, []);
```

```tsx
// Bad: eslint-disable로 회피
useEffect(() => {
  fetchData(userId);
  // eslint-disable-next-line react-hooks/exhaustive-deps
}, []);

// Good: 의존성 정직하게
useEffect(() => {
  fetchData(userId);
}, [userId]);
```

### 클린업 미비

구독, 타이머, 이벤트 리스너의 정리를 잊는다.

```tsx
// Bad: 메모리 누수
useEffect(() => {
  const ws = new WebSocket(url);
  ws.onmessage = (e) => setData(JSON.parse(e.data));
  // WebSocket이 영원히 열려있음
}, [url]);

// Good: 클린업
useEffect(() => {
  const ws = new WebSocket(url);
  ws.onmessage = (e) => setData(JSON.parse(e.data));
  return () => ws.close();
}, [url]);
```

**면접관 피드백:** "클린업 함수가 없습니다. 컴포넌트가 언마운트되면 어떤 일이 발생할까요?"

---

## 타입 안티패턴

### any 남발

```tsx
// Bad
const handleResponse = (data: any) => {
  return data.users.map((u: any) => u.name);
};

// Good
interface ApiResponse {
  users: Array<{ id: string; name: string }>;
}

const handleResponse = (data: ApiResponse) => {
  return data.users.map(u => u.name);
};
```

### 과도한 타입 단언

```tsx
// Bad: as로 강제 변환
const user = {} as User;
const element = document.getElementById('root') as HTMLDivElement;

// Good: 타입 가드 사용
const element = document.getElementById('root');
if (element instanceof HTMLDivElement) {
  // element는 HTMLDivElement
}

// 또는 null 체크
const element = document.getElementById('root');
if (!element) throw new Error('Root element not found');
```

### 불필요한 타입 파라미터

```tsx
// Bad: 타입 파라미터가 한 곳에서만 쓰임
function log<T>(value: T): void {
  console.log(value);
}

// Good: 제네릭이 필요 없음
function log(value: unknown): void {
  console.log(value);
}
```

**면접관 피드백:** "이 제네릭 파라미터는 한 곳에서만 사용되어 불필요합니다."

---

## 테스트 안티패턴

### 구현 세부사항 테스트

```tsx
// Bad: 내부 상태를 직접 검사
it('should update count', () => {
  const { result } = renderHook(() => useCounter());
  act(() => result.current.increment());
  expect(result.current.count).toBe(1); // 내부 구현에 의존
});

// Good: 사용자 관점에서 테스트
it('should display updated count when button clicked', () => {
  render(<Counter />);
  fireEvent.click(screen.getByRole('button', { name: '증가' }));
  expect(screen.getByText('1')).toBeInTheDocument();
});
```

### 과도한 모킹

```tsx
// Bad: 모든 것을 모킹
jest.mock('./useAuth');
jest.mock('./useProducts');
jest.mock('./useCart');
jest.mock('react-router-dom');
jest.mock('./analytics');

// Good: 최소한의 모킹, 실제 동작 테스트
// MSW로 API만 모킹하고 나머지는 실제 코드 사용
const server = setupServer(
  rest.get('/api/products', (req, res, ctx) => {
    return res(ctx.json(mockProducts));
  })
);
```

### 스냅샷 남용

```tsx
// Bad: 전체 컴포넌트 스냅샷
it('should render', () => {
  const { container } = render(<ProductPage />);
  expect(container).toMatchSnapshot(); // 아무 변경이나 깨짐
});

// Good: 의미 있는 assertion
it('should display product name and price', () => {
  render(<ProductCard product={mockProduct} />);
  expect(screen.getByText('MacBook Pro')).toBeInTheDocument();
  expect(screen.getByText('₩2,490,000')).toBeInTheDocument();
});
```

**면접관 피드백:** "이 테스트는 구현 세부사항에 의존하고 있어서, 리팩토링하면 깨질 수 있습니다. 사용자 행동 기반으로 바꿔보세요."
