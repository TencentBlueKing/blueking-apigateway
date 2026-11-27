/** /gateways/{gateway_id}/mcp-servers/ [GET] */
export interface IGatewaysMcpServersListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** MCPServer 筛选条件，支持模糊匹配 MCPServer 名称或描述 */
  keyword?: string
  /** MCPServer 状态筛选 */
  status?: 0 | 1
  /** 环境 ID 筛选 */
  stage_id?: number
  /** 标签筛选 */
  label?: string
  /** 分类筛选，支持单个或多个分类名称，多个分类以逗号分隔 */
  categories?: string
  /** 排序方式 */
  order_by?: 'updated_time' | '-updated_time' | 'created_time' | '-created_time' | 'name' | '-name' | '-status'
}

/** /gateways/{gateway_id}/mcp-servers/-/categories/ [GET] */
export interface IGatewaysMcpServersCategoriesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/mcp-servers/-/filter-options/ [GET] */
export interface IGatewaysMcpServersFilterOptionsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/mcp-servers/-/remote-prompts/ [GET] */
export interface IGatewaysMcpServersRemotePromptsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 搜索关键字 */
  keyword?: string
}

/** /gateways/{gateway_id}/mcp-servers/-/stage-release-check/ [GET] */
export interface IGatewaysMcpServersStageReleaseCheckReadQuery {
  /** Stage ID */
  stage_id: number
  /** 资源版本 ID */
  resource_version_id: number
}

/** /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/tools/ [GET] */
export interface IGatewaysMcpServersToolsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

// PATCH /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/ - 更新 MCPServer 部分信息
export interface IMCPServerUpdateInputSLZ {
  title?: string // MCPServer 中文名/显示名称
  description?: string // MCPServer 描述
  is_public?: boolean
  labels?: string[] // MCPServer 标签列表
  resource_names?: string[] // MCPServer 资源名称列表
  tool_names?: string[] // MCPServer 工具名称列表
  prompts?: IMCPServerCreateInputSLZ['prompts']
  protocol_type?: 'sse' | 'streamable_http' // MCP 协议类型
  category_ids?: number[] // MCPServer 分类 ID 列表
  oauth2_public_client_enabled?: boolean
  oauth2_personal_client_enabled?: boolean
  raw_response_enabled?: boolean
}

// PATCH /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/status/ - 更新 MCPServer 状态，如启用、停用
export interface IMCPServerUpdateStatusInputSLZ {
  status: number
}

// POST /gateways/{gateway_id}/mcp-servers/ - 创建 MCPServer
export interface IMCPServerCreateInputSLZ {
  name: string
  title?: string
  description: string
  stage_id: number
  is_public?: boolean
  oauth2_public_client_enabled?: boolean
  oauth2_personal_client_enabled?: boolean
  raw_response_enabled?: boolean
  labels?: string[]
  resource_names: string[]
  tool_names: string[]
  prompts?: {
    id: number
    name: string
    code: string
    content?: string
    updated_time?: string
    updated_by?: string
    labels?: string[]
    is_public?: boolean
    space_code?: string
    space_name?: string
  }[]
  protocol_type?: 'sse' | 'streamable_http'
  category_ids?: number[]
}

// POST /gateways/{gateway_id}/mcp-servers/-/remote-prompts/batch/ - 根据 ID 列表批量获取第三方平台 Prompts 内容
export interface IMCPServerRemotePromptsBatchInputSLZ {
  ids: number[]
}

// POST /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/user-custom-doc/ - 创建 MCPServer 用户自定义文档
export interface IMCPServerUserCustomDocInputSLZ {
  content: string
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/
 */
export interface IMCPServerListOutput {
  id: number
  name: string
  title: string
  description: string
  is_public: boolean
  labels: string[]
  resource_names: string[]
  tool_names: string[]
  tools_count: number
  url: string
  status: number
  protocol_type: 'sse' | 'streamable_http'
  stage: {
    id: number
    name: string
  }
  updated_time: string
  created_time: string
  categories: IMCPServerCategoryOutput[]
  is_official: boolean
  is_featured: boolean
  prompts_count: number
  oauth2_public_client_enabled?: boolean
  oauth2_personal_client_enabled?: boolean
  app_permission_risk?: any
  [key: string]: any
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/categories/
 */
export interface IMCPServerCategoryOutput {
  id: number
  name: string
  display_name: string
  description?: string
  sort_order?: number
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/filter-options/
 */
export interface IMCPServerFilterOptionsOutput {
  labels?: string[]
  stages?: {
    id: number
    name: string
  }[]
  categories?: IMCPServerCategoryOutput[]
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/remote-prompts/
 */
export interface IMCPServerRemotePromptsOutput {
  prompts: {
    id: number
    name: string
    code: string
    content: string
    updated_time: string
    updated_by: string
    labels: string[]
    is_public: boolean
    space_code: string
    space_name: string
  }[]
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/remote-prompts/batch/
 */
export interface IMCPServerRemotePromptsBatchOutput {
  prompts: {
    id: number
    name: string
    code: string
    content: string
    updated_time: string
    updated_by: string
    labels: string[]
    is_public: boolean
    space_code: string
    space_name: string
  }[]
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/stage-release-check/
 */
export interface IMCPServerStageReleaseCheckOutput {
  has_related_changes: boolean
  deleted_resource_count: number
  details: {
    resource_name: string
    mcp_server: {
      id: number
      name: string
      title: string
    }
  }[]
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/
 */
export interface IMCPServerRetrieveOutput {
  id: number
  name: string
  title: string
  description: string
  is_public: boolean
  is_official: boolean
  is_featured: boolean
  oauth2_public_client_enabled: boolean
  raw_response_enabled: boolean
  labels: string[]
  resource_names: string[]
  tool_names: string[]
  tools_count: number
  url: string
  status: number
  protocol_type: 'sse' | 'streamable_http'
  stage: {
    id: number
    name: string
  }
  updated_time: string
  created_time: string
  categories: IMCPServerCategoryOutput[]
  oauth2_personal_client_enabled?: boolean
  prompts: string | any[]
  tools?: any[]
  gateway?: {
    id: number
    name: string
    is_official?: boolean
  }
  [key: string]: any
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/configs/
 */
export interface IMCPServerConfigListOutput {
  configs: {
    name: string
    display_name: string
    content: string
    install_url: string
  }[]
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/guideline/
 */
export interface IMCPServerGuidelineOutput {
  content: string
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/tools/
 */
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
  labels: string
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/tools/{tool_name}/doc/
 */
export interface IMCPServerToolDocOutput {
  type: string
  content: string
  updated_time: string
  schema: {
    [key: string]: string | null
  }
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/user-custom-doc/
 */
export interface IMCPServerUserCustomDocOutput {
  content: string
}
