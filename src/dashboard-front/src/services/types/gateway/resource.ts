import type { IDocsOpenAPISchema } from '@/services/types/docs/gateway.ts';
import type { IGatewayLabelOutput } from '@/services/types/gateway/label.ts';
import type { IDocListOutput } from '@/services/types/gateway/resource-doc.ts';
import type { IAuthConfig, IImportedResource, ResourceChangeType } from '@/types/resource';

/** /gateways/{gateway_id}/resources/ [GET] */
export interface IGatewaysResourcesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 资源名称，完整匹配 */
  name?: string
  /** 资源前端请求路径，完整匹配 */
  path?: string
  /** 资源请求方法，完整匹配 */
  method?: string
  /** 认证方式，多个以逗号 , 分割并取并集 */
  auth_type?: string
  /** 标签 ID，多个以逗号 , 分割 */
  label_ids?: string
  /** 后端服务 ID */
  backend_id?: number | null
  /** 后端服务名称，完整匹配 */
  backend_name?: string
  /** 资源类型 */
  kind?: 'standard' | 'ai'
  /** 资源筛选条件，支持模糊匹配资源名称，前端请求路径 */
  keyword?: string
  /** 排序字段 */
  order_by?: '-id' | 'name' | '-name' | 'path' | '-path' | 'updated_time' | '-updated_time'
  no_page?: boolean
}

/** /gateways/{gateway_id}/resources/backend-path/check/ [GET] */
export interface IGatewaysResourcesBackendPathCheckReadQuery {
  /** 请求路径 */
  path?: string
  /** 后端服务 ID */
  backend_id: number
  /** 后端服务的 path */
  backend_path: string
}

/** /gateways/{gateway_id}/resources/with/verified-user-required/ [GET] */
export interface IGatewaysResourcesWithVerifiedUserRequiredListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

// PATCH /gateways/{gateway_id}/resources/{resource_id}/deprecation/ - 更新资源弃用标记
export interface IResourceDeprecationUpdateInputSLZ {
  is_deprecated: boolean // 是否弃用
  deprecated_note?: string // 弃用说明，取消弃用时为空字符串
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
  auth_config: IAuthConfig
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
    auth_config: IAuthConfig
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
    } | null
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
  doc_language?: string
  allow_overwrite?: boolean
  include_change_type?: boolean
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
    auth_config: IAuthConfig
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

// PUT /gateways/{gateway_id}/resources/batch/
export interface IResourceBatchUpdateInputSLZ {
  ids: number[] // 资源 ID 列表
  is_public: boolean // 是否公开，true：公开，false：不公开
  allow_apply_permission: boolean // 是否允许应用在开发者中心申请访问资源的权限
  is_update_labels?: boolean // 是否批量修改标签，true:需要批量修改标签，false：不批量修改标签
  label_ids?: number[] // 标签 ID 列表
}

// PUT /gateways/{gateway_id}/resources/{resource_id}/labels/
export interface IResourceLabelUpdateInputSLZ {
  label_ids: number[] // 标签 ID 列表
}

/**
 * GET /gateways/{gateway_id}/resources/
 */
export interface IResourceListPageOutput {
  id: number
  name: string
  is_deprecated: boolean
  deprecated_note: string
  description: string | null
  kind: 'standard' | 'ai'
  method: string
  path: string
  created_time: string | null
  updated_time: string | null
  backend: {
    id: number
    name: string
    kind: 'standard' | 'ai'
  }
  labels: IGatewayLabelOutput[]
  docs: Pick<IDocListOutput, 'id' | 'language'>[]
  has_updated: boolean
  plugin_count: number
  auth_config: IResourceAuthConfigOutput
}

/**
 * GET /gateways/{gateway_id}/resources/-/path-conflicts/
 */
export interface IResourcePathConflictResourceOutput {
  id: number | null
  name: string
  method: string
  path: string
  normalized_path: string
}

/**
 * 冲突组：normalized_path 组内资源归一化路径相同，两两互相冲突；
 * literal_parameter 组只保证基准资源与其他路径重叠，组内资源之间不保证两两冲突
 */
export interface IResourcePathConflictGroupOutput {
  method: string
  type: 'normalized_path' | 'literal_parameter'
  resources_truncated: boolean
  resources: IResourcePathConflictResourceOutput[]
}

/**
 * GET /gateways/{gateway_id}/resources/-/path-conflicts/
 */
export interface IResourcePathConflictOutput {
  has_conflicts: boolean
  conflicts: IResourcePathConflictGroupOutput[]
  truncated: boolean
}

/**
 * GET /gateways/{gateway_id}/resources/backend-path/check/
 */
export interface IBackendPathCheckOutput {
  stage: {
    id: number
    name: string
  }
  backend_urls: string[]
}

/**
 * GET /gateways/{gateway_id}/resources/with/verified-user-required/
 */
export interface IResourceWithVerifiedUserRequiredOutput {
  id: number
  name: string
}

interface IResourceAuthConfigOutput {
  auth_verified_required: boolean
  app_verified_required: boolean
  resource_perm_required: boolean
  oauth2_public_client_enabled?: boolean
  oauth2_personal_client_enabled?: boolean
}

/**
 * GET /gateways/{gateway_id}/resources/{id}/
 */
export interface IResourceRetrieveOutput {
  id: number
  name: string
  is_deprecated: boolean
  deprecated_note: string
  description: string | null
  description_en: string | null
  kind: 'standard' | 'ai'
  method: string
  path: string
  match_subpath: boolean
  enable_websocket: boolean
  is_public: boolean
  allow_apply_permission: boolean
  auth_config: IResourceAuthConfigOutput
  backend: {
    id: number
    config: Record<string, unknown>
  }
  labels: IGatewayLabelOutput[]
  schema: IDocsOpenAPISchema
  released_stages: string[]
}

/** POST /gateways/{gateway_id}/resources/import/doc/preview/ */
export interface IResourceImportDocPreviewOutput {
  doc: string
}

/** POST /gateways/{gateway_id}/resources/import/check/ */
export interface IResourceImportCheckResult extends IImportedResource {
  change_type?: ResourceChangeType
  kind: 'standard' | 'ai'
  path_display: string
  is_deprecated: boolean
  deprecated_note: string
}
