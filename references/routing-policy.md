# Routing Policy — 모델/벤더 라우팅의 단일 진실

> 라우팅 결정의 canonical 문서 (2026-06-12 신설 — Option C Phase 1 H4).
> 구 `instructions/agent-patterns/model-routing.md`(티어 매트릭스)를 대체 — 원문은 `archive/instructions/model-routing.md` 보존.
> 스킬/에이전트별 권장 티어 힌트는 [`routing-hints.md`](routing-hints.md) (본 정책의 보조 표).

---

## 1. 라우팅 가능한 축 — 정직한 능력 서술

| 축 | 라우팅 가능? | 수단 |
|---|---|---|
| **티어** (haiku/sonnet/opus/fable) | ✅ | 에이전트 frontmatter `model:` 핀, Task() model param |
| **벤더** (claude/codex) | ✅ | codex CLI 호출 (reasoning_effort는 codex만 실제 param) |
| **모델 버전** (4.8 vs 4.7 …) | ❌ | 별칭 슬롯이라 불가. 유일한 버전 노브 = 세션 전역 `settings.json` `"model"` (/model) |
| **effort** (Claude 서브에이전트) | ⚠️ advisory | Task()에 effort param 없음 — 권고만 가능. 실제 레버 = 티어 선택 + codex reasoning_effort |

**실측 (2026-06-11, main=claude-fable-5[1m]):** `model: opus` 핀 서브에이전트의 transcript `.message.model` = `claude-opus-4-8`. **티어 별칭은 main 모델이 아니라 해당 티어의 최신으로 해석**된다. 따라서:
- 핀 유지 = 티어 최신 고정 (비용 예측 가능)
- 핀 제거 = main 세션 모델 상속 (main이 상위 티어면 비용 상승)

`model_version`은 **표시/추적 전용** — 라우팅 노브 아님 (verbatim 기록, `docs/contracts/event-schema.md` §5).

## 2. 핀 정책 (14개 — 산출: `grep -l 'model:' agents/*.md | wc -l`)

| 핀 | 에이전트 | 근거 |
|---|---|---|
| `haiku` ×2 | scout, lint-fixer | **기계적 작업 비용 격리** (DEFENDED — main 2x 단가 시대에 가치 상승) |
| `sonnet` ×10 | implementor, deep-executor, assayer, code-reviewer, git-operator, researcher, refactor-advisor, vision, codex, build-fixer | 일꾼 티어 — 품질/비용 균형 |
| `opus` ×2 | architect, analyst | 깊은 분석. **2026-06-12 사용자 결정 ⓐ: 핀 유지** — opus-4-8 고정($5/$25). 제거(=Fable 상속, 2x) 대안은 기각. 재논의 트리거: opus 티어 가격/성능 구조가 바뀔 때 |

**원칙**: 핀은 비용 통제 수단이다. 새 상위 티어(예: fable)가 나와도 핀된 에이전트는 영향받지 않는다 — 의도된 동작. 일괄 핀 제거 금지 (2026-06-11 검토: haiku 에이전트 최대 10x 비용 회귀).

## 3. effort 정책

- API enum: `low|medium|high|xhigh|max`. **`ultracode`는 Claude Code 하니스 전용 레벨** (xhigh + 워크플로우 오케스트레이션) — API param으로 전달 금지, 기록은 verbatim.
- **Claude 서브에이전트의 effort 상한은 advisory** — 하니스가 강제 불가. `AUTO_EFFORT_MAX=xhigh` (Phase 2에서 routing.json에 명문화 예정)는 auto 경로 권고 상한이고, `max`/`ultracode`는 manual-only.
- 실제 비용 제어 수단: ① 티어 핀 (§2) ② codex `reasoning_effort` (실 param) ③ 작업 명세를 첫 턴에 완결되게 (재질문 루프 감소).

## 4. 결정 시점과 운반

- 라우팅 결정은 **/start GROUND→PLAN 경계에서 1회** (scout의 저비용 신호 수신 후) — per-phase 재라우팅 churn 금지.
- 결정의 운반: `bin/forge emit-event` → `.claude/state/route.json` (latest-only) → `bin/forge status --json`의 `route` 키 → HUD 표시 (Phase 2-3 플래그 뒤). 계약: `docs/contracts/event-schema.md`.
- RoutingDecision shape (canonical — OVERHAUL_PLAN §5): `{agent, model(tier), model_version(표시전용), role, effort_per_phase, cross_vendor}`.

## 5. Phase 2+ 예정 (이 문서가 확장될 자리)

- complexity judge → effort 매핑 표 (LOW→low, MED→medium/high, HIGH→high/xhigh; `routing.json`의 AUTO_EFFORT_MAX 상수)
- FR3 role split (codex-plan/claude-code) 선택 규칙 — off by default, graceful skip
