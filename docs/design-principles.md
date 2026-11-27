# code-forge 설계 원칙 (Design Principles)

> 이 문서는 code-forge의 모든 의사결정이 따라야 할 핵심 원칙을 기록한다.
> 새 기능 추가, 구조 변경, 에이전트 설계 시 이 원칙에 부합하는지 확인할 것.
> host pack과 새 실행 core의 전환은 [2026-10-18 최종 개선 계획](../plan/code-forge-final-improvement-plan-2026-10-18.md)을 따른다. 문서화와 구현·실호스트·배포 완료는 별도로 기록한다.

---

## 1. 본질적 목적

**"어떤 레포지토리든, 그 레포에 최적화된 에이전트 환경을 세팅해준다."**

- 세팅된 후에는 에이전트들이 그 레포의 **상황/맥락/정책/컨벤션을 완전히 이해**하고 동작한다
- 프론트엔드뿐 아니라 백엔드, 모바일, 인프라까지 — "어떤 레포든"이 목표
- 현재는 프론트엔드(React/Next.js) 모듈이 완성, 백엔드/모바일은 v3.0 로드맵

---

## 2. 크로스플랫폼 (Claude + Codex)

**"Claude든 Codex든, 서브에이전트든 병렬 처리든 막힘 없이 동작한다."**

- **공통 원본, 호스트 어댑터**: 사고 규칙·skill 본문·검증 기준을 모델/벤더 중립으로 유지하고 실제 host 차이만 빌드·설치 단계에서 변환한다. 이 공통 원본과 장기 실행을 맡는 새 core를 구분한다.
- **현재 상태를 과장하지 않는다**: Claude 플러그인 어댑터는 존재하지만 Codex는 `AGENTS.md`와 CLI 브리지 중심의 부분 지원이다. 선택한 plugin/project 설치 방식의 discovery·권한·hook·제거를 실증한 뒤 지원을 선언한다. 특정 출력 디렉터리 생성만으로 완료 처리하지 않는다.
- **`/code-forge:codex`는 호환 브리지일 뿐**: Claude가 공식 Codex plugin/CLI를 호출하는 교차 검증 경로와, Codex가 code-forge를 직접 호스트하는 네이티브 경로를 구분한다.
- **호스트별 능력 차이를 숨기지 않는다**: 모델명, reasoning effort, 권한, 훅 이벤트, 도구 이름은 각 어댑터가 해석한다. 공통 정책에 특정 호스트 문법을 넣지 않는다.
- **opt-in과 graceful degradation**: 어느 한 호스트나 외부 서비스가 없어도 공통 코어와 다른 호스트가 계속 동작해야 한다.

### 왜 Codex를 독립 호스트로 발전시키는가

- 다른 모델의 관점은 같은 모델의 역할극과 동일한 증거가 아니다.
- 사용자가 Claude와 Codex 중 하나를 주 실행기로 선택해도 같은 불변 제약과 검증 계약을 얻어야 한다.
- 브리지 한 개를 유지하는 것보다 공통 소스에서 두 어댑터를 생성하는 편이 장기 드리프트를 줄인다.

---

## 3. 토큰 최적화

**"프리셋/조합 방식으로 불필요한 토큰 소비를 최소화한다."**

- **얇은 척추(thin spine)**: 자동 적재 문서에는 불변 제약, 승인 경계, 검증 명령, 조건부 포인터만 둔다.
- **증거 기반 확장**: 처음부터 관련 문서를 모두 읽지 않는다. 대상 파일과 가장 가까운 기존 패턴에서 시작하고, 해결되지 않은 질문이 있을 때만 다음 참조를 연다.
- **progressive disclosure**: 스킬은 이름·설명으로 발견하고 선택된 스킬 본문과 필요한 reference만 읽는다. 선택되지 않은 스킬의 상세 절차는 주입하지 않는다.
- **CLAUDE.md 60줄 상한**: 매 턴마다 로드되므로 핵심 포인터만 유지
- **include와 포인터 구분**: `@` include는 해당 본문에 항상 필요한 계약에만 쓴다. 선택적 상세는 Markdown 링크로 두고 해당 phase에서 명시적으로 Read한다.
- **Smith 빌드타임 컴파일**: STATE+ACT 상속 체인을 런타임에 해석하지 않고 정적 .md로 사전 컴파일
- **에이전트별 도구 제한**: 불필요한 도구를 disallowedTools로 차단하여 도구 선택 오버헤드 감소
- **권한과 역할 구분**: agent 지침·도구 목록은 host sandbox와 같은 보장이 아니다. Codex custom agent의 부모 권한 상속 등 실제 제한을 adapter에서 확인한다.
- **프리셋**: 5개 모듈을 한 줄로 지정 (standard, modern-stack)
- **위임에도 비용 기준 적용**: 독립적인 read-heavy 작업이거나 메인 컨텍스트 오염을 실제로 줄일 때만 서브에이전트를 쓴다. 한 파일·한 판단을 병렬 에이전트로 쪼개지 않는다.

---

## 4. 독립성

**"외부 의존성 최소, 플러그인 단독으로 완전한 가치 제공."**

- 외부 서비스(Codex, Figma MCP, Jira MCP) 없이도 핵심 기능이 100% 동작
- MCP 연동은 전부 opt-in — 미설정 시 graceful degradation
- `session-init.sh`는 `CLAUDE_PLUGIN_ROOT`가 없으면 자신의 설치 경로를 기준으로 동작하고, 선택 기능의 의존성이 없으면 조용히 건너뛴다
- **레지스트리는 배포 채널, 런타임 의존 아님**: 설치 후에는 100% 로컬 동작
- **직접 실행 보존**: 새 core 없이도 native pack을 사용할 수 있어야 한다. core 설치만으로 작은 작업에 원장·Inbox를 강제하지 않는다. managed Work의 결과가 불명확할 때 native로 자동 재실행하지 않는다.

### 향후 스킬 레지스트리 통합 원칙

- 로컬에서만 쓸 수도, 레지스트리에 등록할 수도 있다
- 등록하면 다른 프로젝트/팀원이 검색 → 다운로드 → 로컬 세팅
- 런타임에 레지스트리 호출 제로 — 설치/업데이트 시에만 사용

---

## 5. 사용자 경험

**"설치 → 세팅 → 사용까지 매끄럽게."**

- **무소음 원칙**: session-init.sh는 버전 일치 시 아무 출력 없음. 불일치 시에만 한 줄 알림
- **최소 놀람 원칙**: 읽기 전용·가역적 검사는 조용히 수행할 수 있지만, 파일 변경·외부 쓰기·비용·파괴적 작업은 범위와 결과를 드러낸다
- **명시적 업데이트**: session start는 기본적으로 네트워크를 호출하지 않는다. dev clone 자동 갱신은 `FORGE_AUTO_UPDATE=1` opt-in이며, 실제 업데이트 뒤에는 `/setup` 재실행 필요성을 한 줄로 알린다
- **Smith 온보딩**: /code-forge:setup이 Smith on 시 /code-forge:smith-create-agent를 자동 호출하며, 그 내부에서 /code-forge:smith-build를 자동 호출
- **hooks**: 위험 명령은 차단한다. 자동 lint/format은 프로젝트의 로컬 바이너리가 있을 때만 실행하며 패키지를 자동 다운로드하지 않는다

---

## 6. 대장간 체계 (Forge Concept)

**"인지적 도제이론을 대장간 메타포로 구현한다."**

인지적 도제이론(Cognitive Apprenticeship)은 6단계로 구성된다: Modeling(시범) → Coaching(지도) → Scaffolding(발판) → Fading(제거) → Articulation(명료화) → Reflection(성찰). 대장간 메타포는 이 이론을 Claude Code 플러그인 구조로 옮긴 것이다.

| 대장간 | 역할 | 구현체 | 도제이론 |
|--------|------|--------|---------|
| **Forge** (대장간) | 전체 작업·학습 환경 | CodeForge 제품군. 기존 host pack과 계획 중인 실행 core | 학습 환경 |
| **Smith** (대장장이) | 에이전트 빌드 시스템 | `plugins/smith/` | Modeling (에이전트가 어떻게 동작해야 하는지 정의) |
| **Anvil** (작업대) | 사용자 인터페이스 | CLI, 스킬, 커맨드 | Coaching (작업마다 가이드) |
| **Whetstone** (숫돌) | 코딩 연습 | 별도 `coding-practice` 프로젝트 | Scaffolding → Fading (점진적 힌트 → 힌트 제거) |
| **Blueprint** (설계도) | 사고모델 + 규칙 | `rules/` | Articulation (원칙 명료화) |
| **Bellows** (풀무) | 로깅/관찰 | `hooks/` | Reflection (사용 패턴 성찰) |
| **Assayer** (감정사) | 테스트 전략·BDD·테스트 작성 | `agents/assayer.md` | 검증할 기준의 명료화 |

이 체계는 코드에 강제하지 않는다. 디렉토리명은 Claude Code 스펙을 따른다. 대장간 이름은 문서와 커뮤니케이션에서만 사용한다.

Blueprint의 사고 guidance·개인 preference와 기계적으로 집행할 invariant·승인 경계를 구분한다. 새 core는 관리 중인 Work의 권한·독립 검증·승인·실행 원장을 소유한다. Assayer의 테스트 작성과 core verifier의 판정, Bellows 관찰과 core ledger의 권위 상태는 서로 대체하지 않는다. Attempt 안의 GAVA `APPLY`와 action의 실제 반영 `APPLY`도 namespace로 구분한다.

Glow는 session/live 표시, Hearth는 재채택할 경우 다중 source의 Markdown 보고서를 맡는다. Herdr는 제어 가능한 터미널 adapter이며 관찰 UI와 같은 권한으로 취급하지 않는다. core schema·DB를 UI가 직접 수정하지 않는다.

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
- 기본 guided 흐름의 구현 확인·커밋 확인 checkpoint를 보존한다. managed 경로에서는 질문·승인을 Inbox에 연결하고 기존에 유효하게 허용한 범위를 반복 질문하지 않는다. 별도 외부 action·권한 확대는 해당 경계에서 확인한다.
- 3단계 fallback: Pencil 메모 → Figma 링크 → 캡처 이미지 순으로 graceful degradation
- 진입점은 단순하게 유지하고, 내부 복잡성은 점진적 컨텍스트와 필요한 만큼의 에이전트만으로 흡수

---

## 9. Whetstone 원칙

**"에이전트가 코드를 짜주는 동안, 사람도 실력을 쌓아야 한다."**

Whetstone은 code-forge 내장 스킬이 아니라 별도 `coding-practice` 프로젝트다. 내장 기능처럼 안내하지 않는다.

- 면접관 페르소나: 답을 주지 않고 질문으로 이끈다
- 4단계 힌트 시스템 (Scaffolding의 점진적 구현): 레벨 1(방향) → 2(개념) → 3(구체적 단서) → 4(거의 정답)
- 힌트를 요청하지 않으면 주지 않는다 — 스스로 생각하는 시간 보장
- 완성 후 리뷰: "이 접근법의 trade-off는?" 같은 심화 질문으로 Articulation 유도
- knowledge/ 파일을 참조하여 "이건 React 베스트 프랙티스 위반입니다" 같은 근거 있는 피드백
- 개인 프로필은 승인된 원본과 프로젝트 overlay로 전달한다. 공개 host pack에 개인 연습 원문을 번들하지 않는다.
- `forge whet`는 반복 패턴의 규칙 후보를 만드는 호환 명령이다. 학습용 Whetstone과 구분하며 사람이 채택하기 전에는 효력이 없다.

---

## 10. assayer (테스트 생성) 자립 원칙

**"code-forge 설치만으로 TDD + BDD + 자동 수정이 완전 동작한다."**

- 외부 패키지 의존 없이 code-forge 자체 assayer 에이전트로 해결
- `docs/assayer-guide.md`에 상세 가이드 (선택자 우선순위, 모킹 사유 분류, Fail-First 전략 등)
- agents/assayer.md는 핵심 계약을 자체 보유하고, 막힌 단계에서만 가이드의 대응 절을 점진 적재
- TDD 모드: 소스 미존재 시 자동으로 Red-Green-Refactor 사이클 진입
- managed Work에서는 Assayer가 테스트를 제안·작성하고, core verifier가 고정된 RepositoryProfile·recipe로 독립 판정한다. 테스트·fixture·threshold 약화를 검출해야 한다.

---

## 의사결정 체크리스트

새 기능이나 구조 변경을 검토할 때:

- [ ] 이 변경이 "어떤 레포든 최적 환경" 목적에 기여하는가?
- [ ] 외부 의존성을 추가하지 않는가? (추가한다면 opt-in인가?)
- [ ] 토큰 효율을 해치지 않는가? (에이전트 크기, CLAUDE.md 크기)
- [ ] 자동 적재 대신 조건부 포인터나 스킬 reference로 늦출 수 있는가?
- [ ] 서브에이전트 추가가 조율 비용보다 큰 독립 이득을 만드는가?
- [ ] 자동 동작이 가역적이고 범위가 명확하며, 변경 결과가 사용자에게 보이는가?
- [ ] 공통 코어와 호스트 어댑터 경계를 지키고 현재 Claude/Codex 지원 수준을 과장하지 않는가?
- [ ] Smith STATE와 modules의 경계를 존중하는가?
- [ ] 대장간 메타포에 부합하는가? (Forge/Smith/Anvil/Whetstone/Blueprint 체계와 충돌하지 않는가?)
- [ ] 개인 판단 기준과 프로젝트 정책을 보존하고 실제 적재·사용자 개입·작업 효과로 개선을 검증하는가?
- [ ] 기존 명령·Voice·Glow·프로젝트 정본과 배포/복구 계약을 보존하는가?
