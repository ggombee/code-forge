---
name: python-fastapi
description: FastAPI 기반 Python 백엔드 컨벤션
---

# FastAPI 컨벤션

## 프로젝트 구조

```
app/
├── main.py          # FastAPI 앱 진입점, 라우터 등록
├── api/             # 라우터 모음 (v1/, v2/ 등 버전 분리)
├── core/            # 설정, 의존성, 보안
├── models/          # SQLAlchemy ORM 모델
├── schemas/         # Pydantic 스키마 (요청/응답)
├── services/        # 비즈니스 로직 (라우터와 분리)
└── tests/
```

## 네이밍 규칙

- 파일/모듈: `snake_case`
- 클래스: `PascalCase`
- 함수/변수: `snake_case`
- 상수: `UPPER_SNAKE_CASE`
- Pydantic 스키마: `{Entity}Request`, `{Entity}Response`

## 에러 처리

- `HTTPException(status_code=..., detail=...)` 사용
- 공통 에러는 `app/core/exceptions.py`에 커스텀 예외 클래스로 정의
- 전역 exception handler는 `main.py`에 `@app.exception_handler` 등록

## 테스트

- `pytest` + `httpx.AsyncClient` 조합
- `conftest.py`에 DB fixture, 앱 fixture 정의
- 단위 테스트: `services/` 레이어 집중
- 통합 테스트: 라우터 엔드포인트 전체 흐름
