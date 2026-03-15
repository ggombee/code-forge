---
name: tailwind
description: Tailwind CSS 스타일링 규칙. className 패턴, cn() 유틸 사용, tailwind.config, dark mode.
---

# Tailwind CSS 컨벤션

---

## 기본 규칙

- 스타일은 Tailwind className으로 작성한다
- 조건부/동적 className은 `cn()` 유틸을 사용한다
- 커스텀 값이 필요할 때는 `tailwind.config`에 추가한다
- 인라인 `style` prop 사용은 최소화한다

---

## cn() 유틸 (clsx + tailwind-merge)

```typescript
// src/utils/cn.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

```typescript
// ✅ 좋은 예: cn()으로 조건부 클래스 처리
import { cn } from '@/utils/cn';

interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  className?: string;
  children: React.ReactNode;
}

function Button({ variant = 'primary', size = 'md', disabled, className, children }: ButtonProps) {
  return (
    <button
      disabled={disabled}
      className={cn(
        // 기본 스타일
        'inline-flex items-center justify-center rounded-md font-medium transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
        // variant
        {
          'bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500': variant === 'primary',
          'bg-gray-100 text-gray-900 hover:bg-gray-200 focus-visible:ring-gray-500': variant === 'secondary',
          'bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500': variant === 'danger',
        },
        // size
        {
          'h-8 px-3 text-sm': size === 'sm',
          'h-10 px-4 text-sm': size === 'md',
          'h-12 px-6 text-base': size === 'lg',
        },
        // disabled
        disabled && 'cursor-not-allowed opacity-50',
        // 외부 className (마지막에 적용)
        className,
      )}
    >
      {children}
    </button>
  );
}
```

```typescript
// ❌ 나쁜 예: 템플릿 리터럴로 클래스 조합 (Tailwind merge 없음)
const className = `btn ${variant === 'primary' ? 'bg-blue-600' : 'bg-gray-100'} ${disabled ? 'opacity-50' : ''}`;

// ❌ 나쁜 예: 동적 클래스명 생성 (Tailwind PurgeCSS가 감지 못함)
const color = 'blue';
const className = `bg-${color}-600`; // ❌ 제거됨
```

---

## tailwind.config 설정

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        brand: '#1677ff',
      },
      fontFamily: {
        sans: ['Pretendard', 'system-ui', 'sans-serif'],
      },
      spacing: {
        18: '4.5rem',
        88: '22rem',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      screens: {
        xs: '475px', // 커스텀 브레이크포인트
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),       // 폼 스타일 초기화
    require('@tailwindcss/typography'),  // prose 스타일
  ],
};

export default config;
```

---

## Dark Mode

```typescript
// tailwind.config.ts - class 전략 (수동 제어)
const config: Config = {
  darkMode: 'class', // 또는 'media' (시스템 설정 기반)
  ...
};
```

```typescript
// Dark mode 적용 예시
function Card({ children }: { children: React.ReactNode }) {
  return (
    <div
      className={cn(
        'rounded-lg border p-6',
        'bg-white text-gray-900',             // light
        'dark:bg-gray-800 dark:text-gray-100', // dark
        'border-gray-200 dark:border-gray-700',
      )}
    >
      {children}
    </div>
  );
}
```

```typescript
// Dark mode 토글 (class 전략)
function ThemeToggle() {
  const [isDark, setIsDark] = useState(false);

  const toggleTheme = () => {
    setIsDark(!isDark);
    document.documentElement.classList.toggle('dark');
  };

  return <button onClick={toggleTheme}>{isDark ? '라이트 모드' : '다크 모드'}</button>;
}
```

---

## 반응형 디자인

```typescript
// Mobile-first 반응형 클래스
function ResponsiveGrid() {
  return (
    <div
      className={cn(
        'grid gap-4',
        'grid-cols-1',      // 기본 (mobile)
        'sm:grid-cols-2',   // sm: 640px+
        'md:grid-cols-3',   // md: 768px+
        'lg:grid-cols-4',   // lg: 1024px+
      )}
    >
      {items.map((item) => (
        <div key={item.id} className="rounded-lg border p-4">
          {item.name}
        </div>
      ))}
    </div>
  );
}
```

---

## 자주 사용하는 패턴

```typescript
// Flexbox 중앙 정렬
'flex items-center justify-center'

// 텍스트 말줄임
'truncate'               // 1줄
'line-clamp-2'           // 2줄 (CSS)

// 카드 기본 스타일
'rounded-lg border border-gray-200 bg-white p-6 shadow-sm'

// 반응형 숨김
'hidden md:block'        // mobile 숨김, md+ 표시
'block md:hidden'        // md+ 숨김, mobile 표시

// 포커스 링
'focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500'

// 트랜지션
'transition-colors duration-200'
'transition-all duration-300 ease-in-out'
```

---

## 체크리스트

- [ ] 동적/조건부 className은 `cn()` 사용?
- [ ] 동적 클래스명을 템플릿 리터럴로 생성하지 않음?
- [ ] 커스텀 색상/간격은 `tailwind.config`에 추가?
- [ ] Mobile-first 반응형 작성 (`sm:`, `md:`, `lg:` 순서)?
- [ ] Dark mode 클래스는 `dark:` 접두사로 작성?
- [ ] `content` 배열에 모든 파일 패턴 포함?
