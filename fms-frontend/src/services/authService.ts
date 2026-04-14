import http from "./http"
import type { ApiSingleResponse } from "@/types/api"
import type { User } from "@/types/models"

interface LoginRequest  { email: string; password: string }
interface TokenResponse { access_token: string; token_type: string; expires_in: number }
interface LoginResponse extends TokenResponse { user: User }

export const authService = {
  async login(body: LoginRequest): Promise<LoginResponse> {
    const res: ApiSingleResponse<LoginResponse> = await http.post("/auth/login", body)
    return res.data
  },

  async refresh(): Promise<TokenResponse> {
    const res: ApiSingleResponse<TokenResponse> = await http.post("/auth/refresh")
    return res.data
  },

  async getMe(): Promise<User> {
    const res: ApiSingleResponse<User> = await http.get("/auth/me")
    return res.data
  },

  async logout(): Promise<void> {
    await http.post("/auth/logout")
  },
}
