<template>
  <div class="p-6 space-y-6">

    <!-- ── 상단 통계 카드 ──────────────────────────────────────── -->
    <div class="grid grid-cols-2 xl:grid-cols-4 gap-4">
      <StatCard
        label="전체 차량"
        :value="fleetStore.vehicles.length"
        icon="total"
        color="primary"
      />
      <StatCard
        label="운행 중"
        :value="fleetStore.runningCount"
        icon="running"
        color="success"
      />
      <StatCard
        label="미확인 알림"
        :value="alertStore.unacknowledgedCount"
        icon="alert"
        color="danger"
      />
      <StatCard
        label="오프라인"
        :value="fleetStore.offlineVehicles.length"
        icon="offline"
        color="secondary"
      />
    </div>

    <!-- ── 본문 2열 레이아웃 ────────────────────────────────────── -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">

      <!-- 차량 상태 목록 (2/3 너비) -->
      <div class="xl:col-span-2 bg-surface dark:bg-secondary-800 rounded-2xl border border-secondary-200 dark:border-secondary-700">
        <div class="flex items-center justify-between px-5 py-4 border-b border-secondary-100 dark:border-secondary-700">
          <h2 class="text-sm font-semibold text-secondary-900 dark:text-white">차량 현황</h2>
          <RouterLink
            to="/app/vehicles"
            class="text-xs text-primary-500 hover:text-primary-600 dark:text-primary-400 font-medium"
          >
            전체 보기 →
          </RouterLink>
        </div>

        <!-- 로딩 -->
        <div v-if="fleetStore.isListLoading" class="p-5 space-y-3">
          <div v-for="i in 5" :key="i" class="h-14 bg-secondary-100 dark:bg-secondary-700 rounded-lg animate-pulse" />
        </div>

        <!-- 빈 상태 -->
        <div
          v-else-if="fleetStore.vehicles.length === 0"
          class="flex flex-col items-center justify-center py-16 text-secondary-400"
        >
          <svg class="w-10 h-10 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <p class="text-sm">등록된 차량이 없습니다.</p>
        </div>

        <!-- 차량 목록 -->
        <ul v-else class="divide-y divide-secondary-100 dark:divide-secondary-700">
          <li
            v-for="vehicle in recentVehicles"
            :key="vehicle.id"
            class="flex items-center gap-4 px-5 py-3.5 hover:bg-secondary-50 dark:hover:bg-secondary-700/50 transition-colors cursor-pointer"
            @click="$router.push(`/app/vehicles/${vehicle.id}`)"
          >
            <!-- 상태 아이콘 -->
            <div :class="['w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0', statusBg(vehicle.status)]">
              <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
              </svg>
            </div>

            <!-- 차량 정보 -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <span class="text-sm font-semibold text-secondary-900 dark:text-white">{{ vehicle.plate_number }}</span>
                <StatusBadge :status="vehicle.status" />
              </div>
              <p class="text-xs text-secondary-500 dark:text-secondary-400 truncate">
                {{ vehicle.model }} · {{ vehicle.assigned_driver?.user_full_name ?? '미배정' }}
              </p>
            </div>

            <!-- 배터리 -->
            <div class="text-right flex-shrink-0">
              <p class="text-sm font-medium" :class="batteryColor(vehicle.latest_sensor?.battery_level_pct ?? null)">
                {{ vehicle.latest_sensor?.battery_level_pct != null
                  ? `${vehicle.latest_sensor.battery_level_pct.toFixed(0)}%`
                  : '—' }}
              </p>
              <p class="text-xs text-secondary-400">배터리</p>
            </div>

            <!-- 알림 배지 -->
            <span
              v-if="vehicle.unacknowledged_alerts_count > 0"
              class="flex-shrink-0 w-5 h-5 rounded-full bg-danger-500 text-white text-xs font-bold flex items-center justify-center"
            >
              {{ vehicle.unacknowledged_alerts_count > 9 ? '9+' : vehicle.unacknowledged_alerts_count }}
            </span>
          </li>
        </ul>
      </div>

      <!-- 최근 알림 (1/3 너비) -->
      <div class="bg-surface dark:bg-secondary-800 rounded-2xl border border-secondary-200 dark:border-secondary-700">
        <div class="flex items-center justify-between px-5 py-4 border-b border-secondary-100 dark:border-secondary-700">
          <h2 class="text-sm font-semibold text-secondary-900 dark:text-white">최근 알림</h2>
          <RouterLink
            to="/app/alerts"
            class="text-xs text-primary-500 hover:text-primary-600 dark:text-primary-400 font-medium"
          >
            전체 보기 →
          </RouterLink>
        </div>

        <!-- 로딩 -->
        <div v-if="alertStore.isLoading" class="p-5 space-y-3">
          <div v-for="i in 5" :key="i" class="h-16 bg-secondary-100 dark:bg-secondary-700 rounded-lg animate-pulse" />
        </div>

        <!-- 빈 상태 -->
        <div
          v-else-if="alertStore.alerts.length === 0"
          class="flex flex-col items-center justify-center py-16 text-secondary-400"
        >
          <svg class="w-10 h-10 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
          </svg>
          <p class="text-sm">새 알림이 없습니다.</p>
        </div>

        <!-- 알림 목록 -->
        <ul v-else class="divide-y divide-secondary-100 dark:divide-secondary-700 max-h-[400px] overflow-y-auto">
          <li
            v-for="alert in recentAlerts"
            :key="alert.id"
            class="px-5 py-3 hover:bg-secondary-50 dark:hover:bg-secondary-700/50 transition-colors cursor-pointer"
            @click="$router.push('/app/alerts')"
          >
            <div class="flex items-start gap-3">
              <span :class="['mt-0.5 w-2 h-2 rounded-full flex-shrink-0', severityDot(alert.severity)]" />
              <div class="flex-1 min-w-0">
                <p class="text-xs font-medium text-secondary-900 dark:text-white truncate">{{ alert.title }}</p>
                <p class="text-xs text-secondary-500 dark:text-secondary-400">
                  {{ alert.vehicle.plate_number }} · {{ formatTime(alert.triggered_at) }}
                </p>
              </div>
              <span
                v-if="!alert.is_acknowledged"
                class="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-primary-500 mt-1.5"
              />
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue"
import { useFleetStore } from "@/stores/fleet"
import { useAlertStore } from "@/stores/alert"
import type { VehicleStatus, AlertSeverity } from "@/types/models"

// ── sub-components (인라인 정의) ──────────────────────────────
import { defineComponent, h } from "vue"

const StatCard = defineComponent({
  props: {
    label: String,
    value: Number,
    icon:  String,
    color: String,
  },
  setup(props) {
    const bgMap: Record<string, string> = {
      primary:   "bg-primary-50 dark:bg-primary-900/30 text-primary-500",
      success:   "bg-success-50 dark:bg-success-900/30 text-success-600",
      danger:    "bg-danger-50 dark:bg-danger-900/30 text-danger-500",
      secondary: "bg-secondary-100 dark:bg-secondary-700 text-secondary-500",
    }
    const iconPath: Record<string, string> = {
      total:    "M13 10V3L4 14h7v7l9-11h-7z",
      running:  "M5 3l14 9-14 9V3z",
      alert:    "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z",
      offline:  "M18.364 5.636a9 9 0 010 12.728M15.536 8.464a5 5 0 010 7.072M6.343 17.657a9 9 0 010-12.728M9.172 15.536a5 5 0 010-7.072",
    }
    return () => h("div", {
      class: "bg-surface dark:bg-secondary-800 rounded-2xl border border-secondary-200 dark:border-secondary-700 p-5",
    }, [
      h("div", { class: "flex items-center justify-between mb-3" }, [
        h("span", { class: "text-sm text-secondary-500 dark:text-secondary-400" }, props.label),
        h("div", { class: `w-9 h-9 rounded-lg flex items-center justify-center ${bgMap[props.color ?? "primary"]}` }, [
          h("svg", { class: "w-5 h-5", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
            h("path", { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: iconPath[props.icon ?? "total"] }),
          ]),
        ]),
      ]),
      h("p", { class: "text-3xl font-bold text-secondary-900 dark:text-white" }, props.value ?? 0),
    ])
  },
})

const StatusBadge = defineComponent({
  props: { status: String },
  setup(props) {
    const map: Record<string, string> = {
      RUNNING:  "bg-success-100 dark:bg-success-900/30 text-success-700 dark:text-success-400",
      IDLE:     "bg-secondary-100 dark:bg-secondary-700 text-secondary-600 dark:text-secondary-300",
      CHARGING: "bg-info-100 dark:bg-info-900/30 text-info-700 dark:text-info-400",
      ALERT:    "bg-danger-100 dark:bg-danger-900/30 text-danger-700 dark:text-danger-400",
      OFFLINE:  "bg-secondary-200 dark:bg-secondary-600 text-secondary-500 dark:text-secondary-400",
    }
    const label: Record<string, string> = {
      RUNNING: "운행", IDLE: "대기", CHARGING: "충전", ALERT: "알림", OFFLINE: "오프라인",
    }
    return () => h("span", {
      class: `text-xs font-medium px-1.5 py-0.5 rounded-md ${map[props.status ?? "OFFLINE"]}`,
    }, label[props.status ?? "OFFLINE"] ?? props.status)
  },
})

// ── 스토어 ─────────────────────────────────────────────────────
const fleetStore = useFleetStore()
const alertStore = useAlertStore()

const recentVehicles = computed(() => fleetStore.vehicles.slice(0, 8))
const recentAlerts   = computed(() => alertStore.alerts.slice(0, 10))

onMounted(() => {
  fleetStore.fetchVehicles({ page_size: 8 })
})

// ── 헬퍼 ───────────────────────────────────────────────────────
function statusBg(status: VehicleStatus): string {
  const map: Record<VehicleStatus, string> = {
    RUNNING:  "bg-success-500",
    IDLE:     "bg-secondary-400",
    CHARGING: "bg-info-500",
    ALERT:    "bg-danger-500",
    OFFLINE:  "bg-secondary-300",
  }
  return map[status] ?? "bg-secondary-400"
}

function batteryColor(pct: number | null): string {
  if (pct === null) return "text-secondary-400"
  if (pct <= 15)    return "text-danger-500"
  if (pct <= 30)    return "text-warning-500"
  return "text-success-600 dark:text-success-400"
}

function severityDot(severity: AlertSeverity): string {
  const map: Record<AlertSeverity, string> = {
    DANGER:  "bg-danger-500",
    WARNING: "bg-warning-500",
    INFO:    "bg-info-500",
  }
  return map[severity]
}

function formatTime(isoString: string): string {
  const d = new Date(isoString)
  const now = new Date()
  const diffMs = now.getTime() - d.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 1)   return "방금 전"
  if (diffMin < 60)  return `${diffMin}분 전`
  const diffH = Math.floor(diffMin / 60)
  if (diffH < 24)    return `${diffH}시간 전`
  return d.toLocaleDateString("ko-KR", { month: "short", day: "numeric" })
}
</script>
