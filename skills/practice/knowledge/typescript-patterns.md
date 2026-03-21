# TypeScript 고급 패턴

/practice 면접관 참조 자료. 타입 관련 피드백 시 근거로 사용.

---

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
