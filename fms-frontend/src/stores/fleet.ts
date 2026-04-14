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

  /** 폴링용 조용한 갱신 — 로딩 스피너 없음, positionHistory 보존
   *  데모 시뮬레이션 실행 중일 때는 positionHistory를 건드리지 않음 */
  async function refreshVehicles(): Promise<void> {
    try {
      const res = await vehicleService.list({ page_size: 100 })

      if (!_simTimer.value) {
        // 시뮬레이션 OFF: 실제 API 위치로 이력 갱신
        const nextHistory = new Map(positionHistory.value)
        for (const v of res.data) {
          if (!v.latest_sensor?.latitude || !v.latest_sensor?.longitude) continue
          if (!nextHistory.has(v.id)) {
            const initPoints = v.status === "RUNNING" ? 40 : v.status === "ALERT" ? 20 : 5
            nextHistory.set(v.id, buildInitialHistory(
              v.latest_sensor.latitude, v.latest_sensor.longitude, initPoints,
            ))
          } else {
            const hist    = nextHistory.get(v.id)!
            const cutoff  = Date.now() - HISTORY_MS
            const updated = [
              ...hist.filter(p => p.timestamp >= cutoff),
              { lat: v.latest_sensor.latitude, lng: v.latest_sensor.longitude, timestamp: Date.now() },
            ].slice(-HISTORY_MAX)
            nextHistory.set(v.id, updated)
          }
        }
        positionHistory.value = nextHistory
      }
      // 차량 메타데이터(상태·배터리 등)는 항상 갱신
      vehicles.value = res.data
    } catch {
      // 백그라운드 갱신 실패는 무시
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
  const _simHeadings = new Map<string, number>()

  // 한강 금지 구역 (강남구는 한강 이남이라 해당 없음 — 빈 배열 유지)
  const WATER_ZONES: { latMin: number; latMax: number; lngMin: number; lngMax: number }[] = []

  // 강남구 테헤란로 이동 허용 경계
  const BOUNDS = { latMin: 37.493, latMax: 37.514, lngMin: 127.022, lngMax: 127.068 }

  // 테헤란로 일대 초기 분산 위치 (차량 수만큼 순환)
  const GANGNAM_STARTS = [
    { lat: 37.4990, lng: 127.0276 }, // 강남역 인근
    { lat: 37.5005, lng: 127.0335 }, // 역삼역 인근
    { lat: 37.5010, lng: 127.0390 }, // 테헤란로 중간
    { lat: 37.4985, lng: 127.0430 }, // 선릉역 인근
    { lat: 37.5020, lng: 127.0475 }, // 삼성역 인근
    { lat: 37.5000, lng: 127.0520 }, // 봉은사역 인근
    { lat: 37.4975, lng: 127.0300 }, // 강남구청 방향
    { lat: 37.5015, lng: 127.0450 }, // 코엑스 방향
    { lat: 37.4960, lng: 127.0360 }, // 논현동 방향
    { lat: 37.5030, lng: 127.0550 }, // 잠실 방향
  ]

  function _isInWater(lat: number, lng: number): boolean {
    return WATER_ZONES.some(z =>
      lat >= z.latMin && lat <= z.latMax && lng >= z.lngMin && lng <= z.lngMax
    )
  }

  /** 물 위에 있는 차량을 가장 가까운 육지(강 남·북쪽 둑)로 즉시 이동 */
  function _snapToLand(lat: number, lng: number): { lat: number; lng: number } {
    if (!_isInWater(lat, lng)) return { lat, lng }
    const zone = WATER_ZONES[0]
    const distToSouth = Math.abs(lat - zone.latMin)
    const distToNorth = Math.abs(lat - zone.latMax)
    return distToSouth < distToNorth
      ? { lat: zone.latMin - 0.001, lng }   // 강 남쪽 둑
      : { lat: zone.latMax + 0.001, lng }   // 강 북쪽 둑
  }

  function startDemoSimulation(intervalMs = 1500): void {
    if (_simTimer.value) return

    // ── 시작 시 모든 차량을 테헤란로 일대로 강제 배치 ──────────
    let startIdx = 0
    for (const v of vehicles.value) {
      const sensor = realtimeLocations.value.get(v.id) ?? v.latest_sensor
      const base   = GANGNAM_STARTS[startIdx % GANGNAM_STARTS.length]
      startIdx++

      // 기준점 ±300m 범위에서 약간씩 랜덤 분산
      const lat = base.lat + (Math.random() - 0.5) * 0.003
      const lng = base.lng + (Math.random() - 0.5) * 0.004

      const seedSensor = {
        ...(sensor ?? { time: new Date().toISOString(), speed_kmh: 0,
          battery_level_pct: 80, battery_voltage_v: null,
          battery_temp_celsius: null, engine_rpm: null, odometer_km: null }),
        latitude:  lat,
        longitude: lng,
      }

      updateRealtimeLocation(v.id, seedSensor)

      // 이력도 새 위치 기준으로 재생성
      const initPoints = v.status === "RUNNING" ? 30 : v.status === "ALERT" ? 15 : 3
      const next = new Map(positionHistory.value)
      next.set(v.id, buildInitialHistory(lat, lng, initPoints))
      positionHistory.value = next
    }

    _simTimer.value = setInterval(() => {
      for (const v of vehicles.value) {
        if (v.status !== "RUNNING" && v.status !== "ALERT") continue

        const raw = realtimeLocations.value.get(v.id) ?? v.latest_sensor
        if (!raw?.latitude || !raw?.longitude) continue

        // 현재 위치가 물 위라면 먼저 육지로 이동
        const { lat: curLat, lng: curLng } = _snapToLand(raw.latitude, raw.longitude)
        const sensor = { ...raw, latitude: curLat, longitude: curLng }

        // 방향 유지하되 조금씩 꺾기
        let heading = _simHeadings.get(v.id) ?? Math.random() * Math.PI * 2
        heading += (Math.random() - 0.5) * 0.35

        const step = 0.00011
        let newLat = curLat + Math.cos(heading) * step
        let newLng = curLng + Math.sin(heading) * step * 1.3

        // 한강 진입 시: 남북(위도) 방향 반사
        // Math.PI - heading → cos 부호 반전(남북 뒤집기), sin 유지(동서 유지)
        if (_isInWater(newLat, newLng)) {
          heading = Math.PI - heading
          newLat  = curLat + Math.cos(heading) * step
          newLng  = curLng + Math.sin(heading) * step * 1.3
        }

        // 서울 남북 경계 바운스 (남북 반사)
        if (newLat < BOUNDS.latMin || newLat > BOUNDS.latMax) {
          heading = Math.PI - heading
          newLat  = curLat + Math.cos(heading) * step
          newLng  = curLng + Math.sin(heading) * step * 1.3
        }

        // 서울 동서 경계 바운스 (동서 반사)
        if (newLng < BOUNDS.lngMin || newLng > BOUNDS.lngMax) {
          heading = -heading
          newLat  = curLat + Math.cos(heading) * step
          newLng  = curLng + Math.sin(heading) * step * 1.3
        }

        _simHeadings.set(v.id, heading)

        updateRealtimeLocation(v.id, {
          ...sensor,
          latitude:  newLat,
          longitude: newLng,
          speed_kmh: 20 + Math.random() * 20,
          time:      new Date().toISOString(),
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
    fetchVehicles, fetchVehicleDetail, refreshVehicles, updateRealtimeLocation,
    selectVehicle, clearSelectedVehicle,
    startDemoSimulation, stopDemoSimulation,
  }
})
