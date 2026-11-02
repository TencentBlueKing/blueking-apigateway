/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

/*
* MCP Server 相关类型
*  */

export type IMCPTabType = 'tool' | 'prompt';

// MCPServer列表
export interface IMCPServer {
  id: number
  name: string
  title?: string
  description: string
  is_public: boolean
  labels: string[]
  resource_names: string[]
  tool_names?: string[]
  tools_count: number
  url: string
  status: number
  protocol_type?: string
  stage: {
    id: number
    name: string
  }
  updated_time?: string
  created_time?: string
  categories?: IMCPServerCategory[]
  is_official?: boolean
  is_featured?: boolean
  raw_response_enabled?: boolean
  prompts_count?: number
  oauth2_public_client_enabled?: boolean
  oauth2_personal_client_enabled?: boolean
  app_permission_risk?: {
    has_risk: boolean
    risk_tools: string[]
  }
  tools?: IMCPServerTool[]
  prompts?: IMCPServerPrompt[] | string
  order_by?: string
  [key: string]: any
}

// 工具schema
export interface IMCPServerToolSchema {
  properties: {
    data: {
      properties: {
        resource_info: {
          properties: {
            auth_config: {
              properties: {
                app_verified_required: {
                  type: string
                  description: string
                }
                resource_perm_required: {
                  type: string
                  description: string
                }
                user_verified_required: {
                  type: string
                  description: string
                }
              }
              type: string
            }
            description: {
              type: string
              description: string
            }
            enable_websocket: {
              type: string
              description: string
            }
            id: {
              type: string
              description: string
            }
            is_public: {
              type: string
              description: string
            }
            labels: {
              type: string
              description: string
              properties: {
                label: {
                  properties: {
                    id: {
                      type: string
                      description: string
                    }
                    name: {
                      type: string
                      description: string
                    }
                  }
                  type: string
                }
              }
            }
            match_subpath: {
              type: string
              description: string
            }
            method: {
              type: string
              description: string
            }
            name: {
              type: string
              description: string
            }
            path: {
              type: string
              description: string
            }
          }
          type: string
        }
      }
      type: string
    }
  }
  type: string
}

// MCPServer工具
export interface IMCPServerTool {
  id: number
  name: string
  description?: string
  description_en?: string
  method?: string
  path?: string
  mode_type?: IMCPTabType
  tool_name?: string
  isOverflow?: boolean
  has_openapi_schema?: boolean
  verified_user_required?: boolean
  verified_app_required?: boolean | string[]
  resource_perm_required?: boolean | string[]
  allow_apply_permission?: boolean | string[]
  labels?: string | {
    id: number
    name: string
  }[]
  gateway_label_ids?: number[]
  match_subpath: boolean
  enable_websocket: boolean
  is_public: boolean
  doc_updated_time?: {
    zh: string
  }
  proxy: {
    config: string
    backend: {
      id: number
      name: string
      config: {
        type: string
        timeout: number
        loadbalance: string
        hosts: {
          scheme: string
          host: string
          weight: number
        }[]
        checks: {
          passive: {
            type: string
            healthy: {
              http_statuses: number[]
              successes: number
            }
            unhealthy: {
              http_statuses: number[]
              http_failures: number
              timeouts: number
            }
          }
        }
      }
    }
  }
  contexts?: IResourceAuthResponse
  plugins: {
    binding_type: string
    config: Record<string, any>
    id: number
    name: string
    priority: number
    type: string
  }[]
  openapi_schema?: {
    version: string
    parameters: {
      description: string
      in: string
      name: string
      required: boolean
      schema: {
        type: string
      }
    }[]
    none_schema: boolean
    responses?: {
      default?: {
        content?: Record<string, IMCPServerToolSchema>
        description?: string
      }
    }
  }
}

// MCPServerPrompt
export interface IMCPServerPrompt {
  id: number
  name: string
  code: string
  content?: string
  mode_type?: IMCPTabType
  space_name?: string
  space_code?: string
  updated_by?: string
  updated_time?: string
  is_public: boolean
  is_no_perm?: boolean
  isOverflow?: boolean
  labels?: string[]
}

// MCP分类
export interface IMCPServerCategory {
  name: string
  display_name: string
  description?: string
  id: number
  sort_order?: number
}

// MCP配置
export interface IMCPAIConfig {
  name: string
  display_name: string
  content: string
  install_url: string
}

//  McpServer创建/编辑基础表单信息
export interface IMCPFormData {
  name: string
  title: string
  description: string
  stage_id: number
  is_public: boolean
  oauth2_public_client_enabled: boolean
  oauth2_personal_client_enabled: boolean
  raw_response_enabled: boolean
  labels: string[]
  categories: string[]
  protocol_type: string
  url?: string
}

// 列表接口筛选泛型
export interface IMCPFilterParams {
  order_by: string
  status?: string
  keyword?: string
  stage_id?: string
  categories?: string[] | string
  label?: string
  [key: string]: any
}

// config 是 JSON 字符串，解析后对应的对象结构
export interface IResourceAuthConfig {
  skip_auth_verification: boolean
  auth_verified_required: boolean
  app_verified_required: boolean
  resource_perm_required: boolean
}

export interface IResourceAuthResponse {
  resource_auth: {
    id: number
    scope_type: string
    scope_id: number
    type: string
    config: string | IResourceAuthConfig | undefined
    schema?: {
      id: number
      name: string
      type: string
      version: string
    }
  }
}

// tool工具勾选项
export interface IMCPToolSelections {
  name: string
  tool_name?: string
  id?: number
  contexts?: IResourceAuthResponse
}

//  UI 扩展类型
export type IMCPServerWithUIState = IMCPServer & { is_checked?: boolean };

// 重命名tool_name
export type ToolNameRowType = Partial<IMCPServerTool & {
  tool_name: string
  isShow: boolean
}>;

export interface IPermissionApprovalFilterValue {
  bk_app_code: string
  applied_by: string
  mcp_server_id: string | number
  state?: string
  order_by?: string
}

export interface IPermissionApprovalAction {
  id: number
  mcp_server_id: number | string
  status: 'approved' | 'rejected' | ''
  comment: string
}
