import type { DocMaintainers } from '@/types/gateway';

// /docs/esb/boards/{board}/sdks/
export interface IDocsEsbBoardsSdksListResponse {
  board_label: string
  sdk_name: string
  sdk_description: string
  sdk_version_number: string
  sdk_download_url: string
  sdk_install_command: string
}

// /docs/esb/boards/{board}/sdks/doc/
export interface IDocsEsbBoardsSdksDocReadResponse {
  content: string
}

// /docs/esb/boards/{board}/sdks/latest/
export interface IDocsEsbBoardsSdksLatestReadResponse {
  board_label: string
  sdk_name: string
  sdk_description: string
  sdk_version_number: string
  sdk_download_url: string
  sdk_install_command: string
}

// /docs/esb/boards/{board}/sdks/usage-example/
export interface IDocsEsbBoardsSdksUsageExampleReadResponse {
  content: string
}

// /docs/esb/boards/{board}/systems/
export interface IDocsEsbBoardsSystemsListResponse {
  board: string
  board_label: string
  categories: ISystemCategorySLZ[]
}

export interface ISystemCategorySLZ {
  id: string
  name: string
  systems: ISystemSLZ[]
}

export interface ISystemSLZ {
  name: string
  description: string | null
}

// /docs/esb/boards/{board}/systems/{system_name}/
export interface IDocsEsbBoardsSystemsReadResponse {
  name: string
  description: string
  comment: string | null
  maintainers: string[]
}

// /docs/esb/boards/{board}/systems/{system_name}/components/
export interface IDocsEsbBoardsSystemsComponentsListResponse {
  id: number
  name: string
  description: string
  verified_app_required: boolean
  verified_user_required: boolean
  component_permission_required: boolean
}

// /docs/esb/boards/{board}/systems/{system_name}/components/search/
export interface IDocsEsbBoardsSystemsComponentsSearchListResponse {
  id: number
  name: string
  description: string
  system_name: string
}

// /docs/esb/boards/{board}/systems/{system_name}/components/{component_name}/doc/
export interface IDocsEsbBoardsSystemsComponentsDocReadResponse {
  type: string
  content: string
  updated_time: string | null
}

// /docs/gateways/
export interface IDocsGatewaysListResponse {
  kind?: number
  id: number
  name: string
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
  updated_time: string
  source?: DocsDocSource
  render_mode?: DocsDocRenderMode
  plugins?: IDocsResourceDocPlugin[]
  openapi_schema?: IDocsOpenAPISchema
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
