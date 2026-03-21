---
name: jest
description: Jest 테스트 컨벤션. __tests__/ 구조, useFakeTimers, AAA 패턴, 한글 테스트명.
---

# Jest 유닛 테스트 컨벤션

순수 함수(utils, helpers, lib, adapters)에 대한 유닛 테스트 작성 규칙.
컴포넌트/훅 테스트는 `assayer` 에이전트가 담당한다.

## 적용 대상

- `utils/`, `helpers/`, `lib/`, `adapters/` 내 순수 함수
- 날짜 계산, 가격 계산, 포맷팅, 상태 변환, 데이터 매핑 등

---

## 파일 위치

```
{파일경로}/__tests__/{파일명}.test.ts
```

**예시:**

- `utils/period.ts` → `utils/__tests__/period.test.ts`
- `adapters/mapOrderToVm.ts` → `adapters/__tests__/mapOrderToVm.test.ts`

---

## 테스트 구조 (필수 준수)

```typescript
import { 함수명 } from '../파일명';

describe('함수명', () => {
  // 날짜/시간 의존 함수는 필수
  beforeAll(() => {
    jest.useFakeTimers().setSystemTime(new Date('2025-01-15T00:00:00.000Z'));
  });

  afterAll(() => {
    jest.useRealTimers();
  });

  describe('정상 케이스', () => {
    it('일반적인 입력에 대해 올바른 결과 반환', () => {
      expect(함수(입력)).toEqual(기대값);
    });
  });

  describe('경계값', () => {
    it('최소값 처리', () => {});
    it('최대값 처리', () => {});
    it('빈 값 처리', () => {});
  });

  describe('에러 케이스', () => {
    it('잘못된 입력 시 에러/기본값 반환', () => {});
  });
});
```

---

## 테스트 케이스 도출 (필수)

| 카테고리    | 설명                        | 예시                       |
| ----------- | --------------------------- | -------------------------- |
| 정상 케이스 | 일반적인 유효 입력          | `getPeriod('last14Days')`  |
| 경계값      | 0, 빈 배열, null, undefined | `formatPrice(0)`           |
| 에러 케이스 | 잘못된 타입, 범위 초과      | `getPeriod('invalid')`     |
| 정책 케이스 | 비즈니스 규칙 반영          | `last14Days는 14일 전부터` |

---

## 날짜 함수 필수 케이스

```typescript
describe('getPeriod', () => {
  beforeAll(() => {
    jest.useFakeTimers().setSystemTime(new Date('2025-01-15T00:00:00.000Z'));
  });

  afterAll(() => {
    jest.useRealTimers();
  });

  it('last14Days - 오늘 기준 14일 전부터 오늘까지', () => {
    expect(getPeriod('last14Days')).toEqual(['2025-01-01', '2025-01-15']);
  });

  it('thisMonth - 해당 월 1일부터 말일까지', () => {
    expect(getPeriod('thisMonth')).toEqual(['2025-01-01', '2025-01-31']);
  });

  it('lastMonth - 이전 월 1일부터 말일까지', () => {
    expect(getPeriod('lastMonth')).toEqual(['2024-12-01', '2024-12-31']);
  });

  it('잘못된 옵션 입력 시 기본값 반환', () => {
    expect(getPeriod('invalid')).toEqual(['2025-01-01', '2025-01-15']);
  });
});
```

---

## 가격/계산 함수 필수 케이스

```typescript
describe('calculateDiscount', () => {
  it('정상 할인율 적용', () => {
    expect(calculateDiscount(10000, 10)).toBe(9000);
  });

  it('0% 할인', () => {
    expect(calculateDiscount(10000, 0)).toBe(10000);
  });

  it('100% 할인', () => {
    expect(calculateDiscount(10000, 100)).toBe(0);
  });

  it('음수 금액 처리', () => {
    expect(() => calculateDiscount(-1000, 10)).toThrow();
  });
});
```

---

## 매핑/변환 함수 필수 케이스

```typescript
describe('mapOrderToVm', () => {
  it('모든 필드가 있는 경우', () => {
    const order = { id: '1', status: 'active', items: [...] };
    expect(mapOrderToVm(order)).toEqual({
      orderId: '1',
      statusText: '진행중',
      itemCount: 3,
    });
  });

  it('optional 필드가 없는 경우', () => {
    const order = { id: '1', status: 'active' };
    expect(mapOrderToVm(order)).toEqual({
      orderId: '1',
      statusText: '진행중',
      itemCount: 0,
    });
  });

  it('null/undefined 입력', () => {
    expect(mapOrderToVm(null)).toEqual(DEFAULT_ORDER_VM);
  });
});
```

---

## 네이밍 컨벤션

```typescript
// describe: 함수명 또는 모듈명
describe('getPeriod', () => {
  // 중첩 describe: 시나리오 그룹
  describe('정상 케이스', () => {
    // it: 구체적인 동작 설명 (한글 권장)
    it('last14Days 옵션은 14일 전부터 오늘까지 반환', () => {});
  });
});
```

---

## 금지 사항

- **구현 상세 의존 금지**: 내부 함수 spy, private 메서드 접근
- **외부 의존성 실제 호출 금지**: API, DB, 파일 시스템
- **테스트 간 상태 공유 금지**: 전역 변수로 테스트 연결
- **하드코딩된 날짜 금지**: `jest.useFakeTimers()` 사용

---

## 테스트 실행

```bash
# test 스크립트 확인
yarn workspace {해당앱} run | rg "^\s+test"

# 단일 파일
yarn workspace {해당앱} test -- --testPathPattern="period.test.ts"

# 전체
yarn workspace {해당앱} test
```

---

## 정책 보호 테스트

리팩토링 시 기존 동작을 보호하는 테스트:

```typescript
// 현재 동작을 "캡처"
describe('기간 필터 정책 (회귀 방지)', () => {
  // 이 테스트가 깨지면 = 정책이 바뀐 것
  // 의도된 변경인지 확인 필요
});
```

---

## 체크리스트

- [ ] 정상 케이스 포함?
- [ ] 경계값 (0, 빈 값, null) 포함?
- [ ] 에러 케이스 포함?
- [ ] 날짜 함수면 `jest.useFakeTimers()` 사용?
- [ ] 정책 관련 함수면 정책 케이스 포함?
