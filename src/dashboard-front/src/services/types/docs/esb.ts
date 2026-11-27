// GET /docs/esb/boards/{board}/sdks/
export interface IDocsEsbBoardsSdksListQuery {
  limit?: number
  offset?: number
  language: 'unknown' | 'python' | 'golang' | 'java'
}

// GET /docs/esb/boards/{board}/sdks/doc/
export interface IDocsEsbBoardsSdksDocReadQuery {
  language: 'unknown' | 'python' | 'golang' | 'java'
}

// GET /docs/esb/boards/{board}/sdks/latest/
export interface IDocsEsbBoardsSdksLatestReadQuery {
  language: 'unknown' | 'python' | 'golang' | 'java'
}

// GET /docs/esb/boards/{board}/sdks/usage-example/
export interface IDocsEsbBoardsSdksUsageExampleReadQuery {
  language: 'unknown' | 'python' | 'golang' | 'java'
  system_name: string
  component_name: string
}

// GET /docs/esb/boards/{board}/systems/
export interface IDocsEsbBoardsSystemsListQuery {
  limit?: number
  offset?: number
}

// GET /docs/esb/boards/{board}/systems/{system_name}/components/
export interface IDocsEsbBoardsSystemsComponentsListQuery {
  limit?: number
  offset?: number
}

// GET /docs/esb/boards/{board}/systems/{system_name}/components/search/
export interface IDocsEsbBoardsSystemsComponentsSearchListQuery {
  limit?: number
  offset?: number
  keyword?: string
}

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
