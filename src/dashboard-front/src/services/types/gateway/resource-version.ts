import type { IMCPServerToolSchema, IResourceAuthResponse } from '@/types/mcp-server';

/** /gateways/{gateway_id}/resource-versions/ [GET] */
export interface IGatewaysResourceVersionsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 资源版本筛选条件，支持模糊匹配 */
  keyword?: string
}

/** /gateways/{gateway_id}/resource-versions/diff/ [GET] */
export interface IGatewaysResourceVersionsDiffReadQuery {
  /** 对比源的资源版本 ID，可传数字、数字字符串或空字符串。发布预览也可省略。 */
  source_resource_version_id?: number | string | null
  /** 对比目标的资源版本 ID，可传数字或数字字符串。空字符串表示使用资源编辑区。 */
  target_resource_version_id: number | string | null
}

/** /gateways/{gateway_id}/resource-versions/{id}/ [GET] */
export interface IGatewaysResourceVersionsReadQuery {
  /** stage_id */
  stage_id?: number
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
  file_type: 'yaml' | 'json' | 'zip'
}

// POST /gateways/{gateway_id}/resource-versions/{id}/export-docs/
export interface IResourceVersionDocExportInputSLZ {
  file_type?: 'zip' | 'tgz'
}

/**
 * GET /gateways/{gateway_id}/resource-versions/
 */
export interface IResourceVersionListOutput {
  id: number
  version: string
  comment: string
  schema_version: string
  created_time: string
  created_by: string
  released_stages: {
    id: number
    name: string
  }[]
  sdk_count: number
  deletable?: boolean
}

/** 后端版本 diff 返回的差异对象，仅包含存在变更的字段；值可能为 false、0、null、空集合或嵌套对象。 */
export type ResourceVersionDiff = Record<string, unknown>;

/** 资源版本快照中的插件绑定配置 */
export interface IResourceVersionPlugin {
  id: number
  name: string
  type: string
  config: Record<string, any>
}

/** 资源版本快照中的上下文配置（兼容历史 JSON 字符串与当前对象格式） */
export interface IResourceVersionDiffContexts {
  resource_auth?: {
    config?: string | Record<string, boolean>
  }
}

/** 资源版本快照中的后端代理配置（兼容历史 JSON 字符串与当前对象格式） */
export interface IResourceVersionDiffProxy {
  type: 'http' | 'mock'
  backend_id?: number | null
  config?: string | Record<string, any>
}

/** 版本比较接口返回的资源快照；旧快照缺失的可选字段由展示层归一化补齐。 */
export interface IResourceVersionDiffResource {
  id: number
  name: string
  method: string
  path: string
  kind?: 'standard' | 'ai'
  description?: string | null
  match_subpath?: boolean
  enable_websocket?: boolean
  is_deprecated?: boolean
  deprecated_note?: string
  is_public?: boolean
  allow_apply_permission?: boolean
  api_labels?: (number | string)[]
  disabled_stages?: string[]
  contexts?: IResourceVersionDiffContexts
  proxy?: IResourceVersionDiffProxy
  plugins?: IResourceVersionPlugin[]
  openapi_schema?: Record<string, any>
  doc_updated_time?: Record<string, string>
  diff?: ResourceVersionDiff | null
}

/** GET /gateways/{gateway_id}/resource-versions/diff/ */
export interface IResourceVersionDiffOutput {
  add: IResourceVersionDiffResource[]
  delete: IResourceVersionDiffResource[]
  update: {
    source: IResourceVersionDiffResource
    target: IResourceVersionDiffResource
  }[]
}

/**
 * GET /gateways/{gateway_id}/resource-versions/{id}/
 */
export interface IResourceVersionRetrieveOutput {
  id: number
  version: string
  comment: string
  schema_version: string
  resources: {
    id: number
    name: string
    kind: 'standard' | 'ai'
    is_deprecated: boolean
    deprecated_note: string
    gateway_label_ids?: number[]
    description: string
    description_en: string
    method: string
    path: string
    match_subpath: boolean
    enable_websocket: boolean
    is_public: boolean
    allow_apply_permission: boolean
    doc_updated_time: {
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
    has_openapi_schema: boolean
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
  }[]
  created_time: string
  created_by: string
}

/** 普通与可编程资源版本的下一版本号 */
export interface INextResourceVersionOutput {
  version: string
}

/** GET /gateways/{gateway_id}/resource-versions/need-new-version/ */
export type INeedNewResourceVersionOutput
  = | { need_new_version: false }
    | {
      need_new_version: true
      msg: string
    };
