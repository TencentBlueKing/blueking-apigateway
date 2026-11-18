import type { DocMaintainers } from '@/types/gateway';

// GET /docs/gateways/
export interface IDocsGatewaysListQuery {
  limit?: number
  offset?: number
  keyword?: string
  show_plugin_gateway?: boolean
}

// GET /docs/gateways/{gateway_name}/resources/
export interface IDocsGatewaysResourcesListQuery {
  limit?: number
  offset?: number
  stage_name: string
}

// GET /docs/gateways/{gateway_name}/resources/{resource_name}/doc/
export interface IDocsGatewaysResourcesDocReadQuery {
  stage_name: string
  source?: string
}

// GET /docs/gateways/{gateway_name}/sdks/usage-example/
export interface IDocsGatewaysSdksUsageExampleReadQuery {
  language: 'unknown' | 'python' | 'golang' | 'java'
  stage_name: string
  resource_name: string
  resource_id?: number
  source?: string
}

// GET /docs/gateways/{gateway_name}/stages/
export interface IDocsGatewaysStagesListQuery {
  limit?: number
  offset?: number
}

// GET /docs/sdks/doc/
export interface IDocsSdksDocReadQuery {
  language: 'unknown' | 'python' | 'golang' | 'java'
}

// GET /docs/gateways/{gateway_name}/
export interface IDocsGatewaysReadQuery {
  source?: string
}

export interface IDocsPermissionApplyInput {
  bk_app_code: string
  reason: string
  resource_name: string
}

// /docs/gateways/
export interface IDocsGatewaysListResponse {
  kind?: number
  id: number
  name: string
  display_name?: string
  description: string | null
  tenant_mode: string | null
  tenant_id: string | null
  maintainers: string[]
  doc_maintainers: DocMaintainers
  is_official: boolean
  is_plugin_gateway: boolean
  is_deprecated: boolean
  deprecated_note: string
  api_url: string | null
  sdks: IDocsGatewaySDK[]
}

// /docs/gateways/{gateway_name}/
export type IDocsGatewaysReadResponse = IDocsGatewaysListResponse;

// /docs/gateways/{gateway_name}/resources/
export interface IDocsGatewaysResourcesListResponse {
  id: number
  name: string
  description: string | null
  method: string
  path: string
  verified_user_required: boolean
  verified_app_required: boolean
  resource_perm_required: boolean
  allow_apply_permission: boolean
  labels: {
    id: number
    name: string
  }[]
  is_deprecated: boolean
  deprecated_note: string
}

export interface IDocsResourceDocPlugin {
  type: string
  config?: Record<string, unknown>
}

// 文档参数渲染所使用的 OpenAPI Schema 节点。
export interface IDocsSchemaObject {
  type?: string | string[]
  description?: string
  required?: string[]
  properties?: Record<string, IDocsSchemaObject>
  items?: IDocsSchemaObject
  [keyword: string]: unknown
}

export interface IDocsOpenAPISchema {
  none_schema?: boolean
  parameters?: {
    name: string
    in: 'header' | 'query' | 'path' | 'cookie'
    required?: boolean
    description?: string
    schema?: IDocsSchemaObject
  }[]
  requestBody?: {
    description?: string
    required?: boolean
    content?: Record<string, { schema?: IDocsSchemaObject }>
  }
  responses?: Record<string, {
    description?: string
    content?: Record<string, { schema?: IDocsSchemaObject }>
  }>
}

export type DocsDocSource = 'import' | 'custom' | 'openapi';

export type DocsDocRenderMode = 'auto' | 'schema_first' | 'markdown_first';

// /docs/gateways/{gateway_name}/resources/{resource_name}/doc/
export interface IDocsGatewaysResourcesDocReadResponse {
  type: string
  content: string
  updated_time: string | null
  is_deprecated: boolean
  deprecated_note: string
  source?: DocsDocSource
  render_mode?: DocsDocRenderMode
  plugins?: IDocsResourceDocPlugin[]
  openapi_schema?: IDocsOpenAPISchema
  // 请求方法，如 GET
  method?: string
  // 完整调用地址
  resource_url?: string
  // 认证说明（Markdown）
  auth_content?: string
  // 文档正文（Markdown）
  body_content?: string
}

// POST /docs/gateways/{gateway_name}/permissions/apply/
export interface IDocsGatewaysPermissionApplyResponse {
  record_id: number
  bk_app_code: string
  gateway_name: string
  resource_name: string
  itsm_ticket_id: string
  itsm_ticket_url: string
}

// /docs/gateways/{gateway_name}/sdks/
export interface IDocsGatewaysSdksListResponse {
  stage: IStageSLZ
  resource_version: IResourceVersionSLZ
  sdk: ISDKSLZ | null
}

export interface IStageSLZ {
  id: number
  name: string
}

export interface IResourceVersionSLZ {
  id: number
  version: string
}

export interface ISDKSLZ {
  name: string
  version: string
  url: string
  install_command: string
}

// /docs/gateways/{gateway_name}/sdks/usage-example/
export interface IDocsGatewaysSdksUsageExampleReadResponse {
  content: string
}

// /docs/gateways/{gateway_name}/stages/
export interface IDocsGatewaysStagesListResponse {
  id: number
  name: string
  description: string | null
}

// /docs/sdks/doc/
export interface IDocsSdksDocReadResponse {
  content: string
}

// 网关列表和详情响应中内嵌的 SDK。
export interface IDocsGatewaySDK extends ISDKSLZ {
  language: string
}
