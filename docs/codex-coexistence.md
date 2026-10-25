# Claude–Codex 멀티런타임 설계

> **현재 상태:** Claude Code 네이티브, Codex 부분 지원. OpenAI 공식 Claude bridge와 `/code-forge:codex` 호환 wrapper는 Codex 네이티브 호스팅과 다르다.
> **정책 SSOT:** [`references/routing-policy.md`](../references/routing-policy.md)
> **전환 계획:** [2026-10-18 최종 개선 계획](../plan/code-forge-final-improvement-plan-2026-10-18.md). 아래 native pack과 새 core runtime은 별도 검증 대상이다.

---

## 1. 지원 수준을 구분한다

| 경로 | 의미 | 현재 |
|---|---|---|
| **Claude native** | Claude plugin이 skills, agents, hooks를 직접 로드 | 동작 |
| **Claude → Codex bridge** | 사용자가 공식 `codex-plugin-cc`를 직접 실행하거나 Claude가 CLI로 Codex 호출 | 두 경로 동작 |
| **Codex native** | Codex가 code-forge의 skills, agents, hooks를 직접 로드 | 설계 단계 |

`AGENTS.md`를 Codex가 읽는 것만으로 전체 지원이라고 부르지 않는다. 현재 `skills/`, `agents/`, `hooks/hooks.json`, `/setup`은 Claude 형식과 도구 이름에 묶여 있다.

## 2. 현재 호환성

| 표면 | Codex에서 현재 상태 | 필요한 변화 |
|---|---|---|
| `AGENTS.md` | 네이티브 로드 가능 | 자동 적재 내용은 최소 계약으로 유지 |
| `rules/`, `references/` | 파일로 읽을 수 있음 | 선택된 workflow에서만 지연 로드 |
| `skills/` | portable plugin으로 배포 가능하나 이 저장소의 설치·호스트 검증은 미완료 | 공통 정책과 필요한 특화 본문, 선별 pack과 host manifest 생성 |
| `agents/*.md` | Claude frontmatter | `.codex/agents/*.toml` 생성. 별도 sandbox는 부모 session/프로세스에서 적용 |
| `hooks/hooks.json` | Claude 경로·matcher·payload 전제 | Codex용 manifest + payload normalizer |
| `skills/setup` | AskUserQuestion·`CLAUDE_PLUGIN_ROOT` 의존 | host-neutral `forge setup` CLI로 핵심 이동 |
| `.claude/state/` | 직접 경로는 Claude 편향 | 현재 bridge는 `bin/forge`를 거치고, native adapter 전에 중립 저장소 전환 검토 |
| `/code-forge:codex` | Claude에서 Codex CLI 자동 호출 | 공식 plugin의 사용자 직접 명령과 별개인 호환 wrapper |

Codex는 root부터 현재 디렉터리까지 `AGENTS.md`를 계층적으로 읽으며, 스킬은 이름·설명만 먼저 노출하고 선택된 `SKILL.md`를 나중에 읽는다. 따라서 root 지침을 키우기보다 progressive disclosure를 활용해야 한다. [AGENTS.md 공식 문서](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [Skills 공식 문서](https://learn.chatgpt.com/docs/build-skills)

## 3. 목표 구조

기억·맥락 연결과 관리형 실행은 별도 선택이다. native 호스트에 승인된 기억만 제공할 때는 managed Work를 요구하거나 코어가 실행 완료를 판정하지 않는다. 기억 접근·전송·갱신 권한은 여전히 집행하며 실제 행동·피드백을 관측하지 못하는 연결은 그 한계를 표시한다.

여러 모델이 공통 개인화 코어의 승인된 기억·판단 기준을 사용하도록 연결한다. 개인 어시스턴트는 지속되는 제품 경험이며 native/custom agent는 실행 구성이다. 코어가 선택한 기억·지시의 revision과 실제 전달을 확인하고 결과·교정을 같은 근거 체계에 돌려준다. 호스트별 전달본은 정본을 대체하지 않으며 삭제·철회·오래된 cache·동시 수정·모델 교체를 검사한다. 기존 로컬 OSS 사용에 서버 연결을 강제하지 않는다.

제품 중심을 정책·지침 구성 compiler와 결정적 도구로 옮기고 host 접점은 필요한 기능만 노출하는 방향을 검증한다. 아래 트리는 원본과 배포 접점의 구분이며 전체 workflow 본문을 모두 설치·주입한다는 뜻은 아니다. managed core는 고정된 모듈·산출물을 직접 소비하며 plugin의 `/start`를 다시 실행 엔진으로 사용하지 않는다. 현재/최소 plugin·직접 소비의 비용 비교와 단계적 전환은 [통합 계획 §2](../plan/code-forge-final-improvement-plan-2026-10-18.md#2-저장소를-나누는-이유와-소유권)를 따른다.

```text
공통 소스
├── rules/ + references/          # 불변 규칙·라우팅·검증
├── skills/                       # workflow 원본
├── plugins/smith/agents/         # STATE + ACT 원본
└── bin/forge                     # 상태·진단·결정적 도구·향후 setup/build

호스트 어댑터
├── Claude: .claude-plugin + agents/*.md + hooks/hooks.json
└── Codex:  portable plugin의 skills/ + 선택형 project agent/hook 설치
```

공통 정책의 변경 전파를 유지하되, 호스트·모델별 별도 파일과 본문을 허용한다. 빌드는 공통 정책과 명시적으로 소유한 특화 원본을 합성해 호스트별 출력물을 만들고, 각 component/지원 조합의 정본·digest와 정책 drift를 검사한다. Claude용 전문의 기계적 변환만으로 충분하다고 가정하지 않는다. 같은 저장소에서 시작하되 배포·의존성·소유권 문제를 실증하면 저장소 분리도 ADR로 결정한다.

필수 지침은 Codex의 `AGENTS.md` 등 자동 적재 경로에 직접 제공하고 `CLAUDE.md`를 읽으라는 자연어 포인터에만 의존하지 않는다. 적재 방식과 공용/특화 본문의 품질·비용 비교는 [통합 계획 §3](../plan/code-forge-final-improvement-plan-2026-10-18.md#3-멀티모델-지원의-정확한-범위)을 따른다. 별도 파일이 디스크에 있다는 이유로 모두 주입하지 않는다. 동일 동작 보장 대신 공통 안전성·권한·검증 기준과 지원 조합별 품질을 확인한다.

Codex는 루트 `plugin.json`과 `skills/`를 쓰는 portable 형식 및 `.codex-plugin/plugin.json` 호환 형식을 지원한다. project-local `.agents/skills`는 선택 설치 방식으로 검증하며 유일한 배포 경로로 고정하지 않는다. lifecycle hooks가 포함된 pack은 현재 수동 desktop 설치·신뢰 검토 경로와 공개 디렉터리 배포 조건을 구분한다. [공식 패키징 문서](https://developers.openai.com/plugins/build/plugins)

agent가 목표·환경·필요 효과에 맞는 기능과 다음 행동을 선택하고 host/core가 권한·예산·상태·검사 근거를 집행한다. 지원 수준은 고정된 스킬 호출 순서의 일치가 아니라 이 계약과 실제 결과로 판단한다. 최소 한 흐름부터 실증하며 모든 스킬 변환이나 범용 SDK를 선행 조건으로 만들지 않는다. 현재 소스별 공백과 profile의 정본·수명은 통합 계획 §4~5를 따른다.

### Codex skill adapter

- 기본 설치는 모든 스킬이 아니라 **core pack**만 노출한다.
- 고비용·외부 호출·대규모 workflow는 `agents/openai.yaml`에서 implicit invocation을 끄고 명시 호출만 허용한다.
- `${CLAUDE_PLUGIN_ROOT}` 참조는 빌드 시 상대 경로나 host-neutral forge root로 변환한다. 도구·호출 흐름·예시까지 달라야 하면 별도 Codex 본문을 작성·평가한다.
- 선택된 `SKILL.md`와 직접 연결된 reference만 읽는다. 검사 실행·테스트 작성·환경 설치를 다른 효과로 선언하고 미지원 capability를 묵시적으로 대신 실행하지 않는다.
- managed 하위 호출은 같은 Work의 남은 예산·질문/승인·검사 계약을 공유한다. `/start`·`test`의 로컬 전체 흐름을 중첩 실행하거나 하위 loop마다 재시도 한도를 초기화하지 않는다.

Codex는 초기 스킬 목록에 context budget을 적용하고, 스킬이 많으면 설명을 줄이거나 일부를 생략할 수 있다. 전체 카탈로그를 그대로 복제하지 않는 이유다. [Skills 공식 문서](https://learn.chatgpt.com/docs/build-skills)

### Codex agent adapter

프로젝트 범위 custom agent는 `.codex/agents/*.toml`로 생성한다.

별도 custom agent는 기본 agent에 같은 프로젝트 지식·도구를 제공하는 것보다 이득이 있을 때만 추천한다. 아래 역할 표는 능력 후보이며 모든 프로젝트에 생성할 목록이 아니다. 지식은 작은 profile/skill로 전달하고 역할 파일은 0개일 수 있다. Smith·custom agent 효용 비교와 기존 정의의 유지·자동 이관·보류·복구는 통합 계획 §2·8을 따른다.

기본은 최소 프로젝트 계약과 필요한 profile/로컬 근거를 선택해 현재 모델에 전달하는 경로다. profile은 기존 지침·manifest를 재사용하고 같은 정보의 중복 파일이나 매 요청의 생성형 선택 단계를 추가하지 않는다. 잘 설정된 native 모델, 선택 profile 추가, 임시 agent 추가의 품질·초기/유지·작업당 비용을 나눠 비교하고 이득 있는 단계만 사용한다.

일회 작업은 우리 skill/compiler가 최소 지침·도구 요구·완료 조건을 조립해 native 기본 subagent의 작업 prompt로 전달하는 경로를 우선 비교한다. 별도 실행 설정이 필요할 때만 지원되는 임시 custom 구성을 사용하며, 새 TOML 파일의 실행 중 discovery·갱신·정리를 검증 없이 가정하지 않는다. 기존 프로젝트 agent 원본/출력에 임시 정의를 덮어쓰거나 종료 시 삭제하지 않는다. 결과·검증·usage·인계 근거를 회수한 뒤 종료하고 작업용 정의만 정리한다. 임시 구성은 실제 권한을 확대하지 않으며 file/thread 종료가 host/provider 기록 삭제를 뜻하지 않는다. 상세 생명주기와 비용 비교는 통합 계획 §2를 따른다.

| 공통 역할 | 필요한 실행 경계 | model class | reasoning |
|---|---|---|---|
| scanner | read-only | FAST | low |
| builder | workspace-write | BALANCED | medium |
| critic | read-only | DEEP | high |
| researcher | read-only | BALANCED/DEEP | medium/high |

현재 표는 필요한 경계를 표현하며 TOML이 경계를 강제한다는 보장이 아니다. custom agent는 모델·effort·지침과 지원되는 capability 축소 설정을 가질 수 있지만 sandbox·approval·provider·MCP는 부모 설정을 상속한다. 향후 resolver는 모델 설정과 부모 session/별도 프로세스의 권한 설정을 구분해 검증한다. [Subagents 공식 문서](https://learn.chatgpt.com/docs/agent-configuration/subagents)

TOML의 역할 지침만으로 별도 read-only sandbox를 만들지 않는다. 제한된 부모 session 또는 `codex exec` 프로세스의 sandbox와 MCP·API·plugin·hook의 부수효과를 따로 확인한다. 실행 전후 diff 0은 로컬 쓰기 탐지의 보조 신호다. 자동 bridge는 `--ignore-user-config`로 사용자 config를 제외하되 project config와 도구 표면은 별도로 감사한다. CRITICAL critic은 side-effecting 도구를 비활성화하거나 stub 처리한 통제 fixture/profile에서만 실행한다.

### Hook adapter

hook의 정책 로직과 호스트 payload 파싱을 분리한다.

```text
Claude payload ─┐
                ├─ normalize-event ─→ guard / log / quality core
Codex payload ──┘
```

- Claude 전용 `Notification`, `FileChanged` 같은 이벤트를 Codex에 억지로 복제하지 않는다.
- 공통 lifecycle만 매핑하고, 지원하지 않는 이벤트는 capability report에 `unsupported`로 남긴다.
- Codex project hook은 trusted project에서만 실행되며 변경 시 재검토 대상이다. [Hooks 공식 문서](https://learn.chatgpt.com/docs/hooks)
- write 차단은 프롬프트가 아니라 sandbox와 실제 tool event에서 강제한다.

### Setup adapter

장기적으로 `/setup`의 결정적 부분을 다음 CLI로 이동한다.

```bash
bin/forge setup --host auto
bin/forge build --target claude
bin/forge build --target codex
bin/forge build --target all
```

스킬은 대화형 UI와 승인만 담당하고, 스택 감지·파일 생성·검증은 테스트 가능한 CLI가 담당한다. 이렇게 해야 Claude의 `AskUserQuestion` 유무와 무관하게 Codex CLI에서도 같은 결과를 만들 수 있다.

### 배포와 업데이트

CodeForge의 지침 구성·결정적 도구는 버전 있는 묶음과 host별 native 패키지로 전달한다. Codex도 plugin을 지원하는 환경에서는 필요한 기능만 담은 native 설치·갱신을 우선 실증하고, 플러그인 경로가 없는 host에는 대체 pack과 설치·갱신 도구를 제공한다. 최소 plugin만으로 같은 효율이 나오면 큰 구조 변경을 생략한다. 공통 도구는 필요한 패키지에 함께 넣을 수 있으며 모든 사용자의 별도 CLI·daemon 설치나 매 작업 중계를 전제하지 않는다. 단일 release catalog에서 host별 manifest·version/digest·호환 조합을 연결하고, 아직 도착하지 않은 채널은 배포 완료로 표시하지 않는다.

native plugin manager는 자신이 설치한 cache를 갱신하고 공통 도구는 자신이 소유한 프로젝트 생성물을 관리한다. 독립 pack 갱신은 공통 도구가 맡으며 같은 경로에 두 updater를 붙이지 않는다. 사용자가 선택한 자동 갱신 범위 안에서는 반복 승인 없이 새 세션 경계에 적용하되 실행 중 Work의 버전은 유지한다. 설치된 패키지·실제 적재된 세션·생성된 AGENTS/Smith 출력의 버전을 각각 확인한다. host별 갱신·고정·활성화·rollback 지원과 검사 기준은 [통합 계획 §8](../plan/code-forge-final-improvement-plan-2026-10-18.md#8-출시와-완료-판정)을 따른다. 이 설치·갱신 도구는 아직 구현하지 않았다.

## 4. 모델·사고 깊이 오케스트레이션

공통 라우터는 모델명을 고르지 않고 다음 중립 결과만 낸다.

```json
{
  "complexity": "LOW|MEDIUM|HIGH|CRITICAL",
  "phase": "ground|plan|build|verify",
  "model_class": "FAST|BALANCED|DEEP",
  "effort_level": "minimal|low|medium|high|xhigh|max|ultra",
  "orchestration": "direct|scan|plan-build|plan-build-critic|checkpoint-verify",
  "plan_required": true,
  "critic_required": false,
  "actual_orchestration": "pending|direct|scan|plan-build|plan-build-critic|checkpoint-verify",
  "actual_agents": [],
  "actual_model_class": null,
  "actual_effort_level": null
}
```

향후 P1/P2 Codex resolver가 이를 custom agent의 `model`·`model_reasoning_effort`와 별도 부모 session/프로세스 권한 설정으로 변환한다. 현재 snapshot의 route 값은 권고와 관측 기록이며 native runtime을 제어하지 않는다. Claude adapter는 티어 alias와 실제 지원되는 권한 경계로 변환하고, 강제할 수 없는 effort는 advisory로 기록한다.

높은 reasoning은 자동 정답 보장이 아니며 토큰과 지연을 늘린다. 대표 작업 eval에서 이득이 확인된 경우에만 높인다. OpenAI 공식 가이드도 lean prompt, 의도적인 effort 선택, 동일 task 비교를 권장한다. [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model)

## 5. 상태와 재진입

- 새 `.codex/state`나 Paperthin `.re0`를 만들지 않는다.
- 현재 Claude→Codex CLI bridge의 상태 조회·기록은 Claude 호스트가 `bin/forge`를 거쳐 수행한다.
- 향후 Codex native adapter도 직접 `.claude/state/`를 쓰지 않고 `bin/forge` 호환 표면을 사용하게 한다.
- 기존 `.claude/state` 경로는 당분간 내부 호환 세부로 취급한다.
- 중립 `.forge/state`로 이동하려면 forge-glow 등 기존 consumer의 dual-read 배포가 먼저다.
- session start에는 원문 tail 대신 `Needs you → Changed → Next`의 짧은 briefing만 주입하는 방향으로 전환한다.
- 중립 runtime 경로로 이동해도 프로젝트의 progress·ADR와 개인 프로필 정본을 복제하지 않는다. 새 core의 Work ledger와 기존 `forge-status/v1`은 별도 계약으로 연결한다.
- `native` 직접 작업과 명시적으로 접수한 `managed` Work를 구분한다. core 장애 때 managed Work를 native로 자동 재실행하지 않는다.

음성 전사도 인증된 동일 작업의 입력으로 연결한다. host별 로컬 dictation·자동 paste는 웹·모바일의 실행 승인과 별도다. 개인 선호는 `coding-practice` 없이 사용할 수 있으며 기존 승인 원본의 선택 참조만 허용한다. 사람의 코딩 연습 저장소는 native pack·서비스 설치나 출시의 의존성이 아니다.

## 6. 단계별 구현

### P0 — truth cleanup

- 폐지된 스킬·없는 agent·깨진 경로 제거
- routing SSOT를 위험 기반 중립 정책으로 정리
- `/debate`의 강제 합의와 고정 모델 제거
- deprecated `codex mcp-server` 설정 대신 OpenAI 공식 Claude plugin/CLI를 기본 bridge로 안내
- 문서 참조 무결성 검사를 CI와 `forge doctor`에 연결

### P1 — Codex dry-run compiler

- 공통 정책과 필요한 host/model 특화 본문을 합성하는 선별 pack·manifest를 임시 출력 디렉터리에 생성
- 실제 효용 비교에 필요한 custom agent TOML 후보만 생성. native 기본 agent로 충분하면 프로젝트별 역할 출력은 생략
- 출력 diff와 schema만 검증하고 사용자 홈이나 프로젝트 설정은 변경하지 않음
- token·latency·trigger 정확도는 `route.json`이 아니라 fixture runner의 일회성 CI artifact로 비교

### P2 — opt-in project adapter

- 사용자 승인 범위 안에서 plugin 또는 project-local 설치 방식을 선택하고 생성 파일 소유권을 기록
- Codex에서 instruction discovery, positive/negative skill trigger, sandbox, hook fixture를 smoke test
- Claude 결과와 동일한 불변 제약·검증 기준을 적용하는지 비교하고 지원 조합별 실제 품질을 확인
- 검사 부재·테스트 생성·설치 효과, 공유 retry budget, 질문/재개·증거 보존과 검증 뒤 hook 변경의 무효화 fixture 확인

### P3 — distribution

- G0b에서 선택하고 두 호스트에서 검증한 native plugin/대체 pack을 공통 release 계약으로 배포
- 설치물별 갱신 주체·선택한 자동 갱신·다음 세션 활성화·프로젝트 생성물 이관·rollback/uninstall 검증
- 전역 자동 설치, 사용자 홈 자동 수정, silent 외부 action은 금지

## 7. 출시 게이트

Codex native 지원은 다음을 모두 통과한 뒤에만 README의 지원 기능으로 승격한다.

- 첫 도구 실행 전에 필수 root instruction이 직접 적재되고 필요한 skill만 선택되는지 확인. 계층·override·크기 제한·다른 호스트 파일 공존·재개/압축의 중복·누락 검사
- 명시 전용 스킬 자동 호출 0건
- scanner/critic의 TOML과 제한된 부모 session/프로세스 조합 fixture에서 로컬 쓰기 0건. builder는 승인된 경로의 쓰기와 범위 밖 차단 검증
- CRITICAL critic의 side-effecting MCP·API·plugin·hook 비활성 또는 stub 검증
- 실행 전후 project diff 0건(로컬 쓰기 탐지 신호이며 외부 부수효과 증명은 아님)
- Claude/Codex fixture에서 critical invariant 누락 0건
- 공용/특화 본문을 같은 작업·정책으로 비교하고 cold/warm token·간접 Read·cache·재시도·latency·성공률·검증 완료당 총비용과 유지 비용에 근거해 채택
- hook payload fixture와 config schema 검증 통과
- 설치·제거 후 사용자 기존 설정이 보존됨
- 패키지 업데이트 뒤 실제 새 세션의 적재 버전과 프로젝트 생성물이 승인된 조합에 해당함. 실행 중 갱신·두 host 버전 차이·부분 실패·복구 검사 통과

## 8. cross-model bridge

Claude에서 Codex를 호출할 때 사용자 직접 workflow에는 [OpenAI 공식 `codex-plugin-cc`](https://github.com/openai/codex-plugin-cc)를 우선한다. 공식 `/codex:review`·`/codex:adversarial-review`는 사용자 직접 명령이고, `/codex:rescue`는 조사·수정 위임이다. `skills/codex`는 자동 실행이 필요할 때의 CLI wrapper이며 `agents/codex.md`는 read-only review 전용이다.

- 자동 단일 리뷰는 검증된 wrapper가 작업공간 밖 mode-600 임시 파일에 prompt를 준비한 뒤 `codex exec --ignore-user-config --sandbox read-only - < "$CODEX_PROMPT_FILE"`로 stdin 전달한다. raw 목표나 로그를 shell argv에 보간하지 않는다. 이 sandbox는 로컬 파일시스템 경계이며 project config와 외부 도구는 별도 감사한다. [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)
- `codex mcp-server` 기반 신규 연결은 만들지 않는다. 기존 사용자는 [`codex-mcp-setup-guide.md`](codex-mcp-setup-guide.md)의 이관 순서를 따른다.
- 모델 ID와 비용 절감률을 문서에 고정하지 않는다.
- bridge가 없어도 Claude native와 향후 Codex native는 독립적으로 동작해야 한다.
- code-forge 호환 wrapper 유지 여부는 실제 사용량과 공식 plugin으로의 대체 가능성을 기준으로 결정한다.

## 하지 않을 것

- Paperthin 또는 모든 code-forge 스킬을 전역으로 일괄 설치
- `AGENTS.md`에 상세 카탈로그·모델표·workflow 전문 삽입
- Claude hook JSON을 이름만 바꿔 Codex에 복사
- prompt 역할극을 read-only sandbox로 간주
- 고정된 최신 모델 ID를 canonical 문서에 보존
- 같은 Work의 상태 원장을 호스트별로 중복 운영하거나 공통 정책의 변경 전파 없이 사본을 유지. 평가로 채택한 별도 host/model 본문과 생성물은 허용
