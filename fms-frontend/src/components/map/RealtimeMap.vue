<template>
  <div class="relative w-full h-full overflow-hidden select-none">

    <!-- ══ Leaflet 지도 컨테이너 ════════════════════════════════ -->
    <div ref="mapEl" class="absolute inset-0" style="z-index: 0;" />

    <!-- ══ 오버레이 레이어 (지도 준비 후 표시) ════════════════════ -->
    <template v-if="mapReady">

      <!-- ── 운행 경로 SVG (차량 선택 시) ─────────────────────── -->
      <Transition name="fade">
        <svg
          v-if="fleetStore.selectedVehicleId"
          class="absolute inset-0 w-full h-full pointer-events-none"
          style="z-index: 500;"
        >
          <!-- 비선택 running 차량 경로 (흐리게) -->
          <polyline
            v-for="v in unselectedRunningVehicles"
            :key="'route-other-' + v.id"
            :points="polylinePixelPoints(v.id)"
            fill="none"
            stroke="#94a3b8"
            stroke-width="1.5"
            stroke-opacity="0.35"
            stroke-linecap="round"
            stroke-linejoin="round"
          />

          <!-- 선택 차량 경로: 글로우 -->
          <polyline
            :points="polylinePixelPoints(fleetStore.selectedVehicleId)"
            fill="none"
            stroke="#3b82f6"
            stroke-width="6"
            stroke-opacity="0.15"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <!-- 선택 차량 경로: 주선 -->
          <polyline
            :points="polylinePixelPoints(fleetStore.selectedVehicleId)"
            fill="none"
            stroke="#3b82f6"
            stroke-width="2.5"
            stroke-opacity="0.85"
            stroke-linecap="round"
            stroke-linejoin="round"
          />

          <!-- 방향 화살표 -->
          <g
            v-for="(arrow, i) in routeArrows(fleetStore.selectedVehicleId)"
            :key="'arrow-' + i"
            :transform="`translate(${arrow.x},${arrow.y}) rotate(${arrow.angle})`"
          >
            <!-- 흰 배경 원 -->
            <circle r="6" fill="white" fill-opacity="0.85" />
            <!-- 화살표 머리 (오른쪽을 기준으로 그린 뒤 회전) -->
            <path d="M-3.5,-3 L3.5,0 L-3.5,3" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </g>

          <!-- 출발점 (초록 원 + "출발" 라벨) -->
          <g v-if="startPointPixel(fleetStore.selectedVehicleId)">
            <circle
              :cx="startPointPixel(fleetStore.selectedVehicleId)!.x"
              :cy="startPointPixel(fleetStore.selectedVehicleId)!.y"
              r="6"
              fill="#10b981"
              fill-opacity="0.95"
              stroke="white"
              stroke-width="1.5"
            />
            <text
              :x="startPointPixel(fleetStore.selectedVehicleId)!.x"
              :y="startPointPixel(fleetStore.selectedVehicleId)!.y - 10"
              text-anchor="middle"
              font-size="9"
              font-weight="700"
              fill="#10b981"
              stroke="white"
              stroke-width="3"
              paint-order="stroke"
            >출발</text>
          </g>
        </svg>
      </Transition>

      <!-- ── 차량 마커 ─────────────────────────────────────────── -->
      <div
        v-for="v in visibleVehicles"
        :key="v.id"
        :style="markerStyle(v)"
        :class="['absolute cursor-pointer group transition-opacity duration-300', markerOpacity(v)]"
        style="z-index: 600; transform: translate(-50%, -100%);"
        @click="handleMarkerClick(v.id)"
      >
        <!-- 선택 강조 링 -->
        <div v-if="fleetStore.selectedVehicleId === v.id"
             class="absolute -inset-1.5 rounded-full border-2 border-primary-400 animate-pulse" />
        <!-- ping 애니메이션 -->
        <span v-if="v.status === 'RUNNING'"
              :class="['absolute inset-0 rounded-full animate-ping opacity-60', statusPingColor(v.status)]" />
        <!-- 마커 핀 -->
        <div :class="['relative w-7 h-7 rounded-full border-2 border-white shadow-lg flex items-center justify-center group-hover:scale-125 group-hover:shadow-xl transition-transform duration-150', markerBgColor(v.status)]">
          <Bike class="w-3.5 h-3.5 text-white" />
        </div>
        <!-- 알림 뱃지 -->
        <div
          v-if="latestAlert(v.id)"
          :class="['absolute top-full left-1/2 -translate-x-1/2 mt-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold whitespace-nowrap shadow pointer-events-none', alertPillClass(latestAlert(v.id)!.severity)]"
        >
          {{ shortAlertTitle(latestAlert(v.id)!.title) }}
        </div>
        <!-- 툴팁 -->
        <div class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2.5 hidden group-hover:block pointer-events-none"
             style="z-index: 700;">
          <div class="bg-secondary-900/95 text-white text-xs rounded-lg px-2.5 py-1.5 whitespace-nowrap shadow-xl">
            <p class="font-semibold">{{ v.plate_number }}</p>
            <p class="text-secondary-300 mt-0.5">
              {{ currentSensor(v)?.speed_kmh?.toFixed(0) ?? 0 }} km/h
              · {{ currentSensor(v)?.battery_level_pct?.toFixed(0) ?? '—' }}%
            </p>
            <p class="text-secondary-400">{{ v.assigned_driver?.user_full_name ?? '미배정' }}</p>
            <p v-if="fleetStore.selectedVehicleId === v.id" class="text-blue-300 mt-0.5">
              경로 {{ filteredHistory(v.id).length }}점
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
      <span class="text-xs text-secondary-500 dark:text-secondary-400">총 {{ fleetStore.vehicles.length }}대</span>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue"
import L from "leaflet"
import "leaflet/dist/leaflet.css"
import { Bike, Plus, Minus } from "lucide-vue-next"
import { useFleetStore } from "@/stores/fleet"
import { useAlertStore } from "@/stores/alert"
import type { Vehicle, VehicleStatus, LatestSensor } from "@/types/models"
import type { PositionPoint } from "@/stores/fleet"

// ── Props ──────────────────────────────────────────────────────
export type MapFilter = "all" | "running" | "low-battery" | "not-running"
const props = withDefaults(defineProps<{ filter?: MapFilter }>(), { filter: "all" })

// ── 스토어 ──────────────────────────────────────────────────────
const fleetStore = useFleetStore()
const alertStore = useAlertStore()

// ── 차량별 최신 미확인 알림 ────────────────────────────────────────
function latestAlert(vehicleId: string) {
  return alertStore.alerts.find(a => !a.is_acknowledged && a.vehicle.id === vehicleId) ?? null
}

function alertPillClass(severity: string): string {
  if (severity === "DANGER")  return "bg-danger-500 text-white"
  if (severity === "WARNING") return "bg-warning-400 text-white"
  return "bg-info-500 text-white"
}

function shortAlertTitle(title: string): string {
  return title.length > 6 ? title.slice(0, 6) + "…" : title
}

// ── Leaflet 인스턴스 ────────────────────────────────────────────
const mapEl    = ref<HTMLElement>()
const mapInst  = ref<L.Map | null>(null)
const tileLayer = ref<L.TileLayer | null>(null)
const mapReady  = ref(false)
const mapTick   = ref(0)

const MIN_ZOOM = 10
const MAX_ZOOM = 18
const currentZoom = computed(() => {
  void mapTick.value
  return mapInst.value?.getZoom() ?? 14
})

const TILE_LIGHT = "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
const TILE_DARK  = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
const TILE_ATTR  =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors ' +
  '&copy; <a href="https://carto.com/attributions">CARTO</a>'

// ── 위치가 있는 차량만 표시 ──────────────────────────────────────
const visibleVehicles = computed(() =>
  fleetStore.vehicles.filter(v => {
    const s = currentSensor(v)
    return s?.latitude != null && s?.longitude != null
  })
)

// ── 현재 센서 데이터 (실시간 우선, 없으면 latest_sensor) ────────
function currentSensor(v: Vehicle): LatestSensor | null {
  return fleetStore.realtimeLocations.get(v.id) ?? v.latest_sensor ?? null
}

// ── Leaflet 초기화 ───────────────────────────────────────────────
onMounted(() => {
  const isDark = () => document.documentElement.classList.contains("dark")

  const map = L.map(mapEl.value!, {
    center:           [37.5548, 127.0420],
    zoom:             14,
    zoomControl:      false,
    attributionControl: true,
    minZoom:          MIN_ZOOM,
    maxZoom:          MAX_ZOOM,
  })

  tileLayer.value = L.tileLayer(
    isDark() ? TILE_DARK : TILE_LIGHT,
    { maxZoom: MAX_ZOOM, attribution: TILE_ATTR, subdomains: "abcd" }
  ).addTo(map)

  map.on("move zoom", () => { mapTick.value++ })
  map.whenReady(() => { mapReady.value = true; mapTick.value++ })

  mapInst.value = map

  const resizeObserver = new ResizeObserver(() => {
    map.invalidateSize()
    mapTick.value++
  })
  resizeObserver.observe(mapEl.value!)

  const darkObserver = new MutationObserver(() => {
    if (!mapInst.value || !tileLayer.value) return
    const dark = isDark()
    mapInst.value.removeLayer(tileLayer.value as unknown as L.Layer)
    tileLayer.value = L.tileLayer(
      dark ? TILE_DARK : TILE_LIGHT,
      { maxZoom: MAX_ZOOM, attribution: TILE_ATTR, subdomains: "abcd" }
    ).addTo(mapInst.value as unknown as L.Map)
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
  void mapTick.value
  const pt = mapInst.value.latLngToContainerPoint([lat, lng])
  return { x: pt.x, y: pt.y }
}

// ── 마커 스타일 (픽셀 위치) ─────────────────────────────────────
function markerStyle(v: Vehicle): Record<string, string> {
  const s = currentSensor(v)
  if (!s?.latitude || !s?.longitude) return { display: "none" }
  const { x, y } = latlngToPixel(s.latitude, s.longitude)
  return { left: `${x}px`, top: `${y}px` }
}

// ── 상태 색상 ──────────────────────────────────────────────────
function markerBgColor(status: VehicleStatus): string {
  const m: Record<VehicleStatus, string> = {
    RUNNING: "bg-success-500", IDLE: "bg-secondary-400",
    CHARGING: "bg-info-500",   ALERT: "bg-danger-500", OFFLINE: "bg-secondary-300",
  }
  return m[status] ?? "bg-secondary-400"
}
function statusPingColor(status: VehicleStatus): string {
  const m: Record<VehicleStatus, string> = {
    RUNNING: "bg-success-400", IDLE: "bg-secondary-300",
    CHARGING: "bg-info-400",   ALERT: "bg-danger-400", OFFLINE: "bg-transparent",
  }
  return m[status] ?? "bg-transparent"
}

// ── 마커 클릭 ──────────────────────────────────────────────────
function handleMarkerClick(id: string): void {
  fleetStore.selectVehicle(fleetStore.selectedVehicleId === id ? null : id)
}

// ── 선택 차량으로 지도 이동 ────────────────────────────────────
watch(() => fleetStore.selectedVehicleId, (id) => {
  if (!id || !mapInst.value) return
  const vehicle = fleetStore.vehicles.find(v => v.id === id)
  if (!vehicle) return
  const sensor = fleetStore.realtimeLocations.get(id) ?? vehicle.latest_sensor
  if (sensor?.latitude && sensor?.longitude) {
    mapInst.value.panTo([sensor.latitude, sensor.longitude], { animate: true, duration: 0.5 })
  }
})

// ── 필터 가시성 ────────────────────────────────────────────────
function isHighlighted(v: Vehicle): boolean {
  switch (props.filter) {
    case "running":     return v.status === "RUNNING"
    case "low-battery": {
      const pct = currentSensor(v)?.battery_level_pct
      return pct != null && pct <= 30 && v.status !== "OFFLINE"
    }
    case "not-running": return v.status === "IDLE" || v.status === "OFFLINE"
    default:            return true
  }
}

function markerOpacity(v: Vehicle): string {
  if (v.id === fleetStore.selectedVehicleId) return "opacity-100"
  if (!isHighlighted(v)) return "opacity-10"
  if (fleetStore.selectedVehicleId) return "opacity-30"
  return "opacity-100"
}

// ── 운행 경로 ──────────────────────────────────────────────────
const SIX_HOURS_MS = 6 * 3_600_000

function filteredHistory(vehicleId: string): PositionPoint[] {
  const cutoff = Date.now() - SIX_HOURS_MS
  return (fleetStore.positionHistory.get(vehicleId) ?? []).filter(p => p.timestamp >= cutoff)
}

function polylinePixelPoints(vehicleId: string): string {
  if (!mapInst.value) return ""
  void mapTick.value
  return filteredHistory(vehicleId)
    .map(p => {
      const pt = mapInst.value!.latLngToContainerPoint([p.lat, p.lng])
      return `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`
    })
    .join(" ")
}

function startPointPixel(vehicleId: string | null): { x: number; y: number } | null {
  if (!vehicleId || !mapInst.value) return null
  void mapTick.value
  const h = filteredHistory(vehicleId)
  if (!h.length) return null
  const pt = mapInst.value.latLngToContainerPoint([h[0].lat, h[0].lng])
  return { x: pt.x, y: pt.y }
}

// ── 경로 방향 화살표 ──────────────────────────────────────────
const ARROW_SPACING_PX = 65   // 화살표 간격 (픽셀)

interface ArrowMarker {
  x:     number
  y:     number
  angle: number   // 회전각도 (도), 오른쪽=0
}

function routeArrows(vehicleId: string | null): ArrowMarker[] {
  if (!vehicleId || !mapInst.value) return []
  void mapTick.value
  const history = filteredHistory(vehicleId)
  if (history.length < 2) return []

  // 히스토리 포인트를 픽셀 좌표로 변환
  const pixels = history.map(p => {
    const pt = mapInst.value!.latLngToContainerPoint([p.lat, p.lng])
    return { x: pt.x, y: pt.y }
  })

  const result: ArrowMarker[] = []
  // 첫 화살표를 경로 중간쯤에 두기 위해 절반 간격부터 시작
  let accumulated = ARROW_SPACING_PX * 0.5

  for (let i = 1; i < pixels.length; i++) {
    const prev = pixels[i - 1]
    const curr = pixels[i]
    const dx   = curr.x - prev.x
    const dy   = curr.y - prev.y
    const segLen = Math.sqrt(dx * dx + dy * dy)
    if (segLen < 0.5) continue

    const angle = Math.atan2(dy, dx) * 180 / Math.PI
    let walked = 0

    while (accumulated + (segLen - walked) >= ARROW_SPACING_PX) {
      const need = ARROW_SPACING_PX - accumulated
      walked += need
      const t = walked / segLen
      result.push({
        x:     prev.x + dx * t,
        y:     prev.y + dy * t,
        angle,
      })
      accumulated = 0
    }
    accumulated += segLen - walked
  }
  return result
}

const unselectedRunningVehicles = computed(() =>
  fleetStore.vehicles.filter(
    v => v.status === "RUNNING" && v.id !== fleetStore.selectedVehicleId
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

:deep(.leaflet-control-attribution) {
  font-size: 9px;
  opacity: 0.6;
  background: transparent;
}
</style>
