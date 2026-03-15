---
name: version-update
description: Node/Rust/Python 프로젝트의 시맨틱 버전을 업데이트하고 안전하게 커밋 및 (선택적) push.
---

# Version Update Skill

> Cross-stack semantic version update for Node/Rust/Python

---

## 스크립트

| 스크립트 | 용도 |
|----------|------|
| `stack-detect.sh` | 프로젝트 타입 식별 |
| `version-find.sh [--plain]` | 버전 파일 위치 탐색 |
| `version-current.sh [file]` | 현재 시맨틱 버전 추출 |
| `version-bump.sh <current> <type>` | 다음 버전 계산 |
| `version-apply.sh <new> [files...]` | 버전 업데이트 적용 |
| `git-commit.sh "msg" [files]` | 변경 파일 커밋 |
| `git-push.sh` | 현재 브랜치 안전 push |

---

## 버전 규칙

| 입력 | 효과 | 예시 |
|------|------|------|
| `+1` or `+patch` | 패치 증가 | `0.1.13 → 0.1.14` |
| `+minor` | 마이너 증가 | `0.1.13 → 0.2.0` |
| `+major` | 메이저 증가 | `0.1.13 → 1.0.0` |
| `x.y.z` | 명시적 지정 | any → `x.y.z` |

---

## 지원 스택

| 스택 | 버전 파일 |
|------|----------|
| Node.js | `package.json` |
| Rust | `Cargo.toml` (`[package].version`) |
| Python | `pyproject.toml`, `setup.py`, `__version__` in `.py` |

모든 스택에서 코드 내 `.version('x.y.z')` 패턴도 지원.

---

## 워크플로우

1. **detect** — 스택 식별
2. **discover** — 버전 파일 탐색
3. **read** — 현재 버전 추출
4. **calculate** — 다음 버전 계산
5. **apply** — 모든 발견된 파일에 업데이트
6. **commit** — conventional commit 형식
7. **push** — (선택적) 안전 push

---

## 안전 규칙

| 금지 |
|------|
| 현재 버전 읽지 않고 업데이트 시작 |
| 여러 버전 파일 중 일부만 업데이트 |
| 보호 브랜치에 force push |
| diff 확인 없이 커밋 |
