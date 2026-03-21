---
name: start
description: MD 파일 또는 텍스트로 작업을 정의하면, 분석 → 디자인 확인 → 구현 → 검증 → 커밋 → PR까지 전체 플로우를 수행한다.
category: workflow
---

# /start — 작업 시작부터 완료까지

MD 파일 또는 자유 텍스트로 작업을 정의하면, 분석 → 디자인 → 구현 → 검증 → 커밋 → PR까지 전체 플로우를 수행한다.

**[즉시 실행]** 이 메시지를 받으면 아래 흐름을 바로 실행하세요.

**작업 내용**: $ARGUMENTS

**참조 규칙**:

- `@../instructions/multi-agent/coordination-guide.md` (병렬 실행)
- `@../instructions/multi-agent/agent-roster.md` (에이전트 선택)
- `@${CLAUDE_PLUGIN_ROOT}/rules/thinking-model.md` (GROUND→APPLY→VERIFY)

---

## 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| (없음) | 전체 플로우 (분석→구현→검증→커밋→PR) | `/start feature.md` |
| `--plan-only` | 분석+계획만 출력하고 멈춤 | `/start feature.md --plan-only` |
| `--no-design` | 디자인 분석 스킵 | `/start "API 엔드포인트 추가" --no-design` |
| `--skip-test` | 테스트 스킵 | `/start style-fix.md --skip-test` |
| `--draft` | Draft PR로 생성 | `/start feature.md --draft` |
| `--no-pr` | 커밋만, PR 생성 안 함 | `/start hotfix.md --no-pr` |

---

## Phase 1: 입력 분석

### 1-1. 입력 판별

| 패턴 | 판별 | 처리 |
|------|------|------|
| `.md` 확장자 | MD 파일 | 파일 읽기 + front-matter 파싱 |
| `.pen` 확장자 | Pencil 파일 | Pencil MCP로 열기 |
| `figma.com/design/` URL | Figma 링크 | URL에서 fileKey/nodeId 추출 |
| 그 외 | 자유 텍스트 | 그대로 요구사항으로 사용 |

### 1-2. MD 파일 구조 (권장)

```markdown
---
title: 로그인 페이지
figma: https://figma.com/design/{fileKey}?node-id={nodeId}
pencil: design/login.pen
---

## 요구사항
- 이메일/비밀번호 로그인
- 소셜 로그인 (Google, GitHub)

## 수용 조건
- [ ] 이메일 유효성 검사
- [ ] 에러 메시지 표시
```

추출 정보: `title`, `figma`, `pencil`, 요구사항, 수용 조건

### 1-3. 프로젝트 구조 파악

```bash
ls -la
cat package.json | head -30
```

- 프로젝트 루트 구조
- 패키지 매니저 (lock 파일로 판단)
- 빌드/린트/테스트 명령어
- profile.json이 있으면 스택 정보 참조

---

## Phase 2: 디자인 분석

> `--no-design` 옵션이거나 디자인 링크가 없으면 **이 Phase 전체를 스킵**.

### 2-1. 디자인 도구 감지 및 분석

**Pencil (.pen 파일 또는 Pencil URL):**

```
mcp__pencil__get_editor_state()      → 현재 상태
mcp__pencil__open_document(path)     → 파일 열기
mcp__pencil__batch_get(patterns)     → 노드 구조 탐색
mcp__pencil__snapshot_layout()       → 레이아웃 확인
mcp__pencil__get_screenshot()        → 시각적 확인
```

Pencil MCP 미연결 시:
→ "Pencil에서 PNG/PDF로 내보내기 후 이미지 경로를 알려주세요" 안내
→ 이미지 제공 시 vision 에이전트로 분석

**Figma (URL):**

```
URL 파싱: https://figma.com/design/{fileKey}/?node-id={nodeId}
  → nodeId 하이픈(-)을 콜론(:)으로 변환

MCP 호출 순서:
  1. get_metadata   → 구조/스타일/컴포넌트
  2. get_screenshot → 시각적 확인 (MEDIUM 이상)
  3. get_design_context → 코드 변환 시 (HIGH)
```

Figma MCP 미연결 시 → REST API fallback:

```bash
if [ -z "$FIGMA_TOKEN" ]; then
  echo "Figma 분석을 위해 다음 중 하나가 필요합니다:"
  echo "  1. Figma MCP 설정 (.mcp.json)"
  echo "  2. FIGMA_TOKEN 환경변수"
  echo "  3. Figma에서 PNG 내보내기 후 경로 제공"
  exit 0
fi
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/images/${FILE_KEY}?ids=${NODE_ID}&format=png&scale=2"
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/${FILE_KEY}/nodes?ids=${NODE_ID}&depth=5"
```

**이미지 파일 (PNG/JPG/PDF):**

```typescript
Task(subagent_type = 'vision', model = 'sonnet',
  prompt = '이 디자인 이미지를 분석: 레이아웃, 컴포넌트, 색상, 간격, 상태별 스타일');
```

### 2-2. 복잡도별 분석 깊이

| 복잡도 | 디자인 분석 범위 | MCP 호출 |
|--------|-----------------|----------|
| LOW (1파일, 스타일 변경) | 스크린샷만 확인 | get_screenshot |
| MEDIUM (2-5파일) | 구조 + 스크린샷 | get_metadata → get_screenshot |
| HIGH (5+파일, 새 화면) | 전체 분석 | get_metadata → get_screenshot → get_design_context |

### 2-3. 디자인 분석 체크리스트

- [ ] 전체 레이아웃 (flex/grid, gap, padding)
- [ ] 주요 컴포넌트 목록
- [ ] 색상 팔레트 (semantic color / hex)
- [ ] 타이포그래피 (size, weight, line-height)
- [ ] 상태별 스타일 (기본/hover/active/disabled/selected)
- [ ] 반응형 동작 (있는 경우)

---

## Phase 3: 코드 분석 + 계획

### 3-1. 병렬 코드 탐색

```typescript
Task(subagent_type = 'scout', model = 'haiku', prompt = '변경 대상 영역 구조 분석');
Task(subagent_type = 'scout', model = 'haiku', prompt = '기존 패턴 및 컨벤션 분석');
Task(subagent_type = 'scout', model = 'haiku', prompt = '관련 유틸/서비스/훅 파악');
```

### 3-2. 디자인 vs 코드 비교 (디자인 분석이 있을 때)

| 항목 | 디자인 | 코드 | 일치 |
|------|--------|------|:----:|
| {항목} | {값} | {값} | O/X |

**불일치 = 반드시 작업 내용에 포함**

### 3-3. 복잡도 판단

| 복잡도 | 기준 | 전략 |
|--------|------|------|
| **LOW** | 1개 파일, 스타일/텍스트 변경 | 바로 구현 |
| **MEDIUM** | 2-5개 파일, 기존 패턴 | 패턴 확인 후 구현 |
| **HIGH** | 5개+ 파일, 새 아키텍처 | Plan 에이전트 호출 |

HIGH 복잡도 시:
```typescript
Task(subagent_type = 'Plan', model = 'opus', prompt = `
  작업: {제목}
  요구사항: {요약}
  디자인: {분석 결과}
  기존 패턴: {확인된 패턴}
  구현 계획 수립 요청
`);
```

### 3-4. 작업 계획 출력

```markdown
## 작업: {제목}

### 디자인
{Figma/Pencil URL 또는 "없음"}

### 분석 결과
- {레이아웃, 컴포넌트, 패턴}

### 작업 내용
1. {할 일 1}
2. {할 일 2}

### 변경 파일
- {파일 목록}

### 검증 방법
- {테스트 전략}
```

---

## 진행 방식: 자동 + 확인 질문

**사용자가 각 스킬을 수동으로 호출할 필요 없다.** Claude가 각 Phase를 자동으로 진행하되, 주요 전환점에서 확인 질문을 한다. 사용자가 "Y" 또는 자연어로 동의하면 다음 Phase로 넘어간다.

```
Phase 1-3 → 자동 실행 (분석은 확인 불필요)
  ↓
"계획이 맞나요? 구현을 시작할까요?" ← 체크포인트 A
  ↓ Y
Phase 4 → 자동 실행 (구현)
  ↓
Phase 5 → 자동 실행 (검증+테스트)
  ↓
"검증 통과했습니다. 커밋하고 PR 올릴까요?" ← 체크포인트 B
  ↓ Y
Phase 6-7 → 자동 실행 (커밋+PR+보고)
```

> `--plan-only` 옵션이면 체크포인트 A에서 종료.
> `--no-pr` 옵션이면 커밋만 하고 PR 스킵.

---

## Phase 4: 구현

체크포인트 A에서 사용자 동의 후 진행.

계획에 따라 코드를 구현한다.

- GROUND에서 관찰한 기존 패턴을 따른다
- 기존 코드와 일관된 스타일 유지
- 디자인 분석 결과와 일치하도록 구현

---

## Phase 5: 검증 + 테스트

구현 완료 후 **자동으로** 검증을 시작한다. 사용자 확인 불필요.

### 5-1. 변경 내용 분석

```bash
git diff
```

변경된 파일 목록과 주요 내용을 파악한다.

### 5-2. 테스트 전략 판단

> 이 기준표는 실패 경험에서 축적된 것. 반드시 따른다.

**변경 파일 분류:**

| 경로 패턴 | 분류 | 테스트 도구 |
|-----------|------|------------|
| `components/`, `views/`, `hooks/` | 컴포넌트/훅 | **assayer 에이전트** |
| `utils/`, `helpers/`, `lib/` | 순수 함수 | **Claude 직접 작성** |
| `styled.ts`, `constants.ts`, `types.ts` | UI/타입 | 스킵 |

**정책 영향 판단:**

| 변경 내용 | 테스트 전략 | 도구 |
|-----------|------------|------|
| 필터/검색 UI 변경 | 통합 테스트 | **assayer** |
| disabled/readonly 조건 변경 | 통합 테스트 | **assayer** |
| 새 UI 상태 추가 | BDD 시나리오 | **assayer** |
| 날짜/기간/가격 계산 변경 | 유닛 테스트 | **Claude 직접** |
| 상태 전이 로직 변경 | 유닛 테스트 | **Claude 직접** |
| 텍스트/라벨/스타일 변경 | 스킵 | - |

> `--skip-test` 옵션이면 이 단계를 건너뛴다. 단, 정책 영향이 감지되면 경고를 출력한다.

### 5-3. 테스트 실행

**컴포넌트/훅 + 정책 영향 → assayer:**
```typescript
Task(subagent_type = 'assayer', prompt = `targetPath: {대상} mode: create`);
```

**순수 함수 + 정책 영향 → Claude 직접:**
대상 파일 분석 → `__tests__/{파일명}.test.ts` 생성 → 실행

**기존 테스트 있음 → 실행만:**
```bash
yarn test  # 또는 npm test, pnpm test
```

### 5-4. 코드 검증 (병렬 실행)

```typescript
Task(subagent_type = 'lint-fixer', model = 'haiku', prompt = '린트 오류 수정');
```

```bash
# 빌드/타입 체크
yarn build  # 또는 npm run build
```

### 5-5. 품질 게이트

> 이 게이트를 통과해야만 커밋으로 진행한다.

- 구현이 요구사항과 정확히 맞는가?
- 잠재 버그/보안 이슈는 없는가?
- 회귀나 사이드 이펙트는 없는가?
- 재사용 가능한 기존 코드를 활용했는가?
- 불필요 코드가 정리됐는가?
- **"지금 배포 가능한가?"** — 근거로 답할 수 있는가?

**하나라도 FAIL이면 커밋/PR 진행 금지. 수정 후 5-4부터 재검증.**

### 5-6. 검증 실패 시

테스트 실패 또는 lint/build 에러가 있으면:
1. 에러 원인 분석
2. 자동 수정 시도
3. 재검증 (5-4부터)
4. 3회 실패 시 사용자에게 상황 보고 + 도움 요청

---

## 체크포인트 B: 커밋 확인

Phase 5 품질 게이트 통과 후:

```
검증이 완료되었습니다.

  lint:  PASS
  build: PASS
  test:  PASS (assayer으로 3개 생성)

커밋하고 PR을 올릴까요? [Y/n]
```

→ Y: Phase 6으로 진행
→ N: 추가 수정 후 Phase 5 재실행

---

## Phase 6: 커밋 + PR

### 6-1. 커밋

```bash
# git add . 금지! 수정한 파일만 명시적으로 add
git add {변경 파일 1} {변경 파일 2}
```

**커밋 메시지:**

```
{type}: {변경 내용 요약}

- {세부 변경 1}
- {세부 변경 2}
```

- type: `feat` / `fix` / `refactor` / `style` / `test` / `docs` / `chore`
- 최근 커밋 메시지 스타일(`git log --oneline -5`)과 일관되게

### 6-2. PR 생성

> `--no-pr` 옵션이면 스킵.

```bash
git push -u origin $(git branch --show-current)

gh pr create \
  --title "{type}: {제목}" \
  --body "$(cat <<'EOF'
## Summary
- {변경 내용}

## Test plan
- [ ] lint/build 통과
- [ ] {테스트 결과}

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

> `--draft` 옵션이면 `--draft` 플래그 추가.
> `gh` CLI 없으면: push 후 PR URL 수동 안내.

---

## Phase 7: 완료 보고

```markdown
## 작업 완료: {제목}

### 검증 결과
- [x] lint 통과
- [x] build 통과
- [x] 테스트 {통과/스킵 (사유)}

### 커밋
- {해시}: {메시지}

### PR
- {PR URL}
```

---

## 전체 플로우 요약

```
/start feature-login.md

Phase 1-3: 자동 실행
  → 입력 분석 → 디자인 분석 → 코드 분석 → 계획 출력

  ── 체크포인트 A: "구현 시작할까요?" ──

Phase 4: 자동 실행
  → 구현

Phase 5: 자동 실행
  → 테스트 전략 판단 → 테스트 → lint/build → 품질 게이트
  (실패 시 자동 수정 → 재검증, 3회 실패 시 사용자에게 보고)

  ── 체크포인트 B: "커밋하고 PR 올릴까요?" ──

Phase 6-7: 자동 실행
  → 커밋 → PR → 완료 보고
```

---

## 관련 스킬 (독립 사용 가능)

| 스킬 | 용도 | 단독 사용 시 |
|------|------|-------------|
| `/done` | 검증+커밋+PR | 이미 구현 끝났을 때 |
| `/quality` | lint/build 검증 | `--lint-only` 등 부분 검증 |
| `/commit` | 커밋만 빠르게 | staged 분석 → 커밋 |
| `/figma-to-code` | Figma 전용 변환 | Emotion 기반 코드 생성 |
