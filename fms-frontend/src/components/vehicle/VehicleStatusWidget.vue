<template>
  <BaseCard v-if="selectedBike" variant="raised" class="w-64">

    <!-- ── 헤더: 차량 번호 + 상태 뱃지 ──────────────────────── -->
    <template #header>
      <div class="flex items-baseline gap-1.5">
        <span class="text-xs font-mono font-bold text-primary-500">#{{ shortId }}</span>
        <span class="text-sm font-bold text-secondary-900 dark:text-white truncate">
          {{ selectedBike.plate_number }}
        </span>
      </div>
      <StatusBadge
        :status="bikeStatusToBadge(selectedBike.status)"
        :text="statusLabel(selectedBike.status)"
        :dot="true"
      />
    </template>

    <!-- ── 닫기 버튼 ─────────────────────────────────────────── -->
    <template #action>
      <button
        @click="fleetStore.selectBike(null)"
        class="text-secondary-400 hover:text-secondary-600 dark:hover:text-secondary-300 transition-colors"
        title="닫기"
      >
        <X class="w-3.5 h-3.5" />
      </button>
    </template>

    <!-- ── 본문: 데이터 항목 ─────────────────────────────────── -->
    <div class="space-y-3.5">

      <!-- 현재 위치 -->
      <div class="flex items-start gap-2.5">
        <MapPin class="w-4 h-4 text-primary-400 mt-0.5 flex-shrink-0" />
        <div class="min-w-0">
          <p class="text-[10px] uppercase tracking-wide text-secondary-400 dark:text-secondary-500">현재 위치</p>
          <p class="text-xs font-medium text-secondary-800 dark:text-secondary-200 tabular-nums">
            {{ selectedBike.lat.toFixed(2) }}°N, {{ selectedBike.lng.toFixed(2) }}°E
          </p>
        </div>
      </div>

      <!-- 현재 속도 -->
      <div class="flex items-center gap-2.5">
        <Gauge class="w-4 h-4 text-info-500 flex-shrink-0" />
        <div class="flex-1">
          <p class="text-[10px] uppercase tracking-wide text-secondary-400 dark:text-secondary-500">현재 속도</p>
          <p class="text-sm font-bold text-secondary-900 dark:text-white tabular-nums">
            {{ selectedBike.speed_kmh ?? 0 }}
            <span class="text-xs font-normal text-secondary-500 ml-0.5">km/h</span>
          </p>
        </div>
        <!-- 속도 시각화 바 (100 km/h 기준) -->
        <div class="w-12 h-1.5 bg-secondary-200 dark:bg-secondary-700 rounded-full overflow-hidden">
          <div
            class="h-full bg-info-400 rounded-full transition-all duration-500"
            :style="{ width: `${Math.min((selectedBike.speed_kmh ?? 0), 100)}%` }"
          />
        </div>
      </div>

      <!-- 배터리 -->
      <div class="flex items-start gap-2.5">
        <Battery :class="['w-4 h-4 flex-shrink-0 mt-0.5', batteryIconColor]" />
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between mb-1.5">
            <p class="text-[10px] uppercase tracking-wide text-secondary-400 dark:text-secondary-500">배터리</p>
            <StatusBadge :status="batteryBadgeStatus" :text="batteryLabel" />
          </div>
          <div class="flex items-center gap-2">
            <div class="flex-1 h-1.5 bg-secondary-200 dark:bg-secondary-700 rounded-full overflow-hidden">
              <div
                :class="['h-full rounded-full transition-all duration-700', batteryBarColor]"
                :style="{ width: `${selectedBike.battery_level}%` }"
              />
            </div>
            <span :class="['text-xs font-bold tabular-nums', batteryTextColor]">
              {{ selectedBike.battery_level.toFixed(1) }}%
            </span>
          </div>
        </div>
      </div>

      <!-- 엔진 온도 -->
      <div class="flex items-center gap-2.5">
        <Thermometer :class="['w-4 h-4 flex-shrink-0', tempIconColor]" />
        <div class="flex-1">
          <p class="text-[10px] uppercase tracking-wide text-secondary-400 dark:text-secondary-500">엔진 온도</p>
          <p class="text-sm font-bold text-secondary-900 dark:text-white tabular-nums">
            {{ engineTemp }}
            <span class="text-xs font-normal text-secondary-500 ml-0.5">°C</span>
          </p>
        </div>
        <span :class="['text-xs px-1.5 py-0.5 rounded font-medium', tempBadgeClass]">
          {{ tempLabel }}
        </span>
      </div>

      <!-- 구분선 + 운전자 -->
      <div class="pt-2 border-t border-slate-100 dark:border-secondary-700 flex items-center gap-2 text-xs">
        <span class="text-secondary-400">운전자</span>
        <span class="font-medium text-secondary-700 dark:text-secondary-300">
          {{ selectedBike.driver_name ?? '미배정' }}
        </span>
        <span class="ml-auto text-[10px] text-secondary-400 tabular-nums">
          {{ lastUpdated }}
        </span>
      </div>
    </div>

  </BaseCard>
</template>

<script setup lang="ts">
import { computed } from "vue"
import { MapPin, Gauge, Battery, Thermometer, X } from "lucide-vue-next"
import BaseCard from "@/components/common/BaseCard.vue"
import StatusBadge from "@/components/common/StatusBadge.vue"
import type { BadgeStatus } from "@/components/common/StatusBadge.vue"
import { useFleetStore } from "@/stores/useFleetStore"
import type { BikeStatus } from "@/stores/useFleetStore"

// ── 스토어 ──────────────────────────────────────────────────────
const fleetStore = useFleetStore()

const selectedBike = computed(() =>
  fleetStore.selectedBikeId
    ? fleetStore.bikes.find(b => b.id === fleetStore.selectedBikeId) ?? null
    : null
)

// ── 차량 ID 축약 (b001 → MK-0001) ───────────────────────────────
const shortId = computed(() =>
  selectedBike.value
    ? `MK-${selectedBike.value.id.replace(/\D/g, "").padStart(4, "0")}`
    : ""
)

// ── 마지막 업데이트 표시 ────────────────────────────────────────
const lastUpdated = computed(() => {
  if (!selectedBike.value) return ""
  const diff = Date.now() - new Date(selectedBike.value.last_updated).getTime()
  const secs = Math.floor(diff / 1000)
  if (secs < 60) return `${secs}초 전`
  return `${Math.floor(secs / 60)}분 전`
})

// ── 상태 관련 헬퍼 ──────────────────────────────────────────────
function bikeStatusToBadge(status: BikeStatus): BadgeStatus {
  const map: Record<BikeStatus, BadgeStatus> = {
    running: "success", idle: "default", charging: "info",
    alert: "danger", offline: "default",
  }
  return map[status]
}

function statusLabel(status: BikeStatus): string {
  const map: Record<BikeStatus, string> = {
    running: "운행 중", idle: "대기", charging: "충전 중",
    alert: "알림", offline: "오프라인",
  }
  return map[status]
}

// ── 배터리 관련 ─────────────────────────────────────────────────
const batteryIconColor = computed(() => {
  const pct = selectedBike.value?.battery_level ?? 100
  if (pct <= 15) return "text-danger-500"
  if (pct <= 30) return "text-warning-500"
  return "text-success-500"
})

const batteryTextColor = computed(() => {
  const pct = selectedBike.value?.battery_level ?? 100
  if (pct <= 15) return "text-danger-500"
  if (pct <= 30) return "text-warning-600 dark:text-warning-400"
  return "text-success-600 dark:text-success-400"
})

const batteryBarColor = computed(() => {
  const pct = selectedBike.value?.battery_level ?? 100
  if (pct <= 15) return "bg-danger-500"
  if (pct <= 30) return "bg-warning-500"
  return "bg-success-500"
})

const batteryBadgeStatus = computed((): BadgeStatus => {
  const pct = selectedBike.value?.battery_level ?? 100
  if (pct <= 15) return "danger"
  if (pct <= 30) return "warning"
  return "success"
})

const batteryLabel = computed(() => {
  const pct = selectedBike.value?.battery_level ?? 100
  if (pct <= 15) return "긴급"
  if (pct <= 30) return "부족"
  if (pct <= 60) return "보통"
  return "양호"
})

// ── 엔진 온도 (속도 기반 결정론적 추정) ─────────────────────────
// speed가 Store에서 reactive하게 변경될 때 computed가 자동 재계산된다.
const engineTemp = computed(() => {
  const speed = selectedBike.value?.speed_kmh ?? 0
  return Math.round(55 + (speed / 100) * 35)
})

const tempIconColor = computed(() => {
  const t = engineTemp.value
  if (t >= 85) return "text-danger-500"
  if (t >= 75) return "text-warning-500"
  return "text-info-400"
})

const tempBadgeClass = computed(() => {
  const t = engineTemp.value
  if (t >= 85) return "bg-danger-100 dark:bg-danger-900/30 text-danger-600 dark:text-danger-400"
  if (t >= 75) return "bg-warning-100 dark:bg-warning-900/30 text-warning-600 dark:text-warning-400"
  return "bg-info-100 dark:bg-info-900/30 text-info-600 dark:text-info-400"
})

const tempLabel = computed(() => {
  const t = engineTemp.value
  if (t >= 85) return "과열"
  if (t >= 75) return "주의"
  return "정상"
})
</script>
