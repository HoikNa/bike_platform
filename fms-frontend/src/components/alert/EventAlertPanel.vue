<template>
  <BaseCard variant="raised" :no-padding="true" class="w-80">

    <!-- ── 헤더 ─────────────────────────────────────────────── -->
    <template #header>
      <div class="flex items-center gap-2">
        <AlertTriangle class="w-4 h-4 text-danger-500 flex-shrink-0" />
        <span class="text-sm font-semibold text-secondary-900 dark:text-white">실시간 알림</span>
      </div>
      <Transition name="fade">
        <span
          v-if="alertStore.alerts.length > 0"
          :key="alertStore.alerts.length"
          class="ml-auto text-xs font-bold px-1.5 py-0.5 rounded-full
                 bg-danger-100 dark:bg-danger-900/30 text-danger-700 dark:text-danger-400"
        >
          {{ alertStore.alerts.length }}
        </span>
      </Transition>
    </template>

    <!-- ── 알림 없음 ─────────────────────────────────────────── -->
    <Transition name="fade">
      <div
        v-if="alertStore.alerts.length === 0"
        class="px-4 py-8 text-center"
      >
        <Info class="w-8 h-8 text-secondary-300 dark:text-secondary-600 mx-auto mb-2" />
        <p class="text-xs text-secondary-400 dark:text-secondary-500">새 알림이 없습니다.</p>
      </div>
    </Transition>

    <!-- ── 알림 목록: TransitionGroup으로 항목 진입/퇴장 애니메이션 ── -->
    <TransitionGroup
      v-if="alertStore.alerts.length > 0"
      name="alert-item"
      tag="ul"
      class="divide-y divide-slate-100 dark:divide-secondary-700"
    >
      <li
        v-for="alert in visibleAlerts"
        :key="alert.id"
        :class="[
          'relative flex items-start gap-3 px-4 py-3',
          'cursor-pointer transition-colors',
          'hover:bg-secondary-50 dark:hover:bg-secondary-700/50',
          'border-l-[3px]',
          severityBorderColor(alert.severity),
        ]"
      >
        <!-- 심각도 아이콘 -->
        <component
          :is="severityIcon(alert.severity)"
          :class="['w-4 h-4 mt-0.5 flex-shrink-0', severityIconColor(alert.severity)]"
        />

        <!-- 알림 내용 -->
        <div class="flex-1 min-w-0">
          <p class="text-xs font-semibold text-secondary-900 dark:text-white truncate">
            {{ alert.title }}
          </p>
          <p class="text-[11px] text-secondary-500 dark:text-secondary-400 mt-0.5">
            {{ alert.plate }} · {{ relativeTime(alert.createdAt) }}
          </p>
        </div>

        <!-- 심각도 뱃지 -->
        <StatusBadge
          :status="alert.severity"
          :text="severityLabel(alert.severity)"
        />
      </li>
    </TransitionGroup>

    <!-- ── 더보기 표시 줄 (접혀 있고 숨겨진 항목이 있을 때) ─── -->
    <div
      v-if="!showAll && hiddenCount > 0"
      class="px-4 py-1.5 text-center border-t border-slate-100 dark:border-secondary-700
             bg-secondary-50/60 dark:bg-secondary-700/30"
    >
      <span class="text-[11px] text-secondary-400 dark:text-secondary-500">
        + {{ hiddenCount }}개 더
      </span>
    </div>

    <!-- ── 푸터 ─────────────────────────────────────────────── -->
    <template #footer>
      <div class="flex items-center justify-between">
        <!-- 전체 보기 / 접기 토글 -->
        <button
          v-if="alertStore.alerts.length > PREVIEW_COUNT"
          @click="showAll = !showAll"
          class="text-xs text-primary-500 hover:text-primary-600 dark:hover:text-primary-400 font-medium transition-colors"
        >
          {{ showAll ? '↑ 접기' : `전체 보기 (${alertStore.alerts.length}개) →` }}
        </button>
        <span v-else class="text-xs text-secondary-400" />

        <button
          v-if="alertStore.alerts.length > 0"
          @click="alertStore.clearAll()"
          class="text-xs text-secondary-400 hover:text-secondary-600 dark:hover:text-secondary-300 transition-colors"
        >
          모두 지우기
        </button>
      </div>
    </template>

  </BaseCard>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue"
import { AlertTriangle, Zap, Info } from "lucide-vue-next"
import type { Component } from "vue"
import BaseCard from "@/components/common/BaseCard.vue"
import StatusBadge from "@/components/common/StatusBadge.vue"
import { useAlertStore } from "@/stores/useAlertStore"
import type { SimSeverity } from "@/stores/useAlertStore"

// ── 상수 ──────────────────────────────────────────────────────
const PREVIEW_COUNT = 5   // 기본 표시 개수

// ── 스토어 ──────────────────────────────────────────────────────
const alertStore = useAlertStore()

// ── 전체 보기 / 접기 ─────────────────────────────────────────
const showAll = ref(false)

const visibleAlerts = computed(() =>
  showAll.value
    ? alertStore.alerts
    : alertStore.alerts.slice(0, PREVIEW_COUNT)
)

const hiddenCount = computed(() =>
  Math.max(0, alertStore.alerts.length - PREVIEW_COUNT)
)

// ── 상대 시간 표시 (currentTime 틱으로 주기적 갱신) ─────────────
const currentTime = ref(Date.now())
let tickId: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  tickId = setInterval(() => { currentTime.value = Date.now() }, 10_000)
})
onUnmounted(() => {
  if (tickId !== null) clearInterval(tickId)
})

function relativeTime(ts: number): string {
  const diff = currentTime.value - ts
  const secs = Math.floor(diff / 1_000)
  if (secs < 10)   return "방금 전"
  if (secs < 60)   return `${secs}초 전`
  const mins = Math.floor(secs / 60)
  if (mins < 60)   return `${mins}분 전`
  return `${Math.floor(mins / 60)}시간 전`
}

// ── 심각도별 스타일 헬퍼 ────────────────────────────────────────
function severityBorderColor(severity: SimSeverity): string {
  const map: Record<SimSeverity, string> = {
    danger:  "border-l-danger-500",
    warning: "border-l-warning-400",
    info:    "border-l-info-400",
  }
  return map[severity]
}

function severityIcon(severity: SimSeverity): Component {
  const map: Record<SimSeverity, Component> = {
    danger:  AlertTriangle,
    warning: Zap,
    info:    Info,
  }
  return map[severity]
}

function severityIconColor(severity: SimSeverity): string {
  const map: Record<SimSeverity, string> = {
    danger:  "text-danger-500",
    warning: "text-warning-500",
    info:    "text-info-400",
  }
  return map[severity]
}

function severityLabel(severity: SimSeverity): string {
  const map: Record<SimSeverity, string> = {
    danger:  "위험",
    warning: "경고",
    info:    "정보",
  }
  return map[severity]
}
</script>

<style scoped>
/* ── TransitionGroup: 알림 항목 진입 애니메이션 ──────────────── */
.alert-item-enter-active {
  transition: all 0.35s ease-out;
}
.alert-item-leave-active {
  transition: all 0.25s ease-in;
  /* 퇴장 시 절대 위치로 흐름에서 제거해 다른 항목 이동을 자연스럽게 */
  position: absolute;
  width: 100%;
}
.alert-item-enter-from {
  opacity: 0;
  transform: translateX(24px);
}
.alert-item-leave-to {
  opacity: 0;
  transform: translateX(24px);
}
/* 다른 항목들이 자리를 메울 때의 이동 트랜지션 */
.alert-item-move {
  transition: transform 0.3s ease;
}

/* ── 뱃지 카운터 페이드 ─────────────────────────────────────── */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
