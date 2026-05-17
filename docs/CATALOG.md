# code-forge — 카탈로그

> CLAUDE.md 핵심에서 분리한 정적 카탈로그. 매 세션 자동 주입 대상 아님 — 필요 시 Read.
> (2026-05-17 redesign: CLAUDE.md 줄 부담 감소 목적)

---

## v4.0 폐지 스킬 (규칙/훅으로 흡수)

| 폐지 | 대체 |
|------|------|
| `/done` | `/start` + 시스템 프롬프트 커밋 절차 |
| `/quality` | hooks(lint-fix.sh + quality-gate.sh) 자동 실행 |
| `/bug-fix` | `thinking-model.md` GROUND "버그 수정 시 2-3 옵션 제시" 규칙 |
| `/refactor` | `thinking-model.md` GROUND "정책 보호 테스트 먼저" 규칙 |

## 모듈 (17개)

| 카테고리 | 모듈 |
|---------|------|
| Framework (Frontend) | `react-nextjs-pages`, `react-nextjs-app`, `react-spa` |
| Framework (Backend) | `python-fastapi`, `python-django`, `node-express`, `go-standard` |
| Design System | `mui`, `ant-design` |
| State | `jotai-tanstack`, `zustand-tanstack`, `redux-rtk` |
| Styling | `emotion`, `tailwind`, `styled-components` |
| Testing | `jest`, `vitest` |

## 프리셋

| 프리셋 | 조합 |
|--------|------|
| `standard` | Pages Router + Jotai + Emotion + Jest |
| `modern-stack` | MUI + App Router + Zustand + Tailwind + Vitest |
| `backend-api` | Node.js Express + Jest |
