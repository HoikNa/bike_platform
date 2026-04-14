/**
 * api.ts — 백엔드 REST API 통합 클라이언트
 *
 * 기존 http.ts(Axios 인스턴스)를 기반으로,
 * 각 화면이 필요로 하는 API 호출을 단순한 함수로 제공합니다.
 *
 * 응답 구조: { success, data, meta }  (http.ts 인터셉터에서 response.data 언팩 완료)
 *
 * baseURL 환경 분기는 http.ts 에서 처리합니다:
 *   로컬         → http://localhost:8000          (VITE_API_BASE_URL 미설정 시 기본값)
 *   프로덕션(Vercel) → .env.production 의 VITE_API_BASE_URL  (API Gateway URL)
 */

import http from "./http"
import type { ApiListResponse, ApiSingleResponse, ApiCursorResponse } from "@/types/api"
import type { Vehicle, Alert } from "@/types/models"

// ── 에러 로깅 인터셉터 (응답 에러 콘솔 출력) ─────────────────────────────
http.interceptors.response.use(
  (res) => res,
  (err) => {
    const status  = err.response?.status ?? "네트워크 오류"
    const code    = err.response?.data?.error?.code ?? "UNKNOWN"
    const message = err.response?.data?.error?.message ?? err.message ?? ""
    console.error(`[API Error] ${status} ${code}: ${message}`, err.config?.url)
    return Promise.reject(err)
  },
)

// ── 차량 ───────────────────────────────────────────────────────────────────

/**
 * GET /vehicles — 차량 전체 목록 조회
 * @param pageSize 한 번에 가져올 차량 수 (기본 100)
 */
export async function fetchVehicles(pageSize = 100): Promise<Vehicle[]> {
  const res: ApiListResponse<Vehicle> = await http.get("/vehicles", {
    params: { page_size: pageSize },
  })
  return res.data
}

/**
 * GET /vehicles/{id} — 차량 상세 조회 (센서·드라이버·알림 포함)
 */
export async function fetchVehicleDetail(id: string): Promise<Vehicle> {
  const res: ApiSingleResponse<Vehicle> = await http.get(`/vehicles/${id}`)
  return res.data
}

// ── 알림 ───────────────────────────────────────────────────────────────────

/**
 * GET /alerts — 최근 알림 목록 조회 (커서 페이지네이션)
 * @param limit 반환 건수 (기본 30)
 */
export async function fetchAlerts(limit = 30): Promise<Alert[]> {
  const res: ApiCursorResponse<Alert> = await http.get("/alerts", {
    params: { limit },
  })
  return res.data
}
