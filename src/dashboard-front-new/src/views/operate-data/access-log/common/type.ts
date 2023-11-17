export interface SearchParamsInterface {
  stage_id?: number
  time_start?: string | number
  time_end?: string | number
  query?: string
}

export interface ChartInterface {
  offset?: number
  limit?: number
  query?: string
  time_range?: number
  time_start?: string | number
  time_end?: string | number
}

export interface LogDetailInterface {
  offset?: number
  limit?: number
  bk_nonce: number
  bk_signature: string
  shared_by: string
  request_id: string
}
