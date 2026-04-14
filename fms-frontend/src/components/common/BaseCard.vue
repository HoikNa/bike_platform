<template>
  <div :class="cardClass">
    <!-- 헤더 슬롯 (선택적) -->
    <div
      v-if="$slots.header || title"
      class="flex items-center justify-between px-5 py-3.5 border-b border-slate-100 dark:border-secondary-700"
    >
      <slot name="header">
        <h3 class="text-sm font-semibold text-secondary-900 dark:text-white">{{ title }}</h3>
      </slot>
      <!-- 우측 액션 영역 (옵션) -->
      <div v-if="$slots.action" class="flex items-center gap-2">
        <slot name="action" />
      </div>
    </div>

    <!-- 본문 슬롯 -->
    <div :class="['flex-1', noPadding ? '' : 'p-5']">
      <slot />
    </div>

    <!-- 푸터 슬롯 (선택적) -->
    <div
      v-if="$slots.footer"
      class="px-5 py-3 border-t border-slate-100 dark:border-secondary-700"
    >
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue"

const props = withDefaults(
  defineProps<{
    /** 헤더 슬롯 없이 간단한 제목만 표시할 때 */
    title?: string
    /** 본문 padding 제거 (테이블, 리스트 등 직접 패딩을 제어할 때) */
    noPadding?: boolean
    /** 카드 변형: default(흰색), flat(그림자 없음), raised(그림자 강화) */
    variant?: "default" | "flat" | "raised"
    /** 추가 CSS 클래스 */
    class?: string
  }>(),
  {
    variant: "default",
    noPadding: false,
  }
)

const cardClass = computed(() => {
  const base = [
    "flex flex-col rounded-xl border border-slate-200 dark:border-secondary-700",
    "bg-surface dark:bg-secondary-800 overflow-hidden",
  ]
  const shadow: Record<string, string> = {
    default: "shadow-sm",
    flat:    "shadow-none",
    raised:  "shadow-md",
  }
  return [...base, shadow[props.variant], props.class ?? ""].filter(Boolean).join(" ")
})
</script>
