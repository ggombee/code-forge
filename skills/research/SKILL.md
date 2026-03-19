---
name: research
description: 구조화된 리서치 수행. 주제별 깊이(quick/standard/deep) 선택, 병렬 수집, 신뢰도 등급 부여, 마크다운 리포트 생성.
category: analysis
---

# Research Skill

> 구조화된 팩트 기반 리서치 및 마크다운 리포트 생성

---

## 트리거

`/research [topic]` + 옵션 플래그:
- `--quick`: 빠른 분석 (3-5 쿼리, 500-1000자)
- (기본): 표준 분석 (5-10 쿼리, 1500-3000자)
- `--deep`: 심층 조사 (10-15 쿼리, 3000-6000자, 반복 패스)

인자 없으면 즉시 주제 요청.

---

## 깊이별 기준

| 항목 | Quick | Standard | Deep |
|------|-------|----------|------|
| 쿼리 수 | 3-5 | 5-10 | 10-15 |
| 최소 출처 | 5 | 10 | 20+ |
| 리포트 길이 | 500-1000자 | 1500-3000자 | 3000-6000자 |
| 반복 패스 | 없음 | 없음 | 있음 (갭 분석) |

---

## 주제 분류

| 유형 | 채널 |
|------|------|
| 기술 비교 | WebSearch + GitHub |
| 시장/트렌드 | WebSearch + 크롤링 |
| 경쟁사 분석 | WebSearch + GitHub |
| 학술 주제 | arXiv + 문서 페칭 |
| 내부 프로젝트 | 코드 탐색 + Grep |

---

## 워크플로우

| Phase | 작업 | 필수 |
|-------|------|------|
| **1. 파싱** | 도구 감지, 주제 분류 | 도구 가용성 확인 |
| **2. 전략** | 핵심 질문 3-5개 정의, 범위 설정 | Sequential thinking |
| **3. 수집** | 병렬 데이터 수집 (researcher, explorer) | 최소 출처 수 준수 |
| **4. 갭 분석** | (deep만) 누락 영역 2차 쿼리 | Sequential thinking |
| **5. 리포트** | 피라미드 원칙: 결론 → 상세 | 출처 URL 필수 |
| **6. 저장** | `.hypercore/research/[NN].topic_summary.md` | 파일 저장 필수 |

---

## 리포트 기준

- 현재 연도 컨텍스트 포함
- 모든 핵심 주장에 출처 URL 명시
- 비교 시 증거 테이블 포함
- 피라미드 원칙: 요약 → 상세

---

## 금지 사항

| 금지 |
|------|
| 출처 없는 주장 |
| 비교 증거 없이 비교 결론 |
| 출력 파일 저장 없이 종료 |
| 최소 출처 수 미달 |

---

## 참조

- `instructions/sourcing/reliable-search.md` — 검색 신뢰도 가이드
- `instructions/context-optimization/redundant-exploration-prevention.md` — 중복 검색 방지
