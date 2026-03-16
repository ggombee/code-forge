# code-forge

> Claude Code 플러그인 — 프로젝트 스택에 맞는 에이전트, 스킬, 컨벤션을 조합하여 제공

---

## 설치

```bash
claude plugin install ggombee/code-forge
```

설치하면 바로 사용 가능합니다. 별도 설정 없이도 21개 에이전트와 20개 스킬이 활성화됩니다.

---

## 시작하기

### 1단계: 프로젝트 스택 세팅 (권장)

```
/setup
```

대화형으로 프로젝트의 프레임워크, 상태관리, 스타일링, 테스팅 스택을 선택합니다.
선택 결과는 `.claude/profile.json`에 저장되고, 이후 에이전트들이 해당 스택의 컨벤션을 자동으로 따릅니다.

```json
// .claude/profile.json 예시
{
  "preset": "partner-standard"
}
```

또는 개별 모듈을 직접 지정할 수도 있습니다:

```json
{
  "modules": {
    "framework": "react-nextjs-app",
    "design-system": "mui",
    "state": "zustand-tanstack",
    "styling": "tailwind",
    "testing": "vitest"
  }
}
```

#### 스택 세팅 없이 사용하면?

**그래도 동작합니다.** 스택 세팅은 선택 사항입니다.

- 세팅 없이도 에이전트, 스킬, 작업 흐름은 모두 정상 작동합니다
- 다만 에이전트가 코드를 작성할 때 **프로젝트 컨벤션을 자동 적용하지 못합니다** (예: Emotion vs Tailwind, Jest vs Vitest 등)
- 에이전트가 기존 코드를 참고하여 스타일을 유추하긴 하지만, `/setup`으로 명시적으로 지정하면 더 일관된 결과를 얻을 수 있습니다

### 2단계: 작업 시작 → 완료

```
/start TICKET-123    # 브랜치 생성, 티켓 분석, 작업 계획
# ... 작업 진행 ...
/done                # 검증 → 커밋 → PR 생성
```

`/start`와 `/done`은 전체 개발 사이클을 자동화합니다. 물론 개별 스킬만 따로 사용해도 됩니다.

---

## 프리셋

자주 쓰는 스택 조합을 프리셋으로 한 번에 적용할 수 있습니다.

| 프리셋 | Framework | Design System | State | Styling | Testing |
|--------|-----------|---------------|-------|---------|---------|
| `partner-standard` | Next.js Pages Router | PDS | Jotai + TanStack Query | Emotion | Jest |
| `modern-stack` | Next.js App Router | MUI | Zustand + TanStack Query | Tailwind | Vitest |

프리셋에 없는 조합이라면 `modules`로 개별 선택하면 됩니다.

---

## 사용 가능한 모듈

| 카테고리 | 선택지 | 하는 일 |
|---------|--------|--------|
| Framework | `react-nextjs-pages` · `react-nextjs-app` · `react-spa` | 라우팅, 페이지 구조, SSR/SSG 컨벤션 |
| Design System | `pds` · `mui` · `ant-design` | 컴포넌트 사용법, 테마 설정 규칙 |
| State | `jotai-tanstack` · `zustand-tanstack` · `redux-rtk` | 상태 관리 패턴, 쿼리 키 관리 |
| Styling | `emotion` · `tailwind` · `styled-components` | 스타일링 방식, 파일 구조 |
| Testing | `jest` · `vitest` | 테스트 작성 패턴, 설정 |

각 모듈은 해당 스택의 **베스트 프랙티스와 코딩 컨벤션**을 에이전트에게 주입합니다.
예를 들어 `emotion` 모듈이 활성화되면, 에이전트는 `css` prop과 `styled` 패턴을 사용하고, `*.styled.ts` 파일 분리 규칙을 따릅니다.

---

## 스킬 가이드

### 작업 흐름

| 스킬 | 설명 | 언제 쓰나 |
|------|------|----------|
| `/start` | 티켓 기반 작업 시작 | 새 작업을 시작할 때. 브랜치 생성 + 컨텍스트 파악 + 계획 |
| `/done` | 작업 완료 처리 | 구현이 끝났을 때. 검증 → 커밋 → PR 생성 |
| `/setup` | 프로젝트 스택 세팅 | 최초 1회 또는 스택 변경 시 |

### 코드 작성/수정

| 스킬 | 설명 | 언제 쓰나 |
|------|------|----------|
| `/generate-test` | BDD 시나리오 기반 테스트 자동 생성 | 컴포넌트나 함수의 테스트가 필요할 때 |
| `/setup-test` | 테스트 환경 초기 세팅 | 프로젝트에 테스트가 아직 없을 때. jest/vitest, MSW 설정 |
| `/bug-fix` | 버그 분석 + 2-3가지 해결 옵션 | 버그를 발견했는데 원인이 불확실할 때 |
| `/refactor` | 리팩토링 분석 + 정책 보호 테스트 | 안전하게 리팩토링하고 싶을 때 |
| `/figma-to-code` | Figma 디자인 → 코드 변환 | Figma URL이 있고 코드로 구현할 때 |
| `/crawler` | Playwright 기반 크롤링 흐름 설계 | 웹사이트 크롤러를 만들 때 |
| `/version-update` | 시맨틱 버전 업데이트 + 커밋 | 릴리스 전 버전을 올릴 때 |

### 분석/사고

| 스킬 | 설명 | 언제 쓰나 |
|------|------|----------|
| `/debate` | 교차 모델 토론 (Claude vs Codex) | 설계 결정에서 여러 관점이 필요할 때 |
| `/research` | 구조화된 리서치 + 신뢰도 등급 리포트 | 기술 선택이나 라이브러리 비교가 필요할 때 |
| `/elon-musk` | 제1원칙 사고법으로 문제 재설계 | 복잡한 문제를 근본부터 다시 생각하고 싶을 때 |
| `/genius-thinking` | TRIZ/SCAMPER/JTBD 프레임워크 아이디어 발상 | 창의적 해결책이 필요할 때 |
| `/startup-validator` | Peter Thiel 7Q + YC PMF 검증 | 사업 아이디어를 엄격하게 검증하고 싶을 때 |

### 도구

| 스킬 | 설명 | 언제 쓰나 |
|------|------|----------|
| `/docs-creator` | CLAUDE.md, README 등 문서 작성 | 프로젝트 문서를 체계적으로 만들 때 |
| `/codex` | OpenAI Codex 페어 프로그래밍 | Codex와 협업하고 싶을 때 (MCP 필요) |
| `/setup-notifier` | Mac 알림 설정 | Claude가 승인 요청할 때 알림을 받고 싶을 때 |
| `/gemini` | Google Gemini CLI 호출 | 멀티모델 비교가 필요할 때 |

### VAS 스킬

| 스킬 | 설명 |
|------|------|
| `/vas-activate` | VAS 에이전트 시스템 활성화 |
| `/vas-create-agent` | 프로젝트 분석 → 맞춤 에이전트 자동 생성 |

---

## 에이전트 (21개)

에이전트는 자동으로 사용됩니다. 직접 호출할 필요 없이, Claude가 작업 맥락에 따라 적절한 에이전트를 선택합니다.

### 분석 전용 — 코드를 읽기만 하고 수정하지 않음

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| `explore` | haiku | 코드베이스 빠른 탐색 |
| `analyst` | opus | 요구사항 분석, 엣지 케이스 발견 |
| `architect` | opus | 아키텍처 분석, 설계 자문 |
| `researcher` | sonnet | 외부 문서/라이브러리 조사 |
| `code-reviewer` | sonnet | 코드 리뷰 (품질+보안) |
| `refactor-advisor` | sonnet | 리팩토링 전략 |
| `vision` | sonnet | 이미지/PDF 분석 |
| `critic` | sonnet | 계획/구현 OKAY/REJECT 판정 |
| `planner` | sonnet | 전략적 계획 수립 |
| `security-reviewer` | sonnet | OWASP Top 10 기반 보안 스캔 |

### 수정 전문 — 코드를 직접 수정

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| `lint-fixer` | haiku | ESLint/TypeScript 오류 수정 |
| `build-fixer` | sonnet | 빌드/컴파일 오류 수정 |
| `testgen` | sonnet | 테스트 코드 생성 |
| `implementation-executor` | sonnet | 계획 기반 즉시 구현 |
| `deep-executor` | sonnet | 자율적 심층 구현 |
| `designer` | sonnet | UI/UX 디자인 설계 및 구현 |
| `document-writer` | sonnet | 기술 문서 작성 |
| `deployment-validator` | sonnet | 배포 전 검증 및 수정 |

### 특수

| 에이전트 | 모델 | 역할 |
|---------|------|------|
| `codex` | sonnet | OpenAI Codex 협업 (MCP opt-in) |
| `git-operator` | sonnet | Git 커밋/브랜치 관리 |
| `qa-tester` | sonnet | tmux 기반 CLI/서비스 테스팅 |

---

## VAS (Vibe-Agent-System)

일반 모드에서는 `agents-default/`의 기본 에이전트가 사용됩니다.
VAS를 활성화하면 STATE(지식) + ACT(행동)를 조합한 **프로젝트 맞춤 에이전트**로 전환됩니다.

### 활성화 방법

세션 시작 시 자동으로 물어보거나, 설정 파일로 미리 지정:

```yaml
# ~/.claude/code-forge.local.md (글로벌)
# .claude/code-forge.local.md (프로젝트 — 글로벌보다 우선)
---
vas:
  enabled: true
---
```

### VAS on/off 차이

| | VAS off (기본) | VAS on |
|---|---------|--------|
| 에이전트 소스 | `agents-default/` | `plugins/vas/agents/_agents/` |
| 에이전트 정의 | Claude Code 네이티브 | STATE + ACT 조합 |
| 프로젝트 전용 | 불가 | `/vas-create-agent`로 맞춤 생성 |

### 언제 VAS를 쓰나?

- **VAS off**: 대부분의 경우 충분합니다. 범용적으로 잘 동작합니다.
- **VAS on**: 특정 스택/도메인에 깊이 최적화된 에이전트가 필요할 때. 예를 들어 "React + Next.js + TypeScript 전문 프론트엔드 구현자"처럼 역할+기술+행동이 정밀하게 조합된 에이전트를 원할 때.

---

## MCP 연동 (선택 사항)

기본 기능은 MCP 서버 없이 모두 동작합니다. 아래는 추가 연동이 필요한 기능:

| MCP 서버 | 관련 기능 | 없으면? |
|----------|----------|--------|
| Codex | `/codex` 페어 프로그래밍 | `/codex` 실행 시 설정 가이드 자동 안내 |
| Figma | `/figma-to-code` 디자인 데이터 fetch | Figma URL 수동 분석으로 폴백 |
| Atlassian | `/start`에서 Jira 티켓 자동 파싱 | 티켓 내용 수동 입력 |

설정 방법은 `docs/codex-mcp-setup-guide.md`를 참고하세요.

---

## 프로젝트 구조

```
code-forge/
├── agents/              # 활성 에이전트 (심링크 — VAS on/off 전환)
├── agents-default/      # 기본 에이전트 21개
├── plugins/vas/         # VAS 에이전트 시스템
│   ├── agents/          #   STATE/ACT 템플릿 + 기본 인스턴스
│   ├── skills/          #   /vas-activate, /vas-create-agent
│   └── rules/           #   VAS 해석 규칙
├── skills/              # 슬래시 스킬 20개
├── modules/             # 스택별 컨벤션 14개
├── presets/             # 프리셋 조합
├── hooks/               # 이벤트 훅 (VAS 전환, 알림)
├── commands/            # 슬래시 커맨드
├── rules/               # 핵심 규칙 (작업 절차, 코딩 표준)
├── instructions/        # 멀티에이전트 협업 가이드
└── docs/                # MCP 설정 가이드
```

---

## FAQ

**Q: 설치만 하면 바로 쓸 수 있나요?**
A: 네. `/setup` 없이도 에이전트와 스킬은 모두 동작합니다. `/setup`은 컨벤션 자동 적용을 위한 권장 단계입니다.

**Q: 프리셋에 내 스택이 없으면?**
A: `modules`로 개별 선택하면 됩니다. 원하는 조합이 모듈 목록에도 없다면, 기존 코드 스타일을 에이전트가 참고하여 작성합니다.

**Q: VAS는 꼭 써야 하나요?**
A: 아닙니다. 기본 모드로도 충분히 강력합니다. VAS는 특정 스택에 더 정밀하게 최적화하고 싶을 때 사용하세요.

**Q: MCP 서버 설정이 필수인가요?**
A: 아닙니다. 모든 핵심 기능은 MCP 없이 동작합니다. Codex 협업, Figma 연동, Jira 연동만 MCP가 필요합니다.

---

## License

MIT
