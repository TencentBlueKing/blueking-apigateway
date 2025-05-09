export interface SearchParamsInterface {
  stage_id?: number // 阶段ID，可选
  resource_id?: string | number // 资源ID，可以是字符串或数字，可选
  time_start?: string | number // 开始时间，可以是字符串或数字，可选
  time_end?: string | number // 结束时间，可以是字符串或数字，可选
  query?: string // 查询字符串，可选
}

export interface ChartInterface {
  offset?: number // 偏移量，可选
  limit?: number // 限制数量，可选
  query?: string // 查询字符串，可选
  time_range?: number // 时间范围，可选
  time_start?: string | number // 开始时间，可以是字符串或数字，可选
  time_end?: string | number // 结束时间，可以是字符串或数字，可选
}

export interface LogDetailInterface {
  offset?: number // 偏移量，可选
  limit?: number // 限制数量，可选
  bk_nonce: string // 随机数，用于安全验证
  bk_signature: string // 签名，用于安全验证
  bk_timestamp: string // 时间戳，用于安全验证
  shared_by: string // 共享者信息
}
