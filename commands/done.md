---
name: done
description: 작업 완료 후 검증 → 커밋 → PR 생성까지 전체 플로우 수행.
---

# /done - 작업 완료 및 PR 생성

구현 완료 후 사용합니다. 검증 → 커밋 → PR 생성 → 정리까지 전체 플로우를 수행합니다.

## 참조 규칙

- `@${CLAUDE_PLUGIN_ROOT}/skills/bug-fix/SKILL.md`

## 흐름

1. lint/build 검증
2. 변경 파일 확인
3. 커밋 메시지 작성
4. PR 생성
5. 정리 (temp 파일 삭제)
