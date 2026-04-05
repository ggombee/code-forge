---
name: done
description: 작업 완료 후 검증 → 테스트 → 커밋 → PR 생성까지 전체 플로우 수행.
category: workflow
---

# /done - 작업 완료 및 PR 생성

> **참조:** 품질 검증 시 `rules/review-guide.md`

구현 완료 후 사용합니다. 검증 → 테스트 → 커밋 → PR 생성까지 전체 플로우를 수행합니다.

**참조 규칙**:

- `@${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/coordination-guide.md` (병렬 실행)
- `@${CLAUDE_PLUGIN_ROOT}/instructions/multi-agent/agent-roster.md` (에이전트 선택)
- `@${CLAUDE_PLUGIN_ROOT}/rules/thinking-model.md` (작업 절차 — VERIFY 기준)

## 사용법

```
/done                    # 현재 브랜치 기준으로 자동 진행
/done --skip-test        # 테스트 스킵 (스타일 변경 등)
/done --force-test       # 테스트 강제 실행
/done --draft            # Draft PR로 생성
```

---

## 1단계: 변경 내용 분석

```bash
git status
git diff --staged
git diff
```

**분석 항목:**
- 변경된 파일 목록
- 주요 변경 내용 요약
- 정책 영향 여부 판단 (아래 기준표 참조)

---

## 2단계: 테스트 전략 판단

> 코드 = 문서. **의도치 않은 정책 변경**을 방지하기 위한 테스트 전략

### 변경 파일 분류

| 경로 패턴 | 분류 | 테스트 도구 |
|-----------|------|------------|
| `components/`, `views/`, `hooks/` | 컴포넌트/훅 | **assayer 에이전트** |
| `utils/`, `helpers/`, `lib/` | 순수 함수 | **Claude 직접 작성** |
| `styled.ts`, `constants.ts`, `types.ts` | UI/타입 | 스킵 |

### 정책 영향 판단 기준

| 변경 내용 | 테스트 전략 | 도구 |
|-----------|------------|------|
| 필터/검색 UI 변경 | 통합 테스트 | **assayer** |
| disabled/readonly 조건 변경 | 통합 테스트 | **assayer** |
| 새 UI 상태 추가 | BDD 시나리오 | **assayer** |
| 날짜/기간/가격 계산 변경 | 유닛 테스트 | **Claude 직접** |
| 상태 전이 로직 변경 | 유닛 테스트 | **Claude 직접** |
| 텍스트/라벨/스타일 변경 | 스킵 | - |

---

## 3단계: 테스트 실행

### Case A: 컴포넌트/훅 + 정책 영향 → assayer 호출

```typescript
Task(subagent_type = 'assayer', prompt = `
  targetPath: {대상 파일}
  mode: create
`);
```

### Case B: 순수 함수 + 정책 영향 → Claude 직접 작성

대상 파일을 분석하여 `__tests__/{파일명}.test.ts` 생성 후 테스트 실행.

### Case C: 기존 테스트 있음 → 실행만

```bash
# profile.json 또는 package.json에서 테스트 명령어 감지
yarn test    # 또는 npm test, pnpm test
```

### Case D: UI only (정책 무관) → 스킵

---

## 4단계: 코드 검증 (병렬 실행)

```typescript
// 병렬 검증
Task(subagent_type = 'lint-fixer', model = 'haiku', prompt = '린트 오류 수정');
```

```bash
# 빌드/타입 체크 (package.json scripts 기준)
yarn build     # 또는 npm run build, pnpm build
```

---

## 4-1단계: 품질 검토 (필수)

VERIFY 기준으로 점검:

- 구현이 목적과 정확히 맞는가?
- 잠재 버그/크리티컬/보안 이슈는 없는가?
- 회귀나 사이드 이펙트는 없는가?
- 재사용/통합 가능한 기존 코드를 활용했는가?
- 불필요 코드가 정리됐는가?
- "지금 배포 가능한가?" 질문에 근거로 답할 수 있는가?

**원칙**: 하나라도 FAIL이면 커밋/PR 진행 금지.

---

## 5단계: 커밋 생성

```bash
# 수정한 파일만 명시적으로 add (git add . 금지)
git add {변경 파일 1} {변경 파일 2}
```

**커밋 메시지 형식:**

```
{type}: {변경 내용 요약}

- {세부 변경 1}
- {세부 변경 2}
```

type: `feat`, `fix`, `refactor`, `style`, `test`, `docs`, `chore`

---

## 6단계: PR 생성

```bash
git push -u origin {현재브랜치}

gh pr create \
  --title "{type}: {제목}" \
  --body "$(cat <<'EOF'
## Summary
- {변경 내용 bullet points}

## Test plan
- [ ] lint/build 통과
- [ ] {테스트 전략}

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

> `gh` CLI가 없으면: `git push` 후 PR URL 수동 안내.

---

## 7단계: 최종 요약 출력

```markdown
## 작업 완료

### 검증 결과
- [x] lint 통과
- [x] build 통과
- [x] 테스트 {통과/스킵 (사유)}

### 커밋
- {커밋 해시}: {커밋 메시지}

### PR
- URL: {PR URL}
- 상태: Open
```

---

## 옵션

| 옵션 | 설명 | 사용 예시 |
|------|------|-----------|
| `--skip-test` | 테스트 스킵 (정책 무관 확인 후) | `/done --skip-test` |
| `--force-test` | 정책 무관이어도 테스트 강제 실행 | `/done --force-test` |
| `--draft` | Draft PR로 생성 | `/done --draft` |

---

## 완료 조건

- [ ] 변경 내용 분석 완료
- [ ] 테스트 전략 판단됨
- [ ] 테스트 실행/스킵 완료 (사유 명시)
- [ ] lint/build 검증 통과
- [ ] 커밋 생성됨
- [ ] PR 생성됨 (URL 출력)
- [ ] 최종 요약 출력됨
