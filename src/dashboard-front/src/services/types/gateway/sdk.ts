/** /gateways/{gateway_id}/sdks/ [GET] */
export interface IGatewaysSdksListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** sdk语言 */
  language?: 'unknown' | 'python' | 'golang' | 'java'
  /** sdk版本号 */
  version_number?: string
  /** 资源版本号id */
  resource_version_id?: number | null
  /** 查询关键字，支持模糊匹配 */
  keyword?: string
}

// POST /gateways/{gateway_id}/sdks/ - sdk创建接口
export interface IGatewaySDKGenerateInputSLZ {
  resource_version_id: number
  language: string
  version?: string
}

/**
 * GET /gateways/{gateway_id}/sdks/
 */
export interface IGatewaySDKListOutput {
  download_url: string
  id: number
  language: string
  version_number: string
  created_time: string
  updated_time: string
  created_by: string
  name: string
  resource_version: {
    id: number
    version: string
  }
}
