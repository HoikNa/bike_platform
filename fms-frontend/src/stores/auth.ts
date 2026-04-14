import { ref, computed } from "vue"
import { defineStore } from "pinia"
import { authService } from "@/services/authService"
import type { User } from "@/types/models"

export const useAuthStore = defineStore("auth", () => {
  // ── State ────────────────────────────────────────────────
  const accessToken = ref<string | null>(localStorage.getItem("access_token"))
  const currentUser = ref<User | null>(null)
  const isLoading   = ref(false)

  // ── Getters ──────────────────────────────────────────────
  const isAuthenticated = computed(() => !!accessToken.value)
  const userRole        = computed(() => currentUser.value?.role ?? null)
  const isAdmin         = computed(() => userRole.value === "ADMIN")
  const isManager       = computed(() => ["ADMIN", "MANAGER"].includes(userRole.value ?? ""))

  // ── Actions ──────────────────────────────────────────────
  async function login(email: string, password: string): Promise<void> {
    isLoading.value = true
    try {
      const data = await authService.login({ email, password })
      accessToken.value = data.access_token
      currentUser.value = data.user
      localStorage.setItem("access_token", data.access_token)
    } finally {
      isLoading.value = false
    }
  }

  async function refresh(): Promise<string> {
    const data = await authService.refresh()
    accessToken.value = data.access_token
    localStorage.setItem("access_token", data.access_token)
    return data.access_token
  }

  async function fetchMe(): Promise<void> {
    // 페이지 새로고침 후 currentUser 복원 (accessToken은 있지만 currentUser=null인 상태)
    currentUser.value = await authService.getMe()
  }

  async function logout(): Promise<void> {
    await authService.logout().catch(() => {})
    accessToken.value = null
    currentUser.value = null
    localStorage.removeItem("access_token")
  }

  return {
    accessToken, currentUser, isLoading,
    isAuthenticated, userRole, isAdmin, isManager,
    login, refresh, fetchMe, logout,
  }
})
