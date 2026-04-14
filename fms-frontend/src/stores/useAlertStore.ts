import { ref } from "vue"
import { defineStore } from "pinia"

// ── 타입 정의 ──────────────────────────────────────────────────
export type SimSeverity  = "danger" | "warning" | "info"

export type SimAlertType =
  | "OVERSPEED"
  | "BATTERY_LOW"
  | "BATTERY_CRITICAL"
  | "GEOFENCE_EXIT"
  | "SUDDEN_ACCEL"

export interface SimAlert {
  /** crypto.randomUUID()로 생성된 고유 ID */
  id:        string
  vehicleId: string
  plate:     string
  type:      SimAlertType
  severity:  SimSeverity
  title:     string
  /** Date.now() 타임스탬프 — 상대 시간 포맷에 사용 */
  createdAt: number
}

// ── 상수 ───────────────────────────────────────────────────────
const MAX_ALERTS = 10

// ── 스토어 ─────────────────────────────────────────────────────
export const useAlertStore = defineStore("sim-alert", () => {

  // ── State ─────────────────────────────────────────────────
  const alerts = ref<SimAlert[]>([])

  // ── Getters ───────────────────────────────────────────────
  /** 가장 최근 위험(danger) 알림 */
  const latestDanger = () =>
    alerts.value.find(a => a.severity === "danger") ?? null

  // ── Actions ───────────────────────────────────────────────

  /**
   * 새 알림을 큐 앞에 추가한다.
   * MAX_ALERTS 초과 시 가장 오래된 항목을 자동으로 제거한다.
   */
  function addAlert(payload: Omit<SimAlert, "id" | "createdAt">): void {
    const newAlert: SimAlert = {
      ...payload,
      id:        crypto.randomUUID(),
      createdAt: Date.now(),
    }
    alerts.value = [newAlert, ...alerts.value].slice(0, MAX_ALERTS)
  }

  /** 알림 전체 삭제 */
  function clearAll(): void {
    alerts.value = []
  }

  /** 특정 알림 단건 제거 */
  function dismiss(id: string): void {
    alerts.value = alerts.value.filter(a => a.id !== id)
  }

  return {
    alerts,
    latestDanger,
    addAlert,
    clearAll,
    dismiss,
  }
})
