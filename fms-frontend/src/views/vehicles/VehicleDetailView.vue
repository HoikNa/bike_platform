<template>
  <div class="p-6 space-y-6">

    <!-- ── 뒤로가기 + 헤더 ────────────────────────────────────── -->
    <div class="flex items-center gap-3">
      <button
        @click="$router.back()"
        class="flex items-center justify-center w-8 h-8 rounded-lg text-secondary-500
               hover:bg-secondary-100 dark:hover:bg-secondary-700 transition-colors"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
      </button>
      <div>
        <h1 class="text-lg font-semibold text-secondary-900 dark:text-white">
          {{ vehicle?.plate_number ?? '차량 상세' }}
        </h1>
        <p class="text-sm text-secondary-500 dark:text-secondary-400">
          {{ vehicle?.manufacturer }} {{ vehicle?.model }}
        </p>
      </div>
    </div>

    <!-- ── 로딩 스켈레톤 ──────────────────────────────────────── -->
    <div v-if="showLoading" class="grid grid-cols-1 xl:grid-cols-3 gap-6">
      <div class="xl:col-span-2 space-y-4">
        <div class="h-40 bg-secondary-100 dark:bg-secondary-800 rounded-2xl animate-pulse" />
        <div class="h-48 bg-secondary-100 dark:bg-secondary-800 rounded-2xl animate-pulse" />
      </div>
      <div class="h-80 bg-secondary-100 dark:bg-secondary-800 rounded-2xl animate-pulse" />
    </div>

    <!-- ── 메인 콘텐츠 ────────────────────────────────────────── -->
    <template v-else-if="vehicle">
      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">

        <!-- 좌측: 차량 정보 + 센서 -->
        <div class="xl:col-span-2 space-y-6">

          <!-- 차량 기본 정보 카드 -->
          <div class="bg-surface dark:bg-secondary-800 rounded-2xl border border-secondary-200 dark:border-secondary-700 p-5">
            <div class="flex items-start justify-between mb-4">
              <div class="flex items-center gap-3">
                <div :class="['w-10 h-10 rounded-xl flex items-center justify-center', statusBg(vehicle.status)]">
                  <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                  </svg>
                </div>
                <div>
                  <p class="text-base font-bold text-secondary-900 dark:text-white">{{ vehicle.plate_number }}</p>
                  <p class="text-xs text-secondary-500">VIN: {{ vehicle.vin ?? '미등록' }}</p>
                </div>
              </div>
              <StatusBadge :status="vehicle.status" size="lg" />
            </div>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
              <InfoItem label="제조사" :value="vehicle.manufacturer" />
              <InfoItem label="모델" :value="vehicle.model" />
              <InfoItem label="연식" :value="`${vehicle.manufacture_year}년`" />
              <InfoItem label="배터리 용량" :value="`${vehicle.battery_capacity_kwh} kWh`" />
            </div>
          </div>

          <!-- 실시간 센서 데이터 -->
          <div class="bg-surface dark:bg-secondary-800 rounded-2xl border border-secondary-200 dark:border-secondary-700 p-5">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-sm font-semibold text-secondary-900 dark:text-white">실시간 센서</h2>
              <div class="flex items-center gap-1.5">
                <span :class="['w-2 h-2 rounded-full', liveData ? 'bg-success-500 animate-pulse' : 'bg-secondary-400']" />
                <span class="text-xs text-secondary-500">{{ liveData ? '실시간' : '마지막 기록' }}</span>
              </div>
            </div>

            <div v-if="sensor" class="grid grid-cols-2 md:grid-cols-3 gap-4">
              <SensorCard
                label="속도"
                :value="sensor.speed_kmh != null ? `${sensor.speed_kmh.toFixed(1)}` : '—'"
                unit="km/h"
                icon="speed"
              />
              <SensorCard
                label="배터리"
                :value="sensor.battery_level_pct != null ? `${sensor.battery_level_pct.toFixed(0)}` : '—'"
                unit="%"
                icon="battery"
                :color="batteryColor(sensor.battery_level_pct)"
              />
              <SensorCard
                label="전압"
                :value="sensor.battery_voltage_v != null ? `${sensor.battery_voltage_v.toFixed(1)}` : '—'"
                unit="V"
                icon="voltage"
              />
              <SensorCard
                label="배터리 온도"
                :value="sensor.battery_temp_celsius != null ? `${sensor.battery_temp_celsius.toFixed(1)}` : '—'"
                unit="°C"
                icon="temp"
              />
              <SensorCard
                label="RPM"
                :value="sensor.engine_rpm != null ? `${sensor.engine_rpm.toLocaleString()}` : '—'"
                unit="rpm"
                icon="rpm"
              />
              <SensorCard
                label="주행 거리"
                :value="sensor.odometer_km != null ? `${sensor.odometer_km.toLocaleString()}` : '—'"
                unit="km"
                icon="odometer"
              />
            </div>
            <div v-else class="text-center py-8 text-secondary-400">
              <p class="text-sm">센서 데이터가 없습니다.</p>
            </div>

            <!-- 마지막 업데이트 시각 -->
            <p v-if="sensor?.time" class="mt-4 text-xs text-secondary-400 text-right">
              마지막 업데이트: {{ formatDateTime(sensor.time) }}
            </p>
          </div>

          <!-- 운행 이력 미니 테이블 -->
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
            <div v-if="vehicleAlerts.length === 0" class="py-10 text-center text-sm text-secondary-400">
              알림이 없습니다.
            </div>
            <ul v-else class="divide-y divide-secondary-100 dark:divide-secondary-700">
              <li
                v-for="alert in vehicleAlerts.slice(0, 5)"
                :key="alert.id"
                class="flex items-start gap-3 px-5 py-3"
              >
                <span :class="['mt-1.5 w-2 h-2 rounded-full flex-shrink-0', severityDot(alert.severity)]" />
                <div class="flex-1 min-w-0">
                  <p class="text-xs font-medium text-secondary-900 dark:text-white truncate">{{ alert.title }}</p>
                  <p class="text-xs text-secondary-500">{{ formatDateTime(alert.triggered_at) }}</p>
                </div>
                <span
                  v-if="!alert.is_acknowledged"
                  class="flex-shrink-0 text-xs px-1.5 py-0.5 rounded-md bg-danger-100 dark:bg-danger-900/30 text-danger-700 dark:text-danger-400"
                >
                  미확인
                </span>
              </li>
            </ul>
          </div>
        </div>

        <!-- 우측: 운전자 정보 + 운행 정보 -->
        <div class="space-y-6">

          <!-- 운전자 정보 -->
          <div class="bg-surface dark:bg-secondary-800 rounded-2xl border border-secondary-200 dark:border-secondary-700 p-5">
            <h2 class="text-sm font-semibold text-secondary-900 dark:text-white mb-4">배정 운전자</h2>
            <template v-if="vehicle.assigned_driver">
              <div class="flex items-center gap-3 mb-4">
                <div class="w-10 h-10 rounded-full bg-primary-500 flex items-center justify-center text-white font-bold text-sm flex-shrink-0">
                  {{ vehicle.assigned_driver.user_full_name.charAt(0) }}
                </div>
                <div>
                  <p class="text-sm font-semibold text-secondary-900 dark:text-white">
                    {{ vehicle.assigned_driver.user_full_name }}
                  </p>
                </div>
              </div>
              <div class="space-y-2.5">
                <DriverItem label="면허번호" :value="vehicle.assigned_driver.license_number" />
                <DriverItem label="면허 만료" :value="formatDate(vehicle.assigned_driver.license_expiry)" />
                <DriverItem label="연락처" :value="vehicle.assigned_driver.phone" />
                <DriverItem
                  label="비상 연락처"
                  :value="vehicle.assigned_driver.emergency_contact ?? '미등록'"
                />
              </div>
            </template>
            <div v-else class="text-center py-8 text-secondary-400">
              <svg class="w-8 h-8 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
              </svg>
              <p class="text-sm">미배정</p>
            </div>
          </div>

          <!-- 현재 운행 -->
          <div class="bg-surface dark:bg-secondary-800 rounded-2xl border border-secondary-200 dark:border-secondary-700 p-5">
            <h2 class="text-sm font-semibold text-secondary-900 dark:text-white mb-4">현재 운행</h2>
            <template v-if="vehicle.active_trip">
              <div class="space-y-2.5">
                <DriverItem label="출발지" :value="vehicle.active_trip.start_address ?? '위치 확인 중'" />
                <DriverItem label="출발 시각" :value="formatDateTime(vehicle.active_trip.started_at)" />
              </div>
            </template>
            <div v-else class="text-center py-6 text-secondary-400">
              <p class="text-sm">운행 중이 아닙니다.</p>
            </div>
          </div>

        </div>
      </div>
    </template>

    <!-- 에러 -->
    <div v-else class="flex flex-col items-center justify-center py-24 text-secondary-400">
      <svg class="w-12 h-12 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
      </svg>
      <p class="text-sm font-medium">차량을 찾을 수 없습니다.</p>
      <button @click="$router.back()" class="mt-3 text-xs text-primary-500 hover:text-primary-600">
        목록으로 돌아가기
      </button>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, defineComponent, h } from "vue"
import { useRoute } from "vue-router"
import { useFleetStore } from "@/stores/fleet"
import { useAlertStore } from "@/stores/alert"
import { useRealtimeStore } from "@/stores/realtime"
import { useDelayedLoading } from "@/composables/useDelayedLoading"
import type { VehicleStatus, AlertSeverity } from "@/types/models"

const route         = useRoute()
const fleetStore    = useFleetStore()
const alertStore    = useAlertStore()
const realtimeStore = useRealtimeStore()

const vehicleId = route.params.vehicleId as string

const vehicle = computed(() => fleetStore.selectedVehicle)

// 실시간 위치 우선 사용, 없으면 vehicle.latest_sensor 사용
const liveData = computed(() => fleetStore.realtimeLocations.get(vehicleId))
const sensor   = computed(() =>
  liveData.value
    ? {
        time:                 liveData.value.time,
        latitude:             liveData.value.latitude,
        longitude:            liveData.value.longitude,
        speed_kmh:            liveData.value.speed_kmh,
        battery_level_pct:    liveData.value.battery_level_pct,
        battery_voltage_v:    liveData.value.battery_voltage_v,
        battery_temp_celsius: liveData.value.battery_temp_celsius,
        engine_rpm:           liveData.value.engine_rpm,
        odometer_km:          liveData.value.odometer_km,
      }
    : vehicle.value?.latest_sensor ?? null
)

const vehicleAlerts = computed(() =>
  alertStore.alerts.filter(a => a.vehicle.id === vehicleId)
)

const { showLoading } = useDelayedLoading(() => fleetStore.isDetailLoading)

onMounted(async () => {
  await fleetStore.fetchVehicleDetail(vehicleId)
  await alertStore.fetchAlerts({ vehicle_id: vehicleId })
  realtimeStore.subscribe([vehicleId])
})

onUnmounted(() => {
  realtimeStore.unsubscribe([vehicleId])
  fleetStore.clearSelectedVehicle()
})

// ── 인라인 서브 컴포넌트 ──────────────────────────────────────
const StatusBadge = defineComponent({
  props: { status: String, size: { type: String, default: "sm" } },
  setup(props) {
    const colorMap: Record<string, string> = {
      RUNNING: "bg-success-100 dark:bg-success-900/30 text-success-700 dark:text-success-400",
      IDLE:    "bg-secondary-100 dark:bg-secondary-700 text-secondary-600 dark:text-secondary-300",
      CHARGING:"bg-info-100 dark:bg-info-900/30 text-info-700 dark:text-info-400",
      ALERT:   "bg-danger-100 dark:bg-danger-900/30 text-danger-700 dark:text-danger-400",
      OFFLINE: "bg-secondary-200 dark:bg-secondary-600 text-secondary-500",
    }
    const labelMap: Record<string, string> = {
      RUNNING: "운행 중", IDLE: "대기", CHARGING: "충전 중", ALERT: "알림", OFFLINE: "오프라인",
    }
    return () => h("span", {
      class: `font-medium rounded-lg px-2 py-1 ${props.size === "lg" ? "text-sm" : "text-xs"} ${colorMap[props.status ?? "OFFLINE"]}`,
    }, labelMap[props.status ?? "OFFLINE"])
  },
})

const InfoItem = defineComponent({
  props: { label: String, value: String },
  setup(props) {
    return () => h("div", {}, [
      h("p", { class: "text-xs text-secondary-500 dark:text-secondary-400" }, props.label),
      h("p", { class: "text-sm font-medium text-secondary-900 dark:text-white mt-0.5" }, props.value ?? "—"),
    ])
  },
})

const DriverItem = defineComponent({
  props: { label: String, value: String },
  setup(props) {
    return () => h("div", { class: "flex items-center justify-between" }, [
      h("span", { class: "text-xs text-secondary-500 dark:text-secondary-400" }, props.label),
      h("span", { class: "text-xs font-medium text-secondary-800 dark:text-secondary-200 text-right" }, props.value ?? "—"),
    ])
  },
})

const iconPaths: Record<string, string> = {
  speed:    "M13 10V3L4 14h7v7l9-11h-7z",
  battery:  "M13 10h7l-9 13v-9H4l9-13v9z",
  voltage:  "M13 10h7l-9 13v-9H4l9-13v9z",
  temp:     "M12 9v3m0 0v3m0-3h3m-3 0H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z",
  rpm:      "M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15",
  odometer: "M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7",
}

const SensorCard = defineComponent({
  props: { label: String, value: String, unit: String, icon: String, color: String },
  setup(props) {
    return () => h("div", {
      class: "bg-secondary-50 dark:bg-secondary-700/50 rounded-xl p-4",
    }, [
      h("div", { class: "flex items-center gap-2 mb-2" }, [
        h("svg", { class: "w-4 h-4 text-secondary-400", fill: "none", viewBox: "0 0 24 24", stroke: "currentColor" }, [
          h("path", { "stroke-linecap": "round", "stroke-linejoin": "round", "stroke-width": "2", d: iconPaths[props.icon ?? "speed"] }),
        ]),
        h("span", { class: "text-xs text-secondary-500 dark:text-secondary-400" }, props.label),
      ]),
      h("div", { class: "flex items-baseline gap-1" }, [
        h("span", {
          class: `text-xl font-bold ${props.color ?? "text-secondary-900 dark:text-white"}`,
        }, props.value),
        h("span", { class: "text-xs text-secondary-400" }, props.unit),
      ]),
    ])
  },
})

// ── 헬퍼 ───────────────────────────────────────────────────────
function statusBg(status: VehicleStatus): string {
  const map: Record<VehicleStatus, string> = {
    RUNNING: "bg-success-500", IDLE: "bg-secondary-400",
    CHARGING: "bg-info-500",   ALERT: "bg-danger-500", OFFLINE: "bg-secondary-300",
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
  return { DANGER: "bg-danger-500", WARNING: "bg-warning-500", INFO: "bg-info-500" }[severity]
}

function formatDateTime(isoString: string): string {
  return new Date(isoString).toLocaleString("ko-KR", {
    month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
  })
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("ko-KR", {
    year: "numeric", month: "long", day: "numeric",
  })
}
</script>
