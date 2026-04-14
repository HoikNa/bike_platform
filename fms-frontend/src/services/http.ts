import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from "axios"

// 타입 확장 임포트 (컴파일 타임 등록)
import "@/types/axios.d.ts"

// ── Axios 인스턴스 생성 ────────────────────────────────────────
const http: AxiosInstance = axios.create({
  baseURL:         import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  timeout:         15_000,
  withCredentials: true,  // Refresh Token HttpOnly 쿠키 자동 전송
  headers: { "Content-Type": "application/json" },
})

// ── 요청 인터셉터: Access Token 자동 주입 ─────────────────────
http.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem("access_token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ── 응답 인터셉터: 봉투 언팩 + TOKEN_EXPIRED 자동 갱신 ────────
http.interceptors.response.use(
  // 성공: response.data({success, data, meta}) 반환
  // 각 서비스에서 .data 로 실제 페이로드 접근
  (response) => response.data,

  async (error) => {
    const original  = error.config as InternalAxiosRequestConfig
    const errorCode = error.response?.data?.error?.code

    // TOKEN_EXPIRED → 1회만 갱신 시도
    if (errorCode === "TOKEN_EXPIRED" && !original._retry) {
      original._retry = true
      try {
        // 동적 임포트로 순환 의존성 방지
        const { useAuthStore } = await import("@/stores/auth")
        const auth = useAuthStore()
        await auth.refresh()   // POST /auth/refresh
        await auth.fetchMe()   // GET /auth/me — currentUser 복원
        return http(original)  // 원래 요청 재시도
      } catch {
        // 갱신 실패 → 로그아웃 + 만료 모달
        const { useAuthStore } = await import("@/stores/auth")
        const { useUIStore }   = await import("@/stores/ui")
        await useAuthStore().logout()
        useUIStore().setTokenExpired(true)
        return Promise.reject(error)
      }
    }

    return Promise.reject(error)
  }
)

export default http
