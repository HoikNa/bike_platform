import { ref, computed } from "vue"
import { defineStore } from "pinia"

// ── 타입 정의 ──────────────────────────────────────────────────
export type BikeStatus = "running" | "idle" | "charging" | "alert" | "offline"

export interface Bike {
  id:            string
  plate_number:  string
  lat:           number
  lng:           number
  battery_level: number
  speed_kmh:     number | null
  status:        BikeStatus
  driver_name:   string | null
  last_updated:  string
}

export interface PositionPoint {
  lat:       number
  lng:       number
  /** Date.now() — 12시간 필터링에 사용 */
  timestamp: number
}

// ── 상수 ───────────────────────────────────────────────────────
const HISTORY_MAX   = 80                    // 최대 보관 포인트 수
const HISTORY_HOURS = 12                    // 이력 범위 (시간)
const HISTORY_MS    = HISTORY_HOURS * 3_600_000

// ── 유틸 ───────────────────────────────────────────────────────
/** 현재 위치로부터 역방향 랜덤 워크로 12시간 이력을 생성한다. */
function buildHistory(
  endLat: number,
  endLng: number,
  points: number,
): PositionPoint[] {
  const now      = Date.now()
  const stepMs   = HISTORY_MS / (points - 1)
  const stepDeg  = 0.0035                   // 약 300m 간격 이동

  // 현재 위치부터 역방향으로 좌표 생성
  const coords: Array<{ lat: number; lng: number }> = [{ lat: endLat, lng: endLng }]
  for (let i = 1; i < points; i++) {
    const p = coords[0]
    coords.unshift({
      lat: Math.max(37.47, Math.min(37.63, p.lat + (Math.random() - 0.5) * stepDeg)),
      lng: Math.max(126.87, Math.min(127.13, p.lng + (Math.random() - 0.5) * stepDeg)),
    })
  }

  // 타임스탬프 부여 (오래된 순 → 최신 순)
  return coords.map((c, i) => ({
    ...c,
    timestamp: now - (points - 1 - i) * stepMs,
  }))
}

// ── 더미 데이터 ────────────────────────────────────────────────
// ── 더미 데이터 (성동구 집중 배치) ────────────────────────────
// 성동구 중심 약 37.555°N, 127.040°E 반경 약 1.5km 이내
const DUMMY_BIKES: Bike[] = [
  { id: "b001", plate_number: "서울 가 1234", lat: 37.5516, lng: 127.0441, battery_level: 78,  speed_kmh: 42,   status: "running",  driver_name: "김민준", last_updated: new Date().toISOString() },
  { id: "b002", plate_number: "서울 나 5678", lat: 37.5572, lng: 127.0388, battery_level: 12,  speed_kmh: 0,    status: "alert",    driver_name: "이서연", last_updated: new Date().toISOString() },
  { id: "b003", plate_number: "서울 다 9012", lat: 37.5538, lng: 127.0312, battery_level: 55,  speed_kmh: 28,   status: "running",  driver_name: "박도윤", last_updated: new Date().toISOString() },
  { id: "b004", plate_number: "서울 라 3456", lat: 37.5491, lng: 127.0502, battery_level: 91,  speed_kmh: 35,   status: "running",  driver_name: "최예린", last_updated: new Date().toISOString() },
  { id: "b005", plate_number: "서울 마 7890", lat: 37.5603, lng: 127.0355, battery_level: 27,  speed_kmh: 0,    status: "idle",     driver_name: "정하준", last_updated: new Date().toISOString() },
  { id: "b006", plate_number: "서울 바 2345", lat: 37.5477, lng: 127.0420, battery_level: 8,   speed_kmh: null, status: "charging", driver_name: null,    last_updated: new Date().toISOString() },
  { id: "b007", plate_number: "서울 사 6789", lat: 37.5558, lng: 127.0473, battery_level: 63,  speed_kmh: 19,   status: "running",  driver_name: "강지유", last_updated: new Date().toISOString() },
  { id: "b008", plate_number: "서울 아 0123", lat: 37.5524, lng: 127.0336, battery_level: 18,  speed_kmh: 0,    status: "idle",     driver_name: "윤시우", last_updated: new Date().toISOString() },
  { id: "b009", plate_number: "서울 자 4567", lat: 37.5588, lng: 127.0521, battery_level: 82,  speed_kmh: null, status: "offline",  driver_name: "임나은", last_updated: new Date(Date.now() - 30 * 60_000).toISOString() },
  { id: "b010", plate_number: "서울 차 8901", lat: 37.5505, lng: 127.0386, battery_level: 22,  speed_kmh: 51,   status: "running",  driver_name: "오준서", last_updated: new Date().toISOString() },
]

/** 상태별 초기 이력 포인트 수 */
const INIT_POINTS: Record<BikeStatus, number> = {
  running:  45,
  alert:    25,
  idle:     15,
  charging: 5,
  offline:  3,
}

// ── 스토어 ─────────────────────────────────────────────────────
export const useFleetStore = defineStore("useFleet", () => {

  // ── State ─────────────────────────────────────────────────
  const bikes          = ref<Bike[]>(DUMMY_BIKES)
  const selectedBikeId = ref<string | null>(null)

  /** 차량별 위치 이력 — 최대 HISTORY_MAX 포인트, 12시간 범위 */
  const positionHistory = ref<Record<string, PositionPoint[]>>(
    Object.fromEntries(
      DUMMY_BIKES.map(b => [
        b.id,
        buildHistory(b.lat, b.lng, INIT_POINTS[b.status]),
      ])
    )
  )

  // ── Getters ───────────────────────────────────────────────
  const runningCount  = computed(() => bikes.value.filter(b => b.status === "running").length)
  const alertCount    = computed(() => bikes.value.filter(b => b.status === "alert").length)
  const chargingCount = computed(() => bikes.value.filter(b => b.status === "charging").length)
  const offlineCount  = computed(() => bikes.value.filter(b => b.status === "offline").length)

  const lowBatteryBikes = computed(() =>
    bikes.value.filter(b => b.battery_level <= 20 && b.status !== "offline")
  )

  // ── Actions ───────────────────────────────────────────────
  function selectBike(id: string | null): void {
    selectedBikeId.value = id
  }

  /** 센서 데이터 부분 업데이트 — 위치 변경 시 이력 자동 기록 */
  function updateVehicleData(
    id: string,
    patch: Partial<Pick<Bike, "lat" | "lng" | "speed_kmh" | "battery_level" | "status">>
  ): void {
    const bike = bikes.value.find(b => b.id === id)
    if (!bike) return
    if (patch.lat           !== undefined) bike.lat           = patch.lat
    if (patch.lng           !== undefined) bike.lng           = patch.lng
    if (patch.speed_kmh     !== undefined) bike.speed_kmh     = patch.speed_kmh
    if (patch.battery_level !== undefined) bike.battery_level = patch.battery_level
    if (patch.status        !== undefined) bike.status        = patch.status
    bike.last_updated = new Date().toISOString()

    // 위치 변경 + 운행 중인 차량만 이력 추가
    if (patch.lat !== undefined && patch.lng !== undefined && bike.status === "running") {
      const prev = positionHistory.value[id] ?? []
      positionHistory.value[id] = [
        ...prev,
        { lat: patch.lat, lng: patch.lng, timestamp: Date.now() },
      ].slice(-HISTORY_MAX)
    }
  }

  return {
    bikes, selectedBikeId, positionHistory,
    runningCount, alertCount, chargingCount, offlineCount, lowBatteryBikes,
    selectBike, updateVehicleData,
  }
})
