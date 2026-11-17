import type { IGatewayLabelOutput } from '@/services/types/gateway/label.ts';
import type { IMCPServerRemotePromptsBatchOutput } from '@/services/types/gateway/mcp-server/server.ts';

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

export interface IMarketplacePermissionApplyInput {
  bk_app_code: string
  reason: string
}

// /mcp-marketplace/categories/
export interface IMCPServerCategoryOutput {
  id: number
  name: string
  display_name: string
  description: string
  sort_order: number
  mcp_server_count: number
}

// /mcp-marketplace/servers/
export interface IMCPServerListOutput {
  id: number
  name: string
  title: string
  description: string
  is_public: boolean
  labels: string[]
  resource_names: (string | null)[]
  tool_names: (string | null)[]
  status: 0 | 1
  protocol_type: 'sse' | 'streamable_http'
  stage: {
    id: number
    name: string
  }
  gateway: {
    id: number
    name: string
    display_name: string
    maintainers: string[]
    is_official: boolean
  }
  tools_count: number
  prompts_count: number
  url: string
  updated_time: string
  created_time: string
  categories: Omit<IMCPServerCategoryOutput, 'mcp_server_count'>[]
  is_official: boolean
  is_featured: boolean
  oauth2_public_client_enabled: boolean
  oauth2_personal_client_enabled: boolean
}

// /mcp-marketplace/servers/{mcp_server_id}/
export interface IMCPServerToolOutput {
  id: number
  name: string
  tool_name: string
  description: string
  method: string
  path: string
  verified_user_required: boolean
  verified_app_required: boolean
  resource_perm_required: boolean
  allow_apply_permission: boolean
  labels: IGatewayLabelOutput[]
}

export interface IMCPServerRetrieveOutput extends IMCPServerListOutput {
  guideline: string
  tools: IMCPServerToolOutput[]
  prompts: IMCPServerRemotePromptsBatchOutput['prompts']
  maintainers: string[]
  user_custom_doc: string
}

// /mcp-marketplace/servers/{mcp_server_id}/configs/
export interface IMCPServerConfigItemOutput {
  name: string
  display_name: string
  content: string
  install_url: string | null
}

export interface IMCPServerConfigListOutput {
  configs: IMCPServerConfigItemOutput[]
}

// /mcp-marketplace/servers/{mcp_server_id}/tools/{tool_name}/doc/
export interface IMCPServerToolDocOutput {
  type: string
  content: string
  updated_time: string
  schema: Record<string, string | null>
}

// 发起 MCPServer 权限申请
export interface IMarketplacePermissionApplyOutput {
  record_id: number
  bk_app_code: string
  mcp_server_id: number
  itsm_ticket_id: string
  itsm_ticket_url: string
}
