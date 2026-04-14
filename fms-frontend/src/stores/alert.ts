import { ref, computed } from "vue"
import { defineStore } from "pinia"
import { alertService } from "@/services/alertService"
import type { Alert } from "@/types/models"

export const useAlertStore = defineStore("alert", () => {
  // ── State ────────────────────────────────────────────────
  const alerts        = ref<Alert[]>([])
  const nextCursor    = ref<string | null>(null)
  const hasNext       = ref(false)
  const isLoading     = ref(false)
  const isLoadingMore = ref(false)

  // ── Getters ──────────────────────────────────────────────
  const unacknowledgedCount = computed(() =>
    alerts.value.filter(a => !a.is_acknowledged).length
  )
  const dangerAlerts = computed(() =>
    alerts.value.filter(a => a.severity === "DANGER")
  )

  // ── Actions ──────────────────────────────────────────────
  async function fetchAlerts(params?: {
    vehicle_id?:      string
    severity?:        string[]
    is_acknowledged?: boolean
  }): Promise<void> {
    isLoading.value = true
    try {
      const res       = await alertService.list({ limit: 30, ...params })
      alerts.value    = res.data
      nextCursor.value = res.meta.next_cursor
      hasNext.value    = res.meta.has_next
    } finally {
      isLoading.value = false
    }
  }

  async function loadMore(): Promise<void> {
    if (!hasNext.value || isLoadingMore.value) return
    isLoadingMore.value = true
    try {
      const res        = await alertService.list({ limit: 30, cursor: nextCursor.value ?? undefined })
      alerts.value     = [...alerts.value, ...res.data]
      nextCursor.value = res.meta.next_cursor
      hasNext.value    = res.meta.has_next
    } finally {
      isLoadingMore.value = false
    }
  }

  async function acknowledge(alertId: string): Promise<void> {
    const updated = await alertService.acknowledge(alertId)
    const idx = alerts.value.findIndex(a => a.id === alertId)
    if (idx !== -1) alerts.value[idx] = updated
  }

  function prependAlert(newAlert: Alert): void {
    // WebSocket ALERT_TRIGGERED 수신 시 목록 최상단 삽입
    alerts.value = [newAlert, ...alerts.value]
  }

  return {
    alerts, nextCursor, hasNext, isLoading, isLoadingMore,
    unacknowledgedCount, dangerAlerts,
    fetchAlerts, loadMore, acknowledge, prependAlert,
  }
})
