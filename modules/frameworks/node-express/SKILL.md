---
name: node-express
description: Express/Fastify 기반 Node.js 백엔드 컨벤션
---

# Node.js Express/Fastify 컨벤션

## 프로젝트 구조

```
src/
├── app.ts           # 앱 초기화, 미들웨어 등록
├── server.ts        # 서버 진입점 (app.ts와 분리)
├── routes/          # 라우터 모음
├── controllers/     # 요청/응답 처리
├── services/        # 비즈니스 로직
├── middleware/      # 커스텀 미들웨어
├── models/          # DB 모델 (Prisma schema 또는 ORM)
└── types/           # 공유 TypeScript 타입
```

## 네이밍 규칙

- 파일: `camelCase.ts` 또는 `kebab-case.ts` (프로젝트 일관성 유지)
- 클래스: `PascalCase`
- 함수/변수: `camelCase`
- 환경변수: `UPPER_SNAKE_CASE`
- 라우트 경로: `kebab-case` (예: `/user-profiles`)

## 에러 처리

- 중앙 집중식 에러 핸들러 미들웨어 (`middleware/errorHandler.ts`)
- `AppError` 커스텀 클래스로 상태 코드 + 메시지 캡슐화
- async 라우터는 `express-async-errors` 또는 `try-catch` wrapper 사용

## 테스트

- `Jest` + `supertest` 조합
- 서비스 레이어 단위 테스트 + 라우터 통합 테스트
- DB mock: `jest.mock` 또는 테스트 전용 DB 인스턴스
