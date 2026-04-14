# code-forge State Schema v1

> `.claude/state/` 하위 파일들의 **계약 명세**. 여기 명시된 포맷/수명주기가 code-forge ↔ forge-glow ↔ 외부 도구 간의 공식 인터페이스입니다.
>
> 이 문서에 없는 파일은 내부 구현 세부이므로 외부 도구가 읽어서는 안 됩니다.

---

## 버전

| ver | 날짜 | 변경 |
|-----|-----|------|
| 1.0 | 2026-04-14 | 초기 명세 |

버전이 올라가면 `.claude/state/schema-version` 파일에 숫자 기록.

---

## 디렉토리 구조

```
.claude/state/
├── schema-version        # "1" (단일 줄)
├── reflect.flag          # (존재 시) 품질 검증 실패 상태
├── quality.jsonl         # (append) 검증 이벤트 로그
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
| `type` | enum | ✅ | `eslint` \| `tsc` \| `scope` \| `test-trigger` \| `policy-sync` \| `reflect` \| `scope-type` \| `cleanup` |
| `status` | enum | ✅ | `pass` \| `warn` \| `fail` |
| `detail` | string | ❌ | 사람이 읽는 상세. JSON 이스케이프 준수 |

**읽는 자**: `skills/forge-status`, forge-glow L3 (adapter 경유 권장)

**GC**:
- 7일 경과 엔트리는 `session-init.sh`가 세션 시작 시 정리
- 파일 크기 10MB 초과 시 절반으로 트리밍 (오래된 것부터)

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
