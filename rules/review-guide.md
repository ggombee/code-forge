---
alwaysApply: true
---

# 리뷰/리팩토링 가이드

Phase 2(리팩토링/리뷰) 시 참조. 설계 철학, 안티패턴, 성능, 평가 기준 통합.

---

## 핵심 철학 (프론트엔드 팀의 가치관)

### 1. 변경하기 쉬운 코드가 최우선

토스는 하루 수십 번 배포하는 환경. "완벽한 설계"보다 **"변경에 강한 코드"**가 생존 원칙이다. 기능 추가/수정 시 영향 범위를 최소화하는 구조가 좋은 코드다.


### 2. 구조적으로 휴먼 에러를 방지

"문서로 주의하세요"가 아니라, **인터페이스 자체가 잘못된 사용을 불가능하게** 만든다. SDK의 Facade 패턴, useFunnel의 타입 시스템, ts-pattern의 exhaustive 매칭 모두 이 원칙.


### 3. 코드에서 자동으로 진실을 추출

문서가 코드와 동기화되지 않는 문제를 코드 자체를 분석해서 해결한다. AST 파싱으로 퍼널 문서 자동 생성, AI 기반 실록봇으로 코드 변경사항 추적.


### 4. 사용자 경험과 개발 생산성을 동시에 추구

둘 중 하나를 포기하지 않는다. SSR로 사용자 경험 개선하면서 esbuild로 개발 빌드 속도도 확보. React Native로 네이티브 경험 제공하면서 코드 공유로 생산성도 확보.


### 5. 점진적 개선 (달리는 기차 바퀴 칠하기)

Greenfield 재작성 대신, 운영 중인 서비스를 **점진적으로 개선**한다. 레거시와 신규 코드가 공존할 수 있는 마이그레이션 전략을 설계한다. 7년된 컬러 시스템도, 결제 레거시도 한번에 바꾸지 않았다.


### 6. 접근성은 기본

"누구나 금융을 쉽게"라는 팀 미션의 기술적 구현. 접근성은 별도 작업이 아니라 **개발 프로세스에 내장**되어야 한다. 스크린리더, 키보드 네비게이션, 시맨틱 마크업은 기본.


### 7. Execution Over Perfection

완벽하게 만들어서 공개하기보다 **빠르게 실행하고 피드백으로 개선**한다. es-toolkit 오픈소스를 3개월 만에 Lodash 대안으로 성장시킨 것처럼. 오픈소스 위원회가 이 문화를 제도적으로 뒷받침.


---

## 설계 원칙

### 인터페이스 강제 (Pit of Success)

사용자가 **올바른 방법으로만 사용하도록** 인터페이스를 설계한다. 잘못된 사용이 컴파일 타임에 에러로 잡히도록 타입 시스템을 활용.

```typescript
// Bad: 순서를 실수할 수 있음
sdk.server.open()
sdk.server.onConnect(...)
sdk.server.close()

// Good: 인터페이스가 올바른 사용만 허용
const server = await sdk.start({ onConnection, onMessage })
await server.stop()
```

### Facade 패턴의 재해석

전통적인 "복잡한 것을 감추는 것"이 아니라, **"사용자의 의도(Intent) 기준으로 인터페이스를 재구성하는 것"**이 핵심. SDK L1(low-level) vs L2(intent-based) 구분.

### Framework Agnostic 설계

코어 로직은 프레임워크에 의존하지 않게 만들고, 프레임워크별 바인딩은 별도 레이어로 분리. React가 아닌 다른 프레임워크로 전환할 때도 코어는 재사용 가능.


### 컴포넌트 트리 = 기능 트리

폴더 구조와 컴포넌트 구조가 기능의 의존 관계를 그대로 반영해야 한다. "이 컴포넌트를 수정하면 어디에 영향이 가는지"가 구조만 보고 파악 가능해야 함.


### 퍼널 상태의 선언적 관리

다단계 흐름(결제, 가입, 인증)을 명령형 라우팅이 아닌 **선언적 상태 머신**으로 관리. useFunnel이 이 철학의 구현체. 각 스텝의 전환 조건이 타입으로 강제됨.


### Single Source of Truth

같은 데이터의 복사본을 여러 곳에서 관리하지 않는다. URL 쿼리 파라미터, 서버 상태, 로컬 상태의 경계를 명확히 하고 각각의 진실 공급원을 하나로 유지.

---

## 기술 선택과 도구

### @use-funnel

토스가 만든 퍼널(다단계 흐름) 관리 라이브러리. 스텝 간 전환을 타입 안전하게 관리하고, 각 스텝에서 사용 가능한 상태를 컴파일 타임에 보장. 복잡한 결제/가입 흐름에서 핵심.

### ts-pattern

패턴 매칭 라이브러리. switch-case의 안전한 대안. exhaustive 매칭으로 모든 케이스를 처리했는지 컴파일 타임에 확인. 판별 유니온(Discriminated Union)과 함께 사용.

### 팀 디자인 시스템 (TDS)

7년간 진화한 디자인 시스템. 토큰 기반 컬러 시스템(시맨틱 토큰 → 프리미티브 토큰). "더 많은 팀이 잘 사용하게 하는 것"이 목표. 사용 빈도 분석으로 불필요한 토큰 제거.

### esbuild + HMR

대규모 모노레포에서의 빌드 속도 문제를 esbuild로 해결. 커스텀 HMR 구현으로 개발 피드백 루프를 수 초 → 밀리초로 단축.

### 모노레포 파이프라인

수백 개 패키지의 빌드/테스트/배포를 효율적으로 관리. 변경된 패키지만 빌드하는 증분 빌드, 의존성 그래프 기반 병렬 실행.

### Granite (RN 프레임워크)

팀의 React Native 프레임워크. 네이티브 앱과 RN의 공존을 위한 아키텍처. 점진적 마이그레이션 지원.

### es-toolkit

Lodash 대안 오픈소스. 번들 크기 97% 감소, 2-3배 빠른 성능. 3개월 만에 npm 주간 370만 다운로드.

---

## 실전 리팩토링 패턴 (PR 사례에서 추출)

팀 모의과제 제출자들의 PR에서 추출한 실전 패턴. 단순 이론이 아닌 실제 적용 사례.

### "추상화와 추출은 다르다"

팀 해설에서 나온 핵심 원칙. 파일을 쪼개는 것(추출)과 의미 있는 인터페이스를 만드는 것(추상화)은 별개.
- 추출: 긴 파일을 여러 파일로 나눔 → 구조만 바뀜
- 추상화: "이 컴포넌트는 무엇을 하는가"가 이름만 보고 알 수 있게 됨

추상화 판단 기준:
- 3곳 이상에서 중복 사용되는가?
- 한눈에 어떤 역할인지 파악 가능한가?

### Suspense + ErrorBoundary 선언적 처리

"선언적 코드" 철학의 구체적 구현. 로딩/에러 상태를 명령형 if문이 아닌 선언적 경계로 처리.
- `useSuspenseQueries`로 병렬 fetch (useQuery 2개 연속 → waterfall 방지)
- 네임스페이스 패턴: `FloorSelectField.Loading`, `FloorSelectField.Error`
- ErrorBoundary의 `onReset`으로 React Query 캐시도 함께 초기화

### 프론트엔드 레이어드 아키텍처

```
remotes (API 호출)
  → model (도메인 모델, DTO 변환)
    → logic (필터링, 정렬 등 비즈니스 로직)
      → view-model (view에 필요한 데이터 가공)
        → view (순수 렌더링, 상태 직접 참조 금지)
```

핵심: 외부 변화(API, 요구사항)로부터 의존성을 끊는 구조.
- 서버 응답을 그대로 쓰지 않고 프론트용 모델로 변환 (DTO)
- Repository 패턴으로 데이터 조회/갱신 캡슐화
- 상수도 API가 될 수 있다 → Repository에서 관리 → OCP 만족

### key prop 리마운트 패턴

useEffect로 상태 초기화하는 대신, key prop 변경으로 컴포넌트를 리마운트.
```tsx
// Anti-pattern: useEffect로 초기화
useEffect(() => { setSelectedRoomId(null); }, [date, startTime, ...]);
// 문제: equipment 배열이 참조 비교 → JSON.stringify 우회 필요

// Better: key로 리마운트
<AvailableRoomContent key={JSON.stringify(filterOption)} />
// 필터 변경 시 상태가 자연스럽게 초기화
```

### URL을 SSOT로 삼는 필터 관리

useEffect + setSearchParams 동기화 대신 URL 자체를 Single Source of Truth로.
```
기존: useState 7개 → useEffect로 URL 동기화 → 동기화 누락 버그
개선: useUrlFilter 훅 → URL이 곧 상태 → props drilling 없이 각 컴포넌트에서 독립 읽기
```

장점: 새로고침 유지, 링크 공유 가능, 뒤로가기 자연스러움

### 서버 데이터 vs 클라이언트 상태 판단 기준

- 서버 데이터 (rooms, reservations) → React Query 캐시에서 직접 읽기
- 클라이언트 상태 (선택, 에러 메시지) → Context 또는 props
- 부모에서 useSuspenseQueries로 prefetch → 하위에서 같은 queryKey로 캐시 hit

### react-hook-form 도입 판단

폼 상태가 5개 이상이고 검증 로직이 복잡하면 도입 고려.
- register (uncontrolled) vs Controller (controlled) 구분
- 필터 에러와 제출 에러를 분리하여 맥락에 맞는 피드백

---

## 코드 가독성 (뇌과학 기반)

## 1. 코드 가독성은 뇌과학이다

출처: "우리는 왜 어떤 코드를 읽기 쉽다고 느낄까" (2026.01.30)

**핵심:** 코드 가독성은 주관이 아니라 인지 과학으로 설명 가능하다.

**평가 기준:**
- **작업 기억 슬롯 (7±2):** 한 함수/컴포넌트에서 동시에 추적해야 하는 변수/상태가 7개 이하인가?
- **청킹(Chunking):** 관련 코드가 의미 단위로 묶여 있는가? (커스텀 훅, 컴포넌트 분리 등)
- **시스템 1/2:** 이름만 보고 직관적으로 이해되는가(시스템1)? 아니면 코드를 자세히 읽어야 하는가(시스템2)?
- **예측 부호화:** 코드 구조가 예측 가능한가? 같은 패턴이 일관적으로 반복되는가?
- **인지 부하 3분류:** 내재적(문제 자체), 외재적(불필요한 복잡성), 본유적(학습 비용). 외재적 부하를 최소화했는가?

---

## 2. 선언적 프로그래밍의 착각과 오해

출처: "선언적 프로그래밍에 대한 착각과 오해" (2025.09.07)

**핵심:** 선언적 코드는 문법이 아니라 사고방식의 문제다. JSX를 쓴다고 선언적인 게 아니다.

**평가 기준:**
- **상태 vs 관계:** 상태를 직접 조작하는 대신, 상태 간 관계를 선언했는가?
- **불가능한 상태 조합 제거:** 타입 시스템으로 잘못된 상태 조합을 원천 차단했는가?
- **정보 흐름 선형성:** 데이터 흐름이 한 방향으로 읽히는가? 순환 참조나 역방향 의존이 없는가?
- **What vs How:** 컴포넌트가 "무엇을 보여주는가"에 집중하는가, "어떻게 보여주는가"에 빠져있는가?

---

## 안티패턴

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

---

## 성능 최적화 체크리스트

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
