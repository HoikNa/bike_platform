<template>
  <div class="p-6 space-y-5">

    <!-- ── 헤더 ──────────────────────────────────────────────── -->
    <div class="flex flex-col sm:flex-row sm:items-center gap-3">
      <div class="flex-1">
        <h1 class="text-lg font-semibold text-secondary-900 dark:text-white">알림 관리</h1>
        <p class="text-sm text-secondary-500 dark:text-secondary-400 mt-0.5">
          미확인 {{ alertStore.unacknowledgedCount }}건
        </p>
      </div>

      <!-- 전체 확인 버튼 -->
      <button
        v-if="alertStore.unacknowledgedCount > 0"
        @click="acknowledgeAll"
        :disabled="isBulkProcessing"
        class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
               bg-primary-500 hover:bg-primary-600 text-white
               disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
      >
        <svg v-if="isBulkProcessing" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        <svg v-else class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
        </svg>
        전체 확인
      </button>
    </div>

    <!-- ── 필터 탭 ─────────────────────────────────────────────── -->
    <div class="flex gap-2 flex-wrap">
      <!-- 확인 상태 -->
      <div class="flex rounded-lg border border-secondary-200 dark:border-secondary-700 overflow-hidden">
        <button
          v-for="opt in ackOptions"
          :key="String(opt.value)"
          @click="selectedAck = opt.value; reload()"
          :class="[
            'px-3 py-1.5 text-xs font-medium transition-colors',
            selectedAck === opt.value
              ? 'bg-primary-500 text-white'
              : 'text-secondary-600 dark:text-secondary-400 hover:bg-secondary-50 dark:hover:bg-secondary-700',
          ]"
        >
          {{ opt.label }}
        </button>
      </div>

      <!-- 심각도 -->
      <button
        v-for="sev in severityOptions"
        :key="sev.value"
        @click="toggleSeverity(sev.value); reload()"
        :class="[
          'px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
          selectedSeverities.includes(sev.value)
            ? sev.activeClass
            : 'border-secondary-300 dark:border-secondary-600 text-secondary-600 dark:text-secondary-400 hover:bg-secondary-50 dark:hover:bg-secondary-700',
        ]"
      >
        {{ sev.label }}
      </button>
    </div>

    <!-- ── 알림 목록 ──────────────────────────────────────────── -->
    <div class="bg-surface dark:bg-secondary-800 rounded-2xl border border-secondary-200 dark:border-secondary-700 overflow-hidden">

      <!-- 로딩 스켈레톤 -->
      <div v-if="showLoading" class="divide-y divide-secondary-100 dark:divide-secondary-700">
        <div v-for="i in 8" :key="i" class="flex items-start gap-4 px-5 py-4">
          <div class="w-2 h-2 rounded-full bg-secondary-200 dark:bg-secondary-700 animate-pulse mt-2 flex-shrink-0" />
          <div class="flex-1 space-y-2">
            <div class="h-3.5 bg-secondary-200 dark:bg-secondary-700 rounded animate-pulse w-2/3" />
            <div class="h-3 bg-secondary-100 dark:bg-secondary-600 rounded animate-pulse w-1/3" />
          </div>
          <div class="h-6 w-16 bg-secondary-100 dark:bg-secondary-700 rounded animate-pulse" />
        </div>
      </div>

      <!-- 빈 상태 -->
      <div
        v-else-if="!alertStore.isLoading && alertStore.alerts.length === 0"
        class="flex flex-col items-center justify-center py-20 text-secondary-400"
      >
        <svg class="w-12 h-12 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
        </svg>
        <p class="text-sm font-medium">알림이 없습니다.</p>
      </div>

      <!-- 목록 -->
      <ul v-else class="divide-y divide-secondary-100 dark:divide-secondary-700">
        <li
          v-for="alert in alertStore.alerts"
          :key="alert.id"
          :class="[
            'flex items-start gap-4 px-5 py-4 transition-colors',
            alert.is_acknowledged
              ? 'opacity-60'
              : 'hover:bg-secondary-50 dark:hover:bg-secondary-700/50',
          ]"
        >
          <!-- 심각도 도트 -->
          <span :class="['mt-2 w-2.5 h-2.5 rounded-full flex-shrink-0', severityDot(alert.severity)]" />

          <!-- 알림 내용 -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-sm font-semibold text-secondary-900 dark:text-white">{{ alert.title }}</span>
              <SeverityBadge :severity="alert.severity" />
            </div>
            <p v-if="alert.description" class="text-xs text-secondary-500 dark:text-secondary-400 mt-0.5 line-clamp-1">
              {{ alert.description }}
            </p>
            <div class="flex items-center gap-3 mt-1.5 flex-wrap">
              <RouterLink
                :to="`/app/vehicles/${alert.vehicle.id}`"
                class="text-xs text-primary-500 hover:text-primary-600 dark:text-primary-400 font-medium"
                @click.stop
              >
                {{ alert.vehicle.plate_number }}
              </RouterLink>
              <span class="text-xs text-secondary-400">{{ formatTime(alert.triggered_at) }}</span>
              <span
                v-if="alert.speed_at_trigger != null"
                class="text-xs text-secondary-400"
              >
                {{ alert.speed_at_trigger.toFixed(0) }} km/h
              </span>
              <span
                v-if="alert.battery_at_trigger != null"
                class="text-xs text-secondary-400"
              >
                배터리 {{ alert.battery_at_trigger.toFixed(0) }}%
              </span>
            </div>
          </div>

          <!-- 확인 버튼 / 확인자 -->
          <div class="flex-shrink-0 text-right">
            <template v-if="alert.is_acknowledged">
              <p class="text-xs text-secondary-400">확인됨</p>
              <p class="text-xs text-secondary-500">{{ alert.acknowledged_by?.full_name }}</p>
            </template>
            <button
              v-else
              @click="handleAcknowledge(alert.id)"
              :disabled="processingIds.has(alert.id)"
              class="px-3 py-1.5 rounded-lg text-xs font-medium border
                     border-primary-300 dark:border-primary-700
                     text-primary-600 dark:text-primary-400
                     hover:bg-primary-50 dark:hover:bg-primary-900/30
                     disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              확인
            </button>
          </div>
        </li>
      </ul>

      <!-- 더보기 트리거 (무한 스크롤) -->
      <div ref="sentinelRef" class="h-1" />

      <!-- 로딩 더보기 -->
      <div v-if="alertStore.isLoadingMore" class="flex items-center justify-center py-5">
        <svg class="w-5 h-5 text-primary-500 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
      </div>

      <!-- 모두 로드됨 -->
      <div
        v-else-if="!alertStore.hasNext && alertStore.alerts.length > 0"
        class="py-4 text-center text-xs text-secondary-400"
      >
        모든 알림을 불러왔습니다.
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, defineComponent, h } from "vue"
import { useAlertStore } from "@/stores/alert"
import { alertService } from "@/services/alertService"
import { useDelayedLoading } from "@/composables/useDelayedLoading"
import { useToast } from "@/composables/useToast"
import type { AlertSeverity } from "@/types/models"

const alertStore = useAlertStore()
const toast      = useToast()

// ── 필터 상태 ──────────────────────────────────────────────────
const selectedAck        = ref<boolean | undefined>(undefined)
const selectedSeverities = ref<string[]>([])
const isBulkProcessing   = ref(false)
const processingIds      = ref(new Set<string>())

const ackOptions = [
  { label: "전체",   value: undefined },
  { label: "미확인", value: false },
  { label: "확인됨", value: true },
]

const severityOptions = [
  {
    value: "DANGER",
    label: "위험",
    activeClass: "border-danger-500 bg-danger-50 dark:bg-danger-900/30 text-danger-700 dark:text-danger-400",
  },
  {
    value: "WARNING",
    label: "경고",
    activeClass: "border-warning-500 bg-warning-50 dark:bg-warning-900/30 text-warning-700 dark:text-warning-400",
  },
  {
    value: "INFO",
    label: "정보",
    activeClass: "border-info-500 bg-info-50 dark:bg-info-900/30 text-info-700 dark:text-info-400",
  },
]

function toggleSeverity(value: string) {
  const idx = selectedSeverities.value.indexOf(value)
  if (idx === -1) selectedSeverities.value.push(value)
  else selectedSeverities.value.splice(idx, 1)
}

function reload() {
  alertStore.fetchAlerts({
    is_acknowledged: selectedAck.value,
    severity:        selectedSeverities.value.length ? selectedSeverities.value : undefined,
  })
}

// ── 무한 스크롤 ────────────────────────────────────────────────
const { showLoading } = useDelayedLoading(() => alertStore.isLoading)

// sentinelRef: IntersectionObserver로 무한 스크롤 트리거
const sentinelRef = ref<HTMLElement | null>(null)
let _observer: IntersectionObserver | null = null

onMounted(() => {
  alertStore.fetchAlerts()
  if (sentinelRef.value) {
    _observer = new IntersectionObserver(entries => {
      if (entries[0]?.isIntersecting && alertStore.hasNext && !alertStore.isLoadingMore) {
        alertStore.loadMore()
      }
    }, { threshold: 0.1 })
    _observer.observe(sentinelRef.value)
  }
})

onUnmounted(() => _observer?.disconnect())

// ── 액션 ───────────────────────────────────────────────────────
async function handleAcknowledge(alertId: string) {
  if (processingIds.value.has(alertId)) return
  processingIds.value = new Set([...processingIds.value, alertId])
  try {
    await alertStore.acknowledge(alertId)
    toast.success("알림을 확인 처리했습니다.")
  } catch {
    toast.error("처리에 실패했습니다.")
  } finally {
    const next = new Set(processingIds.value)
    next.delete(alertId)
    processingIds.value = next
  }
}

async function acknowledgeAll() {
  const unackIds = alertStore.alerts
    .filter(a => !a.is_acknowledged)
    .map(a => a.id)
  if (unackIds.length === 0) return

  isBulkProcessing.value = true
  try {
    await alertService.acknowledgeBulk(unackIds)
    await alertStore.fetchAlerts({
      is_acknowledged: selectedAck.value,
      severity:        selectedSeverities.value.length ? selectedSeverities.value : undefined,
    })
    toast.success(`${unackIds.length}건을 확인 처리했습니다.`)
  } catch {
    toast.error("처리에 실패했습니다.")
  } finally {
    isBulkProcessing.value = false
  }
}

// ── 인라인 컴포넌트 ────────────────────────────────────────────
const SeverityBadge = defineComponent({
  props: { severity: String },
  setup(props) {
    const map: Record<string, string> = {
      DANGER:  "bg-danger-100 dark:bg-danger-900/30 text-danger-700 dark:text-danger-400",
      WARNING: "bg-warning-100 dark:bg-warning-900/30 text-warning-700 dark:text-warning-400",
      INFO:    "bg-info-100 dark:bg-info-900/30 text-info-700 dark:text-info-400",
    }
    const label: Record<string, string> = { DANGER: "위험", WARNING: "경고", INFO: "정보" }
    return () => h("span", {
      class: `text-xs font-medium px-1.5 py-0.5 rounded-md ${map[props.severity ?? "INFO"]}`,
    }, label[props.severity ?? "INFO"])
  },
})

// ── 헬퍼 ───────────────────────────────────────────────────────
function severityDot(severity: AlertSeverity): string {
  return { DANGER: "bg-danger-500", WARNING: "bg-warning-500", INFO: "bg-info-400" }[severity]
}

function formatTime(isoString: string): string {
  const d = new Date(isoString)
  const now = new Date()
  const diffMs  = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1)   return "방금 전"
  if (diffMin < 60)  return `${diffMin}분 전`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24)    return `${diffH}시간 전`
  return d.toLocaleDateString("ko-KR", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
}
</script>
