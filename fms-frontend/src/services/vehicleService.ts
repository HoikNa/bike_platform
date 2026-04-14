import http from "./http"
import type { ApiListResponse, ApiSingleResponse, PageMeta } from "@/types/api"
import type { Vehicle, LatestSensor } from "@/types/models"

interface VehicleListParams {
  page?:      number
  page_size?: number
  status?:    string[]
  q?:         string
}

interface VehicleListResult {
  data: Vehicle[]
  meta: PageMeta
}

export const vehicleService = {
  async list(params: VehicleListParams = {}): Promise<VehicleListResult> {
    // status 배열을 URLSearchParams 다중 값으로 직렬화
    const searchParams = new URLSearchParams()
    if (params.page)      searchParams.set("page",      String(params.page))
    if (params.page_size) searchParams.set("page_size", String(params.page_size))
    if (params.q)         searchParams.set("q",         params.q)
    params.status?.forEach(s => searchParams.append("status", s))

    const res: ApiListResponse<Vehicle> = await http.get(
      `/vehicles?${searchParams.toString()}`
    )
    return { data: res.data, meta: res.meta }
  },

  async getById(id: string): Promise<Vehicle> {
    const res: ApiSingleResponse<Vehicle> = await http.get(`/vehicles/${id}`)
    return res.data
  },

  async create(body: Partial<Vehicle>): Promise<Vehicle> {
    const res: ApiSingleResponse<Vehicle> = await http.post("/vehicles", body)
    return res.data
  },

  async update(id: string, body: Partial<Vehicle>): Promise<Vehicle> {
    const res: ApiSingleResponse<Vehicle> = await http.put(`/vehicles/${id}`, body)
    return res.data
  },

  async remove(id: string): Promise<void> {
    await http.delete(`/vehicles/${id}`)
  },

  async getLatestSensor(vehicleId: string): Promise<LatestSensor> {
    const res: ApiSingleResponse<LatestSensor> = await http.get(
      `/vehicles/${vehicleId}/sensors/latest`
    )
    return res.data
  },
}
