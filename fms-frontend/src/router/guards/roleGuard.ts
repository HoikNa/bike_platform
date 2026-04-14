import type { NavigationGuardNext, RouteLocationNormalized } from "vue-router"
import { useAuthStore } from "@/stores/auth"

export function roleGuard(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
): void {
  const requiredRoles = to.meta.roles as string[] | undefined
  if (!requiredRoles || requiredRoles.length === 0) return next()

  const auth = useAuthStore()
  const role = auth.currentUser?.role

  if (!role || !requiredRoles.includes(role)) {
    return next({ path: "/403" })
  }
  next()
}
