import { ref, computed } from "vue"
import { defineStore } from "pinia"
import { vehicleService } from "@/services/vehicleService"
import type { Vehicle, LatestSensor } from "@/types/models"
import type { PageMeta } from "@/types/api"

// ── 지도 위치 이력 포인트 ─────────────────────────────────────────
export interface PositionPoint {
  lat:       number
  lng:       number
  timestamp: number
}

const HISTORY_MAX  = 80
const HISTORY_HOURS = 6
const HISTORY_MS   = HISTORY_HOURS * 3_600_000

/** 현재 위치에서 역방향 랜덤 워크로 초기 이력 생성 */
function buildInitialHistory(lat: number, lng: number, points: number): PositionPoint[] {
  const now    = Date.now()
  const stepMs = HISTORY_MS / Math.max(points - 1, 1)
  const step   = 0.003

  const coords: Array<{ lat: number; lng: number }> = [{ lat, lng }]
  for (let i = 1; i < points; i++) {
    const p = coords[0]
    coords.unshift({
      lat: p.lat + (Math.random() - 0.5) * step,
      lng: p.lng + (Math.random() - 0.5) * step,
    })
  }

  return coords.map((c, i) => ({
    ...c,
    timestamp: now - (points - 1 - i) * stepMs,
  }))
}

export const useFleetStore = defineStore("fleet", () => {
  // ── State ────────────────────────────────────────────────
  const vehicles          = ref<Vehicle[]>([])
  const selectedVehicle   = ref<Vehicle | null>(null)
  const selectedVehicleId = ref<string | null>(null)
  const pageMeta          = ref<PageMeta | null>(null)
  const isListLoading     = ref(false)
  const isDetailLoading   = ref(false)

  // vehicle_id → 최신 위치 (WebSocket 실시간 갱신)
  const realtimeLocations  = ref<Map<string, LatestSensor>>(new Map())
  // vehicle_id → 위치 이력 (지도 경로 표시)
  const positionHistory    = ref<Map<string, PositionPoint[]>>(new Map())

  // ── Getters ──────────────────────────────────────────────
  const vehicleById = computed(() =>
    (id: string) => vehicles.value.find(v => v.id === id) ?? null
  )
  const alertVehicles   = computed(() => vehicles.value.filter(v => v.status === "ALERT"))
  const offlineVehicles = computed(() => vehicles.value.filter(v => v.status === "OFFLINE"))
  const runningCount    = computed(() => vehicles.value.filter(v => v.status === "RUNNING").length)
  const alertCount      = computed(() => vehicles.value.filter(v => v.status === "ALERT").length)
  const chargingCount   = computed(() => vehicles.value.filter(v => v.status === "CHARGING").length)

  // ── Actions ──────────────────────────────────────────────
  async function fetchVehicles(params?: {
    status?: string[]
    q?: string
    page?: number
    page_size?: number
  }): Promise<void> {
    isListLoading.value = true
    try {
      const res = await vehicleService.list(params)
      vehicles.value = res.data
      pageMeta.value  = res.meta

      // 초기 위치 이력 생성 (latest_sensor 기준)
      const nextHistory = new Map(positionHistory.value)
      for (const v of res.data) {
        if (!nextHistory.has(v.id) && v.latest_sensor?.latitude && v.latest_sensor?.longitude) {
          const initPoints = v.status === "RUNNING" ? 40 : v.status === "ALERT" ? 20 : 5
          nextHistory.set(v.id, buildInitialHistory(
            v.latest_sensor.latitude,
            v.latest_sensor.longitude,
            initPoints,
          ))
        }
      }
      positionHistory.value = nextHistory
    } finally {
      isListLoading.value = false
    }
  }

  async function fetchVehicleDetail(vehicleId: string): Promise<void> {
    isDetailLoading.value = true
    try {
      selectedVehicle.value = await vehicleService.getById(vehicleId)
    } finally {
      isDetailLoading.value = false
    }
  }

  function updateRealtimeLocation(vehicleId: string, sensor: LatestSensor): void {
    // 실시간 위치 업데이트
    const next = new Map(realtimeLocations.value)
    next.set(vehicleId, sensor)
    realtimeLocations.value = next

    // 위치 이력 추가
    if (sensor.latitude != null && sensor.longitude != null) {
      const hist    = positionHistory.value.get(vehicleId) ?? []
      const cutoff  = Date.now() - HISTORY_MS
      const updated = [
        ...hist.filter(p => p.timestamp >= cutoff),
        { lat: sensor.latitude, lng: sensor.longitude, timestamp: Date.now() },
      ].slice(-HISTORY_MAX)

      const nextHist = new Map(positionHistory.value)
      nextHist.set(vehicleId, updated)
      positionHistory.value = nextHist
    }
  }

  function selectVehicle(id: string | null): void {
    selectedVehicleId.value = id
  }

  function clearSelectedVehicle(): void {
    selectedVehicle.value   = null
    selectedVehicleId.value = null
  }

  // ── 데모 시뮬레이션 ──────────────────────────────────────────
  const _simTimer    = ref<ReturnType<typeof setInterval> | null>(null)
  const _simHeadings = new Map<string, number>()   // vehicle_id → 진행 방향(라디안)

  function startDemoSimulation(intervalMs = 1500): void {
    if (_simTimer.value) return

    _simTimer.value = setInterval(() => {
      for (const v of vehicles.value) {
        // RUNNING / ALERT 차량만 이동
        if (v.status !== "RUNNING" && v.status !== "ALERT") continue

        const sensor = realtimeLocations.value.get(v.id) ?? v.latest_sensor
        if (!sensor?.latitude || !sensor?.longitude) continue

        // 방향 유지하되 조금씩 꺾기 (자연스러운 경로)
        let heading = _simHeadings.get(v.id) ?? Math.random() * Math.PI * 2
        heading += (Math.random() - 0.5) * 0.35
        _simHeadings.set(v.id, heading)

        // 1.5초마다 ~12m 이동 (약 28 km/h)
        const step   = 0.00011
        const newLat = sensor.latitude  + Math.cos(heading) * step
        const newLng = sensor.longitude + Math.sin(heading) * step * 1.3

        updateRealtimeLocation(v.id, {
          ...sensor,
          latitude:    newLat,
          longitude:   newLng,
          speed_kmh:   20 + Math.random() * 20,
          recorded_at: new Date().toISOString(),
        })
      }
    }, intervalMs)
  }

  function stopDemoSimulation(): void {
    if (_simTimer.value) {
      clearInterval(_simTimer.value)
      _simTimer.value = null
    }
  }

  return {
    vehicles, selectedVehicle, selectedVehicleId, pageMeta,
    isListLoading, isDetailLoading,
    realtimeLocations, positionHistory,
    vehicleById, alertVehicles, offlineVehicles,
    runningCount, alertCount, chargingCount,
    fetchVehicles, fetchVehicleDetail, updateRealtimeLocation,
    selectVehicle, clearSelectedVehicle,
    startDemoSimulation, stopDemoSimulation,
  }
})
