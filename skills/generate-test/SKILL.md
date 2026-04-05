---
name: generate-test
description: 프론트엔드 테스트 코드를 자동 생성합니다. 소스 코드, Figma 디자인, 요구사항을 분석하여 BDD 시나리오 기반의 테스트 코드를 생성하고 실행까지 수행합니다.
category: implementation
---

# /generate-test

> **참조:** 테스트 설계 시 `rules/build-guide.md` (React/TS 패턴)

프론트엔드 컴포넌트/훅의 테스트 코드를 자동 생성합니다.

## 사용법

```
# 파일 경로 지정
/generate-test src/pages/product/components/ProductCard/index.tsx

# 파일 경로 + Figma 디자인 URL
/generate-test src/pages/product/components/ProductCard/index.tsx --figma https://www.figma.com/design/xxx?node-id=123

# 파일 경로 + Figma + 요구사항 URL (여러 개 가능)
/generate-test src/pages/product/components/ProductCard/index.tsx --figma https://www.figma.com/design/xxx?node-id=123 --req https://www.figma.com/design/xxx?node-id=456 --req https://www.figma.com/design/xxx?node-id=789

# TDD 모드 -- 구현 전에 실패하는 테스트 먼저 생성
/generate-test src/pages/product/components/ProductCard/index.tsx --tdd

# 인자 없이 -- 최근 변경 파일 자동 감지
/generate-test
```

## 실행 워크플로우

### Arguments: `$ARGUMENTS`

**인자가 있는 경우:**

1. 인자를 파싱합니다:
   - 첫 번째 인자: 대상 파일 경로
   - `--figma [URL]`: Figma 디자인 URL
   - `--req [URL]`: 요구사항 URL (여러 개 가능)
   - `--tdd`: TDD 모드 강제 적용 (구현 전에 실패하는 테스트 먼저 생성)

2. 대상 파일이 존재하는지 확인합니다.

3. mode를 결정합니다:
   - `--tdd` 옵션 있음 -> `tdd` 모드
   - `--tdd` 없으면 -> assayer 에이전트가 소스 파일 상태를 보고 자동 결정
     (파일 미존재/스켈레톤 -> tdd, 구현됨+테스트 없음 -> create, 구현됨+테스트 있음 -> update)

4. `assayer` 에이전트에게 Task tool로 위임합니다:

   ```
   Task(subagent_type: "assayer", prompt: "
     targetPath: [대상 파일 경로]
     mode: [create | update | tdd] (--tdd 시 tdd, 아니면 미지정하여 에이전트가 자동 감지)
     figmaUrl: [Figma URL 또는 없음]
     requirementUrls: [요구사항 URL 목록 또는 없음]
   ")
   ```

5. 에이전트 결과를 요약하여 사용자에게 보고합니다.

**인자가 없는 경우 (자동 감지 모드):**

`@see` JSDoc 태그가 있는 파일만 자동 감지 대상으로 합니다. 기획서/디자인 링크가 연결된 파일이 테스트 생성 효과가 가장 높기 때문입니다.

1. `git diff --name-only`와 `git diff --cached --name-only`로 최근 변경 파일 목록을 확인합니다.

2. 기본 필터링:
   - `.ts`, `.tsx`, `.js`, `.jsx` 파일만
   - 제외: `*.test.*`, `*.spec.*`, `*.stories.*`, `*.mock.*`, `styled.*`, `constants.*`, `types.*`
   - 제외 디렉토리: `node_modules`, `dist`, `.next`, `__mocks__`, `__tests__`

3. **`@see` 태그 필터링**: 각 파일을 Grep하여 `@see` JSDoc 태그가 포함된 파일만 대상으로 선정합니다.
   - `@see` 태그가 없는 파일은 자동 감지 대상에서 제외
   - `@see` 태그가 없는 파일에 테스트를 생성하려면 경로를 직접 지정: `/generate-test src/path/to/file.tsx`

4. 대상 목록을 사용자에게 보여주고 확인을 받습니다:

   ```
   @see 태그가 포함된 최근 변경 파일:

   1. src/pages/product/components/ProductCard/index.tsx
      @see Figma(디자인), @see TICKET-12345(이슈) -> 테스트 신규 생성

   2. src/hooks/useCart.ts
      @see Figma(요구사항) -> 기존 테스트 업데이트

   어떤 파일에 대해 테스트를 생성할까요?
   ```

5. 사용자가 선택한 파일에 대해 `assayer` 에이전트를 호출합니다.

6. 전체 결과를 요약합니다.

## 핵심 동작

- Figma URL이 제공되면 에이전트가 **기획서 + 디자인을 분석하여 BDD 시나리오를 도출**하고, 이를 기반으로 테스트를 생성합니다.
- Figma URL이 없으면 **소스 코드 분석만으로 통합 테스트 관점의 테스트**를 생성합니다.
- 소스 코드의 JSDoc `@see` 태그에 Figma/이슈 트래커 링크가 있으면 자동으로 참고합니다.
- 생성된 테스트는 자동으로 실행되며, 실패 시 최대 5회 자동 수정을 시도합니다.
- 프로젝트에 customRender가 없어도 Provider를 자동 분석하여 동작하는 테스트를 생성합니다.

## 외부 서비스 연동

### Figma

- Figma MCP 서버가 설정되어 있으면 자동으로 디자인 데이터를 가져옵니다.
- 미설정 시 사용자에게 Figma 내용 복사/붙여넣기를 요청합니다.

### 이슈 트래커 (Jira / GitHub Issues 등)

소스 코드의 JSDoc `@see` 태그에서 이슈 트래커 URL이 발견되면 자동으로 데이터를 가져옵니다.

- Atlassian MCP 서버가 설정되어 있으면 MCP 도구로 자동 fetch
- GitHub Issues는 gh CLI로 자동 fetch
- MCP 서버가 없으면 사용자에게 내용 붙여넣기 요청
