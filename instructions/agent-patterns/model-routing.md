# Model Routing Guide

> 작업 복잡도에 따라 최적의 모델 선택

---

## 모델 선택 기준

| 모델 | 복잡도 | 비용 | 속도 | 사용 시점 |
|------|--------|------|------|----------|
| **haiku** | LOW | $ | 최고 | 간단한 작업 |
| **sonnet** | MEDIUM | $$ | 중간 | 일반 작업 (기본값) |
| **opus** | HIGH | $$$ | 낮음 | 복잡한 작업 |

---

## Haiku 사용 케이스

| 작업 유형 | 예시 |
|----------|------|
| 파일 탐색 | 코드베이스 구조 분석, 파일 찾기 |
| 린트/포맷 수정 | prefer-const, no-unused-vars |
| 단순 검색 | Glob, Grep 작업 |
| Git 작업 | 커밋, 푸시 (로직 없음) |

**복잡도 기준:** 1-3개 파일, 로직 변경 없음, 단순 CRUD

---

## Sonnet 사용 케이스

| 작업 유형 | 예시 |
|----------|------|
| 기능 구현 | 컴포넌트, 훅, API 연동 |
| 버그 수정 | 로직 오류, 타입 에러 |
| 코드 리뷰 | 품질, 패턴, 규칙 준수 |
| 테스트 작성 | BDD 시나리오, 정책 보호 |
| 리팩토링 | 코드 구조 개선 |

**복잡도 기준:** 4-10개 파일, 중간 복잡도 로직

---

## Opus 사용 케이스

| 작업 유형 | 예시 |
|----------|------|
| 아키텍처 설계 | 시스템 구조, 기술 선택 |
| 요구사항 분석 | 갭 분석, 범위 정의 |
| 복잡한 디버깅 | 다층 스택 이슈 |
| 비즈니스 정책 분석 | 날짜 계산, 가격 로직 |

**복잡도 기준:** 10개+ 파일, 아키텍처 수준 변경, 보안/성능 중요

---

## 비즈니스 정책 = 상향 조정

| 정책 키워드 | 최소 모델 | 이유 |
|------------|----------|------|
| `getPeriod`, `addDate`, 날짜 계산 | **opus** | 비즈니스 규칙 복잡 |
| `disabled`, `readonly` 조건 | **sonnet** | 상태 의존성 |
| `filterState`, 필터 조건 | **sonnet** | 연쇄 영향 |
| 가격, 할인, 계산 로직 | **opus** | 정확성 중요 |

---

## 복잡도 판단 흐름

```
작업 시작
  ↓
파일 수: 1-3개? → haiku / 4-10개? → sonnet / 10개+? → opus
  ↓
로직: 단순 CRUD? → haiku / 일반? → sonnet / 아키텍처? → opus
  ↓
정책 키워드 포함? → sonnet 이상으로 상향
  ↓
보안/성능 중요? → opus
```

---

## Agent별 권장 모델

| Agent | 기본 모델 | 복잡할 때 |
|-------|----------|----------|
| explore | haiku | sonnet |
| analyst | opus | opus (항상) |
| architect | opus | opus (항상) |
| researcher | sonnet | sonnet |
| code-reviewer | sonnet | opus |
| security-reviewer | sonnet | opus |
| refactor-advisor | sonnet | opus |
| lint-fixer | haiku | sonnet |
| build-fixer | sonnet | sonnet |
| testgen | sonnet | sonnet |
| tdd-guide | sonnet | sonnet |
| implementor | sonnet | opus |
| deep-executor | sonnet | opus |
| codex | sonnet | opus |
| git-operator | sonnet | sonnet |

---

## 비용 최적화 전략

1. **탐색은 항상 haiku** (explore)
2. **구현은 기본 sonnet** (implementor, deep-executor)
3. **분석/설계만 opus** (analyst, architect, Plan)
4. **정책 관련 → 무조건 상향**

**예상 비용 절감:** 40-60%
