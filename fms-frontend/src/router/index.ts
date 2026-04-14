import { createRouter, createWebHistory } from "vue-router"
import { authGuard } from "./guards/authGuard"
import { roleGuard } from "./guards/roleGuard"

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    // ── 루트: 앱 진입점으로 리다이렉트 ──
    {
      path: "/",
      redirect: "/app",
    },

    // ── 인증 (AuthLayout) ─────────────────────────────────
    {
      path: "/login",
      name: "Login",
      component: () => import("@/views/auth/LoginView.vue"),
    },

    // ── 관제 대시보드 (AppLayout, 인증 필요) ──────────────
    {
      path: "/app",
      component: () => import("@/layouts/AppLayout.vue"),
      meta: { requiresAuth: true },
      beforeEnter: [authGuard],
      children: [
        {
          path: "",
          redirect: "/app/dashboard",
        },
        {
          path: "dashboard",
          name: "Dashboard",
          component: () => import("@/views/dashboard/DashboardView.vue"),
        },
        {
          path: "vehicles",
          name: "VehicleList",
          component: () => import("@/views/vehicles/VehicleListView.vue"),
        },
        {
          path: "vehicles/:vehicleId",
          name: "VehicleDetail",
          component: () => import("@/views/vehicles/VehicleDetailView.vue"),
        },
        {
          path: "alerts",
          name: "AlertList",
          component: () => import("@/views/alerts/AlertListView.vue"),
        },
        {
          path: "trips",
          name: "TripList",
          component: () => import("@/views/trips/TripListView.vue"),
        },
      ],
    },

    // ── 에러 페이지 ───────────────────────────────────────
    {
      path: "/403",
      name: "Forbidden",
      component: () => import("@/views/errors/ForbiddenView.vue"),
    },
    {
      path: "/:pathMatch(.*)*",
      name: "NotFound",
      component: () => import("@/views/errors/NotFoundView.vue"),
    },
  ],
})

// role 가드는 전역 afterEach 에서 실행
router.beforeEach(roleGuard)

export default router
