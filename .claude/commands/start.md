---
description: 티켓 기반 작업 시작 - Figma/Jira 분석, 계획 수립, 구현 시작 전 품질 게이트 수행
---

# /start - 티켓 작업 시작

## 사용법

```bash
/start BOWD-193
```

## 참조 규칙

- `@../instructions/multi-agent/coordination-guide.md` (병렬 실행)
- `@../rules/frontend/thinking-model.md` (복잡도 판단)
- `@../instructions/validation/release-readiness-gate.md` (계획 품질 게이트)

## 0단계: Figma MCP 연결 확인 (디자인/UI 작업 시에만)

디자인/UI 관련 작업일 때만 실행:

1. `mcp__figma__whoami` 호출로 연결 상태 확인
2. 성공 시 다음 단계 진행
3. 실패 시 안내 후 중단
   - `Figma MCP 연결이 필요합니다. /mcp 실행 후 다시 진행해주세요.`

규칙:
- Figma 정보가 필요하면 MCP 우선
- PAT 방식 전제, OAuth 재인증 시도 금지

## 1단계: 티켓 정보 수집

티켓 URL이 제공되면 조회한다.

수집 항목:
- 제목
- 설명
- Figma URL (있는 경우)

## 2단계: 작업 환경 준비

### 2-1. 변경 대상 경로 확인

변경 대상 경로 기반으로 영향 범위를 판단한다.

### 2-2. `.design-refs` 폴더 생성 (디자인 작업 시에만)

```bash
mkdir -p {대상뷰경로}/.design-refs
```

## 3단계: Figma 디자인 분석 (MCP 우선)

### 3-1. URL 파싱

입력 URL:
- `https://www.figma.com/design/{fileKey}/{name}?node-id={nodeId}`

규칙:
- `node-id` 하이픈(`-`)을 콜론(`:`)으로 변환

### 3-2. 메타데이터 조회 (필수)

```text
mcp__figma__get_metadata({ fileKey, nodeId })
```

### 3-3. 스크린샷 조회 (필요 시)

```text
mcp__figma__get_screenshot({ fileKey, nodeId })
```

- 시각 검증이 필요하면 `.design-refs/`에 저장
- 상태별 색/아이콘/간격/줄바꿈 동작 확인

### 3-4. 디자인 시스템 매칭

프로젝트의 디자인 토큰/시맨틱 컬러 파일을 탐색하여 매칭한다.

### 3-5. 코드 변환 컨텍스트 (필요 시)

```text
mcp__figma__get_design_context({ fileKey, nodeId })
```

### 3-6. MCP 실패 시 fallback

- 안내: `Figma MCP 재연결이 필요합니다. /mcp 실행해주세요.`
- 필요할 때만 Figma API 직접 호출(curl) 사용

## 4단계: 코드 분석 및 Figma 일치 검증

독립 탐색은 병렬 실행:

```typescript
Task(subagent_type="explore", model="haiku", prompt="변경 대상 컴포넌트 구조 분석")
Task(subagent_type="explore", model="haiku", prompt="기존 디자인 시스템 패턴 분석")
Task(subagent_type="explore", model="haiku", prompt="관련 쿼리/서비스 파악")
```

필수 비교:
- 상태별(기본/선택/disabled) 색상
- 버튼/아이콘 유무와 종류
- `gap`, `padding`, `flex-wrap`

권장 명령:

```bash
rg "styled\\.|semanticColor|palette|#[0-9a-fA-F]" {대상파일}
```

## 5단계: 작업 계획 출력

아래 형식으로 출력:

```markdown
## 티켓: {TICKET} - {제목}
### Figma
{전체 URL}
### Figma 스크린샷 분석 결과
{주요 UI 특징/상태별 차이}
### Figma vs 코드 비교
| 항목 | Figma | 코드 | 상태 |
| --- | --- | --- | --- |
| ... | ... | ... | O/X |
### 작업 내용
1. ...
2. ...
### 변경 파일
- ...
### 검증 방법
- 스크린샷 비교
- 추가 테스트 전략
```

## 5-1단계: 임시 컨텍스트 파일 갱신

`.claude/temp`가 없으면 생성 후 갱신:

```bash
mkdir -p .claude/temp
```

- `.claude/temp/analysis.md`: 요구사항/기존 분석/리스크
- `.claude/temp/plan.md`: 확정 구현 단계/검증 계획
- 필요 시 `.claude/temp/order.md`, `.claude/temp/payment.md`

## 6단계: 복잡도 판단 및 구현 전략

- LOW: 1개 파일, 단순 스타일/텍스트
- MEDIUM: 2-5개 파일, 기존 패턴
- HIGH: 5개+ 또는 아키텍처 영향

HIGH면 planner 사용:

```typescript
Task(subagent_type="planner", model="opus", prompt="티켓/피그마/기존패턴 기반 구현 계획 수립")
```

## 7단계: 계획 품질 게이트 (필수)

`release-readiness-gate.md`의 Gate 1 검증:
- 계획 문서화/검토/재검토 완료
- 과도한 구현 제거
- 불명확 항목 사용자 확인

하나라도 FAIL이면 구현 시작 금지.

## 8단계: 구현 시작 여부 확인 (필수)

아래 문구로 확인 후 구현 시작:
- `작업을 시작할까요?`
