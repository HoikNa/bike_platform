<template>
  <span :class="badgeClass">
    <!-- 상태 점 (dot 모드일 때만 표시) -->
    <span
      v-if="dot"
      :class="['inline-block w-1.5 h-1.5 rounded-full mr-1.5 flex-shrink-0', dotColor]"
    />
    {{ text }}
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue"

/** 지원 상태 값 */
export type BadgeStatus = "success" | "warning" | "danger" | "info" | "default"

/** 뱃지 크기 */
export type BadgeSize = "sm" | "md"

const props = withDefaults(
  defineProps<{
    /** 상태 값 → 색상 자동 매핑 */
    status: BadgeStatus
    /** 표시할 텍스트 */
    text: string
    /** 왼쪽에 컬러 점 표시 여부 */
    dot?: boolean
    /** 크기: sm(기본) | md */
    size?: BadgeSize
  }>(),
  {
    dot: false,
    size: "sm",
  }
)

// ── 상태 → 색상 매핑 ────────────────────────────────────────────
const colorMap: Record<BadgeStatus, { bg: string; text: string; dot: string }> = {
  success: {
    bg:   "bg-success-100 dark:bg-success-900/30",
    text: "text-success-700 dark:text-success-400",
    dot:  "bg-success-500",
  },
  warning: {
    bg:   "bg-warning-100 dark:bg-warning-900/30",
    text: "text-warning-700 dark:text-warning-400",
    dot:  "bg-warning-500",
  },
  danger: {
    bg:   "bg-danger-100 dark:bg-danger-900/30",
    text: "text-danger-700 dark:text-danger-400",
    dot:  "bg-danger-500",
  },
  info: {
    bg:   "bg-info-100 dark:bg-info-900/30",
    text: "text-info-700 dark:text-info-400",
    dot:  "bg-info-500",
  },
  default: {
    bg:   "bg-secondary-100 dark:bg-secondary-700",
    text: "text-secondary-600 dark:text-secondary-300",
    dot:  "bg-secondary-400",
  },
}

const sizeClass: Record<BadgeSize, string> = {
  sm: "text-xs px-1.5 py-0.5",
  md: "text-sm px-2.5 py-1",
}

const badgeClass = computed(() => {
  const c = colorMap[props.status]
  return [
    "inline-flex items-center font-medium rounded-md",
    sizeClass[props.size],
    c.bg,
    c.text,
  ].join(" ")
})

const dotColor = computed(() => colorMap[props.status].dot)
</script>
