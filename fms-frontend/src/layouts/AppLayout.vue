<template>
  <div class="flex h-screen bg-background dark:bg-secondary-900 overflow-hidden">

    <!-- ── 사이드바 ──────────────────────────────────────────── -->
    <aside
      :class="[
        'flex flex-col bg-surface dark:bg-secondary-800',
        'border-r border-secondary-200 dark:border-secondary-700',
        'transition-all duration-300 flex-shrink-0',
        uiStore.isSidebarCollapsed ? 'w-16' : 'w-60',
      ]"
    >
      <!-- 로고 -->
      <div class="flex items-center h-16 px-4 border-b border-secondary-200 dark:border-secondary-700 overflow-hidden">
        <div class="flex items-center justify-center w-8 h-8 rounded-lg bg-primary-500 flex-shrink-0">
          <svg class="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        <Transition name="fade">
          <span v-if="!uiStore.isSidebarCollapsed"
            class="ml-3 font-bold text-secondary-900 dark:text-white text-base whitespace-nowrap">
            BikeFMS
          </span>
        </Transition>
      </div>

      <!-- 네비게이션 -->
      <nav class="flex-1 py-3 overflow-y-auto overflow-x-hidden">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :title="uiStore.isSidebarCollapsed ? item.label : undefined"
          :class="[
            'flex items-center mx-2 mb-1 rounded-lg transition-colors',
            uiStore.isSidebarCollapsed ? 'px-3 py-3 justify-center' : 'px-3 py-2.5',
          ]"
          active-class="bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400"
          inactive-class="text-secondary-600 dark:text-secondary-400 hover:bg-secondary-100 dark:hover:bg-secondary-700"
        >
          <svg class="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="item.iconPath" />
          </svg>
          <Transition name="fade">
            <span v-if="!uiStore.isSidebarCollapsed" class="ml-3 text-sm font-medium whitespace-nowrap">
              {{ item.label }}
            </span>
          </Transition>
          <!-- 미확인 알림 배지 -->
          <span
            v-if="item.badge && item.badge > 0 && !uiStore.isSidebarCollapsed"
            class="ml-auto bg-danger-500 text-white text-xs font-bold px-1.5 py-0.5 rounded-full min-w-[20px] text-center"
          >
            {{ item.badge > 99 ? '99+' : item.badge }}
          </span>
          <span
            v-else-if="item.badge && item.badge > 0 && uiStore.isSidebarCollapsed"
            class="absolute top-1 right-1 w-2 h-2 bg-danger-500 rounded-full"
          />
        </RouterLink>
      </nav>

      <!-- 사이드바 접기/펼치기 -->
      <button
        @click="uiStore.toggleSidebar()"
        class="flex items-center justify-center h-12 border-t border-secondary-200 dark:border-secondary-700
               text-secondary-400 dark:text-secondary-500 hover:text-secondary-700 dark:hover:text-secondary-300
               hover:bg-secondary-50 dark:hover:bg-secondary-700/50 transition-colors"
      >
        <svg
          :class="['w-4 h-4 transition-transform duration-300', uiStore.isSidebarCollapsed ? 'rotate-180' : '']"
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
        </svg>
      </button>
    </aside>

    <!-- ── 메인 컨텐츠 영역 ─────────────────────────────────── -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">

      <!-- 헤더 -->
      <header class="flex items-center justify-between h-16 px-6 bg-surface dark:bg-secondary-800
                     border-b border-secondary-200 dark:border-secondary-700 flex-shrink-0">
        <!-- 페이지 제목 (breadcrumb) -->
        <h1 class="text-base font-semibold text-secondary-900 dark:text-white">
          {{ currentPageTitle }}
        </h1>

        <div class="flex items-center gap-3">
          <!-- 다크모드 토글 -->
          <button
            @click="toggleDarkMode"
            class="flex items-center justify-center w-9 h-9 rounded-lg
                   text-secondary-500 dark:text-secondary-400
                   hover:bg-secondary-100 dark:hover:bg-secondary-700 transition-colors"
            :title="isDark ? '라이트 모드' : '다크 모드'"
          >
            <svg v-if="isDark" class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707M17.657 17.657l-.707-.707M6.343 6.343l-.707-.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>
            </svg>
            <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"/>
            </svg>
          </button>

          <!-- 실시간 연결 상태 -->
          <div class="flex items-center gap-1.5 text-xs text-secondary-500 dark:text-secondary-400">
            <span :class="['w-2 h-2 rounded-full', realtimeStore.isConnected ? 'bg-success-500 animate-pulse' : 'bg-secondary-400']" />
            <span class="hidden sm:inline">{{ realtimeStore.isConnected ? '실시간' : '오프라인' }}</span>
          </div>

          <!-- 사용자 메뉴 -->
          <div class="relative" ref="userMenuRef">
            <button
              @click="showUserMenu = !showUserMenu"
              class="flex items-center gap-2 px-3 py-1.5 rounded-lg
                     hover:bg-secondary-100 dark:hover:bg-secondary-700 transition-colors"
            >
              <div class="w-7 h-7 rounded-full bg-primary-500 flex items-center justify-center text-white text-xs font-bold">
                {{ userInitial }}
              </div>
              <span class="hidden md:block text-sm font-medium text-secondary-700 dark:text-secondary-300">
                {{ authStore.currentUser?.full_name ?? '사용자' }}
              </span>
              <svg class="w-4 h-4 text-secondary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            <!-- 드롭다운 -->
            <Transition name="dropdown">
              <div
                v-if="showUserMenu"
                class="absolute right-0 mt-2 w-48 bg-surface dark:bg-secondary-800 rounded-xl shadow-lg
                       border border-secondary-200 dark:border-secondary-700 py-1 z-50"
              >
                <div class="px-3 py-2 border-b border-secondary-100 dark:border-secondary-700">
                  <p class="text-xs font-semibold text-secondary-900 dark:text-white truncate">
                    {{ authStore.currentUser?.full_name }}
                  </p>
                  <p class="text-xs text-secondary-500 dark:text-secondary-400 truncate">
                    {{ authStore.currentUser?.email }}
                  </p>
                </div>
                <button
                  @click="handleLogout"
                  class="flex items-center w-full px-3 py-2 text-sm text-danger-600 dark:text-danger-400
                         hover:bg-secondary-50 dark:hover:bg-secondary-700 transition-colors"
                >
                  <svg class="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                  </svg>
                  로그아웃
                </button>
              </div>
            </Transition>
          </div>
        </div>
      </header>

      <!-- 페이지 콘텐츠 -->
      <main class="flex-1 overflow-y-auto">
        <RouterView />
      </main>
    </div>

    <!-- ── Toast 컨테이너 ─────────────────────────────────────── -->
    <div class="fixed bottom-5 right-5 z-[100] flex flex-col gap-2 items-end pointer-events-none">
      <TransitionGroup name="toast">
        <div
          v-for="toast in uiStore.toastQueue"
          :key="toast.id"
          :class="['flex items-start gap-3 px-4 py-3 rounded-xl shadow-lg pointer-events-auto max-w-sm', toastClass(toast.type)]"
        >
          <svg class="w-5 h-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="toastIcon(toast.type)" />
          </svg>
          <p class="text-sm flex-1">{{ toast.message }}</p>
          <button @click="uiStore.removeToast(toast.id)" class="opacity-60 hover:opacity-100 transition-opacity ml-1">
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </TransitionGroup>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue"
import { useRouter, useRoute } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { useUIStore } from "@/stores/ui"
import { useRealtimeStore } from "@/stores/realtime"
import { useAlertStore } from "@/stores/alert"
import type { ToastType } from "@/stores/ui"

const router      = useRouter()
const route       = useRoute()
const authStore   = useAuthStore()
const uiStore     = useUIStore()
const realtimeStore = useRealtimeStore()
const alertStore  = useAlertStore()

// ── 네비게이션 아이템 ──────────────────────────────────────────
const navItems = computed(() => [
  {
    to: "/app/dashboard",
    label: "대시보드",
    badge: 0,
    iconPath: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6",
  },
  {
    to: "/app/vehicles",
    label: "차량 관리",
    badge: 0,
    iconPath: "M13 10V3L4 14h7v7l9-11h-7z",
  },
  {
    to: "/app/alerts",
    label: "알림 관리",
    badge: alertStore.unacknowledgedCount,
    iconPath: "M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9",
  },
  {
    to: "/app/trips",
    label: "운행 기록",
    badge: 0,
    iconPath: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2",
  },
])

// ── 페이지 제목 ────────────────────────────────────────────────
const pageTitleMap: Record<string, string> = {
  Dashboard:     "대시보드",
  VehicleList:   "차량 관리",
  VehicleDetail: "차량 상세",
  AlertList:     "알림 관리",
  TripList:      "운행 기록",
}
const currentPageTitle = computed(() => pageTitleMap[route.name as string] ?? "BikeFMS")

// ── 다크모드 ───────────────────────────────────────────────────
const isDark = ref(document.documentElement.classList.contains("dark"))
function toggleDarkMode() {
  isDark.value = !isDark.value
  if (isDark.value) {
    document.documentElement.classList.add("dark")
    localStorage.setItem("theme", "dark")
  } else {
    document.documentElement.classList.remove("dark")
    localStorage.setItem("theme", "light")
  }
}

// ── 사용자 이니셜 ──────────────────────────────────────────────
const userInitial = computed(() => {
  const name = authStore.currentUser?.full_name ?? ""
  return name.charAt(0).toUpperCase() || "U"
})

// ── 사용자 드롭다운 ────────────────────────────────────────────
const showUserMenu = ref(false)
const userMenuRef  = ref<HTMLElement | null>(null)

function handleOutsideClick(e: MouseEvent) {
  if (userMenuRef.value && !userMenuRef.value.contains(e.target as Node)) {
    showUserMenu.value = false
  }
}
onMounted(() => document.addEventListener("mousedown", handleOutsideClick))
onUnmounted(() => document.removeEventListener("mousedown", handleOutsideClick))

async function handleLogout() {
  showUserMenu.value = false
  await authStore.logout()
  realtimeStore.disconnect()
  router.push("/login")
}

// ── Toast 스타일 ───────────────────────────────────────────────
function toastClass(type: ToastType): string {
  const map: Record<ToastType, string> = {
    success: "bg-success-50 dark:bg-success-900/30 text-success-800 dark:text-success-300 border border-success-200 dark:border-success-700",
    warning: "bg-warning-50 dark:bg-warning-900/30 text-warning-800 dark:text-warning-300 border border-warning-200 dark:border-warning-700",
    error:   "bg-danger-50 dark:bg-danger-900/30 text-danger-800 dark:text-danger-300 border border-danger-200 dark:border-danger-700",
    info:    "bg-info-50 dark:bg-info-900/30 text-info-800 dark:text-info-300 border border-info-200 dark:border-info-700",
  }
  return map[type]
}
function toastIcon(type: ToastType): string {
  const map: Record<ToastType, string> = {
    success: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z",
    warning: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z",
    error:   "M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z",
    info:    "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
  }
  return map[type]
}

// ── 실시간 WebSocket 연결 ──────────────────────────────────────
onMounted(() => {
  realtimeStore.connect([])
  alertStore.fetchAlerts()
})
onUnmounted(() => {
  realtimeStore.disconnect()
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.dropdown-enter-active { transition: opacity 0.15s, transform 0.15s; }
.dropdown-leave-active { transition: opacity 0.1s, transform 0.1s; }
.dropdown-enter-from, .dropdown-leave-to { opacity: 0; transform: translateY(-8px) scale(0.95); }

.toast-enter-active { transition: all 0.3s ease-out; }
.toast-leave-active { transition: all 0.2s ease-in; }
.toast-enter-from   { opacity: 0; transform: translateX(100%); }
.toast-leave-to     { opacity: 0; transform: translateX(100%); }
.toast-move         { transition: transform 0.3s; }
</style>
