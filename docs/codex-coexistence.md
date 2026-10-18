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
| `skills/` | portable plugin으로 배포 가능하나 이 저장소의 설치·호스트 검증은 미완료 | 공용 본문 재사용, 선별 pack과 host manifest 생성 |
| `agents/*.md` | Claude frontmatter | `.codex/agents/*.toml` 생성. 별도 sandbox는 부모 session/프로세스에서 적용 |
| `hooks/hooks.json` | Claude 경로·matcher·payload 전제 | Codex용 manifest + payload normalizer |
| `skills/setup` | AskUserQuestion·`CLAUDE_PLUGIN_ROOT` 의존 | host-neutral `forge setup` CLI로 핵심 이동 |
| `.claude/state/` | 직접 경로는 Claude 편향 | 현재 bridge는 `bin/forge`를 거치고, native adapter 전에 중립 저장소 전환 검토 |
| `/code-forge:codex` | Claude에서 Codex CLI 자동 호출 | 공식 plugin의 사용자 직접 명령과 별개인 호환 wrapper |

Codex는 root부터 현재 디렉터리까지 `AGENTS.md`를 계층적으로 읽으며, 스킬은 이름·설명만 먼저 노출하고 선택된 `SKILL.md`를 나중에 읽는다. 따라서 root 지침을 키우기보다 progressive disclosure를 활용해야 한다. [AGENTS.md 공식 문서](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [Skills 공식 문서](https://learn.chatgpt.com/docs/build-skills)

## 3. 목표 구조

```text
공통 소스
├── rules/ + references/          # 불변 규칙·라우팅·검증
├── skills/                       # workflow 원본
├── plugins/smith/agents/         # STATE + ACT 원본
└── bin/forge                     # 상태·진단·향후 setup/build

호스트 어댑터
├── Claude: .claude-plugin + agents/*.md + hooks/hooks.json
└── Codex:  portable plugin의 skills/ + 선택형 project agent/hook 설치
```

공통 문서를 복사해 두 벌로 관리하지 않는다. 빌드가 같은 원본에서 호스트별 출력물을 만들고, drift 검사가 출력을 검증한다.

Codex는 루트 `plugin.json`과 `skills/`를 쓰는 portable 형식 및 `.codex-plugin/plugin.json` 호환 형식을 지원한다. project-local `.agents/skills`는 선택 설치 방식으로 검증하며 유일한 배포 경로로 고정하지 않는다. lifecycle hooks가 포함된 pack은 현재 수동 desktop 설치·신뢰 검토 경로와 공개 디렉터리 배포 조건을 구분한다. [공식 패키징 문서](https://developers.openai.com/plugins/build/plugins)

### Codex skill adapter

- 기본 설치는 모든 스킬이 아니라 **core pack**만 노출한다.
- 고비용·외부 호출·대규모 workflow는 `agents/openai.yaml`에서 implicit invocation을 끄고 명시 호출만 허용한다.
- `${CLAUDE_PLUGIN_ROOT}` 참조는 빌드 시 상대 경로나 host-neutral forge root로 변환한다.
- 선택된 `SKILL.md`와 직접 연결된 reference만 읽는다.

Codex는 초기 스킬 목록에 context budget을 적용하고, 스킬이 많으면 설명을 줄이거나 일부를 생략할 수 있다. 전체 카탈로그를 그대로 복제하지 않는 이유다. [Skills 공식 문서](https://learn.chatgpt.com/docs/build-skills)

### Codex agent adapter

프로젝트 범위 custom agent는 `.codex/agents/*.toml`로 생성한다.

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

## 6. 단계별 구현

### P0 — truth cleanup

- 폐지된 스킬·없는 agent·깨진 경로 제거
- routing SSOT를 위험 기반 중립 정책으로 정리
- `/debate`의 강제 합의와 고정 모델 제거
- deprecated `codex mcp-server` 설정 대신 OpenAI 공식 Claude plugin/CLI를 기본 bridge로 안내
- 문서 참조 무결성 검사를 CI와 `forge doctor`에 연결

### P1 — Codex dry-run compiler

- 공용 skill 본문을 재사용하는 선별 pack·manifest를 임시 출력 디렉터리에 생성
- custom agent TOML 3종(scanner/builder/critic) 생성
- 출력 diff와 schema만 검증하고 사용자 홈이나 프로젝트 설정은 변경하지 않음
- token·latency·trigger 정확도는 `route.json`이 아니라 fixture runner의 일회성 CI artifact로 비교

### P2 — opt-in project adapter

- 사용자 승인 범위 안에서 plugin 또는 project-local 설치 방식을 선택하고 생성 파일 소유권을 기록
- Codex에서 instruction discovery, positive/negative skill trigger, sandbox, hook fixture를 smoke test
- Claude 결과와 동일한 불변 제약·검증 결과인지 비교

### P3 — distribution

- 두 호스트의 출력이 안정된 뒤 Codex plugin 또는 범용 plugin 패키징 검토
- 전역 자동 설치, 사용자 홈 자동 수정, silent 외부 action은 금지

## 7. 출시 게이트

Codex native 지원은 다음을 모두 통과한 뒤에만 README의 지원 기능으로 승격한다.

- root instruction과 selected skill만 로드되는지 확인
- 명시 전용 스킬 자동 호출 0건
- scanner/critic의 TOML과 제한된 부모 session/프로세스 조합 fixture에서 로컬 쓰기 0건. builder는 승인된 경로의 쓰기와 범위 밖 차단 검증
- CRITICAL critic의 side-effecting MCP·API·plugin·hook 비활성 또는 stub 검증
- 실행 전후 project diff 0건(로컬 쓰기 탐지 신호이며 외부 부수효과 증명은 아님)
- Claude/Codex fixture에서 critical invariant 누락 0건
- baseline 대비 median token·latency 증가가 허용 범위 이내
- hook payload fixture와 config schema 검증 통과
- 설치·제거 후 사용자 기존 설정이 보존됨

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
- 같은 상태와 정책을 호스트별로 복제
