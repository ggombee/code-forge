---
name: cleanup
description: 작업 산출물 정리. design-refs, test-results, temp 파일 등.
---

# /cleanup

작업 중 생성된 산출물을 정리합니다.

**[즉시 실행]** 아래 워크플로우를 바로 실행하세요.

---

## 사용법

```
/cleanup              → 기본 정리 (design-refs + test-results)
/cleanup --all        → 전체 정리 (temp 파일 포함)
/cleanup --dry-run    → 삭제 없이 목록만 출력
```

---

## Step 1: 정리 대상 스캔

### Arguments: `$ARGUMENTS`

```
--dry-run → 목록만 출력, 삭제 안 함
--all → 전체 대상
없음 → 기본 대상
```

### 기본 정리 대상

| 대상 | 패턴 | 생성 시점 |
|------|------|----------|
| Figma 스크린샷 | `**/.design-refs/*.{png,jpg}` | /start Figma 분석 시 |
| Playwright 결과 | `**/test-results/` | E2E 실행 시 |
| Playwright 리포트 | `**/playwright-report/` | E2E 실행 시 |

### --all 추가 대상

| 대상 | 경로 | 생성 시점 |
|------|------|----------|
| 계획 파일 | `.claude/temp/plan.md` | /start 계획 출력 시 |
| 분석 파일 | `.claude/temp/analysis.md` | /start 분석 시 |
| REFLECT flag | `.claude/state/reflect.flag` | quality-gate 실패 시 |
| Quality 로그 | `.claude/state/quality.jsonl` | quality-gate 실행 시 (보통 GC에 맡김) |

---

## Step 2: 실행

```bash
# 기본 정리
find . -path "*/.design-refs/*.png" -delete 2>/dev/null
find . -path "*/.design-refs/*.jpg" -delete 2>/dev/null
rm -rf **/test-results/ 2>/dev/null
rm -rf **/playwright-report/ 2>/dev/null

# --all 추가
rm -f .claude/temp/plan.md 2>/dev/null
rm -f .claude/temp/analysis.md 2>/dev/null
rm -f .claude/state/reflect.flag 2>/dev/null
```

---

## Step 3: 결과 출력

```markdown
## /cleanup 결과

| 대상 | 삭제 수 |
|------|---------|
| design-refs | N개 |
| test-results | 삭제됨 |
| playwright-report | 삭제됨 |
| .claude/temp | (--all 시) 삭제됨 |
```

---

## 금지 사항

- `e2e/.auth/*.json` 삭제 금지 — 로그인 세션, 수동 삭제만
- `node_modules/.cache` 건드리지 않음 — 빌드 캐시
- `.policy/` 건드리지 않음 — 정책 데이터
- `.claude/docs/` 건드리지 않음 — 정책 문서
- `src/`, `packages/` 건드리지 않음 — 소스 코드