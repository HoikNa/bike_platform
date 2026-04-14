<template>
  <div class="p-6 space-y-5">

    <!-- ── 헤더 ──────────────────────────────────────────────── -->
    <div>
      <h1 class="text-lg font-semibold text-secondary-900 dark:text-white">운행 기록</h1>
      <p v-if="meta" class="text-sm text-secondary-500 dark:text-secondary-400 mt-0.5">
        총 {{ meta.total.toLocaleString() }}건
      </p>
    </div>

    <!-- ── 필터 바 ────────────────────────────────────────────── -->
    <div class="flex gap-3 flex-wrap">
      <div class="relative max-w-xs w-full sm:w-auto">
        <span class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <svg class="w-4 h-4 text-secondary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
          </svg>
        </span>
        <input
          v-model="vehicleFilter"
          type="text"
          placeholder="번호판으로 필터"
          class="w-full pl-9 pr-4 py-2 rounded-lg border border-secondary-300 dark:border-secondary-600
                 bg-surface dark:bg-secondary-800 text-sm text-secondary-900 dark:text-white
                 placeholder:text-secondary-400
                 focus:outline-none focus:ring-2 focus:ring-primary-200 dark:focus:ring-primary-800 focus:border-primary-500"
        />
      </div>
    </div>

    <!-- ── 테이블 ──────────────────────────────────────────────── -->
    <div class="bg-surface dark:bg-secondary-800 rounded-2xl border border-secondary-200 dark:border-secondary-700 overflow-hidden">

      <!-- 테이블 헤더 (lg 이상) -->
      <div class="hidden lg:grid grid-cols-[1.5fr_1fr_1fr_1fr_1fr_1fr_0.5fr] gap-4 px-5 py-3
                  bg-secondary-50 dark:bg-secondary-700/50 text-xs font-semibold text-secondary-500 dark:text-secondary-400
                  border-b border-secondary-100 dark:border-secondary-700">
        <span>차량 / 운전자</span>
        <span>출발</span>
        <span>도착</span>
        <span>거리</span>
        <span>평균속도</span>
        <span>배터리</span>
        <span>알림</span>
      </div>

      <!-- 로딩 스켈레톤 -->
      <div v-if="showLoading" class="divide-y divide-secondary-100 dark:divide-secondary-700">
        <div v-for="i in 8" :key="i" class="flex items-center gap-4 px-5 py-4">
          <div class="flex-1 space-y-2">
            <div class="h-3.5 bg-secondary-200 dark:bg-secondary-700 rounded animate-pulse w-1/3" />
            <div class="h-3 bg-secondary-100 dark:bg-secondary-600 rounded animate-pulse w-2/5" />
          </div>
          <div class="h-3 bg-secondary-200 dark:bg-secondary-700 rounded animate-pulse w-24" />
          <div class="h-3 bg-secondary-200 dark:bg-secondary-700 rounded animate-pulse w-16" />
          <div class="h-3 bg-secondary-200 dark:bg-secondary-700 rounded animate-pulse w-12" />
        </div>
      </div>

      <!-- 빈 상태 -->
      <div
        v-else-if="trips.length === 0"
        class="flex flex-col items-center justify-center py-20 text-secondary-400"
      >
        <svg class="w-12 h-12 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
        </svg>
        <p class="text-sm font-medium">운행 기록이 없습니다.</p>
      </div>

      <!-- 목록 -->
      <ul v-else class="divide-y divide-secondary-100 dark:divide-secondary-700">
        <li
          v-for="trip in filteredTrips"
          :key="trip.id"
          class="px-5 py-4 hover:bg-secondary-50 dark:hover:bg-secondary-700/50 transition-colors"
        >
          <!-- 모바일: 세로 스택 / 데스크탑: 그리드 -->
          <div class="lg:grid lg:grid-cols-[1.5fr_1fr_1fr_1fr_1fr_1fr_0.5fr] lg:gap-4 lg:items-center space-y-2 lg:space-y-0">

            <!-- 차량 / 운전자 -->
            <div>
              <RouterLink
                :to="`/app/vehicles/${trip.vehicle.id}`"
                class="text-sm font-semibold text-primary-600 dark:text-primary-400 hover:underline"
              >
                {{ trip.vehicle.plate_number }}
              </RouterLink>
              <p class="text-xs text-secondary-500 dark:text-secondary-400 mt-0.5">
                {{ trip.driver?.user_full_name ?? '미배정' }}
              </p>
            </div>

            <!-- 출발 -->
            <div>
              <p class="text-xs text-secondary-500 dark:text-secondary-400 lg:hidden mb-0.5">출발</p>
              <p class="text-sm text-secondary-800 dark:text-secondary-200">{{ formatDateTime(trip.started_at) }}</p>
              <p class="text-xs text-secondary-400 truncate max-w-[180px]">{{ trip.start_address ?? '—' }}</p>
            </div>

            <!-- 도착 -->
            <div>
              <p class="text-xs text-secondary-500 dark:text-secondary-400 lg:hidden mb-0.5">도착</p>
              <template v-if="trip.ended_at">
                <p class="text-sm text-secondary-800 dark:text-secondary-200">{{ formatDateTime(trip.ended_at) }}</p>
                <p class="text-xs text-secondary-400 truncate max-w-[180px]">{{ trip.end_address ?? '—' }}</p>
              </template>
              <template v-else>
                <span class="inline-flex items-center gap-1 text-xs font-medium text-success-600 dark:text-success-400">
                  <span class="w-1.5 h-1.5 rounded-full bg-success-500 animate-pulse" />
                  운행 중
                </span>
              </template>
            </div>

            <!-- 거리 -->
            <div>
              <p class="text-xs text-secondary-500 dark:text-secondary-400 lg:hidden">거리</p>
              <p class="text-sm font-medium text-secondary-900 dark:text-white">
                {{ trip.distance_km != null ? `${trip.distance_km.toFixed(1)} km` : '—' }}
              </p>
            </div>

            <!-- 평균속도 -->
            <div>
              <p class="text-xs text-secondary-500 dark:text-secondary-400 lg:hidden">평균속도</p>
              <p class="text-sm text-secondary-700 dark:text-secondary-300">
                {{ trip.avg_speed_kmh != null ? `${trip.avg_speed_kmh.toFixed(0)} km/h` : '—' }}
              </p>
              <p v-if="trip.max_speed_kmh != null" class="text-xs text-secondary-400">
                최고 {{ trip.max_speed_kmh.toFixed(0) }} km/h
              </p>
            </div>

            <!-- 배터리 변화 -->
            <div>
              <p class="text-xs text-secondary-500 dark:text-secondary-400 lg:hidden">배터리</p>
              <template v-if="trip.battery_start_pct != null">
                <div class="flex items-center gap-1.5">
                  <span :class="['text-sm font-medium', batteryColor(trip.battery_start_pct)]">
                    {{ trip.battery_start_pct.toFixed(0) }}%
                  </span>
                  <svg class="w-3 h-3 text-secondary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"/>
                  </svg>
                  <span v-if="trip.battery_end_pct != null" :class="['text-sm font-medium', batteryColor(trip.battery_end_pct)]">
                    {{ trip.battery_end_pct.toFixed(0) }}%
                  </span>
                  <span v-else class="text-sm text-secondary-400">—</span>
                </div>
              </template>
              <span v-else class="text-sm text-secondary-400">—</span>
            </div>

            <!-- 알림 수 -->
            <div>
              <span
                v-if="trip.alert_count > 0"
                class="inline-flex items-center justify-center w-6 h-6 rounded-full
                       bg-danger-100 dark:bg-danger-900/30 text-danger-700 dark:text-danger-400
                       text-xs font-bold"
              >
                {{ trip.alert_count > 9 ? '9+' : trip.alert_count }}
              </span>
              <span v-else class="text-xs text-secondary-400">—</span>
            </div>

          </div>
        </li>
      </ul>

      <!-- 페이지네이션 -->
      <div
        v-if="meta && meta.total_pages > 1"
        class="flex items-center justify-between px-5 py-3 border-t border-secondary-100 dark:border-secondary-700"
      >
        <p class="text-xs text-secondary-500 dark:text-secondary-400">
          {{ meta.page }} / {{ meta.total_pages }} 페이지 · 총 {{ meta.total.toLocaleString() }}건
        </p>
        <div class="flex gap-2">
          <button
            :disabled="meta.page <= 1"
            @click="goPage(meta.page - 1)"
            class="px-3 py-1.5 text-xs rounded-lg border border-secondary-300 dark:border-secondary-600
                   text-secondary-700 dark:text-secondary-300
                   disabled:opacity-40 disabled:cursor-not-allowed
                   hover:bg-secondary-50 dark:hover:bg-secondary-700 transition-colors"
          >
            이전
          </button>
          <button
            :disabled="meta.page >= meta.total_pages"
            @click="goPage(meta.page + 1)"
            class="px-3 py-1.5 text-xs rounded-lg border border-secondary-300 dark:border-secondary-600
                   text-secondary-700 dark:text-secondary-300
                   disabled:opacity-40 disabled:cursor-not-allowed
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
import { ref, computed, onMounted } from "vue"
import { tripService } from "@/services/tripService"
import { useDelayedLoading } from "@/composables/useDelayedLoading"
import type { Trip } from "@/types/models"
import type { PageMeta } from "@/types/api"

const trips      = ref<Trip[]>([])
const meta       = ref<PageMeta | null>(null)
const isLoading  = ref(false)
const vehicleFilter = ref("")

const { showLoading } = useDelayedLoading(() => isLoading.value)

const filteredTrips = computed(() => {
  const q = vehicleFilter.value.trim().toLowerCase()
  if (!q) return trips.value
  return trips.value.filter(t => t.vehicle.plate_number.toLowerCase().includes(q))
})

async function loadTrips(page = 1) {
  isLoading.value = true
  try {
    const res  = await tripService.list({ page, page_size: 20 })
    trips.value = res.data
    meta.value  = res.meta
  } finally {
    isLoading.value = false
  }
}

function goPage(page: number) {
  loadTrips(page)
}

onMounted(() => loadTrips(1))

// ── 헬퍼 ───────────────────────────────────────────────────────
function batteryColor(pct: number): string {
  if (pct <= 15) return "text-danger-500"
  if (pct <= 30) return "text-warning-500"
  return "text-success-600 dark:text-success-400"
}

function formatDateTime(isoString: string): string {
  return new Date(isoString).toLocaleString("ko-KR", {
    month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
  })
}
</script>
