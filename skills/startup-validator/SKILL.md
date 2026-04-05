---
name: startup-validator
description: Peter Thiel 7 Questions + YC PMF + The Mom Test + JTBD로 스타트업 아이디어를 엄격하게 검증. 100점 만점 채점 + 약점 진단 + 개선 로드맵.
category: analysis
user-invocable: false
---

# Startup Validator Skill

> 검증된 프레임워크로 스타트업 아이디어를 평가 (낙관이 아닌 데이터 기반)

---

## 사용 시점

| 상황 | 예시 |
|------|------|
| 아이디어 검증 | 새 스타트업 컨셉 평가 |
| 펀딩 전 | 피칭 전 약점 파악 |
| 피봇 결정 | 현 방향 vs 전환 |
| 경쟁 리뷰 | 경쟁사 대비 포지션 |
| PMF 체크 | Product-Market Fit 준비도 |

사용: `/startup-validator [아이디어]`

---

## 검증 프레임워크

### 1. Peter Thiel 7 Questions (Zero to One)

| # | 질문 | 평가 기준 | 배점 |
|---|------|----------|------|
| 1 | 10배 나은 **기술**을 만들 수 있는가? | 파괴적 vs 점진적 | 15 |
| 2 | **지금**이 적절한 시점인가? | 시장 성숙도, 규제, 기술 준비 | 10 |
| 3 | 작은 시장에서 높은 **독점** 점유율로 시작하는가? | 니치 집중 vs 광범위 확산 | 15 |
| 4 | 적합한 **팀**이 있는가? | Founder-market fit | 10 |
| 5 | **유통** 방법이 있는가? | 채널, GTM 전략 | 15 |
| 6 | 10-20년 **방어** 가능한가? | Moat 내구성 | 15 |
| 7 | 비자명한 **비밀**을 발견했는가? | 고유한 인사이트 | 20 |

### 2. YC PMF Indicators (Michael Seibel)

| 지표 | 설명 |
|------|------|
| 수요 압력 | 수요/사용이 공급 능력을 초과 |
| 유기적 성장 | 40-60% 입소문 |
| 지원 과부하 | 고객 요청 감당 어려움 |
| 다운타임 반응 | 서비스 중단 시 사용자 강한 반응 |
| 반복 사용 | 핵심 지표 반복 행동 패턴 |

**Pre-PMF 체크**:
- 이것은 "머리에 불 붙은" 문제인가?
- 사용자가 소규모 팀의 거친 v1도 채택할 것인가?
- 고객이 지불하고 있는가 (또는 명확히 지불 의향)?

### 3. The Mom Test (Rob Fitzpatrick)

| 규칙 | 좋은 질문 | 나쁜 질문 |
|------|----------|----------|
| 고객 삶 초점 | "지난번에 어떻게 해결했나요?" | "우리 제품 쓰실 건가요?" |
| 과거 행동 | "마지막으로 X한 게 언제?" | "보통 얼마나 자주 X하세요?" |
| 듣기 > 말하기 | 침묵과 후속 질문 | 긴 제품 피칭 |

**거부할 나쁜 데이터**: 빈 칭찬, 가정법 ("쓸 것 같아요"), 커밋 없는 기능 위시리스트

### 4. JTBD Forces of Progress

```
변화 촉진:
  PUSH: 현 상황의 고통
  PULL: 새 솔루션의 매력

변화 저항:
  HABIT: 현 행동의 관성
  ANXIETY: 전환 불안

전환 신호: Push + Pull > Habit + Anxiety
```

### 5. Lean Canvas Critical Checks

| 블록 | 검증 질문 | 위험도 |
|------|----------|--------|
| Problem | 상위 3개 문제가 실재하는가? | High |
| Customer Segments | 얼리어답터가 명확한가? | High |
| UVP | 차별점을 한 문장으로 설명 가능한가? | High |
| Solution | MVP 범위로 검증 가능한가? | Medium |
| Channels | 실용적 획득 경로가 있는가? | Medium |
| Revenue | 사용자가 지불할 것인가? | High |
| Cost Structure | 유닛 이코노믹스가 성립하는가? | Medium |
| Key Metrics | 핵심 지표 1개가 정의되었는가? | Medium |
| Unfair Advantage | 복사하기 어려운 것이 있는가? | High |

---

## 채점 체계

### 총점 (100점)

| 영역 | 배점 | 규칙 |
|------|------|------|
| Thiel 7 Questions | 100 | 위 표 기준 |
| PMF 보너스 | +10 | 3개+ PMF 체크 통과 시 |
| 치명적 약점 페널티 | -10/개 | 미해결 치명적 약점당 |

### 등급

| 등급 | 점수 | 판정 | 다음 단계 |
|------|------|------|----------|
| **S** | 90+ | 즉시 실행 | 전력 투입, 펀딩 준비 |
| **A** | 80-89 | 강함 | 약점 보완 후 진행 |
| **B** | 70-79 | 유망 | 추가 검증 필요 |
| **C** | 60-69 | 재고 필요 | 피봇 고려 |
| **D** | 50-59 | 위험 | 근본 재설계 |
| **F** | <50 | 중단 권장 | 대안 탐색 |

### 약점 심각도

| 수준 | 의미 | 조치 |
|------|------|------|
| **Critical** | 미해결 시 실패 가능 | 즉시 수정 |
| **Major** | 성장 병목 가능 | 6개월 내 수정 |
| **Minor** | 개선 기회 | 낮은 우선순위 |

---

## 워크플로우

| Phase | 작업 | 도구 |
|-------|------|------|
| **0** | 입력 검증 | ARGUMENT 필수 |
| **1** | 핵심 가설 3개 추출 (핵심/가치/성장) | Sequential thinking (3) |
| **2** | 7 Questions 병렬 분석 | 병렬 analyst ×3 |
| **3** | PMF/JTBD Forces 검증 | Sequential thinking (5) |
| **4** | 총점 + 등급 + 약점 맵 | Sequential thinking (3) |
| **5** | 개선 로드맵 | Sequential thinking (3) |
| **6** | `.forge/validation-results/`에 저장 | Write |

---

## 결과 구조

| 섹션 | 내용 |
|------|------|
| **Header** | 날짜, 아이디어명, 총점/등급 |
| **1. Executive Summary** | 한 줄 판정 + 주요 강점/약점 |
| **2. 7 Questions 분석** | 질문별 점수 + 상세 근거 |
| **3. PMF 준비도** | 체크리스트 + Forces 분석 |
| **4. 약점 진단** | 심각도 분류 + 근거 |
| **5. 개선 로드맵** | 즉시/30일/90일 액션 |
| **6. Go/No-Go** | 최종 권고 |

---

## genius-thinking 시너지

```bash
/genius-thinking AI 헬스케어 스타트업 아이디어
/startup-validator [아이디어 1]
/startup-validator [아이디어 2]
/startup-validator [아이디어 3]
```

---

## 참조

- Zero to One (Peter Thiel)
- YC PMF Library
- The Mom Test (Rob Fitzpatrick)
- Customer Development (Steve Blank)
- JTBD (Clayton Christensen)
- Lean Canvas (Ash Maurya)
