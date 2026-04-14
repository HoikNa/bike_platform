<template>
  <div class="p-6 space-y-5">

    <!-- ── 헤더 ──────────────────────────────────────────────── -->
    <div class="flex flex-col sm:flex-row sm:items-center gap-3">
      <div class="flex-1">
        <h1 class="text-lg font-semibold text-secondary-900 dark:text-white">차량 관리</h1>
        <p class="text-sm text-secondary-500 dark:text-secondary-400 mt-0.5">
          총 {{ fleetStore.pageMeta?.total ?? fleetStore.vehicles.length }}대 등록됨
        </p>
      </div>
    </div>

    <!-- ── 필터 바 ────────────────────────────────────────────── -->
    <div class="flex flex-col sm:flex-row gap-3">
      <!-- 검색 -->
      <div class="relative flex-1 max-w-xs">
        <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg class="w-4 h-4 text-secondary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
          </svg>
        </span>
        <input
          v-model="searchQuery"
          type="search"
          placeholder="번호판, 모델명 검색"
          class="w-full pl-9 pr-4 py-2 rounded-lg border border-secondary-300 dark:border-secondary-600
                 bg-surface dark:bg-secondary-800 text-sm text-secondary-900 dark:text-white
                 placeholder:text-secondary-400
                 focus:outline-none focus:ring-2 focus:ring-primary-200 dark:focus:ring-primary-800 focus:border-primary-500"
          @input="onSearchInput"
        />
      </div>

      <!-- 상태 필터 -->
      <div class="flex gap-2 flex-wrap">
        <button
          v-for="opt in statusOptions"
          :key="opt.value"
          @click="toggleStatus(opt.value)"
          :class="[
            'px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors',
            selectedStatuses.includes(opt.value)
              ? opt.activeClass
              : 'border-secondary-300 dark:border-secondary-600 text-secondary-600 dark:text-secondary-400 hover:bg-secondary-50 dark:hover:bg-secondary-700',
          ]"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>

    <!-- ── 테이블 ──────────────────────────────────────────────── -->
    <div class="bg-surface dark:bg-secondary-800 rounded-2xl border border-secondary-200 dark:border-secondary-700 overflow-hidden">

      <!-- 로딩 스켈레톤 -->
      <div v-if="showLoading" class="divide-y divide-secondary-100 dark:divide-secondary-700">
        <div v-for="i in 8" :key="i" class="flex items-center gap-4 px-5 py-4">
          <div class="w-9 h-9 rounded-lg bg-secondary-200 dark:bg-secondary-700 animate-pulse flex-shrink-0" />
          <div class="flex-1 space-y-2">
            <div class="h-3.5 bg-secondary-200 dark:bg-secondary-700 rounded animate-pulse w-1/3" />
            <div class="h-3 bg-secondary-100 dark:bg-secondary-600 rounded animate-pulse w-1/2" />
          </div>
          <div class="h-3.5 bg-secondary-200 dark:bg-secondary-700 rounded animate-pulse w-16" />
          <div class="h-3.5 bg-secondary-200 dark:bg-secondary-700 rounded animate-pulse w-12" />
        </div>
      </div>

      <!-- 빈 상태 -->
      <div
        v-else-if="!fleetStore.isListLoading && fleetStore.vehicles.length === 0"
        class="flex flex-col items-center justify-center py-20 text-secondary-400"
      >
        <svg class="w-12 h-12 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z"/>
        </svg>
        <p class="text-sm font-medium">검색 결과가 없습니다.</p>
        <p class="text-xs mt-1">필터를 변경해 보세요.</p>
      </div>

      <!-- 목록 -->
      <ul v-else class="divide-y divide-secondary-100 dark:divide-secondary-700">
        <li
          v-for="vehicle in fleetStore.vehicles"
          :key="vehicle.id"
          class="flex items-center gap-4 px-5 py-4 hover:bg-secondary-50 dark:hover:bg-secondary-700/50 transition-colors cursor-pointer"
          @click="$router.push(`/app/vehicles/${vehicle.id}`)"
        >
          <!-- 상태 아이콘 -->
          <div :class="['w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0', statusBg(vehicle.status)]">
            <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
          </div>

          <!-- 번호판 + 모델 -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="text-sm font-bold text-secondary-900 dark:text-white">{{ vehicle.plate_number }}</span>
              <StatusBadge :status="vehicle.status" />
              <span
                v-if="vehicle.unacknowledged_alerts_count > 0"
                class="text-xs font-bold px-1.5 py-0.5 rounded-full bg-danger-500 text-white"
              >
                알림 {{ vehicle.unacknowledged_alerts_count }}
              </span>
            </div>
            <p class="text-xs text-secondary-500 dark:text-secondary-400 mt-0.5 truncate">
              {{ vehicle.manufacturer }} {{ vehicle.model }} ({{ vehicle.manufacture_year }})
            </p>
          </div>

          <!-- 운전자 -->
          <div class="hidden md:block text-right flex-shrink-0 w-28">
            <p class="text-sm text-secondary-700 dark:text-secondary-300 truncate">
              {{ vehicle.assigned_driver?.user_full_name ?? '미배정' }}
            </p>
            <p class="text-xs text-secondary-400">운전자</p>
          </div>

          <!-- 속도 -->
          <div class="hidden lg:block text-right flex-shrink-0 w-20">
            <p class="text-sm font-medium text-secondary-900 dark:text-white">
              {{ vehicle.latest_sensor?.speed_kmh != null
                ? `${vehicle.latest_sensor.speed_kmh.toFixed(0)} km/h`
                : '—' }}
            </p>
            <p class="text-xs text-secondary-400">속도</p>
          </div>

          <!-- 배터리 -->
          <div class="text-right flex-shrink-0 w-20">
            <p
              class="text-sm font-medium"
              :class="batteryColor(vehicle.latest_sensor?.battery_level_pct ?? null)"
            >
              {{ vehicle.latest_sensor?.battery_level_pct != null
                ? `${vehicle.latest_sensor.battery_level_pct.toFixed(0)}%`
                : '—' }}
            </p>
            <!-- 배터리 바 -->
            <div class="mt-1 h-1 w-16 bg-secondary-200 dark:bg-secondary-700 rounded-full overflow-hidden">
              <div
                :class="['h-full rounded-full transition-all', batteryBarColor(vehicle.latest_sensor?.battery_level_pct ?? null)]"
                :style="{ width: `${vehicle.latest_sensor?.battery_level_pct ?? 0}%` }"
              />
            </div>
          </div>

          <!-- 화살표 -->
          <svg class="w-4 h-4 text-secondary-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
          </svg>
        </li>
      </ul>

      <!-- 페이지네이션 -->
      <div
        v-if="fleetStore.pageMeta && fleetStore.pageMeta.total_pages > 1"
        class="flex items-center justify-between px-5 py-3 border-t border-secondary-100 dark:border-secondary-700"
      >
        <p class="text-xs text-secondary-500 dark:text-secondary-400">
          {{ fleetStore.pageMeta.page }} / {{ fleetStore.pageMeta.total_pages }} 페이지
        </p>
        <div class="flex gap-2">
          <button
            :disabled="fleetStore.pageMeta.page <= 1"
            @click="goPage(fleetStore.pageMeta.page - 1)"
            class="px-3 py-1.5 text-xs rounded-lg border border-secondary-300 dark:border-secondary-600
                   text-secondary-700 dark:text-secondary-300 disabled:opacity-40 disabled:cursor-not-allowed
                   hover:bg-secondary-50 dark:hover:bg-secondary-700 transition-colors"
          >
            이전
          </button>
          <button
            :disabled="fleetStore.pageMeta.page >= fleetStore.pageMeta.total_pages"
            @click="goPage(fleetStore.pageMeta.page + 1)"
            class="px-3 py-1.5 text-xs rounded-lg border border-secondary-300 dark:border-secondary-600
                   text-secondary-700 dark:text-secondary-300 disabled:opacity-40 disabled:cursor-not-allowed
                   hover:bg-secondary-50 dark:hover:bg-secondary-700 transition-colors"
          >
            다음
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, defineComponent, h } from "vue"
import { useFleetStore } from "@/stores/fleet"
import { useDelayedLoading } from "@/composables/useDelayedLoading"
import type { VehicleStatus } from "@/types/models"

const fleetStore = useFleetStore()

// ── 상태 필터 ──────────────────────────────────────────────────
const statusOptions = [
  { value: "RUNNING",  label: "운행", activeClass: "border-success-500 bg-success-50 dark:bg-success-900/30 text-success-700 dark:text-success-400" },
  { value: "IDLE",     label: "대기", activeClass: "border-secondary-500 bg-secondary-100 dark:bg-secondary-700 text-secondary-700 dark:text-secondary-300" },
  { value: "CHARGING", label: "충전", activeClass: "border-info-500 bg-info-50 dark:bg-info-900/30 text-info-700 dark:text-info-400" },
  { value: "ALERT",    label: "알림", activeClass: "border-danger-500 bg-danger-50 dark:bg-danger-900/30 text-danger-700 dark:text-danger-400" },
  { value: "OFFLINE",  label: "오프라인", activeClass: "border-secondary-400 bg-secondary-100 dark:bg-secondary-700 text-secondary-600 dark:text-secondary-300" },
]

const selectedStatuses = ref<string[]>([])
const searchQuery      = ref("")
let   searchTimer: ReturnType<typeof setTimeout> | null = null

const { showLoading } = useDelayedLoading(() => fleetStore.isListLoading)

function toggleStatus(value: string) {
  const idx = selectedStatuses.value.indexOf(value)
  if (idx === -1) selectedStatuses.value.push(value)
  else selectedStatuses.value.splice(idx, 1)
  fetchWithFilter(1)
}

function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => fetchWithFilter(1), 400)
}

function fetchWithFilter(page = 1) {
  fleetStore.fetchVehicles({
    status:    selectedStatuses.value.length ? selectedStatuses.value : undefined,
    q:         searchQuery.value || undefined,
    page,
    page_size: 15,
  })
}

function goPage(page: number) {
  fetchWithFilter(page)
}

onMounted(() => fetchWithFilter(1))

// ── 인라인 컴포넌트 ────────────────────────────────────────────
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

function batteryBarColor(pct: number | null): string {
  if (pct === null || pct <= 15) return "bg-danger-500"
  if (pct <= 30)                 return "bg-warning-500"
  return "bg-success-500"
}
</script>
