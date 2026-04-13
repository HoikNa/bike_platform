# 11. 모듈화 디자인 시스템 세분화 (Design System Specification)

> **대상**: Vue3 + TailwindCSS v3 기반 지능형 오토바이 FMS  
> **범위**: 관제 대시보드 (Web, 1440px 기준) + 모바일 앱 (App, 390px 기준)  
> **원칙**: 모든 스타일은 Tailwind 유틸리티 클래스로 표현하며, 커스텀 CSS는 최소화한다.

---

## 목차

1. [Foundation — 기초 시각 요소](#1-foundation)
   - 1.1 Color Palette
   - 1.2 Typography
   - 1.3 Spacing & Radius
2. [Atomic Components — 원자 단위](#2-atomic-components)
   - 2.1 Button
   - 2.2 Input & Form Elements
   - 2.3 Badge / Tag
3. [Compound Components — 복합 단위](#3-compound-components)
   - 3.1 Card
   - 3.2 Modal / Dialog
   - 3.3 List Item
4. [Layout Templates — 레이아웃 템플릿](#4-layout-templates)
   - 4.1 관제 대시보드 (Web)
   - 4.2 모바일 앱 (App)
   - 4.3 Auth Page

---

## 1. Foundation

### 1.1 Color Palette

#### `tailwind.config.ts` — 전체 컬러 토큰 정의

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss"

export default {
  content: ["./index.html", "./src/**/*.{vue,ts,tsx}"],
  darkMode: "class", // main.ts에서 document.documentElement.classList.add("dark") 로 활성화
  theme: {
    extend: {
      colors: {
        // ── Primary (브랜드 메인 — 안전/신뢰 계열 딥블루)
        primary: {
          50:  "#eff6ff",
          100: "#dbeafe",
          200: "#bfdbfe",
          300: "#93c5fd",
          400: "#60a5fa",
          500: "#3b82f6",  // ← 기본값 (bg-primary-500)
          600: "#2563eb",  // ← hover 상태
          700: "#1d4ed8",  // ← active / pressed 상태
          800: "#1e40af",
          900: "#1e3a8a",
          950: "#172554",
        },

        // ── Secondary (보조 — 차분한 슬레이트)
        secondary: {
          50:  "#f8fafc",
          100: "#f1f5f9",
          200: "#e2e8f0",
          300: "#cbd5e1",
          400: "#94a3b8",
          500: "#64748b",  // ← 기본값
          600: "#475569",
          700: "#334155",
          800: "#1e293b",
          900: "#0f172a",
          950: "#020617",
        },

        // ── Background / Surface (라이트 모드)
        //    다크 모드는 secondary-900 / secondary-800 을 배경으로 사용
        background: {
          DEFAULT: "#f1f5f9",  // 전체 페이지 배경 (bg-background)
          subtle:  "#e2e8f0",  // 구분선, 비활성 영역
        },
        surface: {
          DEFAULT: "#ffffff",  // 카드, 모달, 사이드바 배경 (bg-surface)
          raised:  "#f8fafc",  // 한 단계 올라온 레이어 (드롭다운 등)
          overlay: "#ffffff",  // 모달 내부 배경
        },

        // ── Semantic Colors
        success: {
          50:  "#f0fdf4",
          100: "#dcfce7",
          200: "#bbf7d0",
          400: "#4ade80",
          500: "#22c55e",  // ← 기본 (정상 운행, 충전 완료)
          600: "#16a34a",
          700: "#15803d",
          900: "#14532d",
        },
        warning: {
          50:  "#fffbeb",
          100: "#fef3c7",
          200: "#fde68a",
          400: "#fbbf24",
          500: "#f59e0b",  // ← 기본 (배터리 부족, 주의 알림)
          600: "#d97706",
          700: "#b45309",
          900: "#78350f",
        },
        danger: {
          50:  "#fff1f2",
          100: "#ffe4e6",
          200: "#fecdd3",
          400: "#fb7185",
          500: "#ef4444",  // ← 기본 (과속, 사고, 오류)
          600: "#dc2626",
          700: "#b91c1c",
          900: "#7f1d1d",
        },
        info: {
          50:  "#f0f9ff",
          100: "#e0f2fe",
          200: "#bae6fd",
          400: "#38bdf8",
          500: "#0ea5e9",  // ← 기본 (일반 알림, 정보)
          600: "#0284c7",
          700: "#0369a1",
          900: "#0c4a6e",
        },
      },
    },
  },
} satisfies Config
```

#### 컬러 사용 가이드라인

| 토큰 | 라이트 클래스 | 다크 클래스 | 사용 컨텍스트 |
|---|---|---|---|
| 페이지 배경 | `bg-background` | `dark:bg-secondary-900` | 최하위 배경 |
| 컴포넌트 배경 | `bg-surface` | `dark:bg-secondary-800` | 카드, 패널 |
| 기본 텍스트 | `text-secondary-900` | `dark:text-secondary-50` | 본문 |
| 보조 텍스트 | `text-secondary-500` | `dark:text-secondary-400` | 레이블, 캡션 |
| 비활성 텍스트 | `text-secondary-300` | `dark:text-secondary-600` | Placeholder, Disabled |
| 구분선 | `border-secondary-200` | `dark:border-secondary-700` | hr, 카드 테두리 |
| Primary 버튼 | `bg-primary-500` | `dark:bg-primary-600` | CTA 버튼 |
| 위험 강조 | `bg-danger-500` | `dark:bg-danger-600` | 과속 배지, 에러 |

---

### 1.2 Typography

#### `tailwind.config.ts` — 폰트 패밀리 확장

```typescript
// tailwind.config.ts (theme.extend 내부)
fontFamily: {
  sans: ["Noto Sans KR", "Pretendard", "ui-sans-serif", "system-ui", "sans-serif"],
  mono: ["JetBrains Mono", "ui-monospace", "monospace"],
},
```

#### `index.html` / `main.ts` — 폰트 로드

```html
<!-- index.html <head> -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap"
  rel="stylesheet"
/>
```

#### 텍스트 계층 (Type Scale)

| 계층 | 역할 | 클래스 조합 | 예시 |
|---|---|---|---|
| Heading 1 | 페이지 타이틀 | `text-3xl font-bold leading-tight tracking-tight` | 관제 대시보드 |
| Heading 2 | 섹션 타이틀 | `text-2xl font-bold leading-snug` | 차량 목록 |
| Heading 3 | 카드 타이틀 | `text-xl font-semibold leading-snug` | 차량 상태 |
| Heading 4 | 서브섹션 | `text-lg font-semibold leading-normal` | 알림 타입 |
| Heading 5 | 레이블 그룹 | `text-base font-semibold leading-normal` | 운행 정보 |
| Heading 6 | 소항목 | `text-sm font-semibold leading-normal uppercase tracking-wide` | 테이블 헤더 |
| Body Large | 본문 강조 | `text-base font-normal leading-relaxed` | 상세 설명 |
| Body | 기본 본문 | `text-sm font-normal leading-relaxed` | 일반 텍스트 |
| Body Small | 보조 본문 | `text-xs font-normal leading-relaxed` | 부연 설명 |
| Caption | 메타 정보 | `text-xs font-normal text-secondary-500` | 타임스탬프 |
| Overline | 카테고리 레이블 | `text-xs font-semibold uppercase tracking-widest text-secondary-400` | 섹션 구분 |

```vue
<!-- 사용 예시: VehicleDetailHeader.vue -->
<template>
  <div>
    <!-- Overline -->
    <p class="text-xs font-semibold uppercase tracking-widest text-secondary-400">
      차량 상세
    </p>
    <!-- Heading 2 -->
    <h2 class="text-2xl font-bold leading-snug text-secondary-900 dark:text-secondary-50">
      {{ vehicle.plate_number }}
    </h2>
    <!-- Caption -->
    <span class="text-xs font-normal text-secondary-500 dark:text-secondary-400">
      마지막 업데이트: {{ lastUpdated }}
    </span>
  </div>
</template>
```

---

### 1.3 Spacing & Radius

#### Spacing 기준 단위 (4px Grid)

TailwindCSS 기본 spacing scale은 4px 단위입니다. 아래 규칙으로 사용 단계를 제한합니다.

| 단계 | Tailwind 값 | 픽셀 | 사용처 |
|---|---|---|---|
| 극소 | `space-1` / `p-1` | 4px | 아이콘 내부 패딩, 배지 gap |
| 소 | `space-2` / `p-2` | 8px | 인라인 요소 간격, 컴팩트 버튼 |
| 기본 | `space-3` / `p-3` | 12px | 기본 버튼 패딩, 인풋 패딩 |
| 중 | `space-4` / `p-4` | 16px | 카드 내부 패딩, 리스트 아이템 |
| 대 | `space-6` / `p-6` | 24px | 카드 외부 여백, 섹션 헤더 |
| 특대 | `space-8` / `p-8` | 32px | 페이지 영역 구분, 모달 패딩 |
| 최대 | `space-12` / `p-12` | 48px | 섹션 간 여백 (데스크탑) |

> **규칙**: 컴포넌트 내부는 `p-4` 이하, 컴포넌트 간 Gap은 `gap-4` ~ `gap-6`, 섹션 간은 `my-8` ~ `my-12`.

#### Border Radius 정책

| 레벨 | 클래스 | 값 | 사용 컴포넌트 |
|---|---|---|---|
| 없음 | `rounded-none` | 0 | 테이블, 전체화면 이미지 |
| 미세 | `rounded` | 4px | 인풋, 셀렉트, 소형 배지 |
| 기본 | `rounded-md` | 6px | 버튼 (Medium/Large), 토스트 |
| 중간 | `rounded-lg` | 8px | 카드, 드롭다운 |
| 크게 | `rounded-xl` | 12px | 모달, 바텀시트, 모바일 카드 |
| 최대 | `rounded-2xl` | 16px | 모바일 전용 대형 카드 |
| 원형 | `rounded-full` | 9999px | 아바타, 소형 상태 인디케이터 |

```vue
<!-- 컴포넌트별 적용 예 -->
<!-- 버튼 -->
<button class="rounded-md px-4 py-2">...</button>

<!-- 카드 -->
<div class="rounded-lg p-6">...</div>

<!-- 모달 -->
<div class="rounded-xl p-8">...</div>

<!-- 상태 dot -->
<span class="rounded-full w-2 h-2 bg-success-500"></span>
```

---

## 2. Atomic Components

### 2.1 Button

#### Variants × States 클래스 매핑

**Solid (채워진 버튼) — Primary**

```vue
<!-- BaseButton.vue -->
<template>
  <button
    :disabled="disabled || loading"
    :class="[baseClasses, variantClasses, sizeClasses, stateClasses]"
    v-bind="$attrs"
  >
    <span v-if="loading" class="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
    <slot />
  </button>
</template>
```

| Variant | 기본 | Hover | Active | Disabled |
|---|---|---|---|---|
| **Solid Primary** | `bg-primary-500 text-white` | `hover:bg-primary-600` | `active:bg-primary-700` | `disabled:bg-secondary-200 disabled:text-secondary-400 disabled:cursor-not-allowed` |
| **Solid Danger** | `bg-danger-500 text-white` | `hover:bg-danger-600` | `active:bg-danger-700` | (동일 disabled 패턴) |
| **Solid Success** | `bg-success-500 text-white` | `hover:bg-success-600` | `active:bg-success-700` | (동일 disabled 패턴) |
| **Outline Primary** | `border border-primary-500 text-primary-500 bg-transparent` | `hover:bg-primary-50` | `active:bg-primary-100` | `disabled:border-secondary-200 disabled:text-secondary-400` |
| **Outline Danger** | `border border-danger-500 text-danger-500 bg-transparent` | `hover:bg-danger-50` | `active:bg-danger-100` | (동일 disabled 패턴) |
| **Ghost / Text** | `text-primary-500 bg-transparent border-transparent` | `hover:bg-primary-50` | `active:bg-primary-100` | `disabled:text-secondary-300` |

```typescript
// composables/useButtonClasses.ts
type Variant = "solid-primary" | "solid-danger" | "solid-success" | "outline-primary" | "outline-danger" | "ghost"
type Size    = "sm" | "md" | "lg"

const BASE = "inline-flex items-center justify-center font-medium transition-colors duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2"

const VARIANT_CLASSES: Record<Variant, string> = {
  "solid-primary":  "bg-primary-500 text-white hover:bg-primary-600 active:bg-primary-700 disabled:bg-secondary-200 disabled:text-secondary-400",
  "solid-danger":   "bg-danger-500 text-white hover:bg-danger-600 active:bg-danger-700 disabled:bg-secondary-200 disabled:text-secondary-400",
  "solid-success":  "bg-success-500 text-white hover:bg-success-600 active:bg-success-700 disabled:bg-secondary-200 disabled:text-secondary-400",
  "outline-primary":"border border-primary-500 text-primary-500 bg-transparent hover:bg-primary-50 active:bg-primary-100 disabled:border-secondary-200 disabled:text-secondary-400",
  "outline-danger": "border border-danger-500 text-danger-500 bg-transparent hover:bg-danger-50 active:bg-danger-100 disabled:border-secondary-200 disabled:text-secondary-400",
  "ghost":          "text-primary-500 bg-transparent hover:bg-primary-50 active:bg-primary-100 disabled:text-secondary-300",
}

const SIZE_CLASSES: Record<Size, string> = {
  sm: "rounded   px-3 py-1.5 text-xs  gap-1.5",
  md: "rounded-md px-4 py-2   text-sm  gap-2",
  lg: "rounded-md px-6 py-3   text-base gap-2",
}

export function useButtonClasses(variant: Variant, size: Size) {
  return [BASE, VARIANT_CLASSES[variant], SIZE_CLASSES[size]].join(" ")
}
```

```vue
<!-- 실사용 예시 -->
<!-- 과속 경고 해제 버튼 (Solid Danger, Large) -->
<BaseButton variant="solid-danger" size="lg">경고 해제</BaseButton>

<!-- 배터리 교체 지시 (Outline, Medium) -->
<BaseButton variant="outline-primary" size="md">충전소 안내</BaseButton>

<!-- 닫기 (Ghost, Small) -->
<BaseButton variant="ghost" size="sm">닫기</BaseButton>
```

**아이콘 전용 버튼 (Icon Button)**

```vue
<!-- 정사각형, 아이콘만 포함 -->
<button
  class="inline-flex items-center justify-center
         w-8 h-8 rounded-md
         text-secondary-500 hover:bg-secondary-100 hover:text-secondary-700
         active:bg-secondary-200
         disabled:text-secondary-300 disabled:cursor-not-allowed
         transition-colors duration-150
         focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-1"
>
  <RefreshIcon class="w-4 h-4" />
</button>
```

---

### 2.2 Input & Form Elements

#### Text Input

```vue
<!-- BaseInput.vue -->
<template>
  <div class="flex flex-col gap-1">
    <!-- 레이블 -->
    <label
      v-if="label"
      :for="inputId"
      class="text-sm font-medium text-secondary-700 dark:text-secondary-300"
    >
      {{ label }}
      <span v-if="required" class="text-danger-500 ml-0.5">*</span>
    </label>

    <!-- 인풋 래퍼 -->
    <div class="relative">
      <!-- 좌측 아이콘 슬롯 -->
      <span
        v-if="$slots.prefix"
        class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none
               text-secondary-400 dark:text-secondary-500"
      >
        <slot name="prefix" />
      </span>

      <input
        :id="inputId"
        v-model="model"
        :type="type"
        :placeholder="placeholder"
        :disabled="disabled"
        :class="inputClasses"
      />

      <!-- 우측 아이콘 슬롯 (에러 아이콘 등) -->
      <span
        v-if="$slots.suffix || hasError"
        class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none"
      >
        <ExclamationCircleIcon v-if="hasError" class="w-4 h-4 text-danger-500" />
        <slot v-else name="suffix" />
      </span>
    </div>

    <!-- 에러 메시지 -->
    <p v-if="errorMessage" class="text-xs text-danger-500 flex items-center gap-1">
      {{ errorMessage }}
    </p>
    <!-- 도움말 텍스트 -->
    <p v-else-if="hint" class="text-xs text-secondary-400 dark:text-secondary-500">
      {{ hint }}
    </p>
  </div>
</template>
```

```typescript
// BaseInput.vue <script setup>
const BASE_INPUT = [
  "w-full rounded border bg-surface text-secondary-900 placeholder-secondary-300",
  "text-sm leading-none",
  "transition-colors duration-150",
  "focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent",
  "dark:bg-secondary-800 dark:text-secondary-50 dark:placeholder-secondary-600",
].join(" ")

const STATE_CLASSES = {
  default:  "border-secondary-300 dark:border-secondary-600",
  error:    "border-danger-500 focus:ring-danger-500",
  disabled: "border-secondary-200 bg-secondary-50 text-secondary-400 cursor-not-allowed dark:bg-secondary-900",
}

const SIZE_PADDING = {
  withPrefix: "pl-9 pr-3 py-2.5",
  withSuffix: "pl-3 pr-9 py-2.5",
  normal:     "px-3 py-2.5",
}
```

**상태별 인풋 클래스 요약**

| 상태 | 추가 클래스 |
|---|---|
| Default | `border-secondary-300 dark:border-secondary-600` |
| Focus | `ring-2 ring-primary-500 border-transparent` (자동 — Tailwind focus:) |
| Error | `border-danger-500 focus:ring-danger-500` |
| Disabled | `border-secondary-200 bg-secondary-50 text-secondary-400 cursor-not-allowed` |

#### Select Box

```vue
<select
  v-model="model"
  :disabled="disabled"
  class="w-full rounded border border-secondary-300 bg-surface
         px-3 py-2.5 pr-8 text-sm text-secondary-900
         appearance-none bg-no-repeat bg-right
         focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent
         disabled:bg-secondary-50 disabled:text-secondary-400 disabled:cursor-not-allowed
         dark:bg-secondary-800 dark:border-secondary-600 dark:text-secondary-50
         transition-colors duration-150"
  :style="{ backgroundImage: `url(\"data:image/svg+xml,%3csvg...chevron-down...%3e\")`, backgroundPosition: 'right 0.75rem center', backgroundSize: '1em 1em' }"
>
  <option v-for="opt in options" :key="opt.value" :value="opt.value">
    {{ opt.label }}
  </option>
</select>
```

#### Checkbox

```vue
<label class="inline-flex items-center gap-2 cursor-pointer select-none group">
  <input
    v-model="model"
    type="checkbox"
    :disabled="disabled"
    class="h-4 w-4 rounded border-secondary-300
           text-primary-500
           focus:ring-2 focus:ring-primary-500 focus:ring-offset-1
           disabled:cursor-not-allowed disabled:opacity-50
           transition-colors duration-150"
  />
  <span
    class="text-sm text-secondary-700 group-has-[:disabled]:text-secondary-400
           dark:text-secondary-300"
  >
    <slot />
  </span>
</label>
```

---

### 2.3 Badge / Tag

차량 상태, 알림 유형, 권한 레벨을 시각적으로 표현합니다.

#### 차량 상태 배지 클래스

```typescript
// src/utils/badgeClasses.ts
export type VehicleStatus = "RUNNING" | "IDLE" | "CHARGING" | "ALERT" | "OFFLINE"
export type AlertSeverity = "INFO" | "WARNING" | "DANGER"
export type UserRole      = "ADMIN" | "MANAGER" | "DRIVER"

// 기본 배지 베이스
const BASE_BADGE = "inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold"

export const VEHICLE_STATUS_BADGE: Record<VehicleStatus, string> = {
  RUNNING:  `${BASE_BADGE} bg-success-100 text-success-700 dark:bg-success-900/30 dark:text-success-400`,
  IDLE:     `${BASE_BADGE} bg-secondary-100 text-secondary-600 dark:bg-secondary-700 dark:text-secondary-300`,
  CHARGING: `${BASE_BADGE} bg-info-100 text-info-700 dark:bg-info-900/30 dark:text-info-400`,
  ALERT:    `${BASE_BADGE} bg-danger-100 text-danger-700 dark:bg-danger-900/30 dark:text-danger-400`,
  OFFLINE:  `${BASE_BADGE} bg-secondary-100 text-secondary-400 dark:bg-secondary-800 dark:text-secondary-500`,
}

export const ALERT_SEVERITY_BADGE: Record<AlertSeverity, string> = {
  INFO:    `${BASE_BADGE} bg-info-100 text-info-700 dark:bg-info-900/30 dark:text-info-400`,
  WARNING: `${BASE_BADGE} bg-warning-100 text-warning-700 dark:bg-warning-900/30 dark:text-warning-500`,
  DANGER:  `${BASE_BADGE} bg-danger-100 text-danger-700 dark:bg-danger-900/30 dark:text-danger-400`,
}

export const ROLE_BADGE: Record<UserRole, string> = {
  ADMIN:   `${BASE_BADGE} bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400`,
  MANAGER: `${BASE_BADGE} bg-secondary-200 text-secondary-700 dark:bg-secondary-700 dark:text-secondary-300`,
  DRIVER:  `${BASE_BADGE} bg-surface border border-secondary-200 text-secondary-600`,
}
```

```vue
<!-- 사용 예시: VehicleStatusBadge.vue -->
<template>
  <span :class="VEHICLE_STATUS_BADGE[status]">
    <!-- 상태 dot -->
    <span :class="dotClass" class="inline-block w-1.5 h-1.5 rounded-full" />
    {{ VEHICLE_STATUS_LABEL[status] }}
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue"
import { VEHICLE_STATUS_BADGE, type VehicleStatus } from "@/utils/badgeClasses"

const props = defineProps<{ status: VehicleStatus }>()

const VEHICLE_STATUS_LABEL: Record<VehicleStatus, string> = {
  RUNNING: "운행중", IDLE: "정차", CHARGING: "충전중", ALERT: "경고", OFFLINE: "오프라인",
}

const dotClass = computed(() => ({
  "bg-success-500": props.status === "RUNNING",
  "bg-secondary-400": props.status === "IDLE" || props.status === "OFFLINE",
  "bg-info-500": props.status === "CHARGING",
  "bg-danger-500": props.status === "ALERT",
}))
</script>
```

**대형 태그 (필터 칩)**

```vue
<!-- 필터 선택 칩 — 선택/비선택 두 가지 상태 -->
<button
  :class="[
    'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium',
    'border transition-colors duration-150',
    'focus-visible:ring-2 focus-visible:ring-primary-500',
    selected
      ? 'bg-primary-500 border-primary-500 text-white'
      : 'bg-surface border-secondary-300 text-secondary-600 hover:border-primary-400 hover:text-primary-600',
  ]"
  @click="$emit('toggle')"
>
  <slot />
  <XMarkIcon v-if="selected" class="w-3 h-3" />
</button>
```

---

## 3. Compound Components

### 3.1 Card

관제 대시보드의 모든 정보 블록은 Card 컴포넌트를 기반으로 합니다.

#### 기본 구조 및 변형

```vue
<!-- BaseCard.vue -->
<template>
  <!-- variant: default | flat | bordered | elevated -->
  <div :class="cardClasses">
    <!-- 카드 헤더 (선택) -->
    <div
      v-if="$slots.header || title"
      class="flex items-center justify-between
             px-5 py-3.5
             border-b border-secondary-100 dark:border-secondary-700"
    >
      <slot name="header">
        <h3 class="text-sm font-semibold text-secondary-700 dark:text-secondary-300">
          {{ title }}
        </h3>
      </slot>
      <slot name="header-action" />
    </div>

    <!-- 카드 바디 -->
    <div :class="['flex-1', bodyPadding]">
      <slot />
    </div>

    <!-- 카드 푸터 (선택) -->
    <div
      v-if="$slots.footer"
      class="px-5 py-3
             border-t border-secondary-100 dark:border-secondary-700
             bg-secondary-50 dark:bg-secondary-800/50
             rounded-b-lg"
    >
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue"

type CardVariant = "default" | "flat" | "bordered" | "elevated"

const props = withDefaults(defineProps<{
  variant?: CardVariant
  title?: string
  noPadding?: boolean
}>(), { variant: "default" })

const BASE = "flex flex-col bg-surface dark:bg-secondary-800 rounded-lg overflow-hidden"

const VARIANT_CLASSES: Record<CardVariant, string> = {
  default:  "shadow-sm border border-secondary-100 dark:border-secondary-700",
  flat:     "border-none shadow-none",
  bordered: "border border-secondary-200 dark:border-secondary-700 shadow-none",
  elevated: "shadow-md border-none",
}

const cardClasses  = computed(() => `${BASE} ${VARIANT_CLASSES[props.variant]}`)
const bodyPadding  = computed(() => props.noPadding ? "" : "p-5")
</script>
```

**대시보드 KPI 카드 (Stat Card)**

```vue
<!-- 예: 총 차량 수, 운행 중 차량, 오늘 알림 수 -->
<template>
  <BaseCard variant="default">
    <div class="flex items-start justify-between">
      <!-- 텍스트 영역 -->
      <div class="flex flex-col gap-1">
        <span class="text-xs font-semibold uppercase tracking-widest text-secondary-400">
          {{ label }}
        </span>
        <span class="text-3xl font-bold text-secondary-900 dark:text-secondary-50 tabular-nums">
          {{ value }}
        </span>
        <span
          v-if="delta"
          :class="delta > 0 ? 'text-success-600' : 'text-danger-600'"
          class="text-xs font-medium flex items-center gap-0.5"
        >
          <ArrowUpIcon v-if="delta > 0" class="w-3 h-3" />
          <ArrowDownIcon v-else class="w-3 h-3" />
          {{ Math.abs(delta) }}% 전일 대비
        </span>
      </div>
      <!-- 아이콘 영역 -->
      <div
        :class="iconBgClass"
        class="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
      >
        <component :is="icon" class="w-5 h-5" :class="iconColorClass" />
      </div>
    </div>
  </BaseCard>
</template>
```

**차량 상태 카드 (Vehicle Status Card)**

```vue
<!-- 지도 좌측 패널의 차량 리스트 카드 -->
<div
  class="group flex flex-col gap-3 p-4
         bg-surface dark:bg-secondary-800
         border border-secondary-100 dark:border-secondary-700
         rounded-lg shadow-sm
         hover:border-primary-300 hover:shadow-md
         transition-all duration-200
         cursor-pointer"
  :class="{ 'ring-2 ring-primary-500 border-primary-500': isSelected }"
  @click="$emit('select')"
>
  <!-- 상단: 차량 번호 + 상태 배지 -->
  <div class="flex items-center justify-between">
    <span class="text-sm font-semibold text-secondary-900 dark:text-secondary-50">
      {{ vehicle.plate_number }}
    </span>
    <VehicleStatusBadge :status="vehicle.status" />
  </div>
  <!-- 중단: 운전자 + 속도 -->
  <div class="flex items-center gap-3 text-xs text-secondary-500">
    <span class="flex items-center gap-1">
      <UserIcon class="w-3 h-3" /> {{ vehicle.driver_name ?? "미배정" }}
    </span>
    <span class="flex items-center gap-1">
      <BoltIcon class="w-3 h-3" /> {{ vehicle.battery_level }}%
    </span>
    <span class="flex items-center gap-1">
      <TruckIcon class="w-3 h-3" /> {{ vehicle.speed }} km/h
    </span>
  </div>
  <!-- 하단: 마지막 위치 -->
  <p class="text-xs text-secondary-400 truncate">
    <MapPinIcon class="w-3 h-3 inline mr-0.5" />{{ vehicle.last_location }}
  </p>
</div>
```

---

### 3.2 Modal / Dialog

#### Z-index 정책

```typescript
// src/utils/zIndex.ts — 전역 레이어 순서
export const Z_INDEX = {
  base:       0,
  raised:     10,   // 드롭다운, 툴팁
  sticky:     20,   // 사이드바, 헤더
  overlay:    30,   // 모달 배경
  modal:      40,   // 모달 창
  toast:      50,   // 토스트 알림
  spinner:    60,   // 전체화면 로딩
} as const
```

```css
/* src/assets/main.css — Tailwind @layer 확장 */
@layer utilities {
  .z-overlay { z-index: 30; }
  .z-modal   { z-index: 40; }
  .z-toast   { z-index: 50; }
}
```

#### Modal 컴포넌트

```vue
<!-- BaseModal.vue -->
<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="modelValue"
        class="fixed inset-0 z-overlay flex items-center justify-center p-4"
        aria-modal="true"
        role="dialog"
        @keydown.esc="$emit('update:modelValue', false)"
      >
        <!-- 오버레이 배경 -->
        <div
          class="absolute inset-0 bg-secondary-900/60 backdrop-blur-sm"
          @click="closeOnBackdrop && $emit('update:modelValue', false)"
        />

        <!-- 모달 창 -->
        <Transition
          enter-active-class="transition-all duration-200"
          enter-from-class="opacity-0 scale-95 translate-y-2"
          enter-to-class="opacity-100 scale-100 translate-y-0"
          leave-active-class="transition-all duration-150"
          leave-from-class="opacity-100 scale-100 translate-y-0"
          leave-to-class="opacity-0 scale-95 translate-y-2"
        >
          <div
            v-if="modelValue"
            :class="[
              'relative z-modal w-full bg-surface dark:bg-secondary-800',
              'rounded-xl shadow-xl',
              'flex flex-col overflow-hidden',
              SIZE_CLASSES[size],
            ]"
          >
            <!-- 헤더 -->
            <div class="flex items-center justify-between px-6 py-4 border-b border-secondary-100 dark:border-secondary-700">
              <h2 class="text-lg font-semibold text-secondary-900 dark:text-secondary-50">
                <slot name="title">{{ title }}</slot>
              </h2>
              <button
                class="w-8 h-8 flex items-center justify-center rounded-md
                       text-secondary-400 hover:bg-secondary-100 hover:text-secondary-600
                       dark:hover:bg-secondary-700
                       transition-colors duration-150"
                @click="$emit('update:modelValue', false)"
              >
                <XMarkIcon class="w-5 h-5" />
              </button>
            </div>

            <!-- 바디 -->
            <div class="flex-1 overflow-y-auto px-6 py-5">
              <slot />
            </div>

            <!-- 푸터 -->
            <div
              v-if="$slots.footer"
              class="flex items-center justify-end gap-3
                     px-6 py-4
                     border-t border-secondary-100 dark:border-secondary-700
                     bg-secondary-50 dark:bg-secondary-800/50"
            >
              <slot name="footer" />
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
type ModalSize = "sm" | "md" | "lg" | "xl" | "full"

withDefaults(defineProps<{
  modelValue: boolean
  title?: string
  size?: ModalSize
  closeOnBackdrop?: boolean
}>(), { size: "md", closeOnBackdrop: true })

defineEmits<{ "update:modelValue": [value: boolean] }>()

const SIZE_CLASSES: Record<ModalSize, string> = {
  sm:   "max-w-sm   max-h-[80vh]",
  md:   "max-w-lg   max-h-[85vh]",
  lg:   "max-w-2xl  max-h-[90vh]",
  xl:   "max-w-4xl  max-h-[90vh]",
  full: "max-w-full max-h-full m-0 rounded-none",
}
</script>
```

**배터리 교체 권고 모달 (실제 사용 예)**

```vue
<BaseModal v-model="showBatteryModal" title="배터리 교체 권고" size="sm">
  <div class="flex flex-col items-center gap-4 py-2">
    <!-- 경고 아이콘 -->
    <div class="w-16 h-16 rounded-full bg-warning-100 flex items-center justify-center">
      <ExclamationTriangleIcon class="w-8 h-8 text-warning-500" />
    </div>
    <p class="text-sm text-center text-secondary-600 dark:text-secondary-300">
      <strong class="text-secondary-900 dark:text-secondary-50">{{ vehicle.plate_number }}</strong>의
      배터리 잔량이 <strong class="text-warning-600">{{ battery }}%</strong>입니다.
      <br />가장 가까운 충전소로 이동을 안내합니다.
    </p>
  </div>

  <template #footer>
    <BaseButton variant="ghost" size="md" @click="showBatteryModal = false">나중에</BaseButton>
    <BaseButton variant="solid-primary" size="md" @click="goToCharging">충전소 안내</BaseButton>
  </template>
</BaseModal>
```

---

### 3.3 List Item

모바일 앱 및 사이드 패널의 반복 리스트에 사용합니다.

#### 기본 List Item 구조

```vue
<!-- BaseListItem.vue -->
<template>
  <!-- li 또는 div로 렌더링 (as prop) -->
  <component
    :is="as"
    :class="[
      'flex items-center gap-3 px-4 py-3',
      'bg-surface dark:bg-secondary-800',
      'border-b border-secondary-100 dark:border-secondary-700 last:border-b-0',
      interactive
        ? 'cursor-pointer hover:bg-secondary-50 dark:hover:bg-secondary-700/50 active:bg-secondary-100 transition-colors duration-150'
        : '',
    ]"
    v-bind="$attrs"
  >
    <!-- 왼쪽: 아이콘 or 아바타 (선택) -->
    <slot name="leading">
      <div
        v-if="leadingIcon"
        class="flex-shrink-0 w-10 h-10 rounded-full
               bg-secondary-100 dark:bg-secondary-700
               flex items-center justify-center"
      >
        <component :is="leadingIcon" class="w-5 h-5 text-secondary-500" />
      </div>
    </slot>

    <!-- 중앙: 주 텍스트 + 보조 텍스트 -->
    <div class="flex-1 min-w-0 flex flex-col gap-0.5">
      <span class="text-sm font-medium text-secondary-900 dark:text-secondary-50 truncate">
        <slot name="title">{{ title }}</slot>
      </span>
      <span
        v-if="$slots.subtitle || subtitle"
        class="text-xs text-secondary-500 dark:text-secondary-400 truncate"
      >
        <slot name="subtitle">{{ subtitle }}</slot>
      </span>
    </div>

    <!-- 오른쪽: 배지, 시간, 화살표 등 -->
    <slot name="trailing">
      <span v-if="trailingText" class="flex-shrink-0 text-xs text-secondary-400">
        {{ trailingText }}
      </span>
      <ChevronRightIcon v-if="interactive" class="flex-shrink-0 w-4 h-4 text-secondary-300" />
    </slot>
  </component>
</template>
```

**알림 리스트 아이템 (Alert List Item)**

```vue
<!-- 알림 목록 아이템 — 미확인 상태 포함 -->
<li
  class="flex items-start gap-3 px-4 py-4
         border-b border-secondary-100 dark:border-secondary-700 last:border-b-0
         cursor-pointer
         hover:bg-secondary-50 dark:hover:bg-secondary-700/50
         transition-colors duration-150"
  :class="{ 'bg-primary-50 dark:bg-primary-900/10': !alert.is_acknowledged }"
>
  <!-- 심각도 아이콘 -->
  <div
    :class="ALERT_ICON_BG[alert.severity]"
    class="flex-shrink-0 mt-0.5 w-8 h-8 rounded-full flex items-center justify-center"
  >
    <component :is="ALERT_ICON[alert.severity]" class="w-4 h-4" :class="ALERT_ICON_COLOR[alert.severity]" />
  </div>

  <div class="flex-1 min-w-0">
    <!-- 타이틀 행 -->
    <div class="flex items-center justify-between gap-2">
      <span class="text-sm font-medium text-secondary-900 dark:text-secondary-50 truncate">
        {{ alert.title }}
      </span>
      <div class="flex-shrink-0 flex items-center gap-1.5">
        <!-- 미확인 dot -->
        <span
          v-if="!alert.is_acknowledged"
          class="w-2 h-2 rounded-full bg-primary-500"
        />
        <span class="text-xs text-secondary-400 whitespace-nowrap">
          {{ formatRelativeTime(alert.triggered_at) }}
        </span>
      </div>
    </div>
    <!-- 서브타이틀 -->
    <p class="mt-0.5 text-xs text-secondary-500 dark:text-secondary-400 line-clamp-1">
      {{ alert.vehicle_plate }} · {{ alert.description }}
    </p>
  </div>
</li>
```

**차량 목록 리스트 아이템 (모바일)**

```vue
<!-- 모바일 앱 차량 목록 -->
<li
  class="flex items-center gap-3 px-4 py-3.5
         bg-surface dark:bg-secondary-800
         border-b border-secondary-100 dark:border-secondary-700
         active:bg-secondary-100 dark:active:bg-secondary-700
         transition-colors duration-150 cursor-pointer"
  @click="$emit('select', vehicle.id)"
>
  <!-- 차량 상태 컬러 바 -->
  <div
    :class="STATUS_LEFT_BAR[vehicle.status]"
    class="flex-shrink-0 w-1 h-12 rounded-full"
  />

  <div class="flex-1 min-w-0">
    <div class="flex items-center justify-between">
      <span class="text-sm font-semibold text-secondary-900 dark:text-secondary-50">
        {{ vehicle.plate_number }}
      </span>
      <VehicleStatusBadge :status="vehicle.status" />
    </div>
    <div class="mt-1 flex items-center gap-3 text-xs text-secondary-500">
      <span>{{ vehicle.driver_name }}</span>
      <span>·</span>
      <span class="flex items-center gap-0.5">
        <BoltIcon class="w-3 h-3" /> {{ vehicle.battery_level }}%
      </span>
    </div>
  </div>

  <ChevronRightIcon class="flex-shrink-0 w-4 h-4 text-secondary-300" />
</li>

<script>
const STATUS_LEFT_BAR: Record<VehicleStatus, string> = {
  RUNNING:  "bg-success-500",
  IDLE:     "bg-secondary-300",
  CHARGING: "bg-info-500",
  ALERT:    "bg-danger-500",
  OFFLINE:  "bg-secondary-200",
}
</script>
```

---

## 4. Layout Templates

### 4.1 관제 대시보드 (Web)

#### 전체 뼈대 구조

```
┌─────────────────────────────────────────────┐
│                  Header (64px)              │ ← fixed top
├──────────────┬──────────────────────────────┤
│              │                              │
│   Sidebar    │       Main Content           │
│  (240px)     │       (flex-1)               │
│  fixed left  │       overflow-y-scroll      │
│              │                              │
└──────────────┴──────────────────────────────┘
```

#### AppLayout.vue

```vue
<!-- src/layouts/AppLayout.vue -->
<template>
  <div class="min-h-screen bg-background dark:bg-secondary-900">
    <!-- ① 헤더 (GNB) -->
    <header
      class="fixed top-0 left-0 right-0 h-16 z-sticky
             flex items-center
             bg-surface dark:bg-secondary-800
             border-b border-secondary-200 dark:border-secondary-700
             shadow-sm px-4"
    >
      <!-- 로고 -->
      <div class="flex items-center gap-2 w-60 flex-shrink-0">
        <img src="@/assets/logo.svg" alt="FMS" class="h-8 w-auto" />
        <span class="text-base font-bold text-secondary-900 dark:text-secondary-50 hidden sm:block">
          FMS
        </span>
      </div>
      <!-- 중앙: 검색 (md 이상) -->
      <div class="flex-1 max-w-xl hidden md:flex px-4">
        <BaseInput placeholder="차량 번호 검색..." class="w-full">
          <template #prefix><MagnifyingGlassIcon class="w-4 h-4" /></template>
        </BaseInput>
      </div>
      <!-- 우측: 알림 + 프로필 -->
      <div class="ml-auto flex items-center gap-2">
        <button class="relative w-9 h-9 flex items-center justify-center rounded-md
                       text-secondary-500 hover:bg-secondary-100 dark:hover:bg-secondary-700
                       transition-colors duration-150">
          <BellIcon class="w-5 h-5" />
          <span
            v-if="unreadCount > 0"
            class="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-danger-500"
          />
        </button>
        <!-- 프로필 아바타 -->
        <button class="w-8 h-8 rounded-full bg-primary-500 text-white text-xs font-bold
                       flex items-center justify-center
                       ring-2 ring-transparent hover:ring-primary-300
                       transition-all duration-150">
          {{ initials }}
        </button>
      </div>
    </header>

    <div class="flex pt-16">
      <!-- ② 사이드바 -->
      <aside
        :class="[
          'fixed left-0 top-16 bottom-0 z-sticky',
          'bg-surface dark:bg-secondary-800',
          'border-r border-secondary-200 dark:border-secondary-700',
          'flex flex-col overflow-y-auto overflow-x-hidden',
          'transition-all duration-300 ease-in-out',
          isSidebarCollapsed ? 'w-16' : 'w-60',
          'hidden md:flex',  // 모바일에서는 숨김
        ]"
      >
        <nav class="flex-1 px-3 py-4 flex flex-col gap-1">
          <SidebarNavItem
            v-for="item in navItems"
            :key="item.path"
            :item="item"
            :collapsed="isSidebarCollapsed"
          />
        </nav>
        <!-- 사이드바 접기 버튼 -->
        <div class="px-3 py-3 border-t border-secondary-100 dark:border-secondary-700">
          <button
            class="w-full flex items-center justify-center h-9 rounded-md
                   text-secondary-400 hover:bg-secondary-100 dark:hover:bg-secondary-700
                   transition-colors duration-150"
            @click="toggleSidebar"
          >
            <ChevronLeftIcon
              :class="['w-4 h-4 transition-transform duration-300', isSidebarCollapsed ? 'rotate-180' : '']"
            />
          </button>
        </div>
      </aside>

      <!-- ③ 메인 콘텐츠 영역 -->
      <main
        :class="[
          'flex-1 min-h-[calc(100vh-4rem)] transition-all duration-300',
          isSidebarCollapsed ? 'md:ml-16' : 'md:ml-60',
        ]"
      >
        <RouterView />
      </main>
    </div>
  </div>
</template>
```

#### 사이드바 네비게이션 아이템

```vue
<!-- SidebarNavItem.vue -->
<template>
  <RouterLink
    :to="item.path"
    custom
    v-slot="{ isActive, navigate }"
  >
    <button
      :class="[
        'w-full flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium',
        'transition-colors duration-150 group',
        isActive
          ? 'bg-primary-50 text-primary-600 dark:bg-primary-900/20 dark:text-primary-400'
          : 'text-secondary-600 hover:bg-secondary-100 dark:text-secondary-400 dark:hover:bg-secondary-700/50',
        collapsed ? 'justify-center' : '',
      ]"
      @click="navigate"
    >
      <component
        :is="item.icon"
        :class="['w-5 h-5 flex-shrink-0', isActive ? 'text-primary-500' : 'text-secondary-400 group-hover:text-secondary-600']"
      />
      <span v-if="!collapsed" class="truncate">{{ item.label }}</span>
      <!-- 알림 카운트 배지 -->
      <span
        v-if="!collapsed && item.badge"
        class="ml-auto min-w-[1.25rem] h-5 px-1 flex items-center justify-center
               text-xs font-semibold rounded-full bg-danger-500 text-white"
      >
        {{ item.badge > 99 ? "99+" : item.badge }}
      </span>
    </button>
  </RouterLink>
</template>
```

#### 대시보드 메인 페이지 그리드

```vue
<!-- views/DashboardView.vue -->
<template>
  <div class="p-6 flex flex-col gap-6">
    <!-- 페이지 타이틀 -->
    <div class="flex items-center justify-between">
      <h1 class="text-2xl font-bold text-secondary-900 dark:text-secondary-50">관제 대시보드</h1>
      <span class="text-xs text-secondary-400">실시간 업데이트</span>
    </div>

    <!-- KPI 카드 행 -->
    <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard v-for="stat in kpiStats" :key="stat.key" v-bind="stat" />
    </div>

    <!-- 메인 2단 레이아웃: 지도 + 차량 목록 -->
    <div class="grid grid-cols-1 gap-4 xl:grid-cols-3">
      <!-- 지도 (2/3 너비) -->
      <div class="xl:col-span-2">
        <BaseCard title="실시간 차량 위치" variant="default" no-padding>
          <div class="h-[480px] rounded-b-lg overflow-hidden">
            <VehicleMap />
          </div>
        </BaseCard>
      </div>
      <!-- 차량 목록 패널 (1/3 너비) -->
      <div class="xl:col-span-1">
        <BaseCard title="차량 현황" variant="default" no-padding>
          <div class="h-[480px] overflow-y-auto">
            <VehicleListPanel />
          </div>
        </BaseCard>
      </div>
    </div>

    <!-- 알림 목록 -->
    <BaseCard title="최근 알림" variant="default">
      <AlertList :items="recentAlerts" />
    </BaseCard>
  </div>
</template>
```

#### 반응형 브레이크포인트 정책

| 브레이크포인트 | 접두사 | 너비 | 레이아웃 변화 |
|---|---|---|---|
| Mobile | (base) | < 768px | 사이드바 숨김, 단일 컬럼, 하단 탭바 |
| Tablet | `md:` | ≥ 768px | 사이드바 접힘(collapsed), 2컬럼 그리드 |
| Desktop | `lg:` | ≥ 1024px | 사이드바 펼침(expanded), 3컬럼 그리드 |
| Wide | `xl:` | ≥ 1280px | 지도+리스트 분리, KPI 4컬럼 |
| Ultra | `2xl:` | ≥ 1536px | 패딩 확대, 최대 너비 제한 (`max-w-screen-2xl mx-auto`) |

---

### 4.2 모바일 앱 (App)

```
┌─────────────────┐
│  Top App Bar    │ ← 56px, fixed top
│  (h-14)         │
├─────────────────┤
│                 │
│  Scrollable     │ ← flex-1, overflow-y-auto
│  Content        │   padding-bottom: 80px (하단 탭바 공간)
│                 │
├─────────────────┤
│ Bottom Nav Bar  │ ← 64px, fixed bottom (safe-area 대응)
│  (h-16)         │
└─────────────────┘
```

#### MobileLayout.vue

```vue
<!-- src/layouts/MobileLayout.vue -->
<template>
  <div class="flex flex-col h-screen bg-background dark:bg-secondary-900 overflow-hidden">
    <!-- ① Top App Bar -->
    <header
      class="flex-shrink-0 h-14 flex items-center justify-between
             px-4
             bg-surface dark:bg-secondary-800
             border-b border-secondary-200 dark:border-secondary-700
             shadow-sm z-sticky"
    >
      <!-- 뒤로가기 or 타이틀 -->
      <div class="flex items-center gap-2">
        <button
          v-if="showBack"
          class="w-9 h-9 flex items-center justify-center rounded-md -ml-2
                 text-secondary-600 hover:bg-secondary-100 dark:text-secondary-300"
          @click="$router.back()"
        >
          <ChevronLeftIcon class="w-5 h-5" />
        </button>
        <h1 class="text-base font-semibold text-secondary-900 dark:text-secondary-50">
          {{ pageTitle }}
        </h1>
      </div>
      <!-- 우측 액션 -->
      <slot name="top-action" />
    </header>

    <!-- ② 스크롤 가능한 콘텐츠 영역 -->
    <main
      class="flex-1 overflow-y-auto overscroll-contain
             pb-safe-bottom"   <!-- iOS Safe Area 대응: env(safe-area-inset-bottom) -->
      style="padding-bottom: calc(4rem + env(safe-area-inset-bottom, 0px))"
    >
      <RouterView />
    </main>

    <!-- ③ Bottom Navigation Bar -->
    <nav
      class="flex-shrink-0 fixed bottom-0 left-0 right-0
             flex items-center justify-around
             h-16 bg-surface dark:bg-secondary-800
             border-t border-secondary-200 dark:border-secondary-700
             shadow-[0_-1px_4px_rgba(0,0,0,0.08)]
             z-sticky"
      style="padding-bottom: env(safe-area-inset-bottom, 0px)"
    >
      <RouterLink
        v-for="tab in bottomTabs"
        :key="tab.path"
        :to="tab.path"
        custom
        v-slot="{ isActive }"
      >
        <button
          class="flex flex-col items-center justify-center gap-1 flex-1 py-2 h-full"
          @click="$router.push(tab.path)"
        >
          <component
            :is="isActive ? tab.activeIcon : tab.icon"
            :class="['w-6 h-6 transition-colors duration-150', isActive ? 'text-primary-500' : 'text-secondary-400']"
          />
          <span
            :class="['text-[10px] font-medium transition-colors duration-150', isActive ? 'text-primary-500' : 'text-secondary-400']"
          >
            {{ tab.label }}
          </span>
        </button>
      </RouterLink>
    </nav>
  </div>
</template>
```

**모바일 바텀시트 (Bottom Sheet)**

```vue
<!-- 배터리 교체 안내, 충전소 선택 등 모바일 전용 -->
<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-300"
      enter-from-class="translate-y-full"
      enter-to-class="translate-y-0"
      leave-active-class="transition-all duration-200"
      leave-from-class="translate-y-0"
      leave-to-class="translate-y-full"
    >
      <div
        v-if="modelValue"
        class="fixed inset-x-0 bottom-0 z-modal
               bg-surface dark:bg-secondary-800
               rounded-t-2xl shadow-2xl
               flex flex-col overflow-hidden"
        :style="{ maxHeight: maxHeight ?? '80vh' }"
      >
        <!-- 드래그 핸들 -->
        <div class="flex justify-center pt-3 pb-2 flex-shrink-0">
          <div class="w-9 h-1 rounded-full bg-secondary-300 dark:bg-secondary-600" />
        </div>
        <!-- 타이틀 -->
        <div
          v-if="title"
          class="px-5 pb-3 flex-shrink-0 border-b border-secondary-100 dark:border-secondary-700"
        >
          <h2 class="text-base font-semibold text-secondary-900 dark:text-secondary-50">
            {{ title }}
          </h2>
        </div>
        <!-- 콘텐츠 -->
        <div class="flex-1 overflow-y-auto overscroll-contain px-5 py-4">
          <slot />
        </div>
        <!-- 액션 버튼 -->
        <div
          v-if="$slots.actions"
          class="px-5 pb-4 pt-3 flex gap-3
                 border-t border-secondary-100 dark:border-secondary-700"
          style="padding-bottom: calc(1rem + env(safe-area-inset-bottom, 0px))"
        >
          <slot name="actions" />
        </div>
      </div>
    </Transition>
    <!-- 배경 오버레이 -->
    <Transition enter-active-class="transition-opacity duration-200" enter-from-class="opacity-0" enter-to-class="opacity-100">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-overlay bg-secondary-900/50"
        @click="$emit('update:modelValue', false)"
      />
    </Transition>
  </Teleport>
</template>
```

---

### 4.3 Auth Page

로그인, 비밀번호 재설정 등 인증 페이지는 **중앙 정렬 카드** 레이아웃을 사용합니다.

```vue
<!-- src/layouts/AuthLayout.vue -->
<template>
  <!-- 배경: 그라디언트 + 패턴 -->
  <div
    class="min-h-screen flex flex-col items-center justify-center
           bg-gradient-to-br from-secondary-900 via-primary-950 to-secondary-900
           px-4 py-12"
  >
    <!-- 배경 장식 (선택적) -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-primary-600/10 blur-3xl" />
      <div class="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-primary-800/10 blur-3xl" />
    </div>

    <!-- 로고 -->
    <div class="relative z-10 mb-8 flex flex-col items-center gap-2">
      <img src="@/assets/logo-white.svg" alt="FMS" class="h-12 w-auto" />
      <span class="text-white/60 text-sm">지능형 오토바이 FMS</span>
    </div>

    <!-- 인증 카드 -->
    <div
      class="relative z-10
             w-full max-w-md
             bg-surface dark:bg-secondary-800
             rounded-2xl shadow-2xl shadow-black/30
             p-8"
    >
      <RouterView />
    </div>

    <!-- 하단 푸터 -->
    <p class="relative z-10 mt-6 text-xs text-white/40">
      © 2026 Bikeplatform. All rights reserved.
    </p>
  </div>
</template>
```

**로그인 폼 (LoginView.vue) — 레이아웃 구조**

```vue
<!-- src/views/auth/LoginView.vue -->
<template>
  <div class="flex flex-col gap-6">
    <!-- 헤더 -->
    <div class="text-center">
      <h1 class="text-2xl font-bold text-secondary-900 dark:text-secondary-50">로그인</h1>
      <p class="mt-1 text-sm text-secondary-500">관제 시스템에 로그인하세요</p>
    </div>

    <!-- 폼 -->
    <form class="flex flex-col gap-4" @submit.prevent="onSubmit">
      <BaseInput
        v-model="form.email"
        label="이메일"
        type="email"
        placeholder="admin@example.com"
        :error-message="errors.email"
        required
        autocomplete="email"
      >
        <template #prefix><EnvelopeIcon class="w-4 h-4" /></template>
      </BaseInput>

      <BaseInput
        v-model="form.password"
        label="비밀번호"
        type="password"
        placeholder="비밀번호를 입력하세요"
        :error-message="errors.password"
        required
        autocomplete="current-password"
      >
        <template #prefix><LockClosedIcon class="w-4 h-4" /></template>
      </BaseInput>

      <!-- 기억하기 + 비밀번호 찾기 -->
      <div class="flex items-center justify-between">
        <label class="inline-flex items-center gap-2 cursor-pointer">
          <input v-model="form.remember" type="checkbox"
                 class="h-4 w-4 rounded border-secondary-300 text-primary-500 focus:ring-primary-500" />
          <span class="text-sm text-secondary-600 dark:text-secondary-400">로그인 유지</span>
        </label>
        <RouterLink
          to="/auth/forgot-password"
          class="text-sm text-primary-600 hover:text-primary-700 hover:underline
                 dark:text-primary-400 transition-colors duration-150"
        >
          비밀번호 찾기
        </RouterLink>
      </div>

      <!-- 에러 메시지 (서버) -->
      <div
        v-if="serverError"
        class="flex items-center gap-2 p-3 rounded-md bg-danger-50 border border-danger-200
               dark:bg-danger-900/20 dark:border-danger-800"
      >
        <ExclamationCircleIcon class="w-4 h-4 flex-shrink-0 text-danger-500" />
        <p class="text-xs text-danger-700 dark:text-danger-400">{{ serverError }}</p>
      </div>

      <!-- 제출 버튼 -->
      <BaseButton
        variant="solid-primary"
        size="lg"
        type="submit"
        :loading="isLoading"
        class="w-full mt-2"
      >
        {{ isLoading ? "로그인 중..." : "로그인" }}
      </BaseButton>
    </form>
  </div>
</template>
```

---

## 부록 A. Toast 알림 컴포넌트

```vue
<!-- src/components/global/ToastContainer.vue -->
<template>
  <Teleport to="body">
    <div
      class="fixed top-4 right-4 z-toast
             flex flex-col gap-2 items-end
             pointer-events-none
             max-w-sm w-full"
    >
      <TransitionGroup
        enter-active-class="transition-all duration-300"
        enter-from-class="opacity-0 translate-x-8 scale-95"
        enter-to-class="opacity-100 translate-x-0 scale-100"
        leave-active-class="transition-all duration-200"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-95 translate-x-4"
        move-class="transition-all duration-200"
      >
        <div
          v-for="toast in toastQueue"
          :key="toast.id"
          class="pointer-events-auto w-full flex items-start gap-3 px-4 py-3 rounded-lg shadow-lg"
          :class="TOAST_CLASSES[toast.type]"
        >
          <component :is="TOAST_ICON[toast.type]" class="w-5 h-5 flex-shrink-0 mt-0.5" />
          <p class="flex-1 text-sm font-medium">{{ toast.message }}</p>
          <button
            class="flex-shrink-0 opacity-60 hover:opacity-100 transition-opacity"
            @click="removeToast(toast.id)"
          >
            <XMarkIcon class="w-4 h-4" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { storeToRefs } from "pinia"
import { useUIStore } from "@/stores/ui"

const uiStore = useUIStore()
const { toastQueue } = storeToRefs(uiStore)
const { removeToast } = uiStore

const TOAST_CLASSES = {
  success: "bg-success-50 border border-success-200 text-success-800 dark:bg-success-900/30 dark:border-success-800 dark:text-success-300",
  warning: "bg-warning-50 border border-warning-200 text-warning-800 dark:bg-warning-900/30 dark:border-warning-800 dark:text-warning-300",
  error:   "bg-danger-50  border border-danger-200  text-danger-800  dark:bg-danger-900/30  dark:border-danger-800  dark:text-danger-300",
  info:    "bg-info-50    border border-info-200    text-info-800    dark:bg-info-900/30    dark:border-info-800    dark:text-info-300",
}
</script>
```

---

## 부록 B. 컴포넌트 디렉토리 구조

```
src/
├── components/
│   ├── base/                  # Atomic 컴포넌트 (재사용 단위)
│   │   ├── BaseButton.vue
│   │   ├── BaseInput.vue
│   │   ├── BaseCard.vue
│   │   ├── BaseModal.vue
│   │   ├── BaseListItem.vue
│   │   ├── BaseBadge.vue
│   │   └── BaseSelect.vue
│   ├── domain/                # 도메인별 Compound 컴포넌트
│   │   ├── vehicle/
│   │   │   ├── VehicleStatusBadge.vue
│   │   │   ├── VehicleCard.vue
│   │   │   └── VehicleListItem.vue
│   │   ├── alert/
│   │   │   ├── AlertListItem.vue
│   │   │   └── AlertSeverityBadge.vue
│   │   └── dashboard/
│   │       ├── StatCard.vue
│   │       └── KpiRow.vue
│   └── global/                # 전역 싱글턴 컴포넌트
│       ├── ToastContainer.vue
│       └── GlobalLoadingBar.vue
├── layouts/
│   ├── AppLayout.vue          # 관제 대시보드 레이아웃
│   ├── MobileLayout.vue       # 모바일 앱 레이아웃
│   └── AuthLayout.vue         # 인증 페이지 레이아웃
└── utils/
    ├── badgeClasses.ts         # 상태 → 클래스 매핑
    └── useButtonClasses.ts     # 버튼 클래스 컴포저블
```

---

> **개정 이력**  
> - v1.0 (2026-04-13): 초안 작성 — Foundation, Atomic, Compound, Layout Template 전 항목
