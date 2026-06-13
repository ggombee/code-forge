---
name: start
description: MD 파일 또는 텍스트로 작업을 정의하면, 분석 → 디자인 확인 → 구현 → 검증 → 커밋 → PR까지 전체 플로우를 수행한다. "이거 만들어줘", "기능 구현해줘", "작업 시작하자", "이 티켓 진행해줘" 등 코드 작업 착수 발화에 사용.
category: workflow
---

# /start — 작업 시작부터 완료까지

> **참조:** 구현 시 `rules/build-guide.md`, 완료 후 검증 시 `rules/review-guide.md`

MD 파일 또는 자유 텍스트로 작업을 정의하면, 분석 → 디자인 → 구현 → 검증 → 커밋 → PR까지 전체 플로우를 수행한다.

**[즉시 실행]** 이 메시지를 받으면 아래 흐름을 바로 실행하세요.

**작업 내용**: $ARGUMENTS

**`--auto` 모드** (슬랙봇/Channels/Remote Control 호환, 비블로킹):
- `$ARGUMENTS`에 `--auto`가 포함되면 아래 동작:
  - Figma MCP 실패 시: 안내 없이 스킵
  - 디자인 확인 단계: MCP 실패면 스킵
  - 구현 시작 확인(8단계): LOW/MEDIUM 복잡도 → 자동 Yes / HIGH → 계획만 출력 후 중단
  - AskUserQuestion 사용 최소화

**참조 규칙**:

- `@${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/coordination-guide.md` (병렬 실행)
- `@${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/agent-roster.md` (에이전트 선택)
- `@${CLAUDE_PLUGIN_ROOT}/rules/thinking-model.md` (GROUND→APPLY→VERIFY)

---

## 옵션

| 옵션 | 설명 | 예시 |
|------|------|------|
| (없음) | 전체 플로우 (분석→구현→검증→커밋→PR) | `/start feature.md` |
| `--auto` | 비블로킹 모드 (슬랙봇/Channels 호환) | `/start TICKET-123 --auto` |
| `--plan-only` | 분석+계획만 출력하고 멈춤 | `/start feature.md --plan-only` |
| `--no-design` | 디자인 분석 스킵 | `/start "API 엔드포인트 추가" --no-design` |
| `--skip-test` | 테스트 스킵 | `/start style-fix.md --skip-test` |
| `--draft` | Draft PR로 생성 | `/start feature.md --draft` |
| `--no-pr` | 커밋만, PR 생성 안 함 | `/start hotfix.md --no-pr` |

---

## Flow CLI 자동 호출 계약 (2026-05-19 redesign G5)

`/start`는 각 Phase에서 [flow-toolkit](https://github.com/ggombee/flow-toolkit)의 `flow` CLI를 자동 호출하여 5-family 통합을 완성한다. `command -v flow` 실패 시 graceful skip (해당 Phase 본 작업은 정상 진행, flow 호출만 스킵).

| Phase | flow 명령 | 효과 |
|---|---|---|
| 1 (티켓 ID 감지) | `flow workflow start <ticket> --json` | `~/.flow/projects/{repo}/workflows/{id}/state.json` 생성. Codex/Cursor 이어받기 기반 |
| 1-2 (BE URL 감지) | `flow spec capture <URL> --redact --json` | `.policy/api-specs/{endpoint}.md` 생성. type 정의 전 응답 우선 |
| 3 (정책 매트릭스) | `flow tc select <ticket> --json` 또는 `flow policy diff <ticket>` | 영향 TC + 변경 컴포넌트 자동 식별 |
| 5 (검증) | `flow run report` + `flow tc verify --stale` + `flow policy lint` | 사이클 결과 + 메타데이터 stale 검증 |
| 7 (회고) | ~~`flow retro`~~ → `forge whet --draft` | 3회+ 반복 패턴 감지 → 규칙 초안 (2026-06-12 교체 — flow 휴면 의존 제거, §7-1) |

자연어 입력에 티켓 ID 패턴(`[A-Z]+-\d+`) 매칭 시 `hooks/auto-flow-trigger.sh` (UserPromptSubmit hook)가 모델 자율 의존 없이 `flow workflow start` / `flow tc select` 강제 호출.

계약: [`docs/contracts/INTEGRATION.md` §4](../../docs/contracts/INTEGRATION.md), [auto-trigger.md](../../../flow-toolkit/packages/flow-rules/docs/auto-trigger.md).

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

### 3-1. 병렬 코드 탐색 (복잡도 조건부 — 2026-06-12 §4-6 사용자 결정)

명백한 LOW(1개 파일, 스타일/텍스트 변경이 요구사항에서 자명)는 **scout 생략**하고 대상 파일 직접 Read. 그 외에는 scout 병렬:

```typescript
Task(subagent_type = 'scout', model = 'haiku', prompt = '변경 대상 영역 구조 분석');
Task(subagent_type = 'scout', model = 'haiku', prompt = '기존 패턴 및 컨벤션 분석');
Task(subagent_type = 'scout', model = 'haiku', prompt = '관련 유틸/서비스/훅 파악');
```

HIGH(§3-3)면 Plan 에이전트가 **필수** — 스폰 생략 금지. (LOW 생략/MEDIUM+ 병렬/HIGH 필수 — 비용은 복잡도에 비례하게)

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

> 위 표가 복잡도 기준의 **유일본** (2026-06-12 단일화 — 구 `references/complexity-judgment.md`는 폐지 스킬 기준 포함이라 `archive/references/`에 통째 보존).

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

### 3-3b. 라우팅 권고 + 기록 (2026-06-12, 마스터플랜 4단계)

복잡도 판단 직후 1회, [`references/routing-policy.md`](../../references/routing-policy.md) §5 표로 effort 권고를 정하고 route.json에 기록한다.

| complexity | effort 권고 | codex reasoning_effort |
|---|---|---|
| LOW | low | low |
| MEDIUM | medium (패턴 불명확 시 high) | medium |
| HIGH | high (새 아키텍처면 xhigh) | high |

```bash
# deep-merge라 quality-gate의 last_gate 등 다른 producer 필드를 지우지 않음 (event-schema.md §1)
echo '{"complexity":"{LOW|MEDIUM|HIGH}","effort_level":"{권고값}","producer":"/start"}' \
  | "${CLAUDE_PLUGIN_ROOT}/bin/forge" emit-event 2>/dev/null || true
```

- **권고 전용** — 메인 세션 effort는 시스템이 못 바꾼다 (/effort는 사용자 전용). 서브에이전트 티어 핀과 codex `reasoning_effort`만 실제 레버.
- 권고는 §3-4 계획 출력의 '라우팅(권고)' 행으로 사용자에게 표시 — 적용 여부는 사용자 선택.

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

### 라우팅 (권고)
- 복잡도 {LOW|MEDIUM|HIGH} → effort {권고값} (적용은 사용자 선택 — /effort)

### 검증 방법
- {테스트 전략}
```

> 계획이 크면(HIGH + 변경 파일 5개+) 체크포인트 A에서 "/handoff로 세션 분리" 옵션을 한 줄 제안.

### 3-5. progress.md append (작업 이어가기 + 의사결정 누적, 2026-05-17 redesign G3, 2026-05-20 G3.5 확장)

체크포인트 A 진행 전, `.claude/state/progress.md`에 ticket entry append. 세션 끊겨도 다음 세션이 `session-init.sh`로 자동 복원.

**기본 (항상 기록)**:
```bash
mkdir -p .claude/state
cat >> .claude/state/progress.md <<EOF

## {ticket-id 또는 작업 제목} — $(date -u +%FT%H:%MZ)

**phase**: ANALYZE (Phase 3 완료, 체크포인트 A 대기)
**files (예정)**: [{변경 파일 목록 — 위 §3-4의 변경 파일}]
**next**: 사용자 승인 후 Phase 4 구현 → Phase 5 검증

EOF
```

**옵션 (모호함 발견 시에만 추가 append)** — implementation-notes 패턴:

```markdown
### 설계 결정
- {명세가 모호해서 자율 판단한 사항 + 이유}

### 편차
- {의도적으로 명세 안 따른 부분 + 이유}

### 트레이드오프
- {고려한 대안들 + 현재 방식 선택 이유}

### 미결 질문 ⚠️
- {사용자 답변/확인 필요한 사항}
```

→ 4섹션 모두 **옵션**. LOW 복잡도 작업은 phase만 기록, 4섹션 스킵.
→ 미결 질문은 `⚠️` 마커로 — session-init이 노출 시 사용자가 즉시 인지.
→ 이후 Phase 4 시작 / Phase 5 통과 / Phase 6 커밋 시점에도 phase 한 줄 update.

계약: `docs/contracts/state-schema.md` §5.

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

### 5-0. flow CLI 자동 호출 (redesign G5, 2026-05-19)

빌드/린트/타입 검증 전후로 flow-toolkit의 사이클 보고 + 메타데이터 검증을 명시 호출 (위 §"Flow CLI 자동 호출 계약" 참조):

```bash
# flow CLI 설치 시에만 실행. 미설치 환경 graceful skip.
if command -v flow >/dev/null 2>&1; then
  flow run report --cycle "$CYCLE" 2>/dev/null || true       # 사이클 결과 → .policy/runs/{cycle}/report.md
  flow tc verify --stale --json 2>/dev/null || true         # affects.components 메타데이터 stale 확인
  flow policy lint --json 2>/dev/null || true               # .policy/*.json schema 검증
fi
```

→ `.policy/` 디렉토리 없는 프로젝트는 flow가 알아서 스킵. 작업 정보 손실 없음.

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

### 7-1. Whetstone 회고 스캔 (2026-06-12 마스터플랜 5단계 — 구 flow retro 교체)

작업 사이클 종료 시 quality.jsonl 반복 패턴을 규칙 초안으로. flow CLI 없이 돌고(휴면 의존 제거), **채택은 사람이**:

```bash
"${CLAUDE_PLUGIN_ROOT}/bin/forge" whet --draft 2>/dev/null || true
```

→ quality.jsonl 없으면 graceful skip. 신규 초안이 생기면 완료 보고에 "규칙 초안 N건 대기 (/forge-status로 확인)" 1줄 포함.

> 구 `flow retro` 호출(redesign G5)은 flow CLI 미설치로 영구 no-op이었음 — 마스터플랜 §3 "flow CLI 켜기" 보류 결정에 따라 Whetstone이 회고 골격을 대신한다.

### 7-2. progress.md 정리 prompt (redesign G3.5c, 2026-05-20)

작업 완료 시 사용자에게 progress.md 정리 의향 묻기. 자동 archive로 히스토리 보존 + 활성 진행 목록 깨끗 유지.

**모델 행동**:
1. `.claude/state/progress.md`에 현 ticket 블록 존재 확인.
2. 존재 시 사용자에게 자연어로 prompt:

> 🎯 **{ticket-id}** 완료. progress.md에서 정리할까요?
> - Yes: 해당 블록을 `.claude/state/progress-archive.md`로 이동 (히스토리 보존)
> - No: progress.md에 그대로 유지 (나중에 다시 참조 가능)

3. **Yes**:
   ```bash
   mkdir -p .claude/state
   # 1. archive에 append (히스토리)
   awk -v t="{ticket-id}" 'BEGIN{p=0} /^## /{p=($0 ~ t)} p' \
     .claude/state/progress.md >> .claude/state/progress-archive.md
   # 2. progress.md에서 제거 (다음 동급 헤더까지)
   awk -v t="{ticket-id}" 'BEGIN{skip=0} /^## /{skip=($0 ~ t)} !skip' \
     .claude/state/progress.md > /tmp/progress.tmp && \
     mv /tmp/progress.tmp .claude/state/progress.md
   ```
4. **No**: 스킵.

**원칙**:
- 사용자 명시 동의 후에만 정리 (자동 삭제 금지 — 정보 보존 가이드라인).
- archive 파일은 10MB 초과 시 `.old.md`로 앞쪽 절반 회전 (삭제 아님 — 완전 히스토리 보존, session-init GC, 2026-06-14).
- 미결 질문(`⚠️`)이 남아있는 ticket은 prompt 시 **경고 추가**: "미결 질문 N개 있음 — 정리 전 확인하세요".

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
| `/test` | 테스트 통합 진입점 (유닛/E2E/세팅 자동 라우팅) | 구현 없이 테스트만 돌릴 때 |
| `/e2e` | 화면 단위 E2E 자동화 (Forge Loop) | 페이지 단위 자동 테스트 |
| `/handoff` | 세션 핸드오프 (progress.md + 킥오프 프롬프트) | 계획이 크거나 컨텍스트가 찼을 때 |
| `/figma-to-code` | Figma 전용 변환 | Emotion 기반 코드 생성 |

> 구 `/done` `/quality`는 v4.0 폐지 — 대체 매핑은 `docs/CATALOG.md`.
