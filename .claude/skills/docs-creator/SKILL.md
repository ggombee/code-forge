---
name: docs-creator
description: Claude Code 문서 작성. CLAUDE.md, SKILL.md, 에이전트/커맨드 문서 효율적 작성.
metadata:
  author: ggombee
  version: "1.0.0"
---

# Docs Creator Skill

> 고밀도, 실행 가능, 유지보수 가능한 문서 작성

---

## 트리거 조건

| 상황 | 작성 대상 |
|------|----------|
| 새 프로젝트 | CLAUDE.md |
| 새 스킬 | skills/*/SKILL.md |
| 새 커맨드 | commands/*.md |
| 새 에이전트 | agents/*.md |
| 규칙 추가 | rules/*.md |

---

## 워크플로우

| Step | 작업 | 도구 |
|------|------|------|
| 1 | 유형 결정, 기존 문서 구조 파악 | Glob, Read |
| 2 | 규칙 추출 (금지 → 필수 → 패턴) | Grep |
| 3 | 작성 (표, 코드, @imports) | Write |
| 4 | 검증 (체크리스트) | - |

### 탐색 병렬 실행

```typescript
Task(subagent_type="explore", model="haiku", prompt="프로젝트 구조 분석")
Task(subagent_type="explore", model="haiku", prompt="기존 문서/규칙 패턴 분석")
```

---

## 문서 작성 원칙

| 원칙 | 방법 |
|------|------|
| **Show, Don't Tell** | 설명 < 코드 예시 |
| **High Density** | 1줄당 최대 정보 (표 활용) |
| **Copy-Paste Ready** | 바로 사용 가능한 코드 |
| **Positive Language** | "Do X" > "Don't Y" |

---

## 금지 패턴

| 금지 | 이유 |
|------|------|
| 장황한 설명 | 토큰 낭비 |
| Claude가 아는 것 반복 | 불필요 |
| CRITICAL/MUST 남발 | 효과 저하 |
| 모호한 지시 | 실행 불가 |

---

## 필수 패턴

| 항목 | 기준 |
|------|------|
| 구조 | 명확한 섹션 구분 (---) |
| 데이터 | 표 형식 압축 |
| 예시 | 실행 가능한 코드 |
| 참조 | @imports로 중복 제거 |
| 버전 | 라이브러리 버전 명시 |

---

## 검증 체크리스트

- [ ] 500줄 이하
- [ ] 표 형식으로 정보 압축
- [ ] 코드 예시 실행 가능
- [ ] @imports 중복 제거
- [ ] 긍정형 지시

---

## 참조 문서

| 문서 | 용도 |
|------|------|
| `@../../instructions/multi-agent/coordination-guide.md` | 병렬 실행 |
| `@../../instructions/validation/forbidden-patterns.md` | 금지 패턴 |
