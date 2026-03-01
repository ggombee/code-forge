# Agent Roster

> 프로젝트에 최적화된 전문 에이전트 카탈로그

**모델 선택 기준**: `./coordination-guide.md` 참조 (단일 진실 공급원)

---

## 에이전트 목록

### Tier 1: 탐색/분석 (READ-ONLY)

| 에이전트       | 기본 모델 | 병렬 | 역할                              |
| -------------- | --------- | ---- | --------------------------------- |
| **explore**    | haiku     | ✅   | 코드베이스 탐색, 패턴 분석        |
| **vision**     | sonnet    | ✅   | 이미지, PDF, 다이어그램 분석      |
| **architect**  | opus      | ❌   | 아키텍처 분석, 근거 기반 권장     |
| **analyst**    | opus      | ❌   | 요구사항 분석, 6-Gap 격차 분석    |
| **critic**     | opus      | ❌   | 계획/구현 OKAY/REJECT 판정       |
| **researcher** | sonnet    | ✅   | 외부 문서 조사, 공식 문서 검색    |

### Tier 2: 계획/설계

| 에이전트     | 기본 모델 | 병렬 | 역할                       |
| ------------ | --------- | ---- | -------------------------- |
| **planner**  | opus      | ❌   | 전략적 계획 수립, 태스크 분해 |
| **designer** | sonnet    | ⚠️   | UI/UX 디자인, 컴포넌트 설계  |

### Tier 3: 구현

| 에이전트                    | 기본 모델 | 병렬 | 역할                          |
| --------------------------- | --------- | ---- | ----------------------------- |
| **implementation-executor** | sonnet    | ⚠️   | 코드 구현, 기능 개발          |
| **deep-executor**           | opus      | ❌   | 자율 딥 워크 (탐색→구현→검증) |
| **build-fixer**             | sonnet    | ✅   | 빌드/타입 오류 최소 diff 수정 |
| **lint-fixer**              | haiku     | ✅   | ESLint/Prettier 오류 수정     |

### Tier 4: 검증/운영

| 에이전트                 | 기본 모델 | 병렬 | 역할                          |
| ------------------------ | --------- | ---- | ----------------------------- |
| **code-reviewer**        | sonnet    | ✅   | 코드 품질, 보안, 유지보수성   |
| **security-reviewer**    | sonnet    | ✅   | OWASP Top 10, 시크릿 탐지    |
| **qa-tester**            | sonnet    | ✅   | tmux 기반 서비스/CLI 테스팅   |
| **deployment-validator** | sonnet    | ❌   | 배포 전 typecheck/lint/build  |
| **document-writer**      | haiku     | ✅   | 기술 문서 작성/업데이트       |
| **git-operator**         | haiku     | ❌   | Git 커밋/푸시                 |

> ⚠️ = 병렬 가능하지만 같은 파일 수정 시 순차 실행 필수

---

## 에이전트 상세

### explore

**목적**: 코드베이스 빠른 탐색, 파일 구조 파악

```typescript
// 단순 구조 탐색: haiku
Task(subagent_type="explore", model="haiku", prompt="src 폴더 구조 파악")

// 정책/로직 분석: sonnet
Task(subagent_type="explore", model="sonnet", prompt="필터 disabled 조건 분석")

// 복잡한 비즈니스 로직: opus
Task(subagent_type="explore", model="opus", prompt="날짜 계산 로직 분석")
```

### code-reviewer

**목적**: PR 전 코드 품질 검증

```typescript
Task(subagent_type="code-reviewer", model="sonnet", prompt="변경된 파일 코드 리뷰")
```

**검토 항목**:

| 항목        | 확인                            |
| ----------- | ------------------------------- |
| Import 순서 | 외부 → 내부(@/) → 상대 경로    |
| 상태 관리   | 서버/전역/폼/로컬 경계 분리    |
| 타입 명시   | return type 필수                |

### analyst

**목적**: 요구사항과 현재 구현 사이의 격차를 6-Gap 프레임워크로 분석

```typescript
Task(subagent_type="analyst", model="opus", prompt="주문 관리 기능 요구사항 대비 현재 구현 격차 분석")
```

**6-Gap**: 기능/데이터/UX/성능/품질/보안 각 영역의 격차를 구조화

### critic

**목적**: 계획/구현 결과를 엄격하게 평가하여 OKAY/REJECT 판정

```typescript
Task(subagent_type="critic", model="opus", prompt="이 구현 계획 검토: .claude/plans/current-plan.md")
```

**판정 기준**: 요구사항 충족, 정책 준수, 범위 적절성, 리스크

### implementation-executor

**목적**: 계획된 코드 구현 실행

```typescript
Task(subagent_type="implementation-executor", model="sonnet", prompt="계획대로 구현")
```

**⚠️ 병렬 제한**: 같은 파일 수정 시 순차 실행 필수

### deep-executor

**목적**: 복잡한 작업을 탐색→계획→구현→검증까지 독립 수행

```typescript
Task(subagent_type="deep-executor", model="opus", prompt="주문 상세 페이지 전체 리팩토링")
```

**특징**: 100턴까지 자율 실행, 전체 6단계 사고 모델 적용, Phase 기반 자체 검증

### lint-fixer

**목적**: ESLint/Prettier 오류 자동 수정

```typescript
Task(subagent_type="lint-fixer", model="haiku", prompt="린트 오류 수정")
```

---

## 조합 패턴

### 탐색 → 구현

```typescript
// 1. 탐색 (haiku - 병렬)
Task(subagent_type="explore", model="haiku", prompt="영향 파일 수, 기존 패턴 확인")

// 2. 계획 수립 (opus - 복잡한 경우)
Task(subagent_type="planner", model="opus", prompt="분석 결과 기반 구현 계획")

// 3. 구현 (sonnet)
Task(subagent_type="implementation-executor", model="sonnet", prompt="계획대로 구현")
```

### 구현 → 검증

```typescript
// 병렬 검증
Task(subagent_type="lint-fixer", model="haiku", prompt="린트 수정")
Task(subagent_type="code-reviewer", model="sonnet", prompt="코드 리뷰")
```

---

## 선택 가이드

| 상황                 | 에이전트                     |
| -------------------- | ---------------------------- |
| "이 파일 어디있어?"  | explore (haiku)              |
| "이 기능 구현해줘"   | implementation-executor (sonnet) |
| "이거 통째로 맡겨"   | deep-executor (opus)         |
| "요구사항 분석해줘"  | analyst (opus)               |
| "이 계획 검증해줘"   | critic (opus)                |
| "계획 먼저 세워줘"   | planner (opus)               |
| "코드 리뷰해줘"      | code-reviewer (sonnet)       |
| "보안 검토해줘"      | security-reviewer (sonnet)   |
| "빌드 오류 수정해줘" | build-fixer (sonnet)         |
| "커밋해줘"           | git-operator (haiku)         |
| "배포 준비 확인해줘" | deployment-validator (sonnet) |
| "UI 디자인해줘"      | designer (sonnet)            |
| "문서 업데이트해줘"  | document-writer (haiku)      |

---

## 참조 문서

| 문서                                  | 용도           |
| ------------------------------------- | -------------- |
| `./coordination-guide.md`             | 병렬 실행 원칙 |
| `../validation/forbidden-patterns.md` | 금지 패턴      |
| `../validation/required-behaviors.md` | 필수 행동      |
