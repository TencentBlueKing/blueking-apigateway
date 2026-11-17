// POST /mcp-marketplace/batch-configs/ 和 /gateways/{gateway_id}/mcp-servers/-/batch-configs/
export interface IMCPServerBatchConfigInput {
  client_type: 'cursor' | 'codebuddy' | 'claude' | 'vscode'
  mcp_server_ids: number[]
}

/**
 * MCP 服务器配置项类型
 */
export interface IServerConfig {
  type?: 'http' | 'sse'
  transportType?: 'streamable-http' | 'sse'
  url: string
  headers?: Record<string, string>
}

/**
 * MCP 顶层配置类型
 */
export interface IMcpClientConfig {
  client_type: string
  display_name: string
  config: { servers: Record<string, IServerConfig> } | { mcpServers: Record<string, IServerConfig> }
}
