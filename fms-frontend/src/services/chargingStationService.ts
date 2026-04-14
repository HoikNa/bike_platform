import http from "./http"
import type { ApiListResponse, PageMeta } from "@/types/api"
import type { ChargingStation } from "@/types/models"

interface StationListParams {
  lat?:            number
  lng?:            number
  radius_km?:      number
  only_available?: boolean
  page?:           number
  page_size?:      number
}

export const chargingStationService = {
  async list(params: StationListParams = {}): Promise<{ data: ChargingStation[]; meta: PageMeta }> {
    const res: ApiListResponse<ChargingStation> = await http.get("/charging-stations", { params })
    return { data: res.data, meta: res.meta }
  },

  async getById(id: string): Promise<ChargingStation> {
    const { data } = await http.get(`/charging-stations/${id}`)
    return data
  },
}
