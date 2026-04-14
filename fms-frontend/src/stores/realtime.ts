import { ref } from "vue"
import { defineStore } from "pinia"

/**
 * realtime.ts — 실시간 연결 상태 스토어
 *
 * WebSocket 대신 단기 폴링(useRealtime composable)을 사용하므로,
 * 이 스토어는 연결 상태 플래그만 관리합니다.
 * 헤더의 "실시간 / 오프라인" 인디케이터가 이 값을 참조합니다.
 */
export const useRealtimeStore = defineStore("realtime", () => {
  const isConnected = ref(false)

  function setConnected(value: boolean): void {
    isConnected.value = value
  }

  return { isConnected, setConnected }
})
