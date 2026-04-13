# 디자인 시스템 규격 (Design System)

**프로젝트**: 지능형 오토바이 FMS  
**버전**: v1.0 | **작성일**: 2026-04-13  
**기술 스택**: TailwindCSS v3, Vue3, TypeScript

---

## 1. 설계 원칙

| 원칙 | 내용 |
|---|---|
| **일관성** | 모든 색상, 간격, 타이포그래피는 이 문서에서 정의된 토큰만 사용 |
| **다크 모드 우선** | 관제 시스템 특성상 어두운 환경에서 장시간 사용. 다크 테마가 기본 |
| **접근성** | WCAG 2.1 AA 기준 — 텍스트 대비비 4.5:1 이상 |
| **컴포넌트 원자성** | Atomic Design 구조 (Atoms → Molecules → Organisms) |

---

## 2. `tailwind.config.js` — 커스텀 토큰 정의

```typescript
// tailwind.config.ts  ← Vite + TypeScript 환경에서 .ts 확장자 사용
import type { Config } from "tailwindcss"

export default {
  content: ["./index.html", "./src/**/*.{vue,ts,tsx}"],
  /**
   * darkMode: "class" — <html> 태그에 "dark" 클래스 존재 시 다크 테마 적용.
   * 관제 시스템 특성상 항상 다크 모드 유지.
   * main.ts에서 document.documentElement.classList.add("dark") 로 강제 적용.
   */
  darkMode: "class",
  theme: {
    extend: {

      // ─── Color Palette ────────────────────────────────────────────
      colors: {

        // Primary — 브랜드 블루 (주요 액션, 링크, 포커스)
        primary: {
          50:  "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",   // 기본 (버튼, 포커스 링)
          600: "#2563eb",   // Hover
          700: "#1d4ed8",   // Active / Pressed
          800: "#1e40af",
          900: "#1e3a8a",
          950: "#172554",
        },

        // Secondary — 슬레이트 (배경, 테두리, 비활성 상태)
        secondary: {
          50:  "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",   // 보조 텍스트
          600: "#475569",   // 아이콘, 비활성 버튼
          700: "#334155",   // 카드 테두리
          800: "#1e293b",   // 카드 배경 (다크)
          900: "#0f172a",   // 페이지 배경 (다크)
          950: "#020617",
        },

        // Success — 그린 (정상, 완료, 운행 중)
        success: {
          50:  "#f0fdf4",
          100: "#dcfce7",
          400: "#4ade80",
          500: "#22c55e",   // 기본
          600: "#16a34a",   // 진한
          700: "#15803d",
        },

        // Warning — 앰버 (경고, 배터리 부족, 과속 임박)
        warning: {
          50:  "#fffbeb",
          100: "#fef3c7",
          400: "#fbbf24",
          500: "#f59e0b",   // 기본
          600: "#d97706",
          700: "#b45309",
        },

        // Danger — 레드 (위험, CRITICAL 알림, 사고)
        danger: {
          50:  "#fff1f2",
          100: "#ffe4e6",
          400: "#f87171",
          500: "#ef4444",   // 기본
          600: "#dc2626",   // Hover
          700: "#b91c1c",   // Active
        },

        // Info — 시안 (정보성 알림, 링크, 도움말)
        info: {
          50:  "#ecfeff",
          100: "#cffafe",
          400: "#22d3ee",
          500: "#06b6d4",
          600: "#0891b2",
        },

        // Surface — 다크 모드 전용 배경 계층
        surface: {
          base    : "#0f172a",  // 최하단 배경 (body)
          elevated: "#1e293b",  // 카드, 패널
          overlay : "#334155",  // 모달, 드롭다운
          border  : "#475569",  // 테두리
        },
      },

      // ─── Typography ───────────────────────────────────────────────
      fontFamily: {
        sans: ["Pretendard", "Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      fontSize: {
        "2xs": ["0.625rem", { lineHeight: "0.875rem" }],   // 10px — 라벨
        xs  : ["0.75rem",  { lineHeight: "1rem" }],        // 12px — 캡션
        sm  : ["0.875rem", { lineHeight: "1.25rem" }],     // 14px — 본문 소
        base: ["1rem",     { lineHeight: "1.5rem" }],      // 16px — 본문
        lg  : ["1.125rem", { lineHeight: "1.75rem" }],     // 18px — 서브 헤딩
        xl  : ["1.25rem",  { lineHeight: "1.75rem" }],     // 20px — 섹션 제목
        "2xl": ["1.5rem",  { lineHeight: "2rem" }],        // 24px — 페이지 제목
        "3xl": ["1.875rem",{ lineHeight: "2.25rem" }],     // 30px — 대형 수치
      },

      // ─── Spacing / Border Radius ──────────────────────────────────
      borderRadius: {
        sm  : "0.25rem",   // 4px  — 뱃지, 태그
        DEFAULT: "0.375rem", // 6px  — 인풋, 작은 버튼
        md  : "0.5rem",    // 8px  — 카드, 버튼
        lg  : "0.75rem",   // 12px — 모달, 패널
        xl  : "1rem",      // 16px — 대형 카드
        "2xl": "1.5rem",   // 24px — 풀 라운드 카드
      },

      // ─── Box Shadow ───────────────────────────────────────────────
      boxShadow: {
        card  : "0 1px 3px 0 rgb(0 0 0 / 0.3), 0 1px 2px -1px rgb(0 0 0 / 0.3)",
        modal : "0 20px 60px -10px rgb(0 0 0 / 0.6)",
        glow  : "0 0 20px -5px rgb(59 130 246 / 0.5)",    // 포커스 글로우
        "glow-danger": "0 0 20px -5px rgb(239 68 68 / 0.5)",
      },

      // ─── Animation ────────────────────────────────────────────────
      keyframes: {
        "fade-in"     : { from: { opacity: "0" }, to: { opacity: "1" } },
        "slide-up"    : { from: { transform: "translateY(8px)", opacity: "0" },
                          to:   { transform: "translateY(0)",   opacity: "1" } },
        "pulse-badge" : { "0%, 100%": { opacity: "1" }, "50%": { opacity: "0.4" } },
      },
      animation: {
        "fade-in"    : "fade-in 150ms ease-out",
        "slide-up"   : "slide-up 200ms ease-out",
        "pulse-badge": "pulse-badge 1.5s ease-in-out infinite",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    // @tailwindcss/line-clamp는 TailwindCSS v3.3+부터 core에 내장됨.
    // 별도 플러그인 설치 시 "already included" 경고 발생 — 제거 필요.
  ],
} satisfies Config;
```

---

## 3. 색상 사용 가이드

### 3.1 다크 테마 레이어 구조

```
surface-base (body, 전체 배경)       bg-secondary-900   #0f172a
  └─ surface-elevated (카드, 패널)   bg-secondary-800   #1e293b
       └─ surface-overlay (모달)     bg-secondary-700   #334155
```

### 3.2 상태별 색상 매핑

| 상태 | 배경 클래스 | 텍스트 클래스 | 테두리 클래스 | 사용 예 |
|---|---|---|---|---|
| 정상/운행 중 | `bg-success-500/10` | `text-success-400` | `border-success-500/30` | 차량 상태 배지 |
| 경고 | `bg-warning-500/10` | `text-warning-400` | `border-warning-500/30` | 배터리 부족 |
| 위험 | `bg-danger-500/10` | `text-danger-400` | `border-danger-500/30` | 과속, 사고 |
| 정보 | `bg-info-500/10` | `text-info-400` | `border-info-500/30` | 안내 배지 |
| 비활성 | `bg-secondary-700` | `text-secondary-400` | `border-secondary-600` | 정차, 점검 |

---

## 4. 타이포그래피 가이드

```
페이지 제목    text-2xl  font-bold    text-white
섹션 제목      text-xl   font-semibold text-white
서브 헤딩      text-lg   font-medium  text-secondary-200
본문           text-base font-normal  text-secondary-300
본문 (소)      text-sm   font-normal  text-secondary-400
캡션/라벨      text-xs   font-medium  text-secondary-500
숫자 대형 표시 text-3xl  font-bold    tabular-nums
```

---

## 5. 공통 컴포넌트 규격

### 5.1 Button

```vue
<!-- components/common/BaseButton.vue -->
<!-- 
  variant: 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline'
  size   : 'xs' | 'sm' | 'md' | 'lg'
  loading: boolean
-->
```

**Tailwind 클래스 조합표**:

| variant | 기본 | Hover | Disabled |
|---|---|---|---|
| `primary` | `bg-primary-600 text-white` | `hover:bg-primary-500` | `disabled:opacity-50 disabled:cursor-not-allowed` |
| `secondary` | `bg-secondary-700 text-secondary-200` | `hover:bg-secondary-600` | `disabled:opacity-50` |
| `danger` | `bg-danger-600 text-white` | `hover:bg-danger-500` | `disabled:opacity-50` |
| `ghost` | `bg-transparent text-secondary-300` | `hover:bg-secondary-800 hover:text-white` | `disabled:opacity-50` |
| `outline` | `border border-secondary-600 text-secondary-300 bg-transparent` | `hover:border-primary-500 hover:text-primary-400` | `disabled:opacity-50` |

| size | 클래스 |
|---|---|
| `xs` | `px-2 py-1 text-xs rounded` |
| `sm` | `px-3 py-1.5 text-sm rounded` |
| `md` | `px-4 py-2 text-sm rounded-md` (기본) |
| `lg` | `px-5 py-2.5 text-base rounded-md` |

**공통 기본 클래스**:
```
inline-flex items-center justify-center gap-2
font-medium transition-colors duration-150
focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-secondary-900
```

---

### 5.2 Badge (상태 배지)

```vue
<!-- components/common/StatusBadge.vue -->
<!-- 
  status: 'active' | 'inactive' | 'warning' | 'danger' | 'info' | 'maintenance'
  pulse : boolean  (실시간 신호 표시 시 깜빡임)
-->
```

**클래스 조합표**:

| status | 클래스 |
|---|---|
| `active` | `bg-success-500/10 text-success-400 border border-success-500/30` |
| `inactive` | `bg-secondary-700 text-secondary-400 border border-secondary-600` |
| `warning` | `bg-warning-500/10 text-warning-400 border border-warning-500/30` |
| `danger` | `bg-danger-500/10 text-danger-400 border border-danger-500/30` |
| `info` | `bg-info-500/10 text-info-400 border border-info-500/30` |
| `maintenance` | `bg-secondary-700 text-secondary-300 border border-secondary-500` |

**공통 기본 클래스**:
```
inline-flex items-center gap-1.5
px-2 py-0.5 text-xs font-medium rounded-sm
```

**pulse dot** (실시간 활성 표시):
```html
<span class="w-1.5 h-1.5 rounded-full bg-success-400 animate-pulse-badge"></span>
```

---

### 5.3 Card

```
<!-- 기본 카드 -->
<div class="
  bg-secondary-800
  border border-secondary-700
  rounded-lg
  shadow-card
  p-4
">

<!-- 인터랙티브 카드 (차량 선택 등) -->
<div class="
  bg-secondary-800
  border border-secondary-700
  rounded-lg
  shadow-card
  p-4
  cursor-pointer
  transition-all duration-150
  hover:border-primary-500/50
  hover:shadow-glow
  active:scale-[0.99]
">

<!-- 경고 상태 카드 -->
<div class="
  bg-danger-500/5
  border border-danger-500/30
  rounded-lg
  p-4
  shadow-glow-danger
">
```

---

### 5.4 Modal

```
<!-- 오버레이 -->
<div class="
  fixed inset-0
  bg-black/60 backdrop-blur-sm
  z-50
  flex items-center justify-center
  p-4
  animate-fade-in
">

<!-- 모달 패널 -->
<div class="
  relative
  bg-secondary-800
  border border-secondary-700
  rounded-lg
  shadow-modal
  w-full max-w-lg
  animate-slide-up
">
  <!-- 헤더 -->
  <div class="flex items-center justify-between p-5 border-b border-secondary-700">
    <h3 class="text-lg font-semibold text-white">제목</h3>
    <button class="p-1.5 rounded hover:bg-secondary-700 text-secondary-400 hover:text-white transition-colors">
      <!-- X 아이콘 -->
    </button>
  </div>

  <!-- 바디 -->
  <div class="p-5 text-sm text-secondary-300">...</div>

  <!-- 푸터 -->
  <div class="flex justify-end gap-3 p-5 border-t border-secondary-700">
    <!-- BaseButton ghost + BaseButton primary -->
  </div>
</div>
```

---

### 5.5 Form Input

```
<!-- 기본 Input -->
<input class="
  w-full
  bg-secondary-900
  border border-secondary-600
  rounded-md
  px-3 py-2
  text-sm text-white
  placeholder:text-secondary-500
  transition-colors duration-150
  focus:outline-none
  focus:border-primary-500
  focus:ring-1 focus:ring-primary-500
  disabled:opacity-50 disabled:cursor-not-allowed
"/>

<!-- 에러 상태 -->
<input class="
  ... (위 클래스 유지)
  border-danger-500
  focus:border-danger-500 focus:ring-danger-500
"/>
<!-- 에러 메시지 -->
<p class="mt-1 text-xs text-danger-400 flex items-center gap-1">
  <!-- 경고 아이콘 --> 필수 입력 항목입니다.
</p>

<!-- 성공 상태 -->
<input class="... border-success-500 focus:border-success-500 focus:ring-success-500"/>

<!-- Select -->
<select class="
  w-full
  bg-secondary-900
  border border-secondary-600
  rounded-md
  px-3 py-2
  text-sm text-white
  focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500
  appearance-none
  cursor-pointer
"/>

<!-- Label -->
<label class="block text-xs font-medium text-secondary-300 mb-1.5">
  레이블 <span class="text-danger-400">*</span>
</label>
```

---

## 6. 레이아웃 시스템

### 6.1 관제 대시보드 레이아웃

```
body: bg-secondary-900 min-h-screen text-white font-sans

┌─────────────────────────────────────────────┐
│  TopNav (h-14, bg-secondary-800,            │
│          border-b border-secondary-700)      │
├──────────────┬──────────────────────────────┤
│  Sidebar     │  Main Content               │
│  (w-64,      │  (flex-1, overflow-y-auto,  │
│  bg-         │   p-6)                       │
│  secondary-  │                             │
│  800,        │                             │
│  border-r    │                             │
│  border-     │                             │
│  secondary-  │                             │
│  700)        │                             │
└──────────────┴──────────────────────────────┘
```

### 6.2 반응형 브레이크포인트

| 이름 | 크기 | 대상 기기 |
|---|---|---|
| `sm` | 640px | 대형 모바일 (가로) |
| `md` | 768px | 태블릿 |
| `lg` | 1024px | 노트북 / 관제 PC |
| `xl` | 1280px | 대형 모니터 |
| `2xl` | 1536px | 초대형 모니터 / 관제 월 |

---

## 7. 아이콘 시스템

```
라이브러리: @heroicons/vue (v2, Outline 기본 / Solid 강조)

<!-- 기본 아이콘 크기 -->
xs   : class="w-3 h-3"    (12px) — 뱃지 내부
sm   : class="w-4 h-4"    (16px) — 버튼 아이콘
base : class="w-5 h-5"    (20px) — 일반 UI
lg   : class="w-6 h-6"    (24px) — 사이드바 메뉴
xl   : class="w-8 h-8"    (32px) — 빈 상태(Empty State) 일러스트

<!-- 사용 예 -->
<ExclamationTriangleIcon class="w-4 h-4 text-warning-400" />
<CheckCircleIcon class="w-4 h-4 text-success-400" />
<XCircleIcon class="w-4 h-4 text-danger-400" />
```

---

## 8. 실시간 데이터 시각화 규격

### 8.1 배터리 게이지 색상 분기

| SOC 범위 | 색상 | Tailwind 클래스 |
|---|---|---|
| 60% ~ 100% | 초록 | `bg-success-500` |
| 20% ~ 59% | 노랑 | `bg-warning-500` |
| 0% ~ 19% | 빨강 (깜빡임) | `bg-danger-500 animate-pulse` |

### 8.2 차량 마커 색상 (지도)

| 상태 | 색상 | 설명 |
|---|---|---|
| 정상 운행 | `#22c55e` (success-500) | 기본 |
| 과속/경고 | `#f59e0b` (warning-500) | WARNING 알림 활성 |
| 위험/사고 | `#ef4444` (danger-500) | CRITICAL 알림 활성 |
| 정차/충전 | `#06b6d4` (info-500) | ENGINE_OFF 상태 |
| 점검 중 | `#64748b` (secondary-500) | MAINTENANCE 상태 |
