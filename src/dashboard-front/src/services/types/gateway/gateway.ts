/** /gateways/ [GET] */
export interface IGatewaysListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/check-name-available/ [GET] */
export interface IGatewaysCheckNameAvailableReadQuery {
  /** 网关名称 */
  name: string
}

// PATCH /gateways/{gateway_id}/ - 更新网关部分信息
export interface IGatewayUpdateInputSLZ {
  display_name?: string | null // 网关展示名
  description?: string // 网关描述
  maintainers?: string[] // 网关维护人员
  doc_maintainers?: {
    type?: 'user' | 'service_account' // 联系人类型
    contacts?: string[] // 联系人
    service_account?: {
      name?: string // 服务号名称
      link?: string // 服务号链接
    }
  }
  extra_info?: {
    language?: 'python' | 'go' | '' // 语言，允许留空
    repository?: string // 仓库
  }
  developers?: string[] // 网关开发者
  is_public?: boolean // 是否公开，true：公开，false：不公开
  bk_app_codes?: string[] // 网关相关的应用列表
  related_app_codes?: string[] // 管理网关的应用列表
  is_deprecated?: boolean
  deprecated_note?: string
}

// POST /gateways/ - 创建网关
export interface IGatewayCreateInputSLZ {
  name: string
  display_name?: string | null
  description?: string
  maintainers?: string[]
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

// POST /gateways/[{gateway_id}/]check-display-name-available/
export interface IGatewayDisplayNameCheckInput {
  display_name: string
}

// PUT /gateways/{gateway_id}/status/
export interface IGatewayUpdateStatusInputSLZ {
  status: number // 网关状态，0：停用，1：启用
}

/**
 * GET /gateways/
 */
export interface IGatewayListOutput {
  id: number
  name: string
  display_name: string
  description: string | null
  tenant_mode: string
  tenant_id: string
  status: number
  kind: number
  is_public: boolean
  is_deprecated: boolean
  deprecated_note: string | null
  is_official: boolean
  resource_count: number
  stages: {
    id: number
    name: string
    released: boolean
  }[]
  extra_info: IGatewayRetrieveOutput['extra_info']
  created_by: string | null
  created_time: string | null
  updated_time: string | null
  operation_status: {
    link?: string
    source?: string
    status?: string
  }
}

/**
 * GET /gateways/check-name-available/
 */
export interface IGatewayCheckNameAvailableOutput {
  is_available: boolean
}

/**
 * GET /gateways/repo-authorization/
 */
export interface IGatewayCheckRepoAuthOutput {
  authorized: boolean
  message: string
  address: string
  auth_docs: string
}

/**
 * GET /gateways/{gateway_id}/
 */
export interface IGatewayRetrieveOutput {
  id: number
  name: string
  display_name: string
  description: string | null
  maintainers: string[]
  doc_maintainers: {
    type: string
    contacts: string[]
    service_account: {
      name: string
      link: string
    }
  }
  developers: string[]
  status: number
  kind: number | null
  is_public: boolean
  created_by: string | null
  created_time: string | null
  updated_time: string | null
  public_key: string
  is_official: boolean
  allow_update_gateway_auth: boolean
  api_domain: string
  docs_url: string
  public_key_fingerprint: string
  bk_app_codes: string[]
  related_app_codes: string[]
  tenant_mode: string
  tenant_id: string
  extra_info: {
    language?: string
    repository?: string
  }
  links: Partial<Record<'develop' | 'logging' | 'more', {
    name: string
    link: string
  }[]>>
  is_deprecated: boolean
  deprecated_note: string | null
}

/**
 * GET /gateways/{gateway_id}/dev-guideline/
 */
export interface IGatewayDevGuidelineOutput {
  content: string
}

/**
 * GET /gateways/{gateway_id}/releasing-status/
 */
export interface IGatewayReleasingStatusOutput {
  is_releasing: boolean
}

/** 网关展示名查重结果 */
export interface IDisplayNameCheckResult {
  is_available: boolean
}
