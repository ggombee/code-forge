---
name: commit
description: staged 변경사항 분석 → 커밋 메시지 생성 → 커밋. 브랜치 워크플로우 지원.
category: workflow
---

# /commit

staged 변경사항을 분석하고 커밋 메시지를 생성한 후 커밋한다.

**[즉시 실행]** 아래 흐름을 바로 실행하세요.

**옵션**: $ARGUMENTS

| 옵션               | 설명                                          |
| ------------------ | --------------------------------------------- |
| `--push`           | 커밋 후 바로 push                             |
| `--no-gate`        | 출시 게이트 점검 스킵                         |
| `--<branch-name>`  | target branch 지정 시 머지 워크플로우 실행    |

---

## Step 1: staged 변경사항 분석

```bash
git status
git diff --staged
git log --oneline -5
```

- staged 파일 목록과 변경 내용을 파악한다
- 최근 커밋 메시지 스타일을 참고한다

## Step 2: 커밋 메시지 생성

변경사항을 분석하여 커밋 메시지를 작성한다:

- **타입**: feat / fix / refactor / chore / docs / test / style
- **범위**: 변경 대상 (컴포넌트명, 모듈명 등)
- **설명**: 무엇을 왜 변경했는지 (한국어 또는 영어, 프로젝트 컨벤션 따름)
- 최근 커밋 메시지 스타일과 일관되게

```
{type}({scope}): {description}

{body - 선택}
```

## Step 3: 커밋 실행

```bash
git commit -m "{생성된 메시지}"
```

## Step 4: 옵션 처리

### `--push` 옵션

커밋 후 바로 push:
```bash
git push -u origin $(git branch --show-current)
```

### Target Branch 워크플로우

`$ARGUMENTS`에 브랜치명이 있는 경우:

```
<branch-name> checkout + pull
  → feature 브랜치 생성
  → 커밋
  → feature 브랜치 push
  → <branch-name>으로 merge
  → <branch-name> checkout + pull
```

1. `git checkout <branch-name>` → `git pull`
2. feature 브랜치 생성: `git checkout -b <feature-branch>`
3. 커밋 실행
4. `git push -u origin <feature-branch>`
5. `git checkout <branch-name>`
6. `git merge <feature-branch>`
7. `git pull`

### 브랜치명 없을 때

```
현재 브랜치 최신화
  → feature branch 생성 (사용자 확인)
  → 커밋 + push
```

1. `git pull` (현재 브랜치 최신화)
2. feature branch 생성 필요 여부를 사용자에게 확인
3. 커밋 실행
4. `git push -u origin <브랜치>`
