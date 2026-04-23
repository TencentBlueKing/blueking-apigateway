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

// GET /docs/gateways/{gateway_name}/sdks/
export interface IDocsGatewaysSdksListQuery {
  limit?: number
  offset?: number
  language: 'unknown' | 'python' | 'golang' | 'java'
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
