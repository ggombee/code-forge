---
description: "브랜치 머지 + push 자동화"
allowed-tools: Bash
---

# Git Merge Command

브랜치를 안전하게 머지하고 push한다.

## 인자 파싱

- `$ARGUMENTS` 형식: `<target> <source>` (예: `main feature/order`)
- target 미지정 시: 현재 브랜치로 머지
- source 미지정 시: 사용자에게 확인

## 실행 순서

### 1. 사전 확인

```bash
# 현재 상태 확인
git status
git branch --show-current

# 커밋되지 않은 변경 확인
git diff --stat
```

- 커밋되지 않은 변경이 있으면 **중단** 후 사용자에게 알림
- stash할지, 커밋할지 확인

### 2. 브랜치 최신화

```bash
git fetch origin
git checkout <target>
git pull origin <target>
```

### 3. 머지 실행

```bash
git merge <source> --no-edit
```

- **충돌 발생 시**: 충돌 파일 목록 표시 후 사용자에게 해결 방법 제안
  - 자동 해결 가능한 경우 제안
  - 수동 해결 필요 시 안내

### 4. 검증 (머지 성공 시)

```bash
# 머지 결과 확인
git log --oneline -5

# lint/build 체크 (package.json 존재 시)
npx tsc --noEmit 2>&1 | head -20
```

### 5. Push

```bash
git push origin <target>
```

### 6. 정리

```bash
# 머지 완료된 source 브랜치 삭제 여부 확인
# 사용자에게 물어본 후 실행
```

## 안전 규칙

- `main`/`master` 브랜치에 force push 절대 금지
- 머지 전 반드시 `git fetch` 수행
- 충돌 시 자동 해결하지 않고 사용자 확인
- `--no-verify` 사용 금지
