import { ref } from "vue"
import { defineStore } from "pinia"
import type { WsBatteryPayload } from "@/types/models"

export type ToastType = "success" | "warning" | "error" | "info"

export interface ToastItem {
  id:       string
  type:     ToastType
  message:  string
  duration: number
}

export const useUIStore = defineStore("ui", () => {
  // ── State ─────────────────────────────────────────────────
  const isSidebarCollapsed    = ref(false)
  const isGlobalLoading       = ref(false)
  const toastQueue            = ref<ToastItem[]>([])
  const batteryModalPayload   = ref<WsBatteryPayload | null>(null)
  const showTokenExpiredModal = ref(false)

  // ── Actions ───────────────────────────────────────────────
  function addToast(item: Omit<ToastItem, "id">): string {
    const id = `toast_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
    toastQueue.value.push({ ...item, id })
    setTimeout(() => removeToast(id), item.duration)
    return id
  }

  function removeToast(id: string): void {
    toastQueue.value = toastQueue.value.filter(t => t.id !== id)
  }

  function openBatteryModal(payload: WsBatteryPayload): void {
    batteryModalPayload.value = payload
  }

  function closeBatteryModal(): void {
    batteryModalPayload.value = null
  }

  function toggleSidebar(): void {
    isSidebarCollapsed.value = !isSidebarCollapsed.value
  }

  function setTokenExpired(value: boolean): void {
    showTokenExpiredModal.value = value
  }

  return {
    isSidebarCollapsed, isGlobalLoading, toastQueue, batteryModalPayload, showTokenExpiredModal,
    addToast, removeToast, openBatteryModal, closeBatteryModal, toggleSidebar, setTokenExpired,
  }
})
