/**
 * GET /mcp-marketplace/categories/
 */
export interface IMCPMarketplaceCategoriesGetQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** MCPServer 筛选条件，支持模糊匹配 MCPServer 名称或描述 */
  keyword?: string
  /** 分类筛选，支持单个或多个分类名称，多个分类以逗号分隔 */
  categories?: string
  /** 排序方式，默认 -updated_time */
  order_by?:
    | 'updated_time'
    | '-updated_time'
    | 'created_time'
    | '-created_time'
    | 'name'
    | '-name'
}

/**
 * GET /mcp-marketplace/servers/
 */
export interface IMCPMarketplaceServersGetQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** MCPServer 筛选条件，支持模糊匹配 MCPServer 名称或描述 */
  keyword?: string
  /** 分类筛选，支持单个或多个分类名称，多个分类以逗号分隔 */
  categories?: string
  /** 排序方式，默认 -updated_time */
  order_by?:
    | 'updated_time'
    | '-updated_time'
    | 'created_time'
    | '-created_time'
    | 'name'
    | '-name'
}

// 批量复制请求参数
export interface IMcpBatchConfigQuery {
  client_type: string
  mcp_server_ids: number[]
}
