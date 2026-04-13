# 프론트엔드 아키텍처 정의서 (Frontend Architecture)

**프로젝트**: 지능형 오토바이 FMS  
**버전**: v1.0 | **작성일**: 2026-04-13  
**기술 스택**: Vue 3.4, Vite 5, TypeScript 5.4, TailwindCSS v3, Pinia 2.x, Vue Router 4

---

## 1. 아키텍처 원칙

| 원칙 | 내용 |
|---|---|
| **Composition API 전용** | `<script setup>` 문법 통일. Options API 사용 금지 |
| **단방향 데이터 흐름** | Store → View → Component. 컴포넌트는 Store를 직접 변이하지 않음 |
| **도메인 분리** | Store, API 서비스, 타입은 도메인별로 파일 분리 |
| **Composable 우선** | 재사용 로직은 반드시 `use*` Composable로 추출 |
| **타입 안전** | `any` 사용 금지. 모든 API 응답은 TypeScript 타입 정의 |

---

## 2. 디렉터리 구조

```
src/
├── main.ts                        # 앱 진입점 (app 생성, 플러그인 등록)
├── App.vue                        # 루트 컴포넌트 (RouterView + Toast 전역)
│
├── router/
│   ├── index.ts                   # Vue Router 설정, 전역 가드
│   └── guards/
│       ├── authGuard.ts           # 인증 필요 라우트 보호
│       └── roleGuard.ts           # 역할 기반 라우트 제한
│
├── stores/                        # Pinia 도메인별 스토어
│   ├── auth/
│   │   └── useAuthStore.ts        # 인증 상태 (토큰, 사용자 정보)
│   ├── fleet/
│   │   └── useFleetStore.ts       # 차량 목록, 선택된 차량 상태
│   ├── realtime/
│   │   └── useRealtimeStore.ts    # WebSocket 연결, 실시간 위치/상태
│   ├── alert/
│   │   └── useAlertStore.ts       # 알림 목록, 미처리 카운트
│   └── ui/
│       └── useUIStore.ts          # 사이드바 접힘, 전역 로딩, Toast 큐
│
├── services/                      # API 통신 계층 (Axios 기반)
│   ├── http.ts                    # Axios 인스턴스 + 인터셉터
│   ├── authService.ts
│   ├── vehicleService.ts
│   ├── sensorService.ts
│   ├── alertService.ts
│   ├── tripService.ts
│   └── chargingStationService.ts
│
├── composables/                   # 재사용 가능한 로직 훅
│   ├── useRealtimeVehicle.ts      # WebSocket 구독 + 실시간 상태 바인딩
│   ├── useNearbyStations.ts       # 근처 충전소 조회 훅
│   ├── useInfiniteAlerts.ts       # Cursor 기반 무한 스크롤 알림 목록
│   ├── useSensorStream.ts         # 센서 데이터 시계열 스트림
│   ├── useAuth.ts                 # 로그인/로그아웃/토큰 갱신 래퍼
│   └── useToast.ts                # 전역 Toast 알림 발송
│
├── types/                         # TypeScript 타입 정의
│   ├── api.ts                     # 공통 API 응답 타입 (SuccessResponse, ErrorResponse)
│   ├── vehicle.ts
│   ├── sensor.ts
│   ├── alert.ts
│   ├── trip.ts
│   ├── auth.ts
│   └── chargingStation.ts
│
├── views/                         # 페이지 단위 컴포넌트 (Vue Router 대상)
│   ├── auth/
│   │   └── LoginView.vue
│   ├── dashboard/
│   │   └── DashboardView.vue      # 메인 관제 화면 (지도 + 우측 패널)
│   ├── vehicles/
│   │   ├── VehicleListView.vue    # 차량 목록
│   │   └── VehicleDetailView.vue  # 차량 상세 + 운행 이력
│   ├── alerts/
│   │   └── AlertManagementView.vue # 알림 관리
│   ├── trips/
│   │   └── TripHistoryView.vue    # 운행 이력 조회
│   └── errors/
│       ├── NotFoundView.vue
│       └── ForbiddenView.vue
│
└── components/                    # 재사용 UI 컴포넌트
    ├── common/                    # Atoms — 원자 단위
    │   ├── BaseButton.vue
    │   ├── BaseInput.vue
    │   ├── BaseSelect.vue
    │   ├── BaseModal.vue
    │   ├── BaseCard.vue
    │   ├── StatusBadge.vue
    │   ├── LoadingSpinner.vue
    │   ├── EmptyState.vue         # 데이터 없음 상태
    │   └── ErrorState.vue         # API 에러 상태
    │
    ├── layout/                    # 레이아웃
    │   ├── AppLayout.vue          # Sidebar + TopNav 감싸는 Shell
    │   ├── TopNav.vue
    │   └── SideNav.vue
    │
    ├── map/                       # 지도 관련 Molecules
    │   ├── FleetMap.vue           # 전체 지도 (Kakao Maps)
    │   ├── VehicleMarker.vue      # 차량 핀 마커
    │   ├── StationMarker.vue      # 충전소 핀 마커
    │   └── RoutePolyline.vue      # 경로 선
    │
    ├── vehicle/                   # 차량 관련 Molecules / Organisms
    │   ├── VehicleListItem.vue    # 목록 한 행
    │   ├── VehicleStatusCard.vue  # 우측 패널 상세 카드
    │   ├── BatteryGauge.vue       # 배터리 게이지 바
    │   └── SpeedIndicator.vue     # 속도계
    │
    ├── alert/
    │   ├── AlertListItem.vue      # 알림 한 행
    │   ├── AlertBanner.vue        # 실시간 경고 배너 (슬라이드인)
    │   └── AlertDetailModal.vue   # 알림 상세 모달
    │
    └── sensor/
        ├── SensorChart.vue        # 시계열 ECharts 차트
        └── TripRouteMap.vue       # 단일 운행 경로 지도
```

---

## 3. Pinia 스토어 상세 정의

### 3.1 `useAuthStore` — 인증

```typescript
// src/stores/auth/useAuthStore.ts
import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { authService } from "@/services/authService"
import type { User, LoginPayload } from "@/types/auth"

export const useAuthStore = defineStore("auth", () => {

  // ── State ────────────────────────────────────────────────────────
  const accessToken = ref<string | null>(localStorage.getItem("access_token"))
  const currentUser = ref<User | null>(null)
  const isLoading   = ref(false)

  // ── Getters ──────────────────────────────────────────────────────
  const isAuthenticated = computed(() => !!accessToken.value)
  const isAdmin         = computed(() => currentUser.value?.role === "ADMIN")
  const isManager       = computed(() => ["ADMIN", "MANAGER"].includes(currentUser.value?.role ?? ""))

  // ── Actions ──────────────────────────────────────────────────────
  async function login(payload: LoginPayload): Promise<void> {
    isLoading.value = true
    try {
      const res = await authService.login(payload)
      accessToken.value = res.access_token
      currentUser.value = res.user
      localStorage.setItem("access_token", res.access_token)
    } finally {
      isLoading.value = false
    }
  }

  async function refresh(): Promise<void> {
    const res = await authService.refresh()
    accessToken.value = res.access_token
    localStorage.setItem("access_token", res.access_token)
  }

  async function logout(): Promise<void> {
    await authService.logout()
    accessToken.value = null
    currentUser.value = null
    localStorage.removeItem("access_token")
  }

  async function fetchMe(): Promise<void> {
    /**
     * GET /auth/me — 현재 토큰의 사용자 정보를 서버에서 조회합니다.
     * refresh() 후 또는 페이지 새로고침 시 currentUser 복원에 사용합니다.
     */
    const res = await authService.me()
    currentUser.value = res
  }

  function setAccessToken(token: string) {
    accessToken.value = token
    localStorage.setItem("access_token", token)
  }

  return { accessToken, currentUser, isLoading,
           isAuthenticated, isAdmin, isManager,
           login, refresh, logout, fetchMe, setAccessToken }
})
```

---

### 3.2 `useFleetStore` — 차량 관리

```typescript
// src/stores/fleet/useFleetStore.ts
import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { vehicleService } from "@/services/vehicleService"
import type { Vehicle, VehicleListParams } from "@/types/vehicle"

export const useFleetStore = defineStore("fleet", () => {

  // ── State ────────────────────────────────────────────────────────
  const vehicles        = ref<Vehicle[]>([])
  const selectedVehicle = ref<Vehicle | null>(null)
  const totalCount      = ref(0)
  const isLoading       = ref(false)
  const error           = ref<string | null>(null)
  const filters = ref<VehicleListParams>({
    status: [],
    page: 1,
    limit: 20,
    sort_by: "created_at",
    order: "desc",
  })

  // ── Getters ──────────────────────────────────────────────────────
  const activeVehicles  = computed(() =>
    vehicles.value.filter(v => v.status === "ACTIVE"))
  const criticalVehicles = computed(() =>
    vehicles.value.filter(v => v.last_state?.soc_pct != null &&
                               v.last_state.soc_pct <= 20))

  // ── Actions ──────────────────────────────────────────────────────
  async function fetchVehicles(): Promise<void> {
    isLoading.value = true
    error.value = null
    try {
      const res = await vehicleService.getList(filters.value)
      vehicles.value  = res.items
      totalCount.value = res.pagination.total
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : "알 수 없는 오류가 발생했습니다."
    } finally {
      isLoading.value = false
    }
  }

  async function selectVehicle(vehicleId: string): Promise<void> {
    isLoading.value = true
    try {
      selectedVehicle.value = await vehicleService.getById(vehicleId)
    } finally {
      isLoading.value = false
    }
  }

  function updateVehicleState(vehicleId: string, state: Partial<Vehicle["last_state"]>) {
    // WebSocket 실시간 업데이트를 Store에 반영
    const target = vehicles.value.find(v => v.id === vehicleId)
    if (target?.last_state) {
      Object.assign(target.last_state, state)
    }
    if (selectedVehicle.value?.id === vehicleId && selectedVehicle.value.last_state) {
      Object.assign(selectedVehicle.value.last_state, state)
    }
  }

  return {
    vehicles, selectedVehicle, totalCount, isLoading, error, filters,
    activeVehicles, criticalVehicles,
    fetchVehicles, selectVehicle, updateVehicleState,
  }
})
```

---

### 3.3 `useRealtimeStore` — WebSocket 실시간

```typescript
// src/stores/realtime/useRealtimeStore.ts
import { defineStore } from "pinia"
import { ref } from "vue"
import { io, Socket } from "socket.io-client"
import { useAuthStore } from "@/stores/auth/useAuthStore"
import { useFleetStore } from "@/stores/fleet/useFleetStore"
import { useAlertStore } from "@/stores/alert/useAlertStore"

export const useRealtimeStore = defineStore("realtime", () => {

  const socket          = ref<Socket | null>(null)
  const isConnected     = ref(false)
  const connectionError = ref<string | null>(null)

  function connect(vehicleIds: string[]): void {
    // 중복 연결 방어: 이미 연결 중이면 구독 목록만 갱신
    if (socket.value?.connected) {
      socket.value.emit("SUBSCRIBE", { vehicleIds })
      return
    }

    const authStore = useAuthStore()
    socket.value = io(import.meta.env.VITE_WS_URL, {
      auth: { token: authStore.accessToken },
      transports: ["websocket"],
      reconnection: true,
      reconnectionDelay: 2000,
      reconnectionAttempts: 10,
    })

    socket.value.on("connect", () => {
      isConnected.value = true
      connectionError.value = null
      // 관심 차량 구독 등록
      socket.value?.emit("SUBSCRIBE", { vehicleIds })
    })

    socket.value.on("disconnect", () => {
      isConnected.value = false
    })

    socket.value.on("connect_error", (err) => {
      connectionError.value = err.message
    })

    // ── 이벤트 핸들러 등록 ────────────────────────────────────────
    const fleetStore = useFleetStore()
    const alertStore = useAlertStore()

    socket.value.on("VEHICLE_LOCATION_UPDATE", (payload) => {
      fleetStore.updateVehicleState(payload.vehicleId, {
        latitude: payload.payload.lat,
        longitude: payload.payload.lng,
        speed_kmh: payload.payload.speedKmh,
        soc_pct: payload.payload.socPct,
        updated_at: payload.ts,
      })
    })

    socket.value.on("ALERT_OVERSPEED", (payload) => {
      alertStore.addRealtimeAlert(payload)
    })

    socket.value.on("ALERT_BATTERY_REPLACE", (payload) => {
      alertStore.addRealtimeAlert(payload)
    })
  }

  function disconnect(): void {
    socket.value?.disconnect()
    socket.value = null
    isConnected.value = false
  }

  return { isConnected, connectionError, connect, disconnect }
})
```

---

### 3.4 `useAlertStore` — 알림 관리

```typescript
// src/stores/alert/useAlertStore.ts
import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { alertService } from "@/services/alertService"
import type { Alert, AlertListParams } from "@/types/alert"

export const useAlertStore = defineStore("alert", () => {

  const alerts         = ref<Alert[]>([])
  const realtimeQueue  = ref<Alert[]>([])   // 실시간 Push 수신 큐
  const nextCursor     = ref<string | null>(null)
  const hasNext        = ref(false)
  const isLoading      = ref(false)

  const unresolvedCount = computed(() =>
    alerts.value.filter(a => !a.is_resolved).length)

  const criticalAlerts = computed(() =>
    realtimeQueue.value.filter(a => a.severity === "CRITICAL"))

  async function fetchAlerts(params: AlertListParams, reset = false): Promise<void> {
    isLoading.value = true
    try {
      const res = await alertService.getList({
        ...params,
        cursor: reset ? undefined : (nextCursor.value ?? undefined),
      })
      if (reset) {
        alerts.value = res.items
      } else {
        alerts.value.push(...res.items)
      }
      nextCursor.value = res.pagination.next_cursor
      hasNext.value    = res.pagination.has_next
    } finally {
      isLoading.value = false
    }
  }

  function addRealtimeAlert(alert: Alert): void {
    realtimeQueue.value.unshift(alert)
    alerts.value.unshift(alert)
    // 큐는 최대 20개 유지
    if (realtimeQueue.value.length > 20) {
      realtimeQueue.value.pop()
    }
  }

  async function resolveAlert(alertId: string): Promise<void> {
    const resolved = await alertService.resolve(alertId)
    const idx = alerts.value.findIndex(a => a.id === alertId)
    if (idx !== -1) alerts.value[idx] = resolved
    realtimeQueue.value = realtimeQueue.value.filter(a => a.id !== alertId)
  }

  return {
    alerts, realtimeQueue, nextCursor, hasNext, isLoading,
    unresolvedCount, criticalAlerts,
    fetchAlerts, addRealtimeAlert, resolveAlert,
  }
})
```

---

## 4. HTTP 서비스 계층

### 4.1 Axios 인스턴스 — `services/http.ts`

```typescript
// src/services/http.ts
import axios, { type AxiosInstance, type AxiosError } from "axios"

let httpInstance: AxiosInstance | null = null

export function createHttp(): AxiosInstance {
  if (httpInstance) return httpInstance

  httpInstance = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL,
    timeout: 15_000,
    withCredentials: true,    // RefreshToken Cookie 포함
    headers: { "Content-Type": "application/json" },
  })

  // ── Request 인터셉터: Access Token 주입 ──────────────────────────
  httpInstance.interceptors.request.use((config) => {
    const token = localStorage.getItem("access_token")
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  })

  // ── Response 인터셉터: 토큰 만료 자동 갱신 ──────────────────────
  /**
   * 인터셉터는 response.data (파싱된 JSON 전체 = { success, data, meta })를 반환.
   * 따라서 서비스 코드에서: const res = await http.get(...)
   *   → res      = { success: true, data: { items, pagination }, meta: {...} }
   *   → res.data = { items: [...], pagination: {...} }  ← 실제 페이로드
   */
  httpInstance.interceptors.response.use(
    (response) => response.data,
    async (error: AxiosError<{ error: { code: string } }>) => {
      const code = error.response?.data?.error?.code
      // _retry 타입은 axios.d.ts 모듈 보강으로 선언 (src/types/axios.d.ts 참고)
      if (code === "TOKEN_EXPIRED" && !error.config?._retry) {
        error.config!._retry = true
        try {
          const res = await httpInstance!.post<{ data: { access_token: string } }>(
            "/v1/auth/refresh"
          )
          const newToken = res.data.access_token
          localStorage.setItem("access_token", newToken)
          error.config!.headers!["Authorization"] = `Bearer ${newToken}`
          return httpInstance!(error.config!)
        } catch {
          localStorage.removeItem("access_token")
          window.location.href = "/login"
        }
      }
      return Promise.reject(error)
    }
  )

  return httpInstance
}

export const http = createHttp()
```

---

### 4.2 서비스 예시 — `services/vehicleService.ts`

```typescript
// src/services/vehicleService.ts
import { http } from "./http"
import type { Vehicle, VehicleListResponse, VehicleListParams } from "@/types/vehicle"

/**
 * http 인터셉터가 response.data(= { success, data, meta }) 를 반환하므로
 * res.data 로 실제 페이로드에 접근합니다.
 * 예: res = { success: true, data: { items, pagination }, meta }
 *     res.data = { items, pagination }
 */
export const vehicleService = {
  async getList(params: VehicleListParams): Promise<VehicleListResponse> {
    const res = await http.get<{ data: VehicleListResponse }>("/v1/vehicles", { params })
    return res.data
  },
  async getById(id: string): Promise<Vehicle> {
    const res = await http.get<{ data: Vehicle }>(`/v1/vehicles/${id}`)
    return res.data
  },
  async create(payload: Partial<Vehicle>): Promise<Vehicle> {
    const res = await http.post<{ data: Vehicle }>("/v1/vehicles", payload)
    return res.data
  },
  async update(id: string, payload: Partial<Vehicle>): Promise<Vehicle> {
    const res = await http.put<{ data: Vehicle }>(`/v1/vehicles/${id}`, payload)
    return res.data
  },
  async softDelete(id: string): Promise<{ deleted_at: string }> {
    const res = await http.delete<{ data: { deleted_at: string } }>(`/v1/vehicles/${id}`)
    return res.data
  },
}
```

---

## 5. 라우터 및 가드

```typescript
// src/router/index.ts
import { createRouter, createWebHistory } from "vue-router"
import { authGuard } from "./guards/authGuard"
import { roleGuard } from "./guards/roleGuard"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: () => import("@/views/auth/LoginView.vue"), meta: { public: true } },

    {
      path: "/",
      component: () => import("@/components/layout/AppLayout.vue"),
      meta: { requiresAuth: true },
      children: [
        { path: "",          redirect: "/dashboard" },
        { path: "dashboard", component: () => import("@/views/dashboard/DashboardView.vue") },
        { path: "vehicles",  component: () => import("@/views/vehicles/VehicleListView.vue") },
        {
          path: "vehicles/:id",
          component: () => import("@/views/vehicles/VehicleDetailView.vue"),
        },
        {
          path: "alerts",
          component: () => import("@/views/alerts/AlertManagementView.vue"),
          meta: { roles: ["ADMIN", "MANAGER"] },
        },
        { path: "trips",     component: () => import("@/views/trips/TripHistoryView.vue") },
      ],
    },

    { path: "/403", component: () => import("@/views/errors/ForbiddenView.vue") },
    { path: "/:pathMatch(.*)*", component: () => import("@/views/errors/NotFoundView.vue") },
  ],
})

router.beforeEach(authGuard)
router.beforeEach(roleGuard)

export default router
```

```typescript
// src/router/guards/authGuard.ts
import type { NavigationGuardNext, RouteLocationNormalized } from "vue-router"
import { useAuthStore } from "@/stores/auth/useAuthStore"

export async function authGuard(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
) {
  if (to.meta.public) return next()

  const auth = useAuthStore()
  if (!auth.isAuthenticated) {
    return next({ path: "/login", query: { redirect: to.fullPath } })
  }

  // 사용자 정보 미로드 시 복원 (토큰은 있지만 새로고침 등으로 currentUser가 null인 경우)
  if (!auth.currentUser) {
    try {
      // refresh()는 새 accessToken만 발급. currentUser 복원을 위해 /auth/me 추가 호출 필요.
      await auth.refresh()
      await auth.fetchMe()   // GET /auth/me → currentUser 세팅
    } catch {
      return next({ path: "/login" })
    }
  }

  next()
}
```

---

## 6. 주요 View 컴포넌트 구조

### 6.1 `DashboardView.vue` — 메인 관제 화면

```
DashboardView
├── FleetMap          (지도 전체 영역, 차량 마커, 충전소 핀)
├── VehicleListPanel  (좌측 또는 하단 — 차량 목록 + 필터)
│   └── VehicleListItem × N
├── VehicleStatusPanel (우측 슬라이드 — 선택 차량 상세)
│   ├── VehicleStatusCard
│   ├── BatteryGauge
│   ├── SpeedIndicator
│   └── RecentAlertList
│       └── AlertListItem × N
└── AlertBanner       (상단 고정 — 실시간 CRITICAL 경고)
```

### 6.2 컴포넌트 Props/Emits 규약

```typescript
// 모든 컴포넌트는 다음 규약을 따름

// Props — defineProps로 명시적 타입 선언
const props = defineProps<{
  vehicleId: string
  isLoading?: boolean
}>()

// Emits — defineEmits로 이벤트 명세
const emit = defineEmits<{
  select:  [vehicleId: string]
  refresh: []
}>()

// v-model 지원 컴포넌트는 modelValue / update:modelValue 컨벤션 준수
```

---

## 6. 누락 보완: 핵심 구현체 정의

### 6.1 `useUIStore` — 전역 UI 상태

```typescript
// src/stores/ui/useUIStore.ts
import { defineStore } from "pinia"
import { ref } from "vue"

export interface ToastItem {
  id: string
  type: "success" | "info" | "warning" | "error"
  message: string
  duration: number   // ms
}

export const useUIStore = defineStore("ui", () => {
  const isSidebarCollapsed = ref(false)
  const isGlobalLoading    = ref(false)
  const toastQueue         = ref<ToastItem[]>([])

  function toggleSidebar() {
    isSidebarCollapsed.value = !isSidebarCollapsed.value
  }

  function addToast(item: Omit<ToastItem, "id">): string {
    const id = `toast_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`
    toastQueue.value.push({ ...item, id })
    // duration 후 자동 제거
    setTimeout(() => removeToast(id), item.duration)
    return id
  }

  function removeToast(id: string) {
    toastQueue.value = toastQueue.value.filter(t => t.id !== id)
  }

  return {
    isSidebarCollapsed, isGlobalLoading, toastQueue,
    toggleSidebar, addToast, removeToast,
  }
})
```

---

### 6.2 `useToast` — Toast 발송 Composable

```typescript
// src/composables/useToast.ts
import { useUIStore } from "@/stores/ui/useUIStore"

const DURATIONS = { success: 3000, info: 3000, warning: 5000, error: 7000 }

export function useToast() {
  const uiStore = useUIStore()

  return {
    success: (message: string) =>
      uiStore.addToast({ type: "success", message, duration: DURATIONS.success }),
    info: (message: string) =>
      uiStore.addToast({ type: "info", message, duration: DURATIONS.info }),
    warning: (message: string) =>
      uiStore.addToast({ type: "warning", message, duration: DURATIONS.warning }),
    error: (message: string) =>
      uiStore.addToast({ type: "error", message, duration: DURATIONS.error }),
  }
}
```

---

### 6.3 `roleGuard.ts` — 역할 기반 라우트 가드

```typescript
// src/router/guards/roleGuard.ts
import type { NavigationGuardNext, RouteLocationNormalized } from "vue-router"
import { useAuthStore } from "@/stores/auth/useAuthStore"

export function roleGuard(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
) {
  const requiredRoles = to.meta.roles as string[] | undefined
  if (!requiredRoles || requiredRoles.length === 0) return next()

  const auth = useAuthStore()
  const userRole = auth.currentUser?.role

  if (!userRole || !requiredRoles.includes(userRole)) {
    return next({ path: "/403" })
  }

  next()
}
```

---

### 6.4 Axios `_retry` 타입 확장

```typescript
// src/types/axios.d.ts
// Axios InternalAxiosRequestConfig에 _retry 프로퍼티를 추가합니다.
import "axios"

declare module "axios" {
  export interface InternalAxiosRequestConfig {
    _retry?: boolean
  }
}
```

> `src/main.ts` 또는 `src/services/http.ts`에서 이 파일이 TypeScript에 포함되도록  
> `tsconfig.json`의 `include` 배열에 `"src/types/**/*.d.ts"`가 있는지 확인하세요.

---

## 7. 환경 변수 관리

```bash
# .env.development
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8001
VITE_KAKAO_MAP_KEY=dev_key_here

# .env.production
VITE_API_BASE_URL=https://api.bikefms.io
VITE_WS_URL=wss://ws.bikefms.io
VITE_KAKAO_MAP_KEY=prod_key_here
```

> 모든 환경 변수는 `src/env.d.ts`에 타입 선언 필수:
> ```typescript
> interface ImportMetaEnv {
>   readonly VITE_API_BASE_URL: string
>   readonly VITE_WS_URL: string
>   readonly VITE_KAKAO_MAP_KEY: string
> }
> ```
