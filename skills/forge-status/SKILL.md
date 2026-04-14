---
name: forge-status
description: code-forge 상태 대시보드. REFLECT flag, quality 이벤트, notepad/decisions, usage 집계를 한 번에. forge-glow 같은 외부 도구는 --json으로 파싱.
---

# /forge-status

code-forge의 현재 런타임 상태를 회고/진단용 단일 뷰로 보여줍니다.
**외부 도구 연동용 JSON surface**도 제공 — `forge status --json`.

**[즉시 실행]** 아래 절차대로 상태를 출력하세요.

---

## 사용법

```
/forge-status              → 사람 읽는 리포트 (상세)
/forge-status --json       → JSON 출력 (forge-glow, CI 연동용)
/forge-status --week       → 최근 7일 quality 추이
/forge-status --reflect    → REFLECT flag 상세
```

---

## Step 1: CLI 호출

플러그인이 제공하는 단일 surface를 호출:

```bash
${CLAUDE_PLUGIN_ROOT}/bin/forge status
```

`--json` 인자 있으면:
```bash
${CLAUDE_PLUGIN_ROOT}/bin/forge status --json
```

→ JSON 그대로 출력하고 종료. 사람이 호출했어도 `--json`이면 파이프라인 용도로 가정.

---

## Step 2: 상세 섹션 추가

`--json`이 아닌 경우, `bin/forge status` 출력 다음에 아래 섹션 보강:

### 2-1. 최근 quality 이벤트 (있으면)

```bash
tail -10 .claude/state/quality.jsonl 2>/dev/null
```

각 이벤트를 사람 읽는 포맷으로 변환:
```
[2026-04-14 10:00] eslint   PASS
[2026-04-14 10:00] tsc      FAIL  2 errors
[2026-04-14 10:00] test-trigger  WARN  TC 없음: src/hooks/useFoo.ts
```

### 2-2. REFLECT flag 상세 (활성 시)

```bash
[ -f .claude/state/reflect.flag ] && cat .claude/state/reflect.flag
```

→ `timestamp`, `failed_blocks`, `failed_files` 파싱하여 테이블화.

### 2-3. Notepad 미리보기 (있으면)

```bash
if [ -f .claude/state/notepad.md ]; then
  echo "=== Notepad 미리보기 ==="
  head -20 .claude/state/notepad.md
fi
```

### 2-4. 최근 decisions (있으면)

```bash
if [ -f .claude/state/decisions.md ]; then
  echo "=== 최근 결정 3건 ==="
  grep -A 3 "^## " .claude/state/decisions.md | tail -15
fi
```

### 2-5. 사용량 (usage.jsonl)

```bash
if [ -f "$HOME/.code-forge/usage.jsonl" ]; then
  echo "=== 이번 주 사용 Top 3 ==="
  # 7일 이내 에이전트/스킬 집계
  CUTOFF=$(date -u -v-7d +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u -d '7 days ago' +"%Y-%m-%dT%H:%M:%SZ")
  awk -v c="$CUTOFF" '$0 !~ /"ts":"'"$CUTOFF"'"/ && match($0,/"name":"([^"]+)"/,n) { print n[1] }' "$HOME/.code-forge/usage.jsonl" | sort | uniq -c | sort -rn | head -3
fi
```

---

## Step 3: 옵션 처리

### `--week`
quality.jsonl에서 최근 7일 이벤트 일별 집계:

```
2026-04-14  █████████ 9 (pass:7 fail:2)
2026-04-13  ████ 4 (pass:4)
2026-04-12  ██████ 6 (pass:5 warn:1)
```

### `--reflect`
REFLECT flag 없으면 "깨끗함" + 최근 해제 시각. 있으면 전체 본문 + 권장 조치:

```
ADAPT 권장 절차:
  1. 실패 파일 Read → 증상 파악
  2. 근인 분석
  3. 수정 → Stop 훅 재실행
  4. 통과 시 flag 자동 삭제

우회: rm .claude/state/reflect.flag
Ack: 본문에 'ack: <이유>' 추가
```

---

## Step 4: 외부 도구 연동 힌트

사람 리포트 맨 아래에 안내:

```
─────────────────────────────────────
외부 도구 (forge-glow, CI, 슬랙봇):
  $CLAUDE_PLUGIN_ROOT/bin/forge status --json
계약: docs/contracts/state-schema.md v1
```

---

## 관련

- `docs/contracts/state-schema.md` — `.claude/state/` 파일 포맷 계약
- `/stats` — Bellows usage.jsonl 전용 집계 (다른 관점)
- `/cleanup` — state 파일 정리
- `forge-glow` — 실시간 statusLine HUD (회고는 /forge-status, 실시간은 glow)

---

## 금지 사항

- `.claude/state/` 파일을 직접 `cat`으로 통째로 쏟아내기 금지 — 항상 파싱/요약
- 외부 도구가 이 스킬을 호출하는 것 금지 — 반드시 `bin/forge status --json` 직접 사용
- 파일 경로 참조를 공식 계약인 것처럼 안내 금지 — 항상 `bin/forge` surface를 권장
