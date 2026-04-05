---
name: python-django
description: Django 기반 Python 백엔드 컨벤션
---

# Django 컨벤션

## 프로젝트 구조

```
project/
├── config/          # settings, urls, wsgi, asgi
│   ├── settings/    # base.py, local.py, production.py 분리
│   └── urls.py
├── apps/            # 기능별 앱 모음
│   └── {app}/
│       ├── models.py
│       ├── views.py
│       ├── serializers.py   # DRF 사용 시
│       ├── urls.py
│       └── tests/
└── requirements/    # base.txt, local.txt, production.txt
```

## 네이밍 규칙

- 파일/모듈: `snake_case`
- 클래스(모델, 뷰, 시리얼라이저): `PascalCase`
- URL name: `{app}:{action}` 형식 (예: `users:detail`)
- 모델 필드: `snake_case`

## 에러 처리

- DRF 사용 시 `ValidationError`, `PermissionDenied`, `NotFound` 활용
- 커스텀 에러는 `apps/core/exceptions.py`에 정의
- `EXCEPTION_HANDLER` 설정으로 전역 에러 포맷 통일

## 테스트

- `pytest-django` + `factory_boy` 조합 권장
- `TestCase` 대신 `pytest` 스타일 선호
- 모델/시리얼라이저 단위 테스트 + API 통합 테스트 분리
