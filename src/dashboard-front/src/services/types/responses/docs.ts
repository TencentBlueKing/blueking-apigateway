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
  maintainers: string | null
}

// /docs/esb/boards/{board}/systems/{system_name}/components/
export interface IDocsEsbBoardsSystemsComponentsListResponse {
  id: number
  name: string
  description: string
  verified_app_required: string
  verified_user_required: string
  component_permission_required: string
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
  id: number
  name: string
  description: string | null
  tenant_mode: string | null
  tenant_id: string | null
  maintainers: (string | null)[]
  doc_maintainers: object
  is_official: string | null
  is_plugin_gateway: string | null
  is_deprecated: boolean
  deprecated_note: string
  api_url: string | null
  sdks: string | null
}

// /docs/gateways/{gateway_name}/
export interface IDocsGatewaysReadResponse {
  id: number
  name: string
  description: string | null
  tenant_mode: string | null
  tenant_id: string | null
  maintainers: (string | null)[]
  doc_maintainers: object
  is_official: string | null
  is_plugin_gateway: string | null
  is_deprecated: boolean
  deprecated_note: string
  api_url: string | null
  sdks: string | null
}

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
  labels: string | null
}

// /docs/gateways/{gateway_name}/resources/{resource_name}/doc/
export interface IDocsGatewaysResourcesDocReadResponse {
  type: string
  content: string
  updated_time: string
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
