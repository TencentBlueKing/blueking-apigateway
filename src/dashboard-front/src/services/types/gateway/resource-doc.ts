/** /gateways/{gateway_id}/resources/{resource_id}/docs/ [GET] */
export interface IGatewaysResourcesDocsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

// POST /gateways/{gateway_id}/docs/archive/parse/ - 导入资源文档前，检查归档文件是否正确
export interface IDocArchiveParseInputSLZ {
  file: File
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
  selected_resource_docs: ISelectedResourceDoc[]
  file: File
}

// POST /gateways/{gateway_id}/docs/import/by-swagger/ - 根据 swagger 描述文件导入资源文档
export interface IDocImportBySwaggerInputSLZ {
  selected_resource_docs: ISelectedResourceDoc[]
  language: 'zh' | 'en'
  swagger: string
}

interface ISelectedResourceDoc {
  language?: 'zh' | 'en'
  resource_name: string
}

// POST /gateways/{gateway_id}/resources/{resource_id}/docs/ - 创建资源文档
export interface IDocInputSLZ {
  language: string
  content?: string
}

/**
 * POST /gateways/{gateway_id}/docs/archive/parse/
 */
export interface IDocArchiveParseOutput {
  filename: string
  language: string
  content_changed: boolean
  resource: {
    id: number
    name: string
    kind: 'standard' | 'ai'
    method: string
    path: string
    description: string
  } | null
  resource_doc: {
    id: number
    language: string
  } | null
}

/**
 * GET /gateways/{gateway_id}/resources/{resource_id}/docs/
 */
export interface IDocListOutput {
  id: number
  language: string
  content: string | null
}
