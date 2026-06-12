# code-forge 플러그인 개선 계획 (2026-04)

> 궁극적 목표: 플러그인이 설치된 어떤 레포든, 신규개발/QA/버그수정 등 모든 작업이 사람처럼 오차 없이 프로젝트에 맞게 자동화되는 것.

---

## 1. 현재 문제 진단

### 1-1. 스킬 과잉 (21개)

사용자가 뭘 써야 할지 모르고, 실제로 잘 안 쓰는 스킬이 있다.

| 문제 스킬 | 사유 |
|-----------|------|
| `/quality` | hooks(lint-fix.sh + quality-gate.sh)가 이미 동일 기능 수행. `yarn lint && tsc` 직접 실행과 차이 없음 |
| `/bug-fix` | `/start`와 역할 중복. 버그도 Jira 티켓으로 들어오니 `/start`로 처리 |
| `/refactor` | thinking-model GROUND-APPLY-VERIFY로 충분. 정책 보호 테스트는 `/generate-test`가 담당 |
| `/done` | 사용자가 잘 안 씀. 핵심 기능(테스트 판단)은 유용하지만 커밋/PR/Jira는 직접 또는 CI/CD로 처리 |

### 1-2. 토큰 비효율

매 대화마다 alwaysApply rules가 컨텍스트에 로드됨.

| 파일 | 줄 수 | 토큰 (~) | 매 턴 필요? |
|------|-------|---------|------------|
| thinking-model.md | 100줄 | ~2K | ✅ 항상 필요 |
| coding-standards.md | 397줄 | ~6K | ❌ 커밋 컨벤션/환경파일 설명 등은 코드 작성 시에만 필요 |
| session-init.md | 47줄 | ~0.8K | ✅ 초기화 시만 |
| **합계** | **544줄** | **~8.8K** | |

coding-standards.md에서 ~140줄을 reference로 분리하면 **매 턴 ~2K 토큰 절약**.

### 1-3. QA 실수 반복 (2026-04-07 사례)

| # | 실수 패턴 | 현재 시스템에서 안 잡히는 이유 |
|---|----------|----------------------------|
| 1 | PDS 라이브러리 내부 동작 미파악 | 사고모델에 "외부 라이브러리 소스 추적" 규칙 없음 |
| 2 | 컴포넌트 호출처 누락 | 수정 시 자동 grep 없음 |
| 3 | 캐시 무효화 타이밍 | 비동기 순서 검증 체크 없음 |
| 4 | 배열 0/1/N건 미확인 | 경계값 체크 규칙 없음 |
| 5 | QA 스크린샷 vs 코드 대조 안 함 | 기대결과 대조 강제 없음 |
| 6 | 수정 후 자체 검증 없이 전달 | Playwright 확인 루프 없음 |

### 1-4. 테스트 관련 산재

5곳에 분산: `/generate-test`, `/setup-test`, `/e2e`, `/setup-e2e`, testgen 에이전트, policy-check.sh

실제로는 **세팅(1회) / 생성 / 실행**이 분리되어 있어 역할은 명확하지만, "테스트 돌려"에 대한 단일 진입점이 없다.

### 1-5. 슬랙봇/자동화 블로킹

`/start` 8단계 "작업을 시작할까요?"가 사용자 응답 대기 → 슬랙봇에서 블로킹.

### 1-6. 클로드 준수율 편차

| 레이어 | 적용 시점 | 준수율 | 이유 |
|--------|----------|--------|------|
| rules (alwaysApply) | 매 대화 자동 | **높음** | 컨텍스트에 항상 로드 |
| MEMORY.md | 매 대화 자동 | **높음** | 시스템 자동 로드 |
| CLAUDE.md | 매 대화 자동 | **높음** | 프로젝트 인스트럭션 |
| skills | 호출 시만 | **중간** | 호출 안 하면 적용 안 됨 |
| references | @참조 시만 | **낮음** | 스킬이 참조해야 로드 |

→ "항상 적용"되어야 할 규칙은 **스킬이 아니라 rules/MEMORY**에 넣어야 함.

---

## 2. 개선 원칙

### 배치 기준

| 판단 기준 | 배치 레이어 | 예시 |
|-----------|------------|------|
| 사용자가 의식적으로 시작하는 멀티스텝 워크플로우 | **스킬** | /start, /e2e |
| 도구 실행 전후 자동 수행되는 기계적 작업 | **훅** | lint --fix, scope 체크 |
| 모든 코드 작업에 항상 적용되는 사고 습관 | **rules** | GROUND/VERIFY 루프 |
| 여러 스킬에서 참조하는 구체 절차 | **references** | 커밋 컨벤션, PR 템플릿 |
| 프로젝트별 구체 규칙 | **MEMORY.md** | QA 수정 프로토콜 |

### 핵심 원칙

1. **hooks로 강제할 수 있는 것은 hooks로** — 사람이 까먹어도 자동 실행
2. **rules에는 사고 프레임워크만** — 간결하게, 토큰 효율적으로
3. **skills는 고유 워크플로우만** — 다른 레이어로 대체 가능하면 폐지
4. **범용성 유지** — 프론트/백엔드, 어떤 스택이든 동작
5. **슬랙봇 호환** — 블로킹 최소화

---

## 3. 구체적 변경 계획

### 3-1. 스킬 정리 (21개 → 18개)

#### 폐지 (3개)

| 스킬 | 폐지 사유 | 기능 분산 |
|------|----------|----------|
| `/quality` | hooks와 100% 중복 | lint-fix.sh(PostEdit) + quality-gate.sh(Stop)가 이미 수행 |
| `/bug-fix` | /start와 중복 | thinking-model GROUND에 "버그 수정 시 2-3 옵션 제시" 규칙 추가 |
| `/refactor` | thinking-model로 충분 | GROUND에 "리팩토링 시 정책 보호 테스트 먼저" 규칙 추가 |

#### /done 경량화

| 현재 기능 | 유지/이동 |
|-----------|----------|
| 변경 분석 (git status/diff) | **이동** → 커밋 시 시스템 프롬프트가 자동 수행 |
| 테스트 전략 판단 + 실행 | **유지** → /done의 핵심 가치 |
| lint/build 검증 | **이동** → hooks가 자동 수행 |
| 품질 검토 (VERIFY 체크리스트) | **이동** → thinking-model VERIFY |
| 커밋/PR 생성 | **이동** → 커밋 시 직접 처리 |
| design-refs 정리 | **이동** → quality-gate.sh Stop hook |
| Jira 완료 처리 | **제거** → CI/CD에서 처리 |

경량화 후 /done은 **"테스트 전략 판단 + 실행"에만 집중**하는 ~80줄 스킬로.

#### 유지 (18개)

```
핵심 워크플로우 (4개):  /start, /done(경량), /generate-test(alias: /test), /e2e
환경 세팅 (3개, 1회성): /setup, /setup-test, /setup-e2e
운영 도구 (3개):       /my-tickets, /anvil, /setup-ticket-alert
전문 도구 (3개):       /figma-to-code, /research, /codex
VAS (3개):            /vas-build, /vas-create-agent, /vas-verify
유틸리티 (2개):        /debate, /crawler
```

---

### 3-2. 사고모델 (thinking-model.md) 변경

**원칙: 비대화 방지. 현재 100줄 → 110줄 이내.**

#### GROUND에 추가 (조건부 항목, 5줄)

```markdown
- (버그 수정 시) 2-3가지 해결 옵션을 도출하고 사용자에게 제시한다
- (리팩토링 시) 정책 보호 테스트를 먼저 작성한다 (/generate-test 활용)
- (외부 라이브러리 수정 시) node_modules에서 소스를 추적하여 내부 동작을 확인한다
```

#### VERIFY에 추가 (3줄)

```markdown
- [ ] 수정 컴포넌트의 모든 호출처를 grep으로 확인했는가?
- [ ] 배열/복합 데이터의 0건, 1건, N건 렌더링을 확인했는가?
- [ ] UI 변경이면 dev 서버 또는 Playwright로 실제 화면을 확인했는가?
```

#### 에이전트 연계 테이블에 테스트 라우팅 추가 (5줄)

```markdown
| 사용자 의도 | 경로 |
|------------|------|
| "테스트 환경 세팅" | /setup-test (유닛) 또는 /setup-e2e (E2E) |
| "이 파일 테스트 만들어" | /generate-test {파일경로} |
| "E2E 만들어" | /e2e {페이지경로} |
```

---

### 3-3. coding-standards.md 다이어트

**현재 397줄 → ~250줄 (매 턴 ~2K 토큰 절약)**

| alwaysApply 유지 (~250줄) | reference로 분리 (~140줄) |
|--------------------------|--------------------------|
| 핵심 원칙 (KISS/DRY/YAGNI) | 커밋 메시지 컨벤션 (~30줄) |
| TypeScript 표준 (네이밍, 타입) | 환경 파일 설명 (~20줄) |
| Import 순서 | API 서비스 메서드 네이밍 (~30줄) |
| React 패턴 | 쿼리 훅/키 팩토리 패턴 (~50줄) |
| Code Smell 감지 | Prettier 설정 (~10줄) |

분리된 내용 → `references/coding-conventions-detail.md`로 이동. /start, /done에서 `@`참조로 필요 시 로드.

---

### 3-4. hooks 강화

#### quality-gate.sh (Stop hook) — scope 체크 추가

```bash
# 기존: tsc + eslint
# 추가: 변경 파일이 계획 범위를 벗어나는지 체크
PLAN_FILES=$(cat .claude/temp/plan.md 2>/dev/null | grep "^- " | sed 's/^- //')
DIFF_FILES=$(git diff --name-only HEAD 2>/dev/null)

# plan에 없는 파일이 수정되면 경고
for f in $DIFF_FILES; do
  if ! echo "$PLAN_FILES" | grep -q "$f"; then
    echo "⚠️ 계획에 없는 파일 수정됨: $f" >&2
  fi
done
```

#### design-refs 자동 정리 (Stop hook에 추가)

```bash
# 작업 완료 시 design-refs 스크린샷 정리
find . -path "*/.design-refs/*.png" -delete 2>/dev/null
find . -path "*/.design-refs/*.jpg" -delete 2>/dev/null
```

---

### 3-5. /start, /done에 --auto 플래그

**슬랙봇/자동화 호환을 위한 비블로킹 모드.**

#### /start --auto

| 단계 | 일반 모드 | --auto 모드 |
|------|----------|------------|
| Figma MCP 실패 | "/mcp 실행해주세요" 안내 | 스킵 |
| 계획 출력 후 | "작업을 시작할까요?" 대기 | LOW/MED → 자동 Yes, HIGH → 계획만 출력 후 중단 |

#### /done --auto

| 단계 | 일반 모드 | --auto 모드 |
|------|----------|------------|
| 테스트 전략 | 판단 후 실행 | 동일 |
| Jira 완료 | "완료 처리할까요?" 대기 | 스킵 (CI/CD에서 처리) |

---

### 3-6. 프로젝트별 MEMORY에 QA 수정 프로토콜

thinking-model에 넣기엔 프로젝트 의존적인 규칙은 MEMORY.md에.

```markdown
### QA 재요청 수정 프로토콜
- 호출처 전수 확인: grep -rl "ComponentName" apps/ packages/
- PDS 콜백 체인 추적: onClickArrow, onChange 등 내부 흐름 코드로 확인
- 비동기 순서 검증: invalidateQueries → await modal/alert → refetch 순서
- 배열/복합 케이스: 0건/1건/N건 각각 UI 확인
- 기대결과 대조: QA 티켓의 기대결과와 코드 수정 후 1:1 대조
- Playwright 확인 후 전달: 수정 후 브라우저에서 동작 확인 없이 사용자에게 전달 금지
```

---

## 4. 변경 사항 요약

| # | 변경 | 크기 | 효과 |
|---|------|------|------|
| 1 | `/quality` 폐지 | S | 스킬 정리, 중복 제거 |
| 2 | `/bug-fix` 폐지 | S | 스킬 정리, /start로 통합 |
| 3 | `/refactor` 폐지 | S | 스킬 정리, rules로 흡수 |
| 4 | `/done` 경량화 (253줄→~80줄) | M | 테스트 판단에만 집중 |
| 5 | thinking-model.md 보강 (+10줄) | S | QA 실수 방지, 테스트 라우팅 |
| 6 | coding-standards.md 다이어트 (-140줄) | M | 매 턴 ~2K 토큰 절약 |
| 7 | quality-gate.sh scope 체크 추가 | S | VERIFY 자동 강제 |
| 8 | /start, /done에 --auto 플래그 | S | 슬랙봇 블로킹 해소 |
| 9 | /generate-test → /test alias | S | 자연스러운 진입점 |

**총 영향**: 스킬 21→18개, alwaysApply 토큰 ~26% 절감, 기존 워크플로우 breaking change 없음.

---

## 5. 실행 순서

| 순서 | 작업 | 의존성 |
|------|------|--------|
| 1 | `/quality`, `/bug-fix`, `/refactor` 폐지 | 없음 |
| 2 | thinking-model.md GROUND/VERIFY 보강 | 1 이후 (bug-fix/refactor 규칙 흡수) |
| 3 | coding-standards.md 다이어트 | 없음 (독립) |
| 4 | `/done` 경량화 | 없음 (독립) |
| 5 | quality-gate.sh scope 체크 추가 | 없음 (독립) |
| 6 | /start, /done에 --auto 플래그 | 4 이후 |
| 7 | /generate-test → /test alias | 없음 (독립) |

2, 3, 4, 5는 독립적이므로 **병렬 진행 가능**.

---

## 6. 평가 기준

변경 후 아래 지표로 효과를 측정:

| 지표 | 현재 | 목표 |
|------|------|------|
| QA 재요청 시 재수정 횟수 | 평균 2-3회 | 1회 |
| alwaysApply 토큰 | ~8.8K | ~6.8K |
| 스킬 수 | 21개 | 18개 |
| 슬랙봇 블로킹 포인트 | 2개 | 0개 (--auto 시) |
| "테스트 돌려" → 올바른 경로 도달 | 불명확 | 라우팅 테이블로 명확 |

---

## 7. 개선 후 평가 계획

### 7-1. 각 변경별 검증 방법

| 변경 | 검증 방법 | 성공 기준 |
|------|----------|----------|
| 스킬 폐지 (quality/bug-fix/refactor) | 2주간 사용자가 해당 스킬 필요성을 느끼는지 모니터링 | 요청 0건 |
| thinking-model 보강 | 다음 QA 재요청 처리 시 실수 패턴 재발 여부 | 6가지 실수 중 재발 0건 |
| coding-standards 다이어트 | 분리 후 코드 품질 저하 없는지 lint/tsc 결과 비교 | 에러 증가 0건 |
| /done 경량화 | 테스트 판단 정확도 유지되는지 | 기존과 동일 |
| quality-gate scope 체크 | 의도하지 않은 파일 수정 감지율 | false positive < 10% |
| --auto 플래그 | 슬랙봇에서 end-to-end 실행 성공률 | 95%+ |

### 7-2. 전체 시스템 회귀 테스트

변경 적용 후 아래 시나리오를 실제 수행하여 회귀 확인:

```
시나리오 1: 신규 개발
  /my-tickets → 티켓 선택 → /start TICKET → 구현 → 커밋 → PR
  체크: /start가 정상 동작, 커밋 컨벤션 준수, 테스트 라우팅 제안

시나리오 2: QA 재요청 수정
  /start QA-XXXXX → 분석 → 수정 → Playwright 확인 → 커밋
  체크: VERIFY에서 호출처/배열/비동기 체크 실행, 자체 검증 후 전달

시나리오 3: 슬랙봇 자동화
  /start TICKET --auto → 자동 분석 → 자동 구현 → /done --auto
  체크: 블로킹 없이 완료, Draft PR 생성

시나리오 4: E2E 테스트 생성
  /e2e /orders → Forge Loop → spec 생성 → 실행
  체크: 테스트 라우팅 테이블 참조하여 올바른 경로 진입

시나리오 5: 리팩토링 (스킬 폐지 후)
  사용자: "이 컴포넌트 리팩토링해줘"
  체크: thinking-model GROUND에서 정책 보호 테스트 먼저 제안
```

### 7-3. 토큰 효율 측정

```
Before: alwaysApply 합계 ~544줄 (~8.8K 토큰)
After:  alwaysApply 합계 ~402줄 (~6.8K 토큰)

측정 방법: 동일 작업을 변경 전/후로 수행하여
  - 총 토큰 사용량 비교
  - 응답 품질(정확도) 비교
  - 사고모델 준수율 비교 (GROUND/VERIFY 실행 빈도)
```

### 7-4. 지속적 개선 루프

```
변경 적용 → 2주 운용 → 메트릭 수집 → 평가 → 다음 개선
                                    ↑              ↓
                                    └──── 피드백 ←──┘
```

수집할 메트릭:
- QA 재요청 시 재수정 횟수
- 사용자가 폐지된 스킬을 요청한 횟수
- thinking-model VERIFY 체크리스트 실행 빈도
- hooks false positive 비율
- 슬랙봇 --auto 성공률