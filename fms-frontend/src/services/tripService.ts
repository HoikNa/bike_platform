import http from "./http"
import type { ApiListResponse, PageMeta } from "@/types/api"
import type { Trip } from "@/types/models"

interface TripListParams {
  page?:       number
  page_size?:  number
  vehicle_id?: string
  driver_id?:  string
}

interface TripListResult {
  data: Trip[]
  meta: PageMeta
}

export const tripService = {
  async list(params: TripListParams = {}): Promise<TripListResult> {
    const searchParams = new URLSearchParams()
    if (params.page)       searchParams.set("page",       String(params.page))
    if (params.page_size)  searchParams.set("page_size",  String(params.page_size))
    if (params.vehicle_id) searchParams.set("vehicle_id", params.vehicle_id)
    if (params.driver_id)  searchParams.set("driver_id",  params.driver_id)

    const res: ApiListResponse<Trip> = await http.get(`/trips?${searchParams.toString()}`)
    return { data: res.data, meta: res.meta }
  },
}
