import { onUnmounted } from "vue"
import { useFleetStore } from "@/stores/useFleetStore"
import { useAlertStore } from "@/stores/useAlertStore"
import type { SimAlertType } from "@/stores/useAlertStore"

// ── 상수 ───────────────────────────────────────────────────────
const TICK_MS            = 1_500   // 1.5초마다 갱신
const OVERSPEED_KMH      = 80      // 과속 임계값
const BATTERY_LOW_PCT    = 20      // 배터리 부족 임계값
const BATTERY_CRIT_PCT   = 10      // 배터리 위험 임계값
const OVERSPEED_PROB     = 0.12    // 과속 발생 확률 (12%)
const GEOFENCE_PROB      = 0.006   // 지오펜스 이탈 확률 (0.6%)
const SUDDEN_ACCEL_PROB  = 0.010   // 급가속 확률 (1.0%)

// ── 알림 중복 방지: vehicleId → alertType → 마지막 발령 timestamp ──
const alertCooldown = new Map<string, Map<SimAlertType, number>>()

function canTrigger(
  vehicleId: string,
  type:      SimAlertType,
  cooldownMs = 30_000,
): boolean {
  const now       = Date.now()
  const byVehicle = alertCooldown.get(vehicleId) ?? new Map<SimAlertType, number>()
  const last      = byVehicle.get(type) ?? 0
  if (now - last < cooldownMs) return false
  byVehicle.set(type, now)
  alertCooldown.set(vehicleId, byVehicle)
  return true
}

// ── 컴포저블 ───────────────────────────────────────────────────
export function useSimulation() {
  const fleetStore = useFleetStore()
  const alertStore = useAlertStore()

  let timerId: ReturnType<typeof setInterval> | null = null

  // ── 단일 틱 로직 ────────────────────────────────────────────
  function tick(): void {
    fleetStore.bikes.forEach(bike => {
      // 오프라인 차량은 건너뜀
      if (bike.status === "offline") return

      // ── 충전 중 차량: 배터리만 서서히 증가 ──────────────────
      if (bike.status === "charging") {
        fleetStore.updateVehicleData(bike.id, {
          battery_level: Math.min(100, bike.battery_level + Math.random() * 0.8),
        })
        return
      }

      // ── 운행 중 / 대기 차량: 위치·속도·배터리 갱신 ──────────

      // 위치 이동 (운행 중일 때만 실질적 이동)
      const moveFactor = bike.status === "running" ? 0.0013 : 0.0002
      const newLat = bike.lat + (Math.random() - 0.5) * moveFactor
      const newLng = bike.lng + (Math.random() - 0.5) * moveFactor

      // 속도: 10% 확률로 과속 구간 진입
      const newSpeed: number = (() => {
        if (bike.status !== "running") return 0
        return Math.random() < OVERSPEED_PROB
          ? Math.round(OVERSPEED_KMH + 1 + Math.random() * 20)   // 81–100 km/h
          : Math.round(15 + Math.random() * 55)                    // 15–70 km/h
      })()

      // 배터리: 운행 중 서서히 감소
      const drainRate  = bike.status === "running" ? 0.25 : 0.05
      const newBattery = Math.max(1, bike.battery_level - Math.random() * drainRate)

      fleetStore.updateVehicleData(bike.id, {
        lat:           newLat,
        lng:           newLng,
        speed_kmh:     newSpeed,
        battery_level: newBattery,
      })

      // ── 알림 조건 평가 ───────────────────────────────────────

      // 과속
      if (newSpeed > OVERSPEED_KMH && canTrigger(bike.id, "OVERSPEED")) {
        alertStore.addAlert({
          vehicleId: bike.id,
          plate:     bike.plate_number,
          type:      "OVERSPEED",
          severity:  "danger",
          title:     `과속 감지 (${newSpeed} km/h)`,
        })
      }

      // 배터리 위험 → 부족 순으로 평가 (위험 우선)
      if (newBattery <= BATTERY_CRIT_PCT && canTrigger(bike.id, "BATTERY_CRITICAL", 60_000)) {
        alertStore.addAlert({
          vehicleId: bike.id,
          plate:     bike.plate_number,
          type:      "BATTERY_CRITICAL",
          severity:  "danger",
          title:     `배터리 위험 (${Math.round(newBattery)}%)`,
        })
      } else if (newBattery <= BATTERY_LOW_PCT && canTrigger(bike.id, "BATTERY_LOW", 45_000)) {
        alertStore.addAlert({
          vehicleId: bike.id,
          plate:     bike.plate_number,
          type:      "BATTERY_LOW",
          severity:  "warning",
          title:     `배터리 부족 (${Math.round(newBattery)}%)`,
        })
      }

      if (bike.status !== "running") return

      // 지오펜스 이탈 (낮은 확률, 60s 쿨다운)
      if (Math.random() < GEOFENCE_PROB && canTrigger(bike.id, "GEOFENCE_EXIT", 60_000)) {
        alertStore.addAlert({
          vehicleId: bike.id,
          plate:     bike.plate_number,
          type:      "GEOFENCE_EXIT",
          severity:  "warning",
          title:     "지오펜스 이탈",
        })
      }

      // 급가속 (낮은 확률, 45s 쿨다운)
      if (Math.random() < SUDDEN_ACCEL_PROB && canTrigger(bike.id, "SUDDEN_ACCEL", 45_000)) {
        alertStore.addAlert({
          vehicleId: bike.id,
          plate:     bike.plate_number,
          type:      "SUDDEN_ACCEL",
          severity:  "info",
          title:     "급가속 감지",
        })
      }
    })
  }

  // ── 생명주기 ─────────────────────────────────────────────────
  function start(): void {
    if (timerId !== null) return   // 이중 시작 방지
    tick()                         // 첫 틱 즉시 실행
    timerId = setInterval(tick, TICK_MS)
  }

  function stop(): void {
    if (timerId === null) return
    clearInterval(timerId)
    timerId = null
  }

  // 컴포넌트 언마운트 시 자동 정리
  onUnmounted(stop)

  return { start, stop }
}
