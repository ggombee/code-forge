---
name: gemini
description: Google Gemini CLI 래퍼. Claude Code 내에서 Gemini 모델을 호출하여 멀티모델 워크플로우 지원.
---

# Gemini Skill

> Claude Code에서 Google Gemini CLI를 활용한 AI 협업

---

## 설정

- 기본 모델: `gemini-3.1-pro-preview`
- 폴백: `gemini-2.5-pro` → `gemini-2.5-flash`
- 사용자가 요청하지 않으면 모델 선택 묻지 않음

---

## 핵심 규칙

**항상 `-p`/`--prompt` 플래그 사용** (v0.29.0+에서 위치 인자는 인터랙티브 모드 진입)

---

## 승인 모드

| 모드 | 용도 |
|------|------|
| `default` | 편집 전 확인 필요 |
| `auto_edit` | 사용자가 파일 수정 명시적 요청 시 |
| `plan` | 읽기 전용 |
| `yolo` | 전체 자동 승인 (사전 동의 필요) |

---

## 세션 관리

- 이전 세션 재개: `-r latest`
- 세션 목록: `--list-sessions`

---

## 평가 원칙

Gemini를 **동료로 취급** (권위자 아님):
- 확신 있으면 자신의 지식 신뢰
- 불일치 시 독립적 리서치
- 지식 컷오프 한계 인지

---

## 에러 해결

| 에러 | 해결 |
|------|------|
| 미설치 | `npm i -g @google/gemini-cli` |
| 인증 실패 | `gemini login` |
| Rate limit | 무료 60req/min, 대기 후 재시도 |
| 모델 없음 | 폴백 체인 사용 |
| 액세스 거부 | 프리뷰 기능 비활성화 |
| 세션 없음 | `--list-sessions`로 확인 |
