import type { NavigationGuardNext, RouteLocationNormalized } from "vue-router"
import { useAuthStore } from "@/stores/auth"

export async function authGuard(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
): Promise<void> {
  const auth = useAuthStore()

  if (!auth.isAuthenticated) {
    return next({ path: "/login", query: { redirect: to.fullPath } })
  }

  // 페이지 새로고침 시: localStorage에 token은 있지만 currentUser가 null인 상태
  if (!auth.currentUser) {
    try {
      await auth.fetchMe()
    } catch {
      await auth.logout()
      return next({ path: "/login" })
    }
  }

  next()
}
