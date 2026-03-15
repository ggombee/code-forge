---
name: pds
description: Partner Design System(PDS) 컴포넌트 우선 사용 규칙. semanticColor 토큰, Figma 연동 패턴.
---

# PDS (Partner Design System) 사용 규칙

---

## 핵심 원칙: PDS 컴포넌트 우선 사용

새 UI를 만들기 전에 반드시 PDS 컴포넌트 존재 여부를 확인한다:

```bash
# PDS 컴포넌트 목록 확인
ls packages/shared/components/
```

---

## semanticColor 토큰 사용

직접 색상값을 쓰지 않고 PDS 토큰을 사용한다:

```typescript
// ✅ 좋은 예
import { semanticColor } from '@repo/shared/styles/foundation/semanticColor';

const StyledButton = styled.button`
  color: ${semanticColor.text.primary};
`;

// ❌ 나쁜 예
const StyledButton = styled.button`
  color: #333333;
`;
```

---

## PDS 래퍼 패턴

PDS 컴포넌트를 동적 import하여 래핑:

```typescript
import { getPDSComponent } from '@repo/shared/utils/dynamicImport.ts';
import type { BadgeProps } from '@pds/components';
export default getPDSComponent<BadgeProps>('Badge');
```

---

## 공통 UI 패키지 패턴

```javascript
// @pwb/ui 패키지의 컴포넌트를 import하여 사용
import { Button, Modal, Table } from '@pwb/ui';
```

---

## Figma 토큰 연동

Figma 작업 시 figma MCP를 항상 우선 사용한다.

- Figma URL이 주어지면 fileKey/nodeId 먼저 추출 후 MCP 호출
- MCP 결과를 받은 후에만 분석/요약/가이드 작성

```
https://www.figma.com/design/{fileKey}/{fileName}?node-id={nodeId}
→ nodeId의 하이픈(-)을 콜론(:)으로 변환
예: node-id=2040-47609 → nodeId: "2040:47609"
```

MCP 호출 우선순위:

| 순위 | 도구                 | 용도                      |
| ---- | -------------------- | ------------------------- |
| 1    | `get_metadata`       | 구조/스타일/컴포넌트 파악 |
| 2    | `get_screenshot`     | 시각적 디자인 확인        |
| 3    | `get_design_context` | 코드 변환 시              |

---

## 전역 스타일

전역 스타일은 `packages/shared/styles/globalStyles`에만 정의한다.

---

## 패턴 참조 체크리스트

새 UI 컴포넌트 작성 전:

- [ ] PDS에 해당 컴포넌트가 있는가?
- [ ] 색상/스타일 상수(semanticColor)가 정의되어 있는가?
- [ ] 직접 색상값(hex, rgb)을 쓰지 않는가?
- [ ] 전역 스타일을 임의로 추가하지 않는가?
