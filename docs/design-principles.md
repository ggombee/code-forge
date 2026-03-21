# code-forge 설계 원칙 (Design Principles)

> 이 문서는 code-forge의 모든 의사결정이 따라야 할 핵심 원칙을 기록한다.
> 새 기능 추가, 구조 변경, 에이전트 설계 시 이 원칙에 부합하는지 확인할 것.

---

## 1. 본질적 목적

**"어떤 레포지토리든, 그 레포에 최적화된 에이전트 환경을 세팅해준다."**

- 세팅된 후에는 에이전트들이 그 레포의 **상황/맥락/정책/컨벤션을 완전히 이해**하고 동작한다
- 프론트엔드뿐 아니라 백엔드, 모바일, 인프라까지 — "어떤 레포든"이 목표
- 현재는 프론트엔드(React/Next.js) 모듈이 완성, 백엔드/모바일은 v3.0 로드맵

---

## 2. 크로스플랫폼 (Claude + Codex)

**"Claude든 Codex든, 서브에이전트든 병렬 처리든 막힘 없이 동작한다."**

- **Claude Code가 주 플랫폼**: 플러그인 시스템(agents/, skills/, hooks/, modules/)은 Claude Code 네이티브
- **Codex는 페어프로그래밍 파트너**: 다른 모델(GPT-4.x)의 **진짜 다른 관점**을 받는 것이 목적
  - Claude 혼자 역할극하는 것과 본질적으로 다름
  - `/debate` cross-model 토론, 코드 리뷰 더블체크, 페어프로그래밍에 사용
- **opt-in 원칙**: Codex가 없어도 100% 동작, 있으면 추가 가치
- **감지 순서**: CLI headless 우선 (토큰 절감), MCP는 멀티턴 필요 시

### 왜 Codex를 제거하지 않는가

2024-2025년 토론에서 "Codex ROI가 낮으니 제거하자"는 의견이 나왔으나 기각됨. 이유:
- 다른 모델의 관점은 Claude self-debate로 대체할 수 없다 (모델 아키텍처가 다르므로)
- opt-in이므로 유지보수 부담이 크지 않다 (codex.md 1개, SKILL.md 1개)
- 쓰는 사람은 쓰고, 안 쓰는 사람은 무시하는 설계가 이미 되어 있다

---

## 3. 토큰 최적화

**"프리셋/조합 방식으로 불필요한 토큰 소비를 최소화한다."**

- **CLAUDE.md 50줄 제한**: 매 턴마다 로드되므로 토큰 누적 방지
- **@참조 lazy loading**: 모듈 컨벤션은 필요할 때만 로드
- **Smith 빌드타임 컴파일**: STATE+ACT 상속 체인을 런타임에 해석하지 않고 정적 .md로 사전 컴파일
- **에이전트별 도구 제한**: 불필요한 도구를 disallowedTools로 차단하여 도구 선택 오버헤드 감소
- **프리셋**: 5개 모듈을 한 줄로 지정 (standard, modern-stack)

---

## 4. 독립성

**"외부 의존성 최소, 플러그인 단독으로 완전한 가치 제공."**

- 외부 서비스(Codex, Figma MCP, Jira MCP) 없이도 핵심 기능이 100% 동작
- MCP 연동은 전부 opt-in — 미설정 시 graceful degradation
- `session-init.sh`는 `CLAUDE_PLUGIN_ROOT` 미설정 시 조용히 종료
- **레지스트리는 배포 채널, 런타임 의존 아님**: 설치 후에는 100% 로컬 동작

### 향후 스킬 레지스트리 통합 원칙

- 로컬에서만 쓸 수도, 레지스트리에 등록할 수도 있다
- 등록하면 다른 프로젝트/팀원이 검색 → 다운로드 → 로컬 세팅
- 런타임에 레지스트리 호출 제로 — 설치/업데이트 시에만 사용

---

## 5. 사용자 경험

**"설치 → 세팅 → 사용까지 매끄럽게."**

- **무소음 원칙**: session-init.sh는 버전 일치 시 아무 출력 없음. 불일치 시에만 한 줄 알림
- **자동 동기화**: 플러그인 업데이트 후 다음 세션에서 CLAUDE.md 자동 재생성
- **Smith 온보딩**: /smith-create-agent가 내부적으로 /smith-build + /smith-verify를 자동 호출
- **hooks**: 사용자가 인지하지 못하는 사이에 자동 lint 수정, 위험 명령 차단

---

## 6. 대장간 체계 (Forge Concept)

**"인지적 도제이론을 대장간 메타포로 구현한다."**

인지적 도제이론(Cognitive Apprenticeship)은 6단계로 구성된다: Modeling(시범) → Coaching(지도) → Scaffolding(발판) → Fading(제거) → Articulation(명료화) → Reflection(성찰). 대장간 메타포는 이 이론을 Claude Code 플러그인 구조로 옮긴 것이다.

| 대장간 | 역할 | 구현체 | 도제이론 |
|--------|------|--------|---------|
| **Forge** (대장간) | 전체 플랫폼 | code-forge | 학습 환경 |
| **Smith** (대장장이) | 에이전트 빌드 시스템 | `plugins/smith/` | Modeling (에이전트가 어떻게 동작해야 하는지 정의) |
| **Anvil** (작업대) | 사용자 인터페이스 | CLI, 스킬, 커맨드 | Coaching (작업마다 가이드) |
| **Whetstone** (숫돌) | 코딩 연습 | `/practice` | Scaffolding → Fading (점진적 힌트 → 힌트 제거) |
| **Blueprint** (설계도) | 사고모델 + 규칙 | `rules/` | Articulation (원칙 명료화) |
| **Bellows** (풀무) | 로깅/관찰 | `hooks/` | Reflection (사용 패턴 성찰) |

이 체계는 코드에 강제하지 않는다. 디렉토리명은 Claude Code 스펙을 따른다. 대장간 이름은 문서와 커뮤니케이션에서만 사용한다.

---

## 7. Smith (Agent Smith System) 설계 철학

**"STATE(지식)와 ACT(행동)를 분리하여 에이전트를 조합한다."**

- STATE class: "이 에이전트가 무엇을 아는가" (React, TypeScript, TDD 등)
- ACT class: "이 에이전트가 어떻게 행동하는가" (분석, 구현, 리뷰 등)
- instance: STATE + ACT 조합 → 컴파일 → 정적 .md

### Smith STATE ↔ modules 경계

| 구분 | 역할 | 예시 |
|------|------|------|
| Smith STATE | 에이전트 **페르소나의 지식 배경** | "나는 React를 안다" |
| modules | **프로젝트 컨벤션** 상세 | "이 프로젝트에서 React를 이렇게 쓴다" |

둘은 다른 역할이므로 통합하지 않는다. STATE는 에이전트의 정체성, modules는 프로젝트의 규칙이다.

---

## 8. /start 원큐 워크플로우 원칙

**"단일 진입점으로 복잡성을 흡수한다."**

- MD 파일, 텍스트, Figma 링크, 이미지 — 어떤 형태든 `/start` 하나로 진입
- 체크포인트 2개(구현 확인, 커밋 확인)만 사용자가 판단, 나머지는 에이전트가 처리
- 3단계 fallback: Pencil 메모 → Figma 링크 → 캡처 이미지 순으로 graceful degradation
- 진입점을 단순하게 유지하면서 내부 워크플로우는 복잡하게 — 복잡성은 에이전트 체인이 처리

---

## 9. /practice (Whetstone) 원칙

**"에이전트가 코드를 짜주는 동안, 사람도 실력을 쌓아야 한다."**

- 면접관 페르소나: 답을 주지 않고 질문으로 이끈다
- 4단계 힌트 시스템 (Scaffolding의 점진적 구현): 레벨 1(방향) → 2(개념) → 3(구체적 단서) → 4(거의 정답)
- 힌트를 요청하지 않으면 주지 않는다 — 스스로 생각하는 시간 보장
- 완성 후 리뷰: "이 접근법의 trade-off는?" 같은 심화 질문으로 Articulation 유도
- knowledge/ 파일을 참조하여 "이건 React 베스트 프랙티스 위반입니다" 같은 근거 있는 피드백

---

## 10. assayer (테스트 생성) 자립 원칙

**"code-forge 설치만으로 TDD + BDD + 자동 수정이 완전 동작한다."**

- 외부 패키지 의존 없이 code-forge 자체 assayer 에이전트로 해결
- `docs/assayer-guide.md`에 상세 가이드 (선택자 우선순위, 모킹 사유 분류, Fail-First 전략 등)
- agents/assayer.md가 가이드를 @참조로 로드
- TDD 모드: 소스 미존재 시 자동으로 Red-Green-Refactor 사이클 진입

---

## 의사결정 체크리스트

새 기능이나 구조 변경을 검토할 때:

- [ ] 이 변경이 "어떤 레포든 최적 환경" 목적에 기여하는가?
- [ ] 외부 의존성을 추가하지 않는가? (추가한다면 opt-in인가?)
- [ ] 토큰 효율을 해치지 않는가? (에이전트 크기, CLAUDE.md 크기)
- [ ] 사용자가 인지하지 못하는 사이에 동작하는가? (hooks, 자동 동기화)
- [ ] Codex opt-in 원칙을 지키는가? (없어도 동작, 있으면 추가 가치)
- [ ] Smith STATE와 modules의 경계를 존중하는가?
- [ ] 대장간 메타포에 부합하는가? (Forge/Smith/Anvil/Whetstone/Blueprint 체계와 충돌하지 않는가?)
