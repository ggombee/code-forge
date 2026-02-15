#!/bin/bash
# Skill Forced Evaluation Hook
# UserPromptSubmit 시 실행되어 스킬 평가를 강제
# 발동률: 20% → 84%

cat << 'EVAL_PROMPT'

## Skill Evaluation Required

Before implementing anything, you MUST complete these steps IN ORDER:

### Step 1 - EVALUATE
Check each available skill against the user's request.
For each skill, state YES or NO with a one-line reason:

Available skills to evaluate:
- bug-fix: 버그 분석 및 수정 (트리거: 버그, 오류, 에러, 동작 안함)
- refactor: 코드 리팩토링 (트리거: 리팩토링, 구조 개선, 중복 제거)
- figma-to-code: 디자인 시안 → 코드 변환 (트리거: 이미지 첨부 + 구현, 시안대로)
- docs-creator: 문서 작성 (트리거: 새 프로젝트, 문서 작성/업데이트)

### Step 2 - ACTIVATE
For every skill you marked YES, use the Skill tool NOW to activate it.
Do NOT skip this step. Do NOT proceed to implementation without activation.

### Step 3 - IMPLEMENT
Only after completing Steps 1 and 2, proceed with implementation.

CRITICAL: The evaluation in Step 1 is WORTHLESS unless you ACTIVATE the matching skills in Step 2. Skipping activation defeats the entire purpose.

EVAL_PROMPT
