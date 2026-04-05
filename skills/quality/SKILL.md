---
name: quality
description: 포맷(Prettier) → 린트(ESLint) → 타입 체크(tsc) 순서로 실행하고 오류 자동 수정. 훅(lint-fix.sh, quality-gate.sh)이 자동 커버하지만 --no-fix(확인만)나 프로젝트 전체 검사가 필요할 때 사용.
category: workflow
user-invocable: false
---

# /quality

코드 품질 검증 파이프라인. 포맷 → 린트 → 타입 체크를 순서대로 실행하고, 오류를 자동 수정한다.

**[즉시 실행]** 아래 흐름을 바로 실행하세요.

**옵션**: $ARGUMENTS

| 옵션            | 설명                            |
| --------------- | ------------------------------- |
| `--format-only` | 포맷(Prettier)만 실행           |
| `--lint-only`   | 린트(ESLint)만 실행             |
| `--type-only`   | 타입 체크만 실행                |
| `--no-fix`      | 자동 수정 없이 오류 목록만 출력 |

---

## Step 1: 프로젝트 환경 감지

```bash
# package.json에서 사용 가능한 스크립트 확인
cat package.json | grep -E '"(format|prettier|lint|tsc|typecheck)"'

# 또는 직접 도구 존재 확인
which prettier eslint tsc 2>/dev/null
```

## Step 2: 포맷 (Prettier)

`--lint-only`, `--type-only` 옵션이 없으면 실행.

```bash
# 프로젝트에 prettier 스크립트가 있으면
yarn format
# 또는 직접 실행
npx prettier --write "src/**/*.{ts,tsx,js,jsx}"
```

`--no-fix` 시:
```bash
npx prettier --check "src/**/*.{ts,tsx,js,jsx}"
```

## Step 3: 린트 (ESLint)

`--format-only`, `--type-only` 옵션이 없으면 실행.

```bash
# 프로젝트에 lint 스크립트가 있으면
yarn lint --fix
# 또는 직접 실행
npx eslint --fix "src/**/*.{ts,tsx,js,jsx}"
```

`--no-fix` 시:
```bash
yarn lint
```

**린트 에러가 남으면:**
1. 자동 수정 가능한 에러는 `--fix`로 해결됨
2. 수동 수정 필요한 에러는 목록 출력
3. 심각한 에러가 있으면 사용자에게 보고 후 다음 단계 계속

## Step 4: 타입 체크 (TypeScript)

`--format-only`, `--lint-only` 옵션이 없으면 실행.

```bash
# tsc --noEmit으로 타입 에러만 확인
yarn tsc --noEmit
# 또는
npx tsc --noEmit
```

**타입 에러가 있으면:**
1. 에러 목록 출력
2. 자동 수정이 가능한 경우 (import 누락, 타입 불일치 등) Edit으로 수정
3. 수정 후 재확인

## Step 5: 결과 보고

```
/quality 완료

포맷 (Prettier): PASS / N개 수정됨
린트 (ESLint):   PASS / N개 에러 (수동 수정 필요)
타입 (tsc):      PASS / N개 에러

총 자동 수정: N개 파일
수동 확인 필요: N개 에러
```
