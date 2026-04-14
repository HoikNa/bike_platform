import { ref } from "vue"
import { defineStore } from "pinia"
import { io, type Socket } from "socket.io-client"
import { useAuthStore } from "./auth"
import { useFleetStore } from "./fleet"
import { useAlertStore } from "./alert"
import { useUIStore } from "./ui"
import type { WsLocationPayload, WsBatteryPayload, Alert } from "@/types/models"

export const useRealtimeStore = defineStore("realtime", () => {
  const socket        = ref<Socket | null>(null)
  const isConnected   = ref(false)
  const subscribedIds = ref<Set<string>>(new Set())

  function connect(vehicleIds: string[]): void {
    const auth = useAuthStore()

    // 이미 연결된 경우 구독만 추가
    if (socket.value?.connected) {
      socket.value.emit("SUBSCRIBE", { vehicle_ids: vehicleIds })
      vehicleIds.forEach(id => subscribedIds.value.add(id))
      return
    }

    socket.value = io(
      `${import.meta.env.VITE_WS_BASE_URL ?? "http://localhost:8000"}/realtime`,
      {
        auth: { token: auth.accessToken },
        transports: ["websocket"],
        reconnectionAttempts: 5,
        reconnectionDelay: 2000,
      }
    )

    // ── 시스템 이벤트 ─────────────────────────────────────
    socket.value.on("connect", () => {
      isConnected.value = true
      socket.value!.emit("SUBSCRIBE", { vehicle_ids: vehicleIds })
      vehicleIds.forEach(id => subscribedIds.value.add(id))
    })

    socket.value.on("disconnect", () => {
      isConnected.value = false
    })

    socket.value.on("error", (err: { code: string }) => {
      if (err.code === "TOKEN_EXPIRED") disconnect()
    })

    // ── 도메인 이벤트 ─────────────────────────────────────
    socket.value.on("VEHICLE_LOCATION_UPDATE", (payload: WsLocationPayload) => {
      useFleetStore().updateRealtimeLocation(payload.vehicle_id, {
        time:                 payload.timestamp,
        latitude:             payload.latitude,
        longitude:            payload.longitude,
        speed_kmh:            payload.speed_kmh,
        battery_level_pct:    payload.battery_level_pct,
        battery_voltage_v:    null,
        battery_temp_celsius: null,
        engine_rpm:           null,
        odometer_km:          null,
      })
    })

    socket.value.on("ALERT_TRIGGERED", (payload: Alert) => {
      useAlertStore().prependAlert(payload)
      useUIStore().addToast({
        type:     payload.severity === "DANGER" ? "error" : "warning",
        message:  payload.title,
        duration: payload.severity === "DANGER" ? 7000 : 5000,
      })
    })

    socket.value.on("BATTERY_REPLACE_REQUIRED", (payload: WsBatteryPayload) => {
      useUIStore().openBatteryModal(payload)
    })

    socket.value.on("VEHICLE_STATUS_CHANGED", () => {
      useFleetStore().fetchVehicles()
    })
  }

  function disconnect(): void {
    socket.value?.disconnect()
    socket.value     = null
    isConnected.value    = false
    subscribedIds.value  = new Set()
  }

  function subscribe(vehicleIds: string[]): void {
    if (!socket.value?.connected) return
    socket.value.emit("SUBSCRIBE", { vehicle_ids: vehicleIds })
    vehicleIds.forEach(id => subscribedIds.value.add(id))
  }

  function unsubscribe(vehicleIds: string[]): void {
    if (!socket.value?.connected) return
    socket.value.emit("UNSUBSCRIBE", { vehicle_ids: vehicleIds })
    vehicleIds.forEach(id => subscribedIds.value.delete(id))
  }

  return {
    socket, isConnected, subscribedIds,
    connect, disconnect, subscribe, unsubscribe,
  }
})
