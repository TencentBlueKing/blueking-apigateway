import type { IAuthConfig } from '@/types/resource';

// PATCH /gateways/{gateway_id}/ - 更新网关部分信息
export interface IGatewayUpdateInputSLZ {
  description?: string // 网关描述
  maintainers: string[] // 网关维护人员
  doc_maintainers?: {
    type?: 'user' | 'service_account' // 联系人类型
    contacts?: string[] // 联系人
    service_account?: {
      name?: string // 服务号名称
      link?: string // 服务号链接
    }
  }
  extra_info?: {
    language?: 'python' | 'go' // 语言
    repository?: string // 仓库
  }
  developers?: string[] // 网关开发者
  is_public?: boolean // 是否公开，true：公开，false：不公开
  bk_app_codes?: string[] // 网关相关的应用列表
  related_app_codes?: string[] // 管理网关的应用列表
  is_deprecated?: boolean
  deprecated_note?: string
}

// PATCH /gateways/{gateway_id}/backends/{id}/
export interface IBackendInputSLZ {
  name: string // 后端服务名称
  description?: string // 描述
  type?: 'http' | 'grpc' // 类型
  configs: {
    type?: 'node' | 'service_discovery' // 类型
    timeout: number // 超时时间
    loadbalance: 'roundrobin' | 'weighted-roundrobin' | 'chash' | 'ewma' | 'least_conn' // 负载均衡
    hash_on?: 'vars' | 'header' | 'cookie' | 'vars_combinations' // hash 类型
    key?: string // hash 键
    hosts: {
      scheme: 'http' | 'https' | 'grpc' | 'grpcs' // 协议
      host: string // 主机
      weight?: number // 权重
    }[] // 主机列表
    checks?: {
      active?: {
        type?: 'http' | 'https' | 'tcp' // 检查类型
        timeout?: number // 超时时间(秒)
        concurrency?: number // 并发数
        http_path?: string // HTTP检查路径
        https_verify_certificate?: boolean // HTTPS证书验证
        healthy?: {
          http_statuses?: number[] // HTTP状态码列表
          successes?: number // 成功次数
          interval?: number // 检查间隔(秒)
        }
        unhealthy?: {
          http_statuses?: number[] // HTTP状态码列表
          http_failures?: number // HTTP失败次数
          tcp_failures?: number // TCP失败次数
          timeouts?: number // 超时次数
          interval?: number // 检查间隔(秒)
        }
      }
      passive?: {
        type?: 'http' | 'https' | 'tcp' // 检查类型
        healthy?: {
          http_statuses?: number[] // HTTP状态码列表
          successes?: number // 成功次数
        }
        unhealthy?: {
          http_statuses?: number[] // HTTP状态码列表
          http_failures?: number // HTTP失败次数
          tcp_failures?: number // TCP失败次数
          timeouts?: number // 超时次数
        }
      }
    }
    stage_id: number
  }[] // 配置
}

// PATCH /gateways/{gateway_id}/labels/{id}/
export interface IGatewayLabelInputSLZ {
  id?: number // 标签 ID
  name: string // 标签名称
}

// PATCH /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/ - 更新 MCPServer 部分信息
export interface IMCPServerUpdateInputSLZ {
  title?: string // MCPServer 中文名/显示名称
  description: string // MCPServer 描述
  is_public?: boolean
  labels?: string[] // MCPServer 标签列表
  resource_names?: string[] // MCPServer 资源名称列表
  tool_names?: string[] // MCPServer 工具名称列表
  prompts?: {
    id: number // Prompt ID（第三方平台的唯一标识）
    name: string // Prompt 名称
    code: string // Prompt 标识码
    content?: string // Prompt 内容
    updated_time?: string // Prompt 更新时间
    updated_by?: string // Prompt 更新人
    labels?: string[] // Prompt 标签列表
    is_public?: boolean // Prompt 是否公开
    space_code?: string // Prompt 所在空间标识
    space_name?: string // Prompt 所在空间名称
  }[] // Prompts 列表
  protocol_type?: 'sse' | 'streamable_http' // MCP 协议类型
  category_ids?: number[] // MCPServer 分类 ID 列表
}

// PATCH /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/labels/ - 更新 MCPServer 标签
export interface IMCPServerUpdateLabelsInputSLZ {
  labels: string[] // MCPServer 标签列表
}

// PATCH /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/app-permission-apply/{id}/status/ - 更新授权审批状态，通过/驳回
export interface IMCPServerAppPermissionApplyUpdateInputSLZ {
  status: 'approved' | 'rejected' // 审批状态
  comment?: string
}

// PATCH /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/status/ - 更新 MCPServer 状态，如启用、停用
export interface IMCPServerUpdateStatusInputSLZ {
  status: number
}

// PATCH /gateways/{gateway_id}/monitors/alarm/strategies/{id}/
export interface IAlarmStrategyInputSLZ {
  id?: number
  name: string
  alarm_type: 'resource_backend'
  alarm_subtype: 'status_code_5xx' | 'gateway_timeout' | 'bad_gateway'
  gateway_label_ids: number[] // 网关标签 id 列表
  config: {
    detect_config: {
      duration: number // 持续时间
      method: 'gt' | 'gte' | 'lt' | 'lte' | 'eq' // 检测方法
      count: number // 次数
    }
    converge_config: {
      duration: number // 持续时间
    }
    notice_config: {
      notice_way: ('wechat' | 'im' | 'mail')[] // 通知方式
      notice_role: 'maintainer'[] // 通知组
      notice_extra_receiver: string[] // 其他通知对象
    }
  }
  effective_stages?: string[] // 生效环境列表
}

// PATCH /gateways/{gateway_id}/monitors/alarm/strategies/{id}/status/ - 更新告警策略状态
export interface IAlarmStrategyUpdateStatusInputSLZ {
  enabled?: boolean
}

// PATCH /gateways/{gateway_id}/plugins/{scope_type}/{scope_id}/{code}/configs/{id}/
export interface IPluginConfigBaseSLZ {
  id?: number
  name?: string
  yaml?: string
  type_id: number // 插件类型
}

// PATCH /gateways/{gateway_id}/resources/batch/
export interface IResourceBatchUpdateInputSLZ {
  ids: number[] // 资源 ID 列表
  is_public: boolean // 是否公开，true：公开，false：不公开
  allow_apply_permission: boolean // 是否允许应用在开发者中心申请访问资源的权限
  is_update_labels?: boolean // 是否批量修改标签，true:需要批量修改标签，false：不批量修改标签
  label_ids?: number[] // 标签 ID 列表
}

// PATCH /gateways/{gateway_id}/resources/{id}/
export interface IResourceInputSLZ {
  name: string // 资源名称
  description?: string // 资源描述
  description_en?: string // 资源英文描述，根据网关功能开关 ENABLE_I18N_SUPPORT 判断是否允许编辑此字段
  method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD' | 'OPTIONS' | 'ANY' // 资源请求方法
  path: string // 前端请求路径
  match_subpath?: boolean // 是否匹配所有子路径
  enable_websocket?: boolean // 是否启用 websocket
  is_public?: boolean // 是否公开，true：公开，false：不公开
  allow_apply_permission?: boolean // 是否允许应用在开发者中心申请访问资源的权限
  auth_config: IAuthConfig
  backend: {
    id: number // 后端服务 ID
    config: {
      method: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD' | 'OPTIONS' | 'ANY' // 请求方法
      path: string // 请求路径
      match_subpath?: boolean // 是否匹配所有子路径
      timeout?: number // 超时时间
      legacy_upstreams?: {
        loadbalance?: 'roundrobin' | 'weighted-roundrobin' | 'chash' | 'ewma' | 'least_conn'
        hosts?: {
          host: string
          weight?: number
        }[]
      }
      legacy_transform_headers?: {
        set?: Record<string, string>
        delete?: string[]
      }
    }
  }
  label_ids?: number[] // 标签 ID 列表
  openapi_schema?: {
    version?: string // OpenAPI schema 版本
    none_schema?: boolean // 是否有无schema
    request_body?: Record<string, string> // body参数
    responses?: Record<string, string> // response参数
    parameters?: Record<string, string>[] // 请求参数列表
  }
}

// PATCH /gateways/{gateway_id}/resources/{resource_id}/docs/{id}/
export interface IDocInputSLZ {
  language: 'en' | 'zh'
  content?: string // 文档内容
}

// PATCH /gateways/{gateway_id}/resources/{resource_id}/labels/
export interface IResourceLabelUpdateInputSLZ {
  label_ids: number[] // 标签 ID 列表
}

// PATCH /gateways/{gateway_id}/stages/{id}/ - 局部更新环境
export interface IStagePartialInputSLZ {
  description: string // 描述
}

// PATCH /gateways/{gateway_id}/stages/{id}/backends/{backend_id}/
export interface IBackendConfigInputSLZ {
  type?: 'node' | 'service_discovery' // 类型
  timeout: number // 超时时间
  loadbalance: 'roundrobin' | 'weighted-roundrobin' | 'chash' | 'ewma' | 'least_conn' // 负载均衡
  hash_on?: 'vars' | 'header' | 'cookie' | 'vars_combinations' // hash 类型
  key?: string // hash 键
  hosts: {
    scheme: 'http' | 'https' | 'grpc' | 'grpcs' // 协议
    host: string // 主机
    weight?: number // 权重
  }[] // 主机列表
  checks?: {
    active?: {
      type?: 'http' | 'https' | 'tcp' // 检查类型
      timeout?: number // 超时时间(秒)
      concurrency?: number // 并发数
      http_path?: string // HTTP检查路径
      https_verify_certificate?: boolean // HTTPS证书验证
      healthy?: {
        http_statuses?: number[] // HTTP状态码列表
        successes?: number // 成功次数
        interval?: number // 检查间隔(秒)
      }
      unhealthy?: {
        http_statuses?: number[] // HTTP状态码列表
        http_failures?: number // HTTP失败次数
        tcp_failures?: number // TCP失败次数
        timeouts?: number // 超时次数
        interval?: number // 检查间隔(秒)
      }
    }
    passive?: {
      type?: 'http' | 'https' | 'tcp' // 检查类型
      healthy?: {
        http_statuses?: number[] // HTTP状态码列表
        successes?: number // 成功次数
      }
      unhealthy?: {
        http_statuses?: number[] // HTTP状态码列表
        http_failures?: number // HTTP失败次数
        tcp_failures?: number // TCP失败次数
        timeouts?: number // 超时次数
      }
    }
  }
}

// PATCH /gateways/{gateway_id}/stages/{id}/programmable/
export interface IProgrammableStageDeployOutputSLZ {
  version?: string // 当前生效资源版本
  repo_info?: string // 当前代码仓库信息
  branch?: string // 上一次部署分支
  commit_id?: string // 上一次部署commit_id
  deploy_id?: string // 上一次部署ID
  created_by?: string // 发布人
  created_time?: string // 发布时间
  latest_deployment?: string // 当前部署信息
  status?: string // 部署状态
}

// PATCH /gateways/{gateway_id}/stages/{id}/status/
export interface IStageStatusInputSLZ {
  status: number // 状态
}

// PATCH /gateways/{gateway_id}/stages/{id}/vars/
export interface IStageVarsSLZ {
  vars?: Record<string, string>
}

// PATCH /gateways/{gateway_id}/status/
export interface IGatewayUpdateStatusInputSLZ {
  status: number // 网关状态，0：停用，1：启用
}

// PATCH /gateways/{gateway_id}/tests/histories/{id}/
export interface IAPIDebugHistoriesListOutputSLZ {
  id?: number // 测试历史ID
  created_time?: string // 创建时间
  gateway_id?: number // 网关ID
  resource_name?: string // 资源名称
  request: Record<string, any> // 请求参数
  response: Record<string, any> // 返回结果
}
