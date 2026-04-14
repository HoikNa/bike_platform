<template>
  <div class="flex flex-col h-full overflow-hidden">

    <!-- ── 상단 통계 카드 ──────────────────────────────────────── -->
    <div class="flex-shrink-0 grid grid-cols-4 gap-2 px-4 pt-2 pb-0">
      <StatCard label="전체 차량"  :value="fleetStore.vehicles.length" icon="total"   color="primary"   />
      <StatCard label="운행 중"    :value="fleetStore.runningCount"     icon="running" color="success"   />
      <StatCard label="미확인 알림" :value="alertStore.unacknowledgedCount" icon="alert" color="danger"  />
      <StatCard label="오프라인"   :value="fleetStore.offlineVehicles.length" icon="offline" color="secondary" />
    </div>

    <!-- ── 차량 목록 + 지도 ────────────────────────────────────── -->
    <div class="flex-1 flex gap-3 p-4 pt-2 min-h-0">

      <!-- 좌측 패널: 차량 목록 -->
      <div class="w-48 flex-shrink-0 flex flex-col min-h-0">

        <!-- 차량 상태 목록 -->
        <div class="bg-surface dark:bg-secondary-800 rounded-2xl border border-secondary-200 dark:border-secondary-700 flex-1 flex flex-col min-h-0">
          <div class="flex items-center justify-between px-4 py-2.5 border-b border-secondary-100 dark:border-secondary-700 flex-shrink-0">
            <h2 class="text-xs font-semibold text-secondary-900 dark:text-white">차량 현황</h2>
            <RouterLink to="/app/vehicles" class="text-xs text-primary-500 hover:text-primary-600 font-medium">
              전체 →
            </RouterLink>
          </div>

          <div v-if="fleetStore.isListLoading" class="p-3 space-y-2">
            <div v-for="i in 4" :key="i" class="h-10 bg-secondary-100 dark:bg-secondary-700 rounded-lg animate-pulse" />
          </div>

          <div v-else-if="fleetStore.vehicles.length === 0"
               class="flex flex-col items-center justify-center py-10 text-secondary-400">
            <p class="text-xs">등록된 차량이 없습니다.</p>
          </div>

          <ul v-else class="divide-y divide-secondary-100 dark:divide-secondary-700 overflow-y-auto flex-1">
            <li
              v-for="vehicle in fleetStore.vehicles"
              :key="vehicle.id"
              :class="[
                'flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors',
                fleetStore.selectedVehicleId === vehicle.id
                  ? 'bg-primary-50 dark:bg-primary-900/20'
                  : 'hover:bg-secondary-50 dark:hover:bg-secondary-700/50',
              ]"
              @click="fleetStore.selectVehicle(fleetStore.selectedVehicleId === vehicle.id ? null : vehicle.id)"
            >
              <span :class="['w-2 h-2 rounded-full flex-shrink-0', statusDot(vehicle.status)]" />
              <div class="flex-1 min-w-0">
                <p class="text-xs font-semibold text-secondary-900 dark:text-white truncate">{{ vehicle.plate_number }}</p>
                <p class="text-xs text-secondary-500 dark:text-secondary-400 truncate">
                  {{ vehicle.assigned_driver?.user_full_name ?? '미배정' }}
                </p>
              </div>
              <div class="text-right flex-shrink-0">
                <p class="text-xs font-medium" :class="batteryColor(vehicle.latest_sensor?.battery_level_pct ?? null)">
                  {{ vehicle.latest_sensor?.battery_level_pct != null
                    ? `${vehicle.latest_sensor.battery_level_pct.toFixed(0)}%`
                    : '—' }}
                </p>
              </div>
              <span
                v-if="vehicle.unacknowledged_alerts_count > 0"
                class="w-4 h-4 rounded-full bg-danger-500 text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0"
              >
                {{ vehicle.unacknowledged_alerts_count > 9 ? '9+' : vehicle.unacknowledged_alerts_count }}
              </span>
            </li>
          </ul>
        </div>

      </div>

      <!-- 지도 (우측, 나머지 너비) -->
      <div class="flex-1 min-w-0 flex flex-col gap-2">

        <!-- 필터 버튼 -->
        <div class="flex gap-2 flex-shrink-0">
          <button
            v-for="f in filterOptions"
            :key="f.value"
            @click="mapFilter = f.value"
            :class="[
              'flex-1 text-xs font-medium px-2 py-1.5 rounded-lg border transition-colors',
              mapFilter === f.value
                ? 'bg-primary-500 text-white border-primary-500'
                : 'bg-surface dark:bg-secondary-800 text-secondary-600 dark:text-secondary-400 border-secondary-200 dark:border-secondary-700 hover:bg-secondary-50 dark:hover:bg-secondary-700',
            ]"
          >
            {{ f.label }}
          </button>
        </div>

        <!-- 지도 -->
        <div class="flex-1 min-h-0 rounded-2xl overflow-hidden border border-secondary-200 dark:border-secondary-700 shadow-sm bg-secondary-100 dark:bg-secondary-800">
          <RealtimeMap v-if="!fleetStore.isListLoading" :filter="mapFilter" />
          <div v-else class="w-full h-full flex items-center justify-center text-secondary-400">
            <div class="text-center">
              <div class="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <p class="text-sm">지도 불러오는 중...</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, defineComponent, h } from "vue"
import { useFleetStore } from "@/stores/fleet"
import { useAlertStore } from "@/stores/alert"
import RealtimeMap from "@/components/map/RealtimeMap.vue"
import type { MapFilter } from "@/components/map/RealtimeMap.vue"
import type { VehicleStatus } from "@/types/models"

const fleetStore = useFleetStore()
const alertStore = useAlertStore()

const mapFilter = ref<MapFilter>("all")

const filterOptions: { value: MapFilter; label: string }[] = [
  { value: "all",          label: "전체" },
  { value: "running",      label: "운행중" },
  { value: "low-battery",  label: "충전 필요" },
  { value: "not-running",  label: "미운행" },
]

onMounted(async () => {
  await fleetStore.fetchVehicles({ page_size: 50 })
  alertStore.fetchAlerts()
  fleetStore.startDemoSimulation()
})

onUnmounted(() => {
  fleetStore.stopDemoSimulation()
})

// ── 인라인 StatCard 컴포넌트 ──────────────────────────────────
const StatCard = defineComponent({
  props: { label: String, value: Number, icon: String, color: String },
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
      class: "bg-surface dark:bg-secondary-800 rounded-lg border border-secondary-200 dark:border-secondary-700 px-3 py-1.5 flex items-center gap-2.5",
    }, [
      h("div", { class: `w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0 ${bgMap[props.color ?? "primary"]}` }, [
        h("svg", { class: "w-3.5 h-3.5", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
          h("path", { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: iconPath[props.icon ?? "total"] }),
        ]),
      ]),
      h("div", { class: "min-w-0" }, [
        h("p", { class: "text-[10px] text-secondary-500 dark:text-secondary-400 leading-none mb-0.5 truncate" }, props.label),
        h("p", { class: "text-base font-bold text-secondary-900 dark:text-white leading-none" }, props.value ?? 0),
      ]),
    ])
  },
})

// ── 헬퍼 ───────────────────────────────────────────────────────
function statusDot(status: VehicleStatus): string {
  const m: Record<VehicleStatus, string> = {
    RUNNING: "bg-success-500", IDLE: "bg-secondary-400",
    CHARGING: "bg-info-500",   ALERT: "bg-danger-500", OFFLINE: "bg-secondary-300",
  }
  return m[status] ?? "bg-secondary-300"
}

function batteryColor(pct: number | null): string {
  if (pct === null) return "text-secondary-400"
  if (pct <= 15)    return "text-danger-500"
  if (pct <= 30)    return "text-warning-500"
  return "text-success-600 dark:text-success-400"
}

</script>
