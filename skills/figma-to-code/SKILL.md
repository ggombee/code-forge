---
name: figma-to-code
description: Figma 디자인을 Emotion 기반 코드로 변환. Pixel-perfect 구현.
category: implementation
user-invocable: false
metadata:
  version: '1.0.0'
---

# Figma to Code Skill

> Figma 디자인을 Emotion styled 기반 코드로 변환

---

## 트리거 조건

| 트리거                        | 반응        |
| ----------------------------- | ----------- |
| Figma URL 제공                | 즉시 실행   |
| "Figma 변환", "디자인 구현"   | 스킬 활성화 |
| `/start` 커맨드 내 Figma 분석 | 자동 연계   |

---

## 워크플로우

### Phase 1: 디자인 추출

```typescript
// Figma MCP 도구로 디자인 컨텍스트 추출
mcp__figma__get_design_context({
  fileKey: '{file_key}',
  nodeId: '{node_id}',
  clientLanguages: 'typescript',
  clientFrameworks: 'react',
});
```

**추출 항목:**

- 레이아웃 구조 (flex, gap, padding)
- 색상 값 (hex → semantic color 매핑)
- 타이포그래피 (font-size, weight, line-height)
- 컴포넌트 계층 구조

---

### Phase 2: 컴포넌트 매핑

**파일 구조:**

```
{컴포넌트}/
├── index.tsx      # 컴포넌트 로직
└── styled.ts      # Emotion styled 정의
```

**styled.ts 템플릿:**

```typescript
import styled from '@emotion/styled';

export const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
`;

// 상태별 스타일 (transient props: $접두사)
export const FilterButton = styled.button<{ $isSelected: boolean }>`
  padding: 8px 16px;
`;
```

**index.tsx 템플릿:**

```typescript
import { FC } from 'react';

import { Container, Title, FilterButton } from './styled';

interface Props {
  // props 정의
}

export const Component: FC<Props> = ({ ...props }) => {
  return (
    <Container>
      {/* styled 컴포넌트 직접 사용 */}
    </Container>
  );
};
```

---

### Phase 3: Agent Teams 병렬 구현 (Claude Max)

여러 컴포넌트를 동시에 생성할 때:

```typescript
TeamCreate({ team_name: 'figma-team', description: 'Figma to Code 변환' });
Task(subagent_type='implementor', team_name='figma-team', name='component-1', model='sonnet',
  prompt='FilterButton 컴포넌트 구현');
Task(subagent_type='implementor', team_name='figma-team', name='component-2', model='sonnet',
  prompt='DateControls 컴포넌트 구현');
// 완료 후 → shutdown_request → TeamDelete
```

> Agent Teams 미가용 시 Task 병렬 호출로 폴백

---

### Phase 4: 검증

**Pixel-perfect 체크리스트:**

- [ ] 레이아웃 (flex-direction, gap, padding) 일치
- [ ] 색상 (semantic color 매핑) 일치
- [ ] 폰트 (size, weight, line-height) 일치
- [ ] 상태별 스타일 (hover, active, disabled) 일치
- [ ] 반응형 동작 (있는 경우)

---

## 금지 패턴

| 금지              | 대안             |
| ----------------- | ---------------- |
| inline style 객체 | Emotion styled   |
| 하드코딩 색상     | semantic color   |
| px 매직넘버       | 변수화 또는 주석 |
| !important        | specificity 조정 |

---

## 참조 문서

| 문서                                                   | 용도            |
| ------------------------------------------------------ | --------------- |
| `@${CLAUDE_PLUGIN_ROOT}/instructions/validation/forbidden-patterns.md` | 금지 패턴       |
