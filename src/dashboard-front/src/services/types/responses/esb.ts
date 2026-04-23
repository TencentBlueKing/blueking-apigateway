// /esb/components/
export interface IESBChannelListResponse {
  count: number
  next: string | null
  previous: string | null
  results: IESBChannel[]
}

// /esb/components/gateway/
export interface IESBGatewayInfoResponse {
  [key: string]: unknown
}

// /esb/components/sync/need-new-release/
export interface IESBNeedNewReleaseResponse {
  [key: string]: unknown
}

// /esb/components/sync/release/histories/
export interface IESBReleaseHistoryListResponse {
  id: number
  created_time: string
  resource_version_name: string
  resource_version_title: string
  resource_version_display: string
  created_by: string
  status: string
  message: string
}

// /esb/components/sync/release/histories/{id}/
export interface IESBReleaseHistoryDetailResponse {
  [key: number]: IComponentResourceBinding
}

// /esb/components/sync/release/histories/{id}/status/
export interface IESBReleaseHistoryStatusResponse {
  status: string
}

// /esb/components/sync/release/status/
export interface IESBReleaseStatusResponse {
  [key: string]: unknown
}

// /esb/components/{id}/
export interface IESBChannelDetailResponse {
  id: number
  system_id: number
  system_name: string
  name: string
  description: string
  method: '' | 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  path: string
  component_codename: string
  permission_level: 'unlimited' | 'normal' | 'sensitive' | 'special'
  verified_user_required: boolean | null
  timeout: number | null
  config: Record<string, string | null>
  is_active: boolean
  api_url: string
  doc_link: string
  is_official: boolean
  updated_time: string | null
  is_created: string
  has_updated: string
}

// /esb/doc-categories/
export interface IDocCategoryListResponse {
  count: number
  next: string | null
  previous: string | null
  results: IDocCategory[]
}

// /esb/doc-categories/{id}/
export interface IDocCategoryDetailResponse {
  id: number
  name: string
  priority: number
  is_official: boolean
  updated_time: string | null
  system_count: number
}

// /esb/status/systems/events/timeline/
export interface ISystemEventsTimelineResponse {
  [key: string]: unknown
}

// /esb/status/systems/summary/
export interface ISystemsSummaryResponse {
  [key: string]: unknown
}

// /esb/status/systems/unstable/
export interface IUnstableSystemsResponse {
  [key: string]: unknown
}

// /esb/status/systems/{system_name}/date-histogram/
export interface ISystemDateHistogramResponse {
  [key: string]: unknown
}

// /esb/status/systems/{system_name}/details/group-by/
export interface ISystemDetailsGroupByResponse {
  [key: string]: unknown
}

// /esb/status/systems/{system_name}/errors/
export interface ISystemErrorsResponse {
  [key: string]: unknown
}

// /esb/status/systems/{system_name}/summary/
export interface ISystemSummaryResponse {
  [key: string]: unknown
}

// /esb/systems/
export interface ISystemListResponse {
  id: number
  name: string
  description: string
  description_en: string | null
  comment: string
  timeout: number | null
  maintainers: string[]
  doc_category_id: number
  doc_category_name: string
  component_count: number
  is_official: boolean
}

// /esb/systems/{id}/
export interface ISystemDetailResponse {
  id: number
  name: string
  description: string
  description_en: string | null
  comment: string
  timeout: number | null
  maintainers: string[]
  doc_category_id: number
  doc_category_name: string
  component_count: number
  is_official: boolean
}

// Definitions
export interface IESBChannel {
  id: number
  system_id: number
  system_name: string
  name: string
  description: string
  method: '' | 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  path: string
  component_codename: string
  permission_level: 'unlimited' | 'normal' | 'sensitive' | 'special'
  verified_user_required: boolean | null
  timeout: number | null
  config: Record<string, string | null>
  is_active: boolean
  api_url: string
  doc_link: string
  is_official: boolean
  updated_time: string | null
  is_created: string
  has_updated: string
}

export interface IComponentResourceBinding {
  resource_id: number
  resource_name: string
  system_name: string
  component_id: number
  component_name: string
  component_method: string
  component_path: string
  component_permission_level: string
}

export interface IComponentReleaseHistoryStatus {
  status: string
}

export interface IDocCategory {
  id: number
  name: string
  priority: number
  is_official: boolean
  updated_time: string | null
  system_count: number
}
