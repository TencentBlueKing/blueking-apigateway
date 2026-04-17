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
  title: string | null
  description: string
  is_public: boolean
  labels: (string | null)[]
  resource_names: (string | null)[]
  tool_names: (string | null)[]
  status: 0 | 1
  protocol_type: 'sse' | 'streamable_http'
  stage: object
  gateway: object
  tools_count: number
  prompts_count: number
  url: string
  updated_time: string
  created_time: string
  categories: string
  is_official: boolean
  is_featured: boolean
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
  labels: string
}

export interface IMCPServerRetrieveOutput {
  id: number
  name: string
  title: string | null
  description: string
  is_public: boolean
  labels: (string | null)[]
  resource_names: (string | null)[]
  tool_names: (string | null)[]
  status: 0 | 1
  protocol_type: 'sse' | 'streamable_http'
  stage: object
  gateway: object
  tools_count: number
  prompts_count: number
  url: string
  updated_time: string
  created_time: string
  categories: string
  is_official: boolean
  is_featured: boolean
  guideline: string
  tools: IMCPServerToolOutput[]
  prompts: string
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

/**
 * MCP 服务器配置项类型
 */
export interface IServerConfig {
  type: string
  url: string
}

/**
 * MCP 顶层配置类型
 */
export interface IMcpClientConfig {
  client_type: string
  display_name: string
  config: {
    servers: Record<string, IServerConfig>
  }
}
