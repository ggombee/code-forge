# Forbidden Patterns

> 프로젝트에서 금지된 패턴 목록

---

## 언어 표현

| 금지                 | 대안                |
| -------------------- | ------------------- |
| "~할 것 같습니다"    | "~합니다"           |
| "아마도", "추측컨대" | 확인 후 명시적 진술 |
| "~일 수 있습니다"    | 조건 명시하여 단정  |
| "should work"        | "테스트 통과 확인"  |

---

## 코드 품질

| 금지                  | 대안                  | 예시                  |
| --------------------- | --------------------- | --------------------- |
| `any` 타입            | `unknown` + 타입 가드 | `data: unknown`       |
| `@ts-ignore`          | 타입 수정             | -                     |
| `// @ts-expect-error` | 타입 수정             | -                     |
| 암시적 `any`          | 명시적 타입           | `(item: Item) => ...` |
| return type 생략      | 명시적 반환 타입      | `: Promise<Order>`    |
| 에러 무시 (빈 catch)  | 적절한 에러 처리      | -                     |

```typescript
// ❌ 금지
const getData = (id) => api.get(`/orders/${id}`);

// ✅ 허용
const getData = (id: string): Promise<OrderResponse> => api.get(`/orders/${id}`);
```

---

## 상태 관리

상세: `.claude/rules/frontend/state-and-server-state.md`

| 금지                    | 대안                  |
| ----------------------- | --------------------- |
| 서버 상태에 useState    | TanStack Query 등     |
| 과도한 전역 상태        | 로컬 상태 우선        |
| Query 내 직접 상태 변경 | mutation + invalidate |

---

## Import 순서

상세: `.claude/rules/frontend/react-nextjs-conventions.md`

외부 라이브러리 → 내부 모듈 (`@/`) → 상대 경로

---

## Git/PR

| 금지                  | 이유          |
| --------------------- | ------------- |
| 커밋 메시지에 AI 표시 | 불필요한 노출 |
| 커밋 메시지에 이모지  | 일관성        |
| force push to master  | 히스토리 파괴 |
| --no-verify           | 검증 우회     |

```bash
# ❌ 금지
git commit -m "feat: add feature (by Claude)"
git push --force origin master

# ✅ 허용
git commit -m "feat: add order list feature"
```

---

## 보안

| 금지                          | 대안                           |
| ----------------------------- | ------------------------------ |
| 토큰/비밀번호 하드코딩        | 환경변수 또는 로컬 env 파일    |
| 스크립트에 자격증명 직접 작성 | `.env.example` + 런타임 주입   |
| 하드코딩된 URL/API 키         | 환경 변수                      |

```bash
# ❌ 금지
TOKEN="ATATT..."

# ✅ 허용
TOKEN="${API_TOKEN:-}"
```

---

## 워크플로우

| 금지                | 대안                |
| ------------------- | ------------------- |
| 읽지 않은 파일 수정 | Read → Edit         |
| 테스트 없이 PR      | 테스트 실행 확인    |
| 린트 오류 무시      | lint-fixer 실행     |
| 기존 정책 임의 변경 | 사용자 확인 후 변경 |
| 검증 단계 스킵      | lint/build 통과 확인 |
| 독립 작업 순차 실행 | 병렬 실행           |

---

## Context/Provider 의존성

Dialog/Modal content 내부에서는 상위 Context 접근이 불가하다.

| 금지                  | 대안                         |
| --------------------- | ---------------------------- |
| Modal 내부에서 context hook 직접 호출 | 상위에서 콜백을 props로 전달 |

```typescript
// ❌ 금지: Dialog/Modal content 내부에서 context hook 사용
const Content = () => {
  const { close } = useModal();
  return <Button onClick={close} />;
};

// ✅ 허용: 상위에서 콜백 전달
const Content = ({ onClose }: { onClose: () => void }) => {
  return <Button onClick={onClose} />;
};
```

---

## API/서비스

| 금지             | 대안                  |
| ---------------- | --------------------- |
| 수동 axios 호출  | 프로젝트 api 래퍼 사용 |
| 직접 에러 핸들링 | Query의 onError       |
| 하드코딩된 URL   | 환경 변수             |

```typescript
// ❌ 금지
const res = await axios.get('https://api.example.com/orders');

// ✅ 허용
const res = await api.get('/api/orders');
```

---

## 테스트

| 금지             | 대안                   |
| ---------------- | ---------------------- |
| 테스트 삭제      | 테스트 수정            |
| 하드코딩된 날짜  | `jest.useFakeTimers()` |
| 구현 상세 테스트 | 동작 중심 테스트       |

---

## 스타일링

| 금지              | 대안                         |
| ----------------- | ---------------------------- |
| inline style 객체 | 프로젝트 스타일링 도구 (Tailwind 또는 styled/css prop) |
| !important        | `&&` specificity             |
| px 하드코딩       | 디자인 토큰                  |
| 하드코딩 색상값   | 시맨틱 컬러 토큰             |

```typescript
// ❌ 금지
<div style={{ marginTop: 20 }}>

// ✅ 허용: styled 컴포넌트
const Container = styled.div`
  margin-top: ${spacing.md};
`;
```

### !important 대신 `&&` specificity 패턴

`&&`는 자기 자신의 클래스를 한번 더 참조하여 specificity를 높이는 기법이다.
`!important`는 이후 override가 불가능해지므로 금지한다.

```typescript
// ❌ 금지
background-color: ${semanticColor.bg} !important;

// ✅ 허용: && 사용 (specificity 0,1,0 → 0,2,0)
&& {
  background-color: ${semanticColor.bg};
}
```

### transient props (`$` prefix)

styled 컴포넌트에 전달하는 custom prop은 `$` prefix를 붙인다.
`$` 없이 전달하면 DOM에 unknown attribute가 전달되어 React warning이 발생한다.

```typescript
// ❌ 금지: DOM에 isActive가 전달됨 → React warning
const Chip = styled.button<{ isActive: boolean }>`...`;
<Chip isActive={true}>

// ✅ 허용: $prefix로 DOM 전달 방지
const Chip = styled.button<{ $isActive: boolean }>`...`;
<Chip $isActive={true}>
```

### inline style vs css prop 구분

| 구문                    | 판정    | 이유                                        |
| ----------------------- | ------- | ------------------------------------------- |
| `style={{ margin: 8 }}` | ❌ 금지 | React의 inline style (정적 스타일에 비효율) |
| `css={{ margin: 8 }}`   | ✅ 허용 | Emotion의 css prop (컴파일 타임 처리)       |

---

## 탐색

| 금지                                           | 대안                    |
| ---------------------------------------------- | ----------------------- |
| 같은 파일 3회 이상 읽기 (변경 후 확인 제외)    | 캐시/메모 활용          |
| "모든 X" 지시에서 전체 대상 열거 없이 작업 시작 | 먼저 전체 목록 파악     |

---

## PR 전 체크리스트

- [ ] `any` 타입 없음
- [ ] return type 명시
- [ ] Import 순서 준수
- [ ] 서버 상태 관리 라이브러리 사용
- [ ] 테스트 작성/실행
- [ ] 린트 오류 없음
