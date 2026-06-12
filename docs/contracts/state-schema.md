# code-forge State Schema v1

> `.claude/state/` 하위 파일들의 **계약 명세**. 여기 명시된 포맷/수명주기가 code-forge ↔ forge-glow ↔ 외부 도구 간의 공식 인터페이스입니다.
>
> 이 문서에 없는 파일은 내부 구현 세부이므로 외부 도구가 읽어서는 안 됩니다.

---

## 버전

| ver | 날짜 | 변경 |
|-----|-----|------|
| 1.0 | 2026-04-14 | 초기 명세 |
| 1.1 | 2026-05-17 | §5 progress.md 신설 (G3), G3.5 4섹션 확장 |
| 1.2 | 2026-06-12 | §6 route.json 신설 (HYBRID transport — event-schema.md §1). schema_version은 "1" 유지 (v1-additive) |

버전이 올라가면 `.claude/state/schema-version` 파일에 숫자 기록.

---

## 디렉토리 구조

```
.claude/state/
├── schema-version        # "1" (단일 줄)
├── reflect.flag          # (존재 시) 품질 검증 실패 상태
├── quality.jsonl         # (append) 검증 이벤트 로그
├── progress.md           # (옵션) 작업 이어가기 + 의사결정 누적 (§5)
├── route.json            # (옵션) 실시간 라우팅 스냅샷 — latest-only 덮어쓰기 (§6)
├── notepad.md            # (옵션) 현재 작업 메모 (사용자 수정 OK)
└── decisions.md          # (옵션) 설계 결정 누적 기록
```

`.claude/temp/` 는 **단일 세션 한정 임시 파일** (plan.md, analysis.md). state가 아님.

---

## 파일별 계약

### 1. `reflect.flag`

**목적**: quality-gate 실패 → 다음 세션에서 ADAPT 강제.

**생성자**: `hooks/quality-gate.sh` (ESLint/tsc/test 실패 시)

**해제자**:
- 자동: `hooks/quality-gate.sh` 가 다음 실행에서 통과하면 삭제
- 수동: `rm .claude/state/reflect.flag`
- 우회: 파일 본문에 `ack: <이유>` 행 추가 시 `session-init.sh`가 주입 스킵

**읽는 자**: `hooks/session-init.sh`, `skills/forge-status` (있을 경우)

**포맷** (YAML-ish, 단순 grep 가능하게):
```
# REFLECT REQUIRED — 이전 턴 품질 검증 실패
# 삭제하려면: rm .claude/state/reflect.flag
---
timestamp: 2026-04-14T10:00:00Z
session_id: abc123
failed_blocks:
  - eslint
  - tsc
failed_files:
  - src/foo.ts
  - src/bar.ts
---
```

**필수 필드**: `timestamp`, `failed_blocks`. 나머지는 옵션.

**수명주기**:
- 생성 → 다음 통과 또는 수동 삭제까지 유지
- 같은 `session_id` 로 3번 연속 재생성 → session-init이 "stuck" 경고 + `/codex` 권장 주입 (Phase J에서 구현)

---

### 2. `quality.jsonl` (append-only)

**목적**: 관찰 가능성 로그. forge-glow HUD + /forge-status 소비.

**생성자**: `hooks/quality-gate.sh` (매 Stop 훅 실행 시)

**포맷** (JSON Lines, 줄당 1 이벤트):
```json
{"ts":"2026-04-14T10:00:00Z","sid":"abc123","type":"eslint","status":"pass","detail":""}
{"ts":"2026-04-14T10:00:01Z","sid":"abc123","type":"tsc","status":"fail","detail":"2 errors"}
{"ts":"2026-04-14T10:00:02Z","sid":"abc123","type":"test-trigger","status":"warn","detail":"TC 없음: src/hooks/useFoo.ts"}
```

**필드 스펙**:

| 필드 | 타입 | 필수 | 설명 |
|-----|------|-----|------|
| `ts` | ISO-8601 UTC | ✅ | 이벤트 시각 |
| `sid` | string | ✅ | 세션 ID (transcript 매칭용) |
| `type` | enum | ✅ | `eslint` \| `tsc` \| `scope` \| `test-trigger` \| `policy-sync` \| `reflect` \| `scope-type` \| `cleanup` \| `whetstone` |
| `status` | enum | ✅ | `pass` \| `warn` \| `fail` |
| `detail` | string | ❌ | 사람이 읽는 상세. JSON 이스케이프 준수 |

**읽는 자**: `skills/forge-status`, forge-glow L3 (adapter 경유 권장)

**집계 화이트리스트 (2026-06-12 신설 — 경합 계약)**:
- 게이트 지표 집계(`bin/forge status`의 quality_pass/warn/fail)와 Whetstone 패턴 스캔(`forge whet`)의 분모는 **게이트 발행 type만**: `eslint` | `tsc` | `test-trigger` | `reflect`.
- 게이트 외 producer가 append하는 type(`whetstone` 등)은 관찰 로그일 뿐 — **집계에서 제외** (self-emit이 pass/fail 분모를 오염시키지 않게).
- 새 self-emit type을 추가하려면 이 화이트리스트엔 넣지 말고 enum에만 등재할 것.

**GC** (2026-06-12 개정 — 삭제 아닌 archive 이동):
- 7일 경과 엔트리는 `session-init.sh`가 세션 시작 시 `quality.archive.jsonl`로 이동 (활성 파일만 가볍게 유지)
- 파일 크기 10MB 초과 시 앞쪽 절반을 archive로 이동
- **유실 0 원칙**: 반복 패턴 히스토리는 Whetstone(규칙 초안 스캔)의 입력 — 스캔 도구는 active+archive 양쪽을 봐야 함
- 비고: 구버전 GC는 gawk 전용 match() 때문에 macOS에서 영구 무동작이었음 (수리 전 기록이 보존된 이유)

**호환성**:
- 외부 도구는 **모르는 `type` 을 보면 무시**해야 함 (forward-compat)
- 필드 추가는 minor bump, 필드 삭제/의미 변경은 major bump

---

### 3. `notepad.md` (옵션)

**목적**: 사용자/Claude의 세션 간 작업 메모.

**소유자**: **사용자** (Claude는 읽기 위주, 쓰기는 명시 지시 시에만)

**읽는 자**: `hooks/session-init.sh` 가 세션 시작 시 컨텍스트로 주입 (최대 100줄)

**포맷**: 자유 Markdown. 섹션 구조 권장:
```markdown
# 현재 작업

## 진행 중
- TICKET-123 주문 필터 수정

## 블로커
- API 응답 스펙 미정 (팀장 확인 대기)

## 다음 턴 메모
- useFoo 리팩토링 시 __tests__ 동반 수정 잊지 말 것
```

**GC**: 없음. 사용자가 직접 정리.

**참고**: MEMORY.md (`~/.claude/` 또는 `.claude/`)와 역할 분리
- MEMORY.md = **장기 지식** (사용자 역할, 도메인 규칙)
- notepad.md = **단기 작업 상태**

---

### 4. `decisions.md` (옵션)

**목적**: 설계 결정 누적. 나중에 "왜 이렇게 했지?" 회고.

**쓰는 자**: `/start` 8단계 완료 시 계획 요약을 append (Phase G에서 구현)

**포맷**:
```markdown
## 2026-04-14 TICKET-123

**문제**: 주문 필터가 여러 탭에서 상태 공유 못 함

**선택지**:
1. 전역 atom — 단순, 리렌더 많음
2. URL query — 공유 링크 가능, 탭 독립
3. context 프로바이더 — 탭 독립 + 제어

**결정**: 2 — 공유 링크 요구사항 때문

**영향 파일**: 3개
```

**GC**: 없음. 100개 엔트리 초과 시 session-init이 경고.

---

### 5. `progress.md` (작업 이어가기 + 의사결정 누적, 2026-05-17 redesign G3 신설, 2026-05-20 G3.5 확장)

**목적**: 작업 중간에 세션이 끊겨도 다음 세션이 이어 받을 수 있게 (cross-session recall) + 모호함 → 자율 판단을 투명하게 기록 (implementation-notes 패턴, Anthropic 개발자 공유 프롬프트 차용).

**쓰는 자**: `/start` 스킬이 Phase 3 분석 완료 시 + Phase 4 시작 시 + Phase 5 통과 시 + 체크포인트 A/B 통과 시 자동 append.

**읽는 자**: `session-init.sh`가 매 세션 시작 시 tail 80줄 주입. 80줄 이하면 전체.

**포맷** (4섹션은 모두 옵션 — 모호함 발견 시에만 기록):

```markdown
## TICKET-123 — 2026-05-20T10:23

**phase**: APPLY (Phase 4)
**files touched**: [src/feature/list.tsx, src/api/list.ts]
**next**: assayer 테스트 생성 → Phase 5 검증

### 설계 결정 (모호함 → 자율 판단, 옵션)
- pagination default size: 명세 모호 → 기존 Order 모듈 패턴 따라 20으로 선택

### 편차 (의도적으로 명세 안 따른 부분, 옵션)
- 명세는 1 API 호출, 실제 2 호출로 분리. 이유: 캐시 효율.

### 트레이드오프 (대안 + 선택 이유, 옵션)
- API 합치기 vs 분리 — 분리 선택 (캐시 효율 > 로딩 속도)

### 미결 질문 ⚠️ (사용자 답변 요청, 옵션)
- BE에 region 필드 없을 때 fallback 'unknown' OK?
- pagination 기본값 20 — 디자인 시안에 명시 없음, 확인 필요

---

## TICKET-456 — 2026-05-20T14:10
**phase**: VERIFY (Phase 5)
**files touched**: [src/auth/signup.tsx]
**next**: 사용자 검수 대기 — 95% 적중률 통과 후 PR
(4섹션 — 이번 작업은 모호함 없어 스킵)
```

**원칙**:
- **4섹션 모두 옵션**. 작은 작업(LOW 복잡도)은 phase/files/next만으로 충분.
- 미결 질문은 `⚠️` 마커 — session-init이 노출 시 시각 강조 (사용자 즉시 인지).
- 의사결정은 "왜 이렇게 했지?" 미래 추적용 — PR description에 첨부 가능.

**GC** (2026-05-20 G3.5c 정리 프로세스 추가):
- `/start` Phase 7 (완료 보고) 종료 시 사용자에게 "이 ticket 완료. progress.md에서 정리할까요?" prompt.
- Yes: 해당 블록을 `.claude/state/progress-archive.md`로 이동 (히스토리 보존).
- No: 그대로 유지 (사용자 자유).
- 80줄 초과 시 session-init이 마지막 80줄만 주입 — 마지막 ticket의 의사결정이 가장 중요.

**forge-hearth 연동**: 다중 프로젝트 dashboard는 각 repo의 `progress.md`를 stitch해서 "현재 진행 중인 ticket + 미결 질문 1줄 요약" 표시. **미결 질문 있는 ticket은 우선 표시**.

**Hermes H2 (G7) 연결**: 사용자가 미결 질문에 반복적으로 같은 답 패턴 보이면 → `coding-practice/.candidate/profile.md` 자동 누적 후보 (G7 작업).

---

### 6. `route.json` (실시간 라우팅 스냅샷, 2026-06-12 신설 — HYBRID transport)

**목적**: "지금 무슨 모델/effort/role로 도는지" **현재 상태 딱 하나** (latest-only). 히스토리는 쌓지 않는다 — 누적 지표는 `usage.jsonl`/`quality.jsonl` 담당. 형식·필드 사전은 [`event-schema.md`](event-schema.md) §1-§2가 단일 진실.

**쓰는 자**: `bin/forge emit-event` (stdin JSON → 원자적 `mv` 덮어쓰기). 호출 주체는 Phase 2+에서 배선 (/start 라우팅 결정 시점, SubagentStop 등) — 현재는 shadow (수동 호출만).

**읽는 자**: `bin/forge status --json`의 `route` 키 (v1-additive — 파일 직독 금지 규약 준수). 없으면 `null`.

**GC**: 불필요 — 단일 파일 덮어쓰기.

---

### 7. `whetstone/` (규칙 초안 디렉토리, 2026-06-12 신설 — 마스터플랜 5단계)

**목적**: quality.jsonl(active+archive)에서 3회+ 반복된 패턴을 규칙 후보 초안으로 적재. **채택은 반드시 사람이** — 자동 승격/자동 PR 없음 (마스터플랜 §3 금지 유지).

**생성자**: `bin/forge whet --draft` (스캔·초안 생성 모두 수동/스킬 트리거 — 백그라운드 자동 생성 없음)

**포맷** (`.claude/state/whetstone/{YYYY-MM-DD}-{slug}.md`):
```markdown
---
status: draft        # draft | accepted | rejected
type: test-trigger   # 패턴이 나온 quality.jsonl type
count: 27
first_seen: 2026-06-08T09:47:24Z
last_seen: 2026-06-12T10:30:00Z
---

## 반복 패턴
TC 없음: apps/cargopass-web/src/components/layout/Header.tsx

## 규칙 후보 (사람이 다듬을 것)
- {모델이 초안 작성 — 채택 전까지 효력 없음}
```

**수명주기**:
- `status: draft` → 사람이 검토 후 `accepted`(규칙으로 승격) 또는 `rejected`로 수정
- **승격 목적지 (2026-06-12 사용자 결정 §4-5)**: 해당 프로젝트의 `.candidate/profile.md` (kkombee 채택 — coding-practice의 기존 .candidate 패턴과 동일 구조). 승격 작업 자체도 사람이 수행
- **rejected slug 재생성 금지** — `forge whet --draft`는 같은 slug의 파일이 존재하면(상태 불문) 건너뜀
- 자동 삭제 없음 (정보 보존)

**읽는 자**: `bin/forge status`(draft 카운트), `hooks/session-init.sh`(draft ≥1 시 1줄 보고), `skills/forge-status` §2-6

**정직한 종료 조건**: 30일간 승격 0건이면 루프 폐기 재평가 (마스터플랜 5단계).

---

## 외부 도구 연동 규약

forge-glow 같은 외부 도구는 **파일 경로 직독 금지**. 대신 아래 surface 사용:

```bash
# code-forge 플러그인이 제공 (Phase H에서 구현)
$CLAUDE_PLUGIN_ROOT/bin/forge status --json
```

이 커맨드가 `.claude/state/` 내용을 **버전 있는 JSON**으로 출력. 파일 위치가 바뀌어도 외부 도구는 영향 없음.

임시로 직독이 필요한 경우(테스트, 디버깅)에는 이 문서의 버전을 고정 참조해야 함.

---

## 마이그레이션

스키마 버전 올라가면:

1. `.claude/state/schema-version` 읽고 현재 버전과 비교
2. 불일치 시 `hooks/session-init.sh` 가 마이그레이션 스크립트 실행
   - `$CLAUDE_PLUGIN_ROOT/hooks/migrate-state.sh v1 v2`
3. 실패 시 현재 상태 보존 + 사용자에게 수동 마이그레이션 안내

---

## 체크리스트 (새 파일 추가 시)

`.claude/state/` 에 새 파일 추가하려면:

- [ ] 이 문서에 "파일별 계약" 섹션 추가 (목적, 생성자, 해제자, 포맷, GC)
- [ ] `hooks/quality-gate.sh` 또는 `session-init.sh` 가 관리 로직 포함
- [ ] 테스트: 의도적 생성 → 예상대로 소비되는지 확인
- [ ] plugin.json version minor bump
