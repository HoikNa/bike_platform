import { ref, computed } from "vue"
import { defineStore } from "pinia"
import { vehicleService } from "@/services/vehicleService"
import type { Vehicle, LatestSensor } from "@/types/models"
import type { PageMeta } from "@/types/api"

export const useFleetStore = defineStore("fleet", () => {
  // ── State ────────────────────────────────────────────────
  const vehicles          = ref<Vehicle[]>([])
  const selectedVehicle   = ref<Vehicle | null>(null)
  const pageMeta          = ref<PageMeta | null>(null)
  const isListLoading     = ref(false)
  const isDetailLoading   = ref(false)
  // vehicle_id → 최신 위치 (WebSocket 실시간 갱신)
  const realtimeLocations = ref<Map<string, LatestSensor>>(new Map())

  // ── Getters ──────────────────────────────────────────────
  const vehicleById = computed(() =>
    (id: string) => vehicles.value.find(v => v.id === id) ?? null
  )
  const alertVehicles   = computed(() => vehicles.value.filter(v => v.status === "ALERT"))
  const offlineVehicles = computed(() => vehicles.value.filter(v => v.status === "OFFLINE"))
  const runningCount    = computed(() => vehicles.value.filter(v => v.status === "RUNNING").length)

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
    // Map 교체로 Vue reactivity 트리거
    const next = new Map(realtimeLocations.value)
    next.set(vehicleId, sensor)
    realtimeLocations.value = next
  }

  function clearSelectedVehicle(): void {
    selectedVehicle.value = null
  }

  return {
    vehicles, selectedVehicle, pageMeta, isListLoading, isDetailLoading, realtimeLocations,
    vehicleById, alertVehicles, offlineVehicles, runningCount,
    fetchVehicles, fetchVehicleDetail, updateRealtimeLocation, clearSelectedVehicle,
  }
})
