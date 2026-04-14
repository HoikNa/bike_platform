// ── 공통 응답 봉투 (Response Envelope) ─────────────────────────
export interface ApiSingleResponse<T> {
  success: boolean
  data: T
  meta: null
}

export interface ApiListResponse<T> {
  success: boolean
  data: T[]
  meta: PageMeta
}

export interface ApiCursorResponse<T> {
  success: boolean
  data: T[]
  meta: CursorMeta
}

export interface PageMeta {
  total:       number
  page:        number
  page_size:   number
  total_pages: number
}

export interface CursorMeta {
  next_cursor: string | null
  has_next:    boolean
  limit:       number
}

// ── 에러 응답 ────────────────────────────────────────────────
export interface ApiError {
  success: false
  data:    null
  meta:    null
  error: {
    code:    string
    message: string
    detail:  Array<{ field: string; message: string }> | null
  }
}
