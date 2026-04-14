import { onMounted, onUnmounted } from "vue"
import { useFleetStore } from "@/stores/fleet"
import { useAlertStore } from "@/stores/alert"
import { useRealtimeStore } from "@/stores/realtime"

/**
 * useRealtime — 단기 폴링 composable
 *
 * 컴포넌트가 mount되면 intervalMs마다 차량·알림을 백그라운드로 갱신합니다.
 * unmount 시 인터벌을 자동으로 정리합니다.
 *
 * @param intervalMs  폴링 간격(ms). 기본 2500ms
 */
export function useRealtime(intervalMs = 2500) {
  const fleetStore    = useFleetStore()
  const alertStore    = useAlertStore()
  const realtimeStore = useRealtimeStore()

  let timer: ReturnType<typeof setInterval> | null = null

  async function poll(): Promise<void> {
    await Promise.all([
      fleetStore.refreshVehicles(),
      alertStore.refreshAlerts(),
    ])
  }

  onMounted(() => {
    realtimeStore.setConnected(true)
    timer = setInterval(poll, intervalMs)
  })

  onUnmounted(() => {
    if (timer !== null) {
      clearInterval(timer)
      timer = null
    }
    realtimeStore.setConnected(false)
  })

  return { poll }
}
