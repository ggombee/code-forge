---
name: go-standard
description: Go 표준 라이브러리 기반 백엔드 컨벤션
---

# Go 표준 라이브러리 컨벤션

## 프로젝트 구조

```
cmd/
└── server/
    └── main.go      # 진입점
internal/            # 외부 노출 불가 패키지
├── handler/         # HTTP 핸들러
├── service/         # 비즈니스 로직
├── repository/      # 데이터 접근 레이어
└── model/           # 도메인 모델
pkg/                 # 외부 공유 가능 패키지
go.mod
go.sum
```

## 네이밍 규칙

- 패키지명: 소문자 단어 (예: `handler`, `repository`)
- 파일명: `snake_case.go`
- exported: `PascalCase`, unexported: `camelCase`
- 인터페이스: 동작 기반 이름 (예: `UserStore`, `Notifier`)
- 에러 변수: `Err` 접두사 (예: `ErrNotFound`)

## 에러 처리

- `fmt.Errorf("...: %w", err)` 로 에러 래핑
- `errors.Is` / `errors.As` 로 타입 확인
- 핸들러에서만 HTTP 상태로 변환, 내부 레이어는 순수 에러 반환
- sentinel 에러는 패키지 레벨에 `var ErrXxx = errors.New(...)` 정의

## 테스트

- `testing` 표준 패키지 + `testify/assert` 조합
- 인터페이스 기반 mock (`mockery` 또는 수동 mock)
- 테이블 기반 테스트(`t.Run`) 적극 활용
- 통합 테스트는 `_integration_test.go` 파일로 분리, `-tags integration` 빌드 태그 사용
