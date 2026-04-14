# Codex 공존 가이드

> code-forge의 `/codex` (MCP/CLI 듀얼)와 OpenAI 공식 `codex-plugin-cc`(`/codex:review` 등)의 역할 분리.

---

## 배경

- **code-forge `/codex`** — MCP 서버 기반 페어 프로그래밍. 대화형. Claude와 Codex가 같은 문맥에서 교차 검증.
- **codex-plugin-cc (OpenAI 공식)** — 역할별 슬래시 커맨드. 리뷰/적대적 리뷰/구조 복구 등 태스크-지향.

둘은 **경쟁이 아니라 보완**. 같이 설치 가능.

---

## 역할 매트릭스

| 작업 유형 | 추천 도구 | 근거 |
|---------|---------|-----|
| 코드 리뷰 (중립) | `/codex:review` | 공식, read-only. 편향 없음. |
| 적대적 리뷰 (반박 필수) | `/codex:adversarial-review` | 공식, 의도적 반대 입장. |
| 버그 복구 (자율 실행) | `/codex:rescue --background` | 공식, 백그라운드 위임. |
| 페어 프로그래밍 (대화) | code-forge `/codex` | 왕복 논의. 구현 옵션 2-3개 교차. |
| 설계 토론 (다관점) | code-forge `/debate` | Claude + Codex + 자체 토론 모드. |
| 구현 검증 (엣지 케이스) | code-forge `/codex` | Task Lead 패턴. |

---

## 설치 공존

```bash
# 공식
claude plugin install codex-plugin-cc

# code-forge는 이미 설치됨
claude plugin list | grep -E "code-forge|codex"
```

충돌 지점: **슬래시 커맨드 네임스페이스**
- 공식: `/codex:review`, `/codex:rescue`, `/codex:adversarial-review` (prefix `codex:`)
- code-forge: `/codex` (prefix 없음)

prefix가 달라서 충돌 없음.

---

## 선택 가이드 (의사결정 플로우)

```
코드 변경 제안이 필요한가?
├─ 아니요 (읽기만) → /codex:review (공식)
├─ 네, 반박 필요 → /codex:adversarial-review (공식)
└─ 네, 대화형 → code-forge /codex
     ├─ 다관점 토론 필요 → /debate
     └─ 단일 관점 교차 검증 → /codex

자율 실행 필요?
└─ /codex:rescue --background (공식)
```

---

## 데이터 경계

| 도구 | 접근 | 쓰기 권한 |
|-----|------|---------|
| `/codex:review` | 파일 읽기 | 없음 (read-only) |
| `/codex:adversarial-review` | 파일 읽기 | 없음 |
| `/codex:rescue` | 파일 읽기/쓰기 | 있음 (자율) |
| code-forge `/codex` (MCP) | 파일 읽기/쓰기 | 있음 (사용자 승인 시) |
| code-forge `/codex` (CLI) | 전체 | 있음 |

---

## 토큰 비용

공식 plugin은 OpenAI API 직접 호출 — Anthropic 토큰 절약.
code-forge `/codex`도 MCP 경유로 별도 과금.

비용 민감 작업 → 공식 우선. 대화 품질 중시 → code-forge.

---

## 통합 시나리오

### 시나리오 1: 복잡한 PR 리뷰

```
1. /start TICKET-123 → 구현
2. /codex:review → 공식의 중립 피드백
3. /codex:adversarial-review → 반박 포인트 도출
4. code-forge /codex "위 반박에 어떻게 대응?" → 대화형 논의
5. 수정 후 /codex:review 재실행 → 최종 통과 확인
```

### 시나리오 2: 디버깅 막힘

```
1. /start "에러: ..." → thinking-model GROUND 2-3 옵션
2. /codex:rescue --background → 자율 복구 시도 (병렬)
3. 대기 중 code-forge /codex → 옵션 추가 브레인스토밍
4. rescue 결과 + 브레인스토밍 비교 → 선택
```

---

## 버전 호환

| 공식 | code-forge | 비고 |
|-----|-----------|-----|
| codex-plugin-cc 1.x | 4.0+ | 네임스페이스 분리, 완전 호환 |

---

## 참고

- plan.md (로컬): `/Users/ggombee/.claude/plans/mossy-marinating-sun.md` — 도구 조합 전략
- `skills/codex/SKILL.md` — code-forge `/codex` 상세
- `skills/debate/SKILL.md` — 교차 모델 토론
