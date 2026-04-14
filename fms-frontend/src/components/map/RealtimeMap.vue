<template>
  <div class="relative w-full h-full overflow-hidden select-none">

    <!-- ══ Leaflet 지도 컨테이너 ════════════════════════════════ -->
    <div ref="mapEl" class="absolute inset-0" style="z-index: 0;" />

    <!-- ══ 오버레이 레이어 (지도 준비 후 표시) ════════════════════ -->
    <template v-if="mapReady">

      <!-- ── 운행 경로 SVG (차량 선택 시) ─────────────────────── -->
      <Transition name="fade">
        <svg
          v-if="fleetStore.selectedBikeId"
          class="absolute inset-0 w-full h-full pointer-events-none"
          style="z-index: 500;"
        >
          <!-- 비선택 running 차량 경로 (흐리게) -->
          <polyline
            v-for="bike in unselectedRunningBikes"
            :key="'route-other-' + bike.id"
            :points="polylinePixelPoints(bike.id)"
            fill="none"
            stroke="#94a3b8"
            stroke-width="1.5"
            stroke-opacity="0.35"
            stroke-linecap="round"
            stroke-linejoin="round"
          />

          <!-- 선택 차량 경로: 글로우 -->
          <polyline
            :points="polylinePixelPoints(fleetStore.selectedBikeId)"
            fill="none"
            stroke="#3b82f6"
            stroke-width="6"
            stroke-opacity="0.15"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <!-- 선택 차량 경로: 주선 -->
          <polyline
            :points="polylinePixelPoints(fleetStore.selectedBikeId)"
            fill="none"
            stroke="#3b82f6"
            stroke-width="2.5"
            stroke-opacity="0.85"
            stroke-dasharray="8 4"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <!-- 출발점 (초록 원) -->
          <circle
            v-if="startPointPixel(fleetStore.selectedBikeId)"
            :cx="startPointPixel(fleetStore.selectedBikeId)!.x"
            :cy="startPointPixel(fleetStore.selectedBikeId)!.y"
            r="5"
            fill="#10b981"
            fill-opacity="0.9"
            stroke="white"
            stroke-width="1.5"
          />
        </svg>
      </Transition>

      <!-- ── 차량 마커 ─────────────────────────────────────────── -->
      <div
        v-for="bike in fleetStore.bikes"
        :key="bike.id"
        :style="markerStyle(bike)"
        :class="['absolute cursor-pointer group transition-opacity duration-300', markerOpacity(bike)]"
        style="z-index: 600; transform: translate(-50%, -100%);"
        @click="handleMarkerClick(bike.id)"
      >
        <!-- 선택 강조 링 -->
        <div v-if="fleetStore.selectedBikeId === bike.id"
             class="absolute -inset-1.5 rounded-full border-2 border-primary-400 animate-pulse" />
        <!-- ping 애니메이션 -->
        <span v-if="bike.status === 'running'"
              :class="['absolute inset-0 rounded-full animate-ping opacity-60', statusPingColor(bike.status)]" />
        <!-- 마커 핀 -->
        <div :class="['relative w-7 h-7 rounded-full border-2 border-white shadow-lg flex items-center justify-center group-hover:scale-125 group-hover:shadow-xl transition-transform duration-150', markerBgColor(bike.status)]">
          <Bike class="w-3.5 h-3.5 text-white" />
        </div>
        <!-- 툴팁 -->
        <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2.5 hidden group-hover:block pointer-events-none"
             style="z-index: 700;">
          <div class="bg-secondary-900/95 text-white text-xs rounded-lg px-2.5 py-1.5 whitespace-nowrap shadow-xl">
            <p class="font-semibold">{{ bike.plate_number }}</p>
            <p class="text-secondary-300 mt-0.5">{{ bike.speed_kmh ?? 0 }} km/h · {{ Math.round(bike.battery_level) }}%</p>
            <p class="text-secondary-400">{{ bike.driver_name ?? '미배정' }}</p>
            <p v-if="fleetStore.selectedBikeId === bike.id" class="text-blue-300 mt-0.5">
              경로 {{ filteredHistory(bike.id).length }}점 · 최근 6시간
            </p>
          </div>
          <div class="w-2 h-2 bg-secondary-900/95 rotate-45 mx-auto -mt-1" />
        </div>
      </div>

    </template>

    <!-- ══ 커스텀 줌 컨트롤 ════════════════════════════════════ -->
    <div
      class="absolute right-3 top-1/2 -translate-y-1/2 flex flex-col items-center gap-1.5"
      style="z-index: 900;"
    >
      <button
        @click="zoomIn"
        :disabled="currentZoom >= MAX_ZOOM"
        class="w-8 h-8 rounded-lg bg-white dark:bg-secondary-800 shadow-md
               flex items-center justify-center
               text-secondary-700 dark:text-secondary-300
               hover:bg-secondary-50 dark:hover:bg-secondary-700
               border border-slate-200 dark:border-secondary-600
               transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        title="확대"
      >
        <Plus class="w-4 h-4" />
      </button>

      <div class="relative flex items-center justify-center" style="height: 88px; width: 32px;">
        <input
          type="range"
          :min="MIN_ZOOM"
          :max="MAX_ZOOM"
          :step="1"
          :value="currentZoom"
          @input="onSliderInput"
          class="accent-primary-500"
          style="width: 88px; transform: rotate(-90deg); cursor: pointer;"
        />
      </div>

      <button
        @click="zoomOut"
        :disabled="currentZoom <= MIN_ZOOM"
        class="w-8 h-8 rounded-lg bg-white dark:bg-secondary-800 shadow-md
               flex items-center justify-center
               text-secondary-700 dark:text-secondary-300
               hover:bg-secondary-50 dark:hover:bg-secondary-700
               border border-slate-200 dark:border-secondary-600
               transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        title="축소"
      >
        <Minus class="w-4 h-4" />
      </button>

      <span class="text-[10px] text-secondary-400 dark:text-secondary-500 font-mono tabular-nums leading-none">
        {{ currentZoom }}
      </span>
    </div>

    <!-- ══ 하단 상태 바 ════════════════════════════════════════ -->
    <div
      class="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-3
             bg-white/85 dark:bg-secondary-800/85 backdrop-blur-sm
             px-4 py-2 rounded-full shadow-sm pointer-events-none"
      style="z-index: 800;"
    >
      <span class="flex items-center gap-1.5 text-xs text-secondary-600 dark:text-secondary-300">
        <span class="w-2 h-2 rounded-full bg-success-500" />
        운행 중 <strong class="text-success-600 dark:text-success-400">{{ fleetStore.runningCount }}</strong>
      </span>
      <span class="w-px h-3 bg-slate-200 dark:bg-secondary-600" />
      <span class="flex items-center gap-1.5 text-xs text-secondary-600 dark:text-secondary-300">
        <span class="w-2 h-2 rounded-full bg-danger-500" />
        알림 <strong class="text-danger-500">{{ fleetStore.alertCount }}</strong>
      </span>
      <span class="w-px h-3 bg-slate-200 dark:bg-secondary-600" />
      <span class="flex items-center gap-1.5 text-xs text-secondary-600 dark:text-secondary-300">
        <span class="w-2 h-2 rounded-full bg-info-400" />
        충전 <strong class="text-info-600 dark:text-info-400">{{ fleetStore.chargingCount }}</strong>
      </span>
      <span class="w-px h-3 bg-slate-200 dark:bg-secondary-600" />
      <span class="text-xs text-secondary-500 dark:text-secondary-400">총 {{ fleetStore.bikes.length }}대</span>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue"
import L from "leaflet"
import "leaflet/dist/leaflet.css"
import { Bike, Plus, Minus } from "lucide-vue-next"
import { useFleetStore } from "@/stores/useFleetStore"
import type { Bike as BikeType, BikeStatus } from "@/stores/useFleetStore"

// ── Props ──────────────────────────────────────────────────────
export type MapFilter = "all" | "running" | "low-battery"
const props = withDefaults(defineProps<{ filter?: MapFilter }>(), { filter: "all" })

// ── 스토어 ──────────────────────────────────────────────────────
const fleetStore = useFleetStore()

// ── Leaflet 인스턴스 ────────────────────────────────────────────
const mapEl      = ref<HTMLElement>()
const mapInst    = ref<L.Map | null>(null)
const tileLayer  = ref<L.TileLayer | null>(null)
const mapReady   = ref(false)
const mapTick    = ref(0)   // move/zoom 시 증가 → 마커 좌표 재계산 트리거

// ── 줌 범위 ──────────────────────────────────────────────────────
const MIN_ZOOM = 10
const MAX_ZOOM = 18
const currentZoom = computed(() => {
  void mapTick.value  // reactive dependency
  return mapInst.value?.getZoom() ?? 12
})

// ── 타일 URL (다크/라이트) ────────────────────────────────────────
const TILE_LIGHT = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
const TILE_DARK  = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
const TILE_ATTR  =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors ' +
  '&copy; <a href="https://carto.com/attributions">CARTO</a>'

// ── Leaflet 초기화 ───────────────────────────────────────────────
onMounted(() => {
  // 다크모드 감지
  const isDark = () => document.documentElement.classList.contains("dark")

  const map = L.map(mapEl.value!, {
    center:           [37.5548, 127.0420],  // 성동구 중심
    zoom:             15,
    zoomControl:      false,
    attributionControl: true,
    minZoom:          MIN_ZOOM,
    maxZoom:          MAX_ZOOM,
  })

  // 초기 타일 레이어
  tileLayer.value = L.tileLayer(
    isDark() ? TILE_DARK : TILE_LIGHT,
    { maxZoom: MAX_ZOOM, attribution: TILE_ATTR, subdomains: "abcd" }
  ).addTo(map)

  // 지도 이동/줌 시 마커 위치 갱신
  map.on("move zoom", () => { mapTick.value++ })
  map.whenReady(() => { mapReady.value = true; mapTick.value++ })

  mapInst.value = map

  // 컨테이너 크기 변화 감지 → Leaflet에 알림
  const resizeObserver = new ResizeObserver(() => {
    map.invalidateSize()
    mapTick.value++
  })
  resizeObserver.observe(mapEl.value!)

  // 다크모드 전환 감지 → 타일 교체
  const darkObserver = new MutationObserver(() => {
    if (!mapInst.value || !tileLayer.value) return
    const dark = isDark()
    mapInst.value.removeLayer(tileLayer.value)
    tileLayer.value = L.tileLayer(
      dark ? TILE_DARK : TILE_LIGHT,
      { maxZoom: MAX_ZOOM, attribution: TILE_ATTR, subdomains: "abcd" }
    ).addTo(mapInst.value)
  })
  darkObserver.observe(document.documentElement, {
    attributes: true, attributeFilter: ["class"],
  })

  onUnmounted(() => {
    resizeObserver.disconnect()
    darkObserver.disconnect()
    map.remove()
  })
})

// ── 위도·경도 → 화면 픽셀 좌표 ──────────────────────────────────
function latlngToPixel(lat: number, lng: number): { x: number; y: number } {
  if (!mapInst.value) return { x: -9999, y: -9999 }
  void mapTick.value  // reactive dependency
  const pt = mapInst.value.latLngToContainerPoint([lat, lng])
  return { x: pt.x, y: pt.y }
}

// ── 마커 스타일 (픽셀 위치) ─────────────────────────────────────
function markerStyle(bike: BikeType): Record<string, string> {
  const { x, y } = latlngToPixel(bike.lat, bike.lng)
  return { left: `${x}px`, top: `${y}px` }
}

// ── 상태 색상 ──────────────────────────────────────────────────
function markerBgColor(status: BikeStatus): string {
  const m: Record<BikeStatus, string> = {
    running: "bg-success-500", idle: "bg-secondary-400",
    charging: "bg-info-500",   alert: "bg-danger-500", offline: "bg-secondary-300",
  }
  return m[status]
}
function statusPingColor(status: BikeStatus): string {
  const m: Record<BikeStatus, string> = {
    running: "bg-success-400", idle: "bg-secondary-300",
    charging: "bg-info-400",   alert: "bg-danger-400", offline: "bg-transparent",
  }
  return m[status]
}

// ── 마커 클릭 (토글 선택) ──────────────────────────────────────
function handleMarkerClick(id: string): void {
  fleetStore.selectBike(fleetStore.selectedBikeId === id ? null : id)
}

// ── 필터 가시성 ────────────────────────────────────────────────
const LOW_BATTERY_THRESHOLD = 30

function isHighlighted(bike: BikeType): boolean {
  switch (props.filter) {
    case "running":     return bike.status === "running"
    case "low-battery": return bike.battery_level <= LOW_BATTERY_THRESHOLD && bike.status !== "offline"
    default:            return true
  }
}

function markerOpacity(bike: BikeType): string {
  // 선택된 차량은 항상 완전히 보임
  if (bike.id === fleetStore.selectedBikeId) return "opacity-100"
  // 필터에 맞지 않는 차량: 강하게 희미하게
  if (!isHighlighted(bike)) return "opacity-10"
  // 필터는 통과했지만 다른 차량이 선택된 경우: 약하게 희미하게
  if (fleetStore.selectedBikeId) return "opacity-30"
  return "opacity-100"
}

// ── 운행 경로: 최근 6시간 이력 필터 ────────────────────────────
const SIX_HOURS_MS = 6 * 3_600_000

function filteredHistory(bikeId: string) {
  const cutoff = Date.now() - SIX_HOURS_MS
  return (fleetStore.positionHistory[bikeId] ?? []).filter(p => p.timestamp >= cutoff)
}

function polylinePixelPoints(bikeId: string): string {
  if (!mapInst.value) return ""
  void mapTick.value  // reactive dependency
  return filteredHistory(bikeId)
    .map(p => {
      const pt = mapInst.value!.latLngToContainerPoint([p.lat, p.lng])
      return `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`
    })
    .join(" ")
}

function startPointPixel(bikeId: string | null): { x: number; y: number } | null {
  if (!bikeId || !mapInst.value) return null
  void mapTick.value  // reactive dependency
  const h = filteredHistory(bikeId)
  if (!h.length) return null
  const pt = mapInst.value.latLngToContainerPoint([h[0].lat, h[0].lng])
  return { x: pt.x, y: pt.y }
}

const unselectedRunningBikes = computed(() =>
  fleetStore.bikes.filter(
    b => b.status === "running" && b.id !== fleetStore.selectedBikeId
  )
)

// ── 줌 조작 ────────────────────────────────────────────────────
function zoomIn(): void  { mapInst.value?.zoomIn() }
function zoomOut(): void { mapInst.value?.zoomOut() }
function onSliderInput(e: Event): void {
  mapInst.value?.setZoom(parseInt((e.target as HTMLInputElement).value))
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s ease; }
.fade-enter-from, .fade-leave-to        { opacity: 0; }

/* Leaflet attribution을 방해받지 않도록 우측 하단 여백 확보 */
:deep(.leaflet-control-attribution) {
  font-size: 9px;
  opacity: 0.6;
  background: transparent;
}
</style>
