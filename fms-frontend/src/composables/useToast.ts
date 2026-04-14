import { useUIStore } from "@/stores/ui"

/**
 * Toast 알림 단축 함수 컴포저블.
 *
 * @example
 * const toast = useToast()
 * toast.success("저장되었습니다.")
 * toast.error("오류가 발생했습니다.")
 */
export function useToast() {
  const uiStore = useUIStore()
  return {
    success: (message: string) => uiStore.addToast({ type: "success", message, duration: 3000 }),
    info:    (message: string) => uiStore.addToast({ type: "info",    message, duration: 3000 }),
    warning: (message: string) => uiStore.addToast({ type: "warning", message, duration: 5000 }),
    error:   (message: string) => uiStore.addToast({ type: "error",   message, duration: 7000 }),
  }
}
