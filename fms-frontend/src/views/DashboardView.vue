<template>
  <div class="flex flex-col h-screen bg-background dark:bg-secondary-900 overflow-hidden">

    <!-- ══════════════════════════════════════════════════════════
         GNB (Global Navigation Bar) — 상단 고정 헤더
    ══════════════════════════════════════════════════════════ -->
    <header class="flex-shrink-0 flex items-center justify-between h-14 px-5
                   bg-surface dark:bg-secondary-800 border-b border-slate-200 dark:border-secondary-700
                   z-sticky shadow-sm">

      <!-- 로고 영역 -->
      <div class="flex items-center gap-2.5">
        <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-500">
          <svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M13 10V3L4 14h7v7l9-11h-7z"/>
          </svg>
        </div>
        <span class="font-bold text-secondary-900 dark:text-white text-base">BikeFMS</span>
        <!-- 환경 배지 -->
        <StatusBadge status="info" text="LIVE" :dot="true" />
      </div>

      <!-- 중앙: 요약 지표 (데스크탑) -->
      <div class="hidden md:flex items-center gap-6">
        <StatChip
          label="운행 중"
          :value="fleetStore.runningCount"
          color="success"
        />
        <StatChip
          label="알림"
          :value="fleetStore.alertCount"
          color="danger"
        />
        <StatChip
          label="충전 중"
          :value="fleetStore.chargingCount"
          color="info"
        />
        <StatChip
          label="오프라인"
          :value="fleetStore.offlineCount"
          color="default"
        />
      </div>

      <!-- 우측: 사용자 영역 -->
      <div class="flex items-center gap-3">
        <!-- 실시간 연결 상태 -->
        <div class="hidden sm:flex items-center gap-1.5 text-xs text-secondary-500 dark:text-secondary-400">
          <span class="w-2 h-2 rounded-full bg-success-500 animate-pulse" />
          실시간 연결
        </div>

        <!-- 알림 벨 -->
        <button class="relative flex items-center justify-center w-8 h-8 rounded-lg
                       text-secondary-500 hover:bg-secondary-100 dark:hover:bg-secondary-700 transition-colors">
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"/>
          </svg>
          <span
            v-if="fleetStore.alertCount > 0"
            class="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-danger-500 text-white text-[10px] font-bold flex items-center justify-center"
          >
            {{ fleetStore.alertCount > 9 ? '9+' : fleetStore.alertCount }}
          </span>
        </button>

        <!-- 사용자 아바타 -->
        <button class="flex items-center gap-2 px-2 py-1 rounded-lg
                       hover:bg-secondary-100 dark:hover:bg-secondary-700 transition-colors">
          <div class="w-7 h-7 rounded-full bg-primary-500 flex items-center justify-center text-white text-xs font-bold">
            A
          </div>
          <span class="hidden md:block text-sm font-medium text-secondary-700 dark:text-secondary-300">
            관리자
          </span>
        </button>
      </div>
    </header>

    <!-- ══════════════════════════════════════════════════════════
         메인 바디: LNB + 지도 캔버스
    ══════════════════════════════════════════════════════════ -->
    <div class="flex flex-1 min-h-0">

      <!-- ── LNB (Left Navigation Bar) — 좌측 고정 사이드바 ── -->
      <aside
        :class="[
          'flex-shrink-0 flex flex-col bg-surface dark:bg-secondary-800',
          'border-r border-slate-200 dark:border-secondary-700',
          'transition-all duration-300 overflow-hidden',
          isSidebarOpen ? 'w-72' : 'w-0 md:w-14',
        ]"
      >
        <!-- 검색 + 필터 헤더 -->
        <div class="flex items-center justify-between px-3 py-3 border-b border-slate-100 dark:border-secondary-700">
          <template v-if="isSidebarOpen">
            <span class="text-xs font-semibold text-secondary-500 dark:text-secondary-400 uppercase tracking-wide">
              차량 목록 ({{ fleetStore.bikes.length }})
            </span>
            <!-- 현 위치 모드 배지 -->
            <span class="flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded-full
                         bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400
                         border border-primary-200 dark:border-primary-700">
              <span class="w-1.5 h-1.5 rounded-full bg-success-500 animate-pulse" />
              현 위치
            </span>
          </template>
          <button
            @click="isSidebarOpen = !isSidebarOpen"
            class="flex items-center justify-center w-8 h-8 rounded-lg
                   text-secondary-500 hover:bg-secondary-100 dark:hover:bg-secondary-700 transition-colors ml-auto"
          >
            <svg :class="['w-4 h-4 transition-transform', isSidebarOpen ? '' : 'rotate-180']"
                 fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7"/>
            </svg>
          </button>
        </div>

        <!-- 검색 입력 (펼쳐진 상태) -->
        <div v-if="isSidebarOpen" class="px-3 py-2 border-b border-slate-100 dark:border-secondary-700">
          <div class="relative">
            <svg class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-secondary-400"
                 fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"/>
            </svg>
            <input
              v-model="searchQuery"
              type="search"
              placeholder="번호판 검색"
              class="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg
                     border border-slate-200 dark:border-secondary-600
                     bg-background dark:bg-secondary-900
                     text-secondary-900 dark:text-white placeholder:text-secondary-400
                     focus:outline-none focus:ring-1 focus:ring-primary-300 focus:border-primary-400"
            />
          </div>
        </div>

        <!-- 차량 목록 -->
        <div class="flex-1 overflow-y-auto">
          <ul class="py-1">
            <li
              v-for="bike in filteredBikes"
              :key="bike.id"
              @click="fleetStore.selectBike(bike.id)"
              :class="[
                'flex items-center gap-3 cursor-pointer transition-colors',
                isSidebarOpen ? 'px-3 py-2.5' : 'px-2 py-3 justify-center',
                fleetStore.selectedBikeId === bike.id
                  ? 'bg-primary-50 dark:bg-primary-900/30'
                  : 'hover:bg-secondary-50 dark:hover:bg-secondary-700/50',
              ]"
            >
              <!-- 상태 도트 -->
              <span :class="['w-2.5 h-2.5 rounded-full flex-shrink-0', statusDotColor(bike.status)]" />

              <!-- 차량 정보 (펼쳐진 상태) -->
              <template v-if="isSidebarOpen">
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-semibold text-secondary-900 dark:text-white truncate">
                    {{ bike.plate_number }}
                  </p>
                  <p class="text-xs text-secondary-500 dark:text-secondary-400">
                    {{ bike.driver_name ?? '미배정' }}
                  </p>
                </div>
                <!-- 배터리 -->
                <div class="flex-shrink-0 text-right">
                  <p :class="['text-xs font-bold', batteryTextColor(bike.battery_level)]">
                    {{ bike.battery_level.toFixed(1) }}%
                  </p>
                </div>
              </template>
            </li>
          </ul>
        </div>

        <!-- LNB 하단 요약 -->
        <div
          v-if="isSidebarOpen"
          class="px-4 py-3 border-t border-slate-100 dark:border-secondary-700 bg-secondary-50 dark:bg-secondary-700/50"
        >
          <div class="grid grid-cols-2 gap-2">
            <BaseCard variant="flat" :no-padding="true" class="!border-0">
              <div class="text-center py-1">
                <p class="text-lg font-bold text-secondary-900 dark:text-white">{{ fleetStore.bikes.length }}</p>
                <p class="text-xs text-secondary-500">전체</p>
              </div>
            </BaseCard>
            <BaseCard variant="flat" :no-padding="true" class="!border-0">
              <div class="text-center py-1">
                <p class="text-lg font-bold text-success-600 dark:text-success-400">{{ fleetStore.runningCount }}</p>
                <p class="text-xs text-secondary-500">운행 중</p>
              </div>
            </BaseCard>
          </div>
        </div>
      </aside>

      <!-- ── 메인 캔버스 영역 ──────────────────────────────────── -->
      <main class="relative flex-1 min-w-0 overflow-hidden">

        <!-- ① 지도: 전체 배경을 RealtimeMap이 채움 -->
        <RealtimeMap class="absolute inset-0" :filter="mapFilter" />

        <!-- ② 좌상단 오버레이: 필터 메뉴 + 차량 상세 위젯 -->
        <div class="absolute top-4 left-4 z-raised flex flex-col gap-2">

          <!-- 차량 필터 메뉴 -->
          <div class="bg-white/92 dark:bg-secondary-800/92 backdrop-blur-sm rounded-xl shadow-md
                      border border-slate-200/80 dark:border-secondary-700 overflow-hidden min-w-[152px]">
            <div class="px-3 pt-2.5 pb-1.5">
              <p class="text-[10px] font-bold text-secondary-400 dark:text-secondary-500 uppercase tracking-widest">
                차량 필터
              </p>
            </div>
            <div class="pb-1.5">
              <button
                v-for="opt in filterOptions"
                :key="opt.value"
                @click="mapFilter = opt.value"
                :class="[
                  'w-full flex items-center gap-2.5 px-3 py-2 text-left transition-colors',
                  mapFilter === opt.value
                    ? 'bg-primary-50 dark:bg-primary-900/30'
                    : 'hover:bg-secondary-50 dark:hover:bg-secondary-700/50',
                ]"
              >
                <span :class="['w-2 h-2 rounded-full flex-shrink-0', opt.dotClass]" />
                <span :class="[
                  'flex-1 text-xs font-medium',
                  mapFilter === opt.value
                    ? 'text-primary-700 dark:text-primary-300'
                    : 'text-secondary-700 dark:text-secondary-300',
                ]">{{ opt.label }}</span>
                <span :class="[
                  'text-[11px] font-bold px-1.5 py-0.5 rounded-full min-w-[1.25rem] text-center tabular-nums',
                  mapFilter === opt.value
                    ? 'bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300'
                    : 'bg-secondary-100 dark:bg-secondary-700 text-secondary-500 dark:text-secondary-400',
                ]">{{ opt.count }}</span>
              </button>
            </div>
          </div>

          <!-- 차량 상세 위젯 (차량 선택 시) -->
          <Transition name="slide-down">
            <VehicleStatusWidget v-if="fleetStore.selectedBikeId" />
          </Transition>
        </div>

        <!-- ④ 알림 패널: 우측 하단 -->
        <div class="absolute bottom-5 right-5 z-raised">
          <EventAlertPanel />
        </div>

      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, defineComponent, h, onMounted } from "vue"
import BaseCard from "@/components/common/BaseCard.vue"
import StatusBadge from "@/components/common/StatusBadge.vue"
import RealtimeMap from "@/components/map/RealtimeMap.vue"
import VehicleStatusWidget from "@/components/vehicle/VehicleStatusWidget.vue"
import EventAlertPanel from "@/components/alert/EventAlertPanel.vue"
import { useFleetStore } from "@/stores/useFleetStore"
import { useSimulation } from "@/composables/useSimulation"
import type { BikeStatus } from "@/stores/useFleetStore"
import type { MapFilter } from "@/components/map/RealtimeMap.vue"

const fleetStore = useFleetStore()

// ── 시뮬레이션: 마운트되면 자동 시작, 언마운트 시 자동 정지 ──────
const { start: startSimulation } = useSimulation()
onMounted(startSimulation)

// ── GNB 상태 ──────────────────────────────────────────────────
const isSidebarOpen = ref(true)
const searchQuery   = ref("")

// ── 지도 차량 필터 ──────────────────────────────────────────────
const LOW_BATTERY_THRESHOLD = 30

const mapFilter = ref<MapFilter>("all")

const filterOptions = computed(() => [
  {
    value: "all"         as MapFilter,
    label: "전체 차량",
    count: fleetStore.bikes.length,
    dotClass: "bg-secondary-400",
  },
  {
    value: "running"     as MapFilter,
    label: "운행중 차량",
    count: fleetStore.runningCount,
    dotClass: "bg-success-500",
  },
  {
    value: "low-battery" as MapFilter,
    label: "충전 필요",
    count: fleetStore.bikes.filter(
      b => b.battery_level <= LOW_BATTERY_THRESHOLD && b.status !== "offline"
    ).length,
    dotClass: "bg-warning-500",
  },
])

// ── 사이드바 차량 검색 필터 ──────────────────────────────────────
const filteredBikes = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return fleetStore.bikes
  return fleetStore.bikes.filter(b => b.plate_number.toLowerCase().includes(q))
})

// ── LNB 헬퍼 ──────────────────────────────────────────────────
function statusDotColor(status: BikeStatus): string {
  const map: Record<BikeStatus, string> = {
    running:  "bg-success-500",
    idle:     "bg-secondary-400",
    charging: "bg-info-500",
    alert:    "bg-danger-500",
    offline:  "bg-secondary-300",
  }
  return map[status]
}

function batteryTextColor(pct: number): string {
  if (pct <= 15) return "text-danger-500"
  if (pct <= 30) return "text-warning-600 dark:text-warning-400"
  return "text-success-600 dark:text-success-400"
}

// ── 인라인 StatChip 컴포넌트 ───────────────────────────────────
const StatChip = defineComponent({
  props: {
    label: String,
    value: Number,
    color: { type: String, default: "default" },
  },
  setup(props) {
    const textColorMap: Record<string, string> = {
      success: "text-success-600 dark:text-success-400",
      danger:  "text-danger-500",
      info:    "text-info-600 dark:text-info-400",
      default: "text-secondary-500 dark:text-secondary-400",
    }
    return () =>
      h("div", { class: "flex items-center gap-1.5" }, [
        h("span", { class: `text-base font-bold tabular-nums ${textColorMap[props.color ?? "default"]}` }, props.value ?? 0),
        h("span", { class: "text-xs text-secondary-500 dark:text-secondary-400" }, props.label),
      ])
  },
})
</script>

<style scoped>
.slide-up-enter-active { transition: all 0.25s ease-out; }
.slide-up-leave-active { transition: all 0.2s ease-in; }
.slide-up-enter-from   { opacity: 0; transform: translateY(-12px); }
.slide-up-leave-to     { opacity: 0; transform: translateY(-8px); }

.slide-down-enter-active { transition: all 0.2s ease-out; }
.slide-down-leave-active { transition: all 0.15s ease-in; }
.slide-down-enter-from   { opacity: 0; transform: translateY(-8px); }
.slide-down-leave-to     { opacity: 0; transform: translateY(-8px); }
</style>
