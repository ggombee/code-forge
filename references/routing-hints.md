# Model Routing Hints

> 스킬/에이전트별 권장 모델 티어. `@` 참조로 필요 시 로드.
> **주의**: 이 파일은 alwaysApply가 아닙니다. thinking-model.md 순수성 보존을 위해 분리됨.

---

## 원칙

- **티어 이름만 사용**: Opus / Sonnet / Haiku (구체 모델 ID, 가격 언급 금지)
- **모델 ID 매핑은 Claude Code `settings.json`에 위임**
- **사고모델과 독립적**: thinking-model.md는 모델 독립적으로 동작, 이 파일은 힌트일 뿐

---

## 스킬별 권장 티어

| 스킬 | 권장 | 근거 |
|------|------|------|
| `/start` (HIGH 복잡도) | **Opus** | 계획 수립 + 다단계 분석, 아키텍처 판단 |
| `/start` (LOW/MED) | **Sonnet** | 일반 구현 |
| `/test --init` | **Sonnet** | 병렬 TC 생성 (Agent Teams) |
| `/test {파일}` | **Sonnet** | 단일 파일 TC 생성 |
| `/e2e` | **Sonnet** | Forge Loop 실행 |
| `/debate` | **Opus** | 다관점 논증, 합의 도출 |
| `/research` | **Sonnet** | 문서 조사 + 요약 |
| `/my-tickets` | **Haiku** | 단순 Jira 조회 + 필터 |
| `/crawler` | **Haiku** | 단순 웹 크롤링 |
| `/figma-to-code` | **Sonnet** | 디자인 분석 + 코드 변환 |
| `/codex` | **Opus** | Codex MCP 호출 (교차 검증) |

---

## 에이전트별 권장 티어

| 에이전트 | 권장 | 근거 |
|---------|------|------|
| architect | **Opus** | 아키텍처 분석, 설계 결정 |
| analyst | **Opus** | 요구사항 분석, 커버리지 갭 발견 |
| Plan | **Opus** | 복잡도 HIGH 작업 계획 수립 |
| explore | **Haiku** | 파일/코드 패턴 탐색 |
| testgen | **Sonnet** | BDD 시나리오 + 테스트 코드 생성 |
| lint-fixer | **Haiku** | 간단 오류 수정 |
| build-fixer | **Sonnet** | 빌드/타입 오류 수정 |
| implementor | **Sonnet** | 계획 기반 구현 |
| code-reviewer | **Opus** | 보안/품질 검토 |
| deep-executor | **Opus** | 자율적 심층 구현 |
| refactor-advisor | **Opus** | 리팩토링 전략 분석 |

---

## 작업 유형별 권장

| 작업 유형 | 권장 | 예시 |
|----------|------|------|
| 복잡한 분석/제안 | **Opus** | 아키텍처 설계, 리팩토링 전략 |
| 일반 구현 | **Sonnet** | 기능 개발, 버그 수정 |
| 단순 탐색/조회 | **Haiku** | 파일 찾기, 티켓 조회 |
| 테스트 작성 | **Sonnet** | TC 생성, spec 작성 |
| 코드 검토 | **Opus** | PR 리뷰, 보안 검토 |

---

## 사용자 선호 (프로젝트별 MEMORY.md 참조)

`MEMORY.md`의 "에이전트 모델 선택" 섹션이 프로젝트별 선호를 정의합니다.

일반적인 패턴:
- **복잡한 사고 필요** → Opus
- **일반 구현** → Sonnet
- **단순 탐색** → Haiku

---

## 모델 변경 대응 (routing drift 방지)

Anthropic이 새 모델 출시 시 이 파일은 **변경 불필요**. 티어 이름(Opus/Sonnet/Haiku)이 유지되는 한 동작.

### 현재 모델 (2026-04-17 기준)

| 티어 | 최신 모델 | 비고 |
|-----|---------|-----|
| **Opus** | claude-opus-4-7 | xhigh effort 지원. 2026-04-16 출시 |
| **Sonnet** | claude-sonnet-4-6 | 기본 코딩 모델 |
| **Haiku** | claude-haiku-4-5 | 경량 탐색용 |

**폐기 예정**: `claude-sonnet-4-20250514`, `claude-opus-4-20250514` → **2026-06-15** 종료. 버전 고정 ID 사용 금지.

모델 ID 매핑은 Claude Code `settings.json` 또는 `.claude/profile.json`에서:
```json
{
  "agents": {
    "analyst": "opus",
    "implementor": "sonnet",
    "explore": "haiku"
  }
}
```

새 모델 티어(예: "ultra")가 추가되면 이 파일에만 행 추가.

---

## 참조 방법

**스킬에서**:
```markdown
@../../references/routing-hints.md
```

**에이전트 spawn 시**:
```typescript
// routing-hints.md의 권장 티어를 참고하여 model 지정
Task(subagent_type='architect', model='opus', prompt='...')
Task(subagent_type='explore', model='haiku', prompt='...')
```