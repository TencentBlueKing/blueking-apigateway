// POST /gateways/ - 创建网关
export interface IGatewayCreateInputSLZ {
  name: string
  description?: string
  maintainers: string[]
  developers?: string[]
  is_public?: boolean
  kind?: number
  extra_info?: {
    language?: string
    repository?: string
  }
  bk_app_codes?: string[]
  tenant_mode: string
  tenant_id?: string
  programmable_gateway_git_info?: {
    repository: string
    account: string
    password: string
  }
}

// POST /gateways/{gateway_id}/ai/batch-translate/ - 批量翻译文档
export interface IBatchTranslateInputSLZ {
  doc_ids?: number[]
  target_language?: string
}

// POST /gateways/{gateway_id}/ai/completion/ - AI Completion
export interface IAICompletionInputSLZ {
  inputs: {
    type: string
    input: string
    enable_streaming?: boolean
    language?: string
  }
}

export interface IHealthCheck {
  active: {
    type: 'http' | 'https' | 'tcp'
    timeout: number
    concurrency: number
    http_path?: string
    https_verify_certificate?: boolean
    healthy: {
      http_statuses?: number[]
      successes: number
      interval: number
    }
    unhealthy: {
      http_statuses?: number[]
      http_failures?: number
      tcp_failures?: number
      timeouts: number
      interval: number
    }
  }
  passive: {
    type: 'http' | 'https' | 'tcp'
    healthy: {
      http_statuses?: number[]
      successes: number
    }
    unhealthy: {
      http_statuses?: number[]
      http_failures?: number
      tcp_failures?: number
      timeouts: number
    }
  }
}

// POST /gateways/{gateway_id}/backends/ - 创建后端服务
export interface IBackendInputSLZ {
  name: string
  description?: string
  type?: string
  configs: {
    type?: string
    timeout: number
    loadbalance: string
    hash_on?: string
    key?: string
    hosts: {
      scheme: string
      host: string
      weight?: number
    }[]
    checks?: IHealthCheck
    stage_id: number
  }[]
}

// POST /gateways/{gateway_id}/docs/archive/parse/ - 导入资源文档前，检查归档文件是否正确
export interface IDocArchiveParseInputSLZ {
  file?: string
}

// POST /gateways/{gateway_id}/docs/export/ - 导出资源文档
export interface IDocExportInputSLZ {
  export_type: string
  file_type?: string
  resource_filter_condition?: {
    name?: string
    path?: string
    method?: string
    label_ids?: number[]
    backend_id?: number
    backend_name?: string
    keyword?: string
  }
  resource_ids?: number[]
}

// POST /gateways/{gateway_id}/docs/import/by-archive/ - 根据归档文件导入资源文档
export interface IDocImportByArchiveInputSLZ {
  selected_resource_docs: Record<string, any>
  file?: string
}

// POST /gateways/{gateway_id}/docs/import/by-swagger/ - 根据 swagger 描述文件导入资源文档
export interface IDocImportBySwaggerInputSLZ {
  selected_resource_docs: {
    language?: string
    resource_name: string
  }[]
  language: string
  swagger: string
}

// POST /gateways/{gateway_id}/labels/ - 新建网关标签
export interface IGatewayLabelInputSLZ {
  id?: number
  name: string
}

// POST /gateways/{gateway_id}/mcp-servers/ - 创建 MCPServer
export interface IMCPServerCreateInputSLZ {
  name: string
  title?: string
  description: string
  stage_id: number
  is_public?: boolean
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
  protocol_type?: string
  category_ids?: number[]
}

// POST /gateways/{gateway_id}/mcp-servers/-/remote-prompts/batch/ - 根据 ID 列表批量获取第三方平台 Prompts 内容
export interface IMCPServerRemotePromptsBatchInputSLZ {
  ids: number[]
}

// POST /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/ - 主动授权应用
export interface IMCPServerAppPermissionCreateInputSLZ {
  bk_app_code: string
}

// POST /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/user-custom-doc/ - 创建 MCPServer 用户自定义文档
export interface IMCPServerUserCustomDocInputSLZ {
  content: string
}

// POST /gateways/{gateway_id}/monitors/alarm/strategies/ - 创建告警策略
export interface IAlarmStrategyInputSLZ {
  id?: number
  name: string
  alarm_type: string
  alarm_subtype: string
  gateway_label_ids: number[]
  config: {
    detect_config: {
      duration: number
      method: string
      count: number
    }
    converge_config: {
      duration: number
    }
    notice_config: {
      notice_way: string[]
      notice_role: string[]
      notice_extra_receiver: string[]
    }
  }
  effective_stages?: string[]
}

// POST /gateways/{gateway_id}/permissions/app-gateway-permissions/ - 网关权限主动授权
export interface IAppPermissionInputSLZ {
  bk_app_code: string
  expire_days: number
  resource_ids: number[]
}

// POST /gateways/{gateway_id}/permissions/app-gateway-permissions/renew/ - 网关权限续期
export interface IAppPermissionIDsSLZ {
  ids?: number[]
  expire_days?: number
}

// POST /gateways/{gateway_id}/permissions/app-permission-apply/approval/ - 审批操作
export interface IAppPermissionApplyApprovalInputSLZ {
  ids: number[]
  part_resource_ids?: Record<string, number[]>
  status: string
  comment: string
}

// POST /gateways/{gateway_id}/permissions/app-permissions/export/ - 网关权限导出
export interface IAppPermissionExportInputSLZ {
  bk_app_code?: string
  resource_id?: number
  keyword?: string
  resource_path?: string
  grant_type?: string
  grant_dimension?: string
  order_by?: string
  export_type: string
  gateway_permission_ids?: number[]
  resource_permission_ids?: number[]
}

// POST /gateways/{gateway_id}/permissions/app-permissions/renew/ - 批量续期
export interface IAppPermissionRenewInputSLZ {
  gateway_dimension_ids?: number[]
  resource_dimension_ids?: number[]
  expire_days: number
}

// POST /gateways/{gateway_id}/plugins/{scope_type}/{scope_id}/{code}/configs/ - 创建一个插件，并且绑定到对应的 scope_type + scope_id
export interface IPluginConfigBaseSLZ {
  id?: number
  name?: string
  yaml?: string
  type_id: number
}

// POST /gateways/{gateway_id}/releases/ - 版本发布接口
export interface IReleaseInputSLZ {
  stage_id: number
  resource_version_id: number
  comment?: string
}

// POST /gateways/{gateway_id}/releases/programmable/deploy/ - 编程网关部署接口
export interface IProgrammableDeployCreateInputSLZ {
  stage_id: number
  branch: string
  version_type: string
  commit_id: string
  version: string
  comment: string
}

// POST /gateways/{gateway_id}/resource-versions/ - 资源版本创建接口
export interface IResourceVersionCreateInputSLZ {
  version: string
  comment?: string
}

// POST /gateways/{gateway_id}/resource-versions/{id}/export/ - 导出资源版本
export interface IResourceVersionExportInputSLZ {
  id?: number
  export_type: string
  file_type: string
}

// POST /gateways/{gateway_id}/resources/ - 新建资源
export interface IResourceInputSLZ {
  name: string
  description?: string
  description_en?: string
  method: string
  path: string
  match_subpath?: boolean
  enable_websocket?: boolean
  is_public?: boolean
  allow_apply_permission?: boolean
  auth_config: {
    auth_verified_required?: boolean
    app_verified_required?: boolean
    resource_perm_required?: boolean
  }
  backend: {
    id: number
    config: {
      method: string
      path: string
      match_subpath?: boolean
      timeout?: number
      legacy_upstreams?: {
        loadbalance?: string
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
  label_ids?: number[]
  openapi_schema?: {
    version?: string
    none_schema?: boolean
    request_body?: Record<string, string>
    responses?: Record<string, string>
    parameters?: Record<string, string>[]
  }
}

// POST /gateways/{gateway_id}/resources/export/ - 导出资源
export interface IResourceExportInputSLZ {
  export_type: string
  file_type?: string
  resource_filter_condition?: {
    name?: string
    path?: string
    method?: string
    label_ids?: string
    backend_id?: number
    backend_name?: string
    keyword?: string
    order_by?: string
  }
  resource_ids?: number[]
}

// POST /gateways/{gateway_id}/resources/import/ - yaml/json check之后的标准化资源数据导入
export interface IResourceImportInputSLZ {
  import_resources?: {
    name: string
    description?: string
    description_en?: string
    method: string
    path: string
    match_subpath?: boolean
    enable_websocket?: boolean
    is_public?: boolean
    allow_apply_permission?: boolean
    auth_config: {
      auth_verified_required?: boolean
      app_verified_required?: boolean
      resource_perm_required?: boolean
    }
    backend_name: string
    backend_config: {
      method: string
      path: string
      match_subpath?: boolean
      timeout?: number
      legacy_upstreams?: {
        loadbalance?: string
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
    labels?: string[]
    plugin_configs?: {
      type: string
      yaml: string
    }[]
    openapi_schema?: Record<string, string>
  }[]
  doc_language?: string
}

// POST /gateways/{gateway_id}/resources/import/check/ - 导入资源检查，导入资源前，检查资源配置是否正确
export interface IResourceImportCheckInputSLZ {
  content: string
  doc_language: string
}

// POST /gateways/{gateway_id}/resources/import/doc/preview/ - 导入文档预览
export interface IResourceImportDocPreviewInputSLZ {
  review_resource: {
    name: string
    description?: string
    description_en?: string
    method: string
    path: string
    match_subpath?: boolean
    enable_websocket?: boolean
    is_public?: boolean
    allow_apply_permission?: boolean
    auth_config: {
      auth_verified_required?: boolean
      app_verified_required?: boolean
      resource_perm_required?: boolean
    }
    backend_name: string
    backend_config: {
      method: string
      path: string
      match_subpath?: boolean
      timeout?: number
      legacy_upstreams?: {
        loadbalance?: string
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
    labels?: string[]
    plugin_configs?: {
      type: string
      yaml: string
    }[]
    openapi_schema?: Record<string, string>
  }
  doc_language?: string
}

// POST /gateways/{gateway_id}/resources/{resource_id}/docs/ - 创建资源文档
export interface IDocInputSLZ {
  language: string
  content?: string
}

// POST /gateways/{gateway_id}/sdks/ - sdk创建接口
export interface IGatewaySDKGenerateInputSLZ {
  resource_version_id: number
  language: string
  version?: string
}

// POST /gateways/{gateway_id}/stages/ - 创建环境
export interface IStageInputSLZ {
  name: string
  description?: string
  backends: {
    id: number
    config: {
      type?: string
      timeout: number
      loadbalance: string
      hash_on?: string
      key?: string
      hosts: {
        scheme: string
        host: string
        weight?: number
      }[]
      checks?: {
        active?: {
          type?: string
          timeout?: number
          concurrency?: number
          http_path?: string
          https_verify_certificate?: boolean
          healthy?: {
            http_statuses?: number[]
            successes?: number
            interval?: number
          }
          unhealthy?: {
            http_statuses?: number[]
            http_failures?: number
            tcp_failures?: number
            timeouts?: number
            interval?: number
          }
        }
        passive?: {
          type?: string
          healthy?: {
            http_statuses?: number[]
            successes?: number
          }
          unhealthy?: {
            http_statuses?: number[]
            http_failures?: number
            tcp_failures?: number
            timeouts?: number
          }
        }
      }
    }
  }[]
}
