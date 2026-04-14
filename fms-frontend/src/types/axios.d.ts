// Axios InternalAxiosRequestConfig 타입 확장
// _retry: TOKEN_EXPIRED 시 무한 갱신 루프 방지 플래그
import "axios"

declare module "axios" {
  export interface InternalAxiosRequestConfig {
    _retry?: boolean
  }
}
