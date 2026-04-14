import http from "./http"
import type { ApiCursorResponse, ApiSingleResponse, CursorMeta } from "@/types/api"
import type { Alert } from "@/types/models"

interface AlertListParams {
  limit?:            number
  cursor?:           string
  vehicle_id?:       string
  severity?:         string[]
  is_acknowledged?:  boolean
}

interface AlertListResult {
  data: Alert[]
  meta: CursorMeta
}

export const alertService = {
  async list(params: AlertListParams = {}): Promise<AlertListResult> {
    const searchParams = new URLSearchParams()
    if (params.limit)   searchParams.set("limit",  String(params.limit))
    if (params.cursor)  searchParams.set("cursor", params.cursor)
    if (params.vehicle_id) searchParams.set("vehicle_id", params.vehicle_id)
    if (params.is_acknowledged !== undefined)
      searchParams.set("is_acknowledged", String(params.is_acknowledged))
    params.severity?.forEach(s => searchParams.append("severity", s))

    const res: ApiCursorResponse<Alert> = await http.get(
      `/alerts?${searchParams.toString()}`
    )
    return { data: res.data, meta: res.meta }
  },

  async getById(id: string): Promise<Alert> {
    const res: ApiSingleResponse<Alert> = await http.get(`/alerts/${id}`)
    return res.data
  },

  async acknowledge(id: string): Promise<Alert> {
    const res: ApiSingleResponse<Alert> = await http.patch(`/alerts/${id}/acknowledge`)
    return res.data
  },

  async acknowledgeBulk(alertIds: string[]): Promise<{ acknowledged_count: number }> {
    const res: ApiSingleResponse<{ acknowledged_count: number }> =
      await http.post("/alerts/acknowledge-bulk", { alert_ids: alertIds })
    return res.data
  },
}
