import type { IHealthCheck } from '@/services/source/backend-services.ts';

/**
 * GET /gateways/
 */
export interface IGatewayListOutput {
  id: number
  name: string
  description: string | null
  maintainers: string[]
  doc_maintainers: string[]
  tenant_mode: string
  tenant_id: string
  status: number
  kind: number
  is_public: boolean
  is_official: string
  resource_count: string
  stages: {
    id: number
    name: string
    released: boolean
  }[]
  extra_info: string
  created_by: string | null
  created_time: string | null
  updated_time: string | null
  operation_status: {
    link: string
    source: string
    status: string
  }
}

/**
 * GET /gateways/check-name-available/
 */
export interface IGatewayCheckNameAvailableOutput {
  is_available: boolean
}

/**
 * GET /gateways/logs/query/{request_id}/
 */
export interface IRequestLogOutput {
  request_id: string | null
  timestamp: number | null
  stage: string | null
  resource_id: number | null
  resource_name: string | null
  app_code: string | null
  client_ip: string | null
  method: string | null
  http_host: string | null
  http_path: string | null
  params: string | null
  body: string | null
  backend_scheme: string | null
  backend_method: string | null
  backend_host: string | null
  backend_path: string | null
  response_body: string | null
  status: number | null
  request_duration: number | null
  backend_duration: number | null
  code_name: string | null
  error: string | null
  response_desc: string | null
}

/**
 * GET /gateways/monitors/alarm/records/summary/
 */
export interface IAlarmRecordSummaryQueryOutput {
  gateway: {
    [key: string]: string | null
  }
  alarm_record_count: number
  strategy_summary: {
    id: number
    name: string
    alarm_record_count: number
    latest_alarm_record: {
      [key: string]: string | null
    }
  }[]
}

/**
 * GET /gateways/{gateway_id}/
 */
export interface IGatewayRetrieveOutput {
  id: number
  name: string
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
  links: string
  is_deprecated: boolean
  deprecated_note: string
}

/**
 * GET /gateways/{gateway_id}/ai/batch-translate/
 */
export interface IBatchTranslateOutput {
  message: string
  doc_count: number
}

/**
 * GET /gateways/{gateway_id}/audits/logs/
 */
export interface IAuditEventLogOutput {
  event_id: string
  system: string
  username: string
  op_time: string
  op_type: string
  op_status: string
  op_object_type: string
  op_object_id: string | null
  op_object: string | null
  data_before: string | null
  data_after: string | null
  comment: string | null
}

/**
 * GET /gateways/{gateway_id}/backends/
 */
export interface IBackendListOutput {
  id: number
  name: string
  description: string
  resource_count: string
  deletable: string
  updated_time: string | null
}

/**
 * GET /gateways/{gateway_id}/backends/{id}/
 */
export interface IBackendRetrieveOutput {
  id: number
  name: string
  description: string | null
  configs: {
    checks?: IHealthCheck
    hosts: {
      scheme: string
      host: string
      weight: number
    }[]
    loadbalance: string
    stage: {
      id: number
      name: string
    }
    timeout: number
    type: string
    hash_on?: string
    key?: string
  }[]
}

/**
 * GET /gateways/{gateway_id}/dev-guideline/
 */
export interface IGatewayDevGuidelineOutput {
  content: string
}

/**
 * GET /gateways/{gateway_id}/docs/archive/parse/
 */
export interface IDocArchiveParseOutput {
  filename: string
  language: string
  content_changed: boolean
  resource: {
    id: number
    name: string
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
 * GET /gateways/{gateway_id}/labels/
 */
export interface IGatewayLabelOutput {
  id: number
  name: string
}

/**
 * GET /gateways/{gateway_id}/labels/{id}/
 */
export interface IGatewayLabelRetrieveOutput {
  id: number
  name: string
}

/**
 * GET /gateways/{gateway_id}/logs/
 */
export interface ILogListOutput {
  count: number
  results: Array<{
    request_id: string | null
    timestamp: number | null
    stage: string | null
    resource_id: number | null
    resource_name: string | null
    app_code: string | null
    client_ip: string | null
    method: string | null
    http_host: string | null
    http_path: string | null
    params: string | null
    body: string | null
    backend_scheme: string | null
    backend_method: string | null
    backend_host: string | null
    backend_path: string | null
    response_body: string | null
    status: number | null
    request_duration: number | null
    backend_duration: number | null
    code_name: string | null
    error: string | null
    response_desc: string | null
  }>
  fields: Array<{
    field: string
    is_filter: true
    label: string
  }> | null
  has_next: boolean
  has_previous: boolean
}

/**
 * GET /gateways/{gateway_id}/logs/timechart/
 */
export interface ITimeChartOutput {
  series: number[]
  timeline: number[]
}

/**
 * GET /gateways/{gateway_id}/logs/{request_id}/
 */
export interface IRequestLogDetailOutput {
  fields: Array<{
    field: string
    is_filter: true
    label: string
  }>
  results: Array<{
    request_id: string | null
    timestamp: number | null
    stage: string | null
    resource_id: number | null
    resource_name: string | null
    app_code: string | null
    client_ip: string | null
    method: string | null
    http_host: string | null
    http_path: string | null
    params: string | null
    body: string | null
    backend_scheme: string | null
    backend_method: string | null
    backend_host: string | null
    backend_path: string | null
    response_body: string | null
    status: number | null
    request_duration: number | null
    backend_duration: number | null
    code_name: string | null
    error: string | null
    response_desc: string | null
  }>
}

/**
 * GET /gateways/{gateway_id}/logs/{request_id}/link/
 */
export interface ILogLinkOutput {
  link: string
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/
 */
export interface IMCPServerListOutput {
  id: number
  name: string
  title: string
  description: string
  is_public: boolean
  labels: (string | null)[]
  resource_names: string[]
  tool_names: string[]
  tools_count: number
  url: string
  status: number
  protocol_type: string
  stage: any
  updated_time: string
  created_time: string
  categories: string
  is_official: boolean
  is_featured: boolean
  prompts_count: number
  oauth2_public_client_enabled?: boolean
  app_permission_risk?: any
  [key: string]: any
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/app-permission-apply/
 */
export interface IMCPServerAppPermissionApplyListOutput {
  id: number
  bk_app_code: string
  applied_by: string
  applied_time: string
  status: string
  mcp_server: {
    id: number
    name: string
    title: string
  }
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/categories/
 */
export interface IMCPServerCategoryOutput {
  id: number
  name: string
  display_name: string
  description: string
  sort_order: number
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/filter-options/
 */
export interface IMCPServerFilterOptionsOutput {
  stages: {
    [key: string]: string | number | null
  }[]
  labels: string[]
  categories: {
    [key: string]: string | number | null
  }[]
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/remote-prompts/
 */
export interface IMCPServerRemotePromptsOutput {
  prompts: {
    id: number
    name: string
    code: string
    content: string
    updated_time: string
    updated_by: string
    labels: string[]
    is_public: boolean
    space_code: string
    space_name: string
  }[]
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/remote-prompts/batch/
 */
export interface IMCPServerRemotePromptsBatchOutput {
  prompts: {
    id: number
    name: string
    code: string
    content: string
    updated_time: string
    updated_by: string
    labels: string[]
    is_public: boolean
    space_code: string
    space_name: string
  }[]
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/-/stage-release-check/
 */
export interface IMCPServerStageReleaseCheckOutput {
  has_related_changes: boolean
  deleted_resource_count: number
  details: {
    resource_name: string
    mcp_server: {
      id: number
      name: string
      title: string
    }
  }[]
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/
 */
export interface IMCPServerRetrieveOutput {
  id: number
  name: string
  title: string
  description: string
  is_public: boolean
  labels: (string | null)[]
  resource_names: string[]
  tool_names: string[]
  tools_count: number
  url: string
  status: number
  protocol_type: string
  stage: any
  updated_time: string
  created_time: string
  categories: string | any[]
  is_official: boolean
  is_featured: boolean
  prompts: string | any[]
  oauth2_public_client_enabled?: boolean
  tools?: any[]
  gateway?: {
    id: number
    name: string
    is_official?: boolean
  }
  [key: string]: any
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/configs/
 */
export interface IMCPServerConfigListOutput {
  configs: {
    name: string
    display_name: string
    content: string
    install_url: string
  }[]
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/guideline/
 */
export interface IMCPServerGuidelineOutput {
  content: string
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/
 */
export interface IMCPServerAppPermissionListOutput {
  id: number
  bk_app_code: string
  expires: string
  grant_type: string
  mcp_server: {
    id: number
    name: string
    title: string
  }
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/app-permission-apply/applicant/
 */
export interface IMCPServerAppPermissionApplyApplicantOutput {
  applicants: string[]
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/{id}/
 */
export interface IMCPServerPermissionRetrieveOutput {
  id: number
  bk_app_code: string
  expires: string
  grant_type: string
  mcp_server: {
    id: number
    name: string
    title: string
  }
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/tools/
 */
export interface IMCPServerToolOutput {
  id: number
  name: string
  tool_name: string
  description: string
  method: string
  path: string
  verified_user_required: boolean
  verified_app_required: boolean
  resource_perm_required: boolean
  allow_apply_permission: boolean
  labels: string
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/tools/{tool_name}/doc/
 */
export interface IMCPServerToolDocOutput {
  type: string
  content: string
  updated_time: string
  schema: {
    [key: string]: string | null
  }
}

/**
 * GET /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/user-custom-doc/
 */
export interface IMCPServerUserCustomDocOutput {
  content: string
}

/**
 * GET /gateways/{gateway_id}/metrics/query-instant/
 */
export interface IMetricInstantOutput {
  instant: number
}

/**
 * GET /gateways/{gateway_id}/metrics/query-range/
 */
export interface IMetricRangeOutput {
  metrics: unknown[]
  series: unknown[]
}

/**
 * GET /gateways/{gateway_id}/metrics/query-summary/
 */
export interface IMetricSummaryOutput {
  count: number
}

/**
 * GET /gateways/{gateway_id}/metrics/query-summary/caller/
 */
export interface IMetricSummaryCallerOutput {
  count: number
}

/**
 * GET /gateways/{gateway_id}/monitors/alarm/records/
 */
export interface IAlarmRecordListOutput {
  id: number
  alarm_id: string
  status: string
  message: string
  created_time: string
  alarm_strategy_names: string
  comment: string
}

/**
 * GET /gateways/{gateway_id}/monitors/alarm/records/{id}/
 */
export interface IAlarmRecordRetrieveOutput {
  id: number
  alarm_id: string
  status: string
  message: string
  created_time: string
  alarm_strategy_names: string
  comment: string
}

/**
 * GET /gateways/{gateway_id}/monitors/alarm/strategies/
 */
export interface IAlarmStrategyListOutput {
  id: number
  name: string
  alarm_type: string
  alarm_subtype: string
  enabled: boolean
  updated_time: string | null
  gateway_labels: string
  effective_stages: string
}

/**
 * GET /gateways/{gateway_id}/monitors/alarm/strategies/{id}/
 */
export interface IAlarmStrategyRetrieveOutput {
  id: number
  name: string
  alarm_type: string
  alarm_subtype: string
  enabled: boolean
  updated_time: string | null
  gateway_labels: string
  effective_stages: string
}

/**
 * GET /gateways/{gateway_id}/permissions/app-gateway-permissions/
 */
export interface IAppGatewayPermissionListOutput {
  allow_apply_by_gateway: boolean
  name: string
}

/**
 * GET /gateways/{gateway_id}/permissions/app-permission-apply/
 */
export interface IAppPermissionApplyListOutput {
  id: number
  bk_app_code: string
  resource_ids: number[]
  status: string
  reason: string
  expire_days: number
  grant_dimension: string
  created_time: string | null
  expire_days_display: string
  grant_dimension_display: string
  applied_by: string
}

/**
 * GET /gateways/{gateway_id}/permissions/app-permission-apply/{id}/
 */
export interface IAppPermissionApplyRetrieveOutput {
  id: number
  bk_app_code: string
  resource_ids: number[]
  status: string
  reason: string
  expire_days: number
  grant_dimension: string
  created_time: string | null
  expire_days_display: string
  grant_dimension_display: string
  applied_by: string
}

/**
 * GET /gateways/{gateway_id}/permissions/app-permission-records/
 */
export interface IAppPermissionRecordListOutput {
  id: number
  bk_app_code: string
  applied_by: string
  applied_time: string
  handled_by: string
  handled_time: string | null
  status: string
  grant_dimension: string
  comment: string
  reason: string
  expire_days: number
  gateway_name: string
  resource_ids: string
  handled_resources: string
  expire_days_display: string
  grant_dimension_display: string
}

/**
 * GET /gateways/{gateway_id}/permissions/app-permission-records/{id}/
 */
export interface IAppPermissionRecordRetrieveOutput {
  id: number
  bk_app_code: string
  applied_by: string
  applied_time: string
  handled_by: string
  handled_time: string | null
  status: string
  grant_dimension: string
  comment: string
  reason: string
  expire_days: number
  gateway_name: string
  resource_ids: string
  handled_resources: string
  expire_days_display: string
  grant_dimension_display: string
}

/**
 * GET /gateways/{gateway_id}/permissions/app-permissions/
 */
export interface IAppPermissionListOutput {
  id: number
  bk_app_code: string
  resource_id: string
  resource_name: string
  resource_path: string
  resource_method: string
  expires: string
  grant_dimension: string
  grant_type: string
  renewable: string
}

// unknown api
export interface IGatewayTenantAppListOutput {
  bk_app_code: string
  name: string
  description: string
  bk_tenant: {
    mode: string
    id: string
  }
}

/**
 * GET /gateways/{gateway_id}/permissions/app-resource-permissions/
 */
export interface IAppResourcePermissionListOutput {
  id: number
  name: string
  gateway_name: string
  description: string
  permission_level: string
  permission_status: string
  doc_link: string
}

/**
 * GET /gateways/{gateway_id}/plugins/
 */
export interface IPluginTypeListOutput {
  id: number
  name: string
  code: string
  is_public: boolean
  notes: string
  related_scope_count: string
  is_bound: string
  tags: string
}

/**
 * GET /gateways/{gateway_id}/plugins/-/tags/
 */
export interface IPluginTypeTagsOutput {
  tags: string[]
}

/**
 * GET /gateways/{gateway_id}/plugins/{code}/bindings/
 */
export interface IPluginBindingListOutput {
  stages: {
    id: number
    name: string
  }[]
  resources: {
    id: number
    name: string
  }[]
}

/**
 * GET /gateways/{gateway_id}/plugins/{code}/form/
 */
export interface IPluginFormOutput {
  id: number
  language: string
  notes: string
  example: string
  style: string
  default_value: string | null
  config: {
    [key: string]: string | null
  }
  type_id: string
  type_code: string
  type_name: string
}

/**
 * GET /gateways/{gateway_id}/plugins/{scope_type}/{scope_id}/
 */
export interface IScopePluginConfigListOutput {
  code: string
  name: string
  config: {
    [key: string]: string | null
  }
  config_id: number
  related_scope_count: string
}

/**
 * GET /gateways/{gateway_id}/plugins/{scope_type}/{scope_id}/{code}/configs/{id}/
 */
export interface IPluginConfigRetrieveOutput {
  id: number
  name: string | null
  yaml: string | null
  type_id: number
}

/**
 * GET /gateways/{gateway_id}/releases/
 */
export interface IReleaseHistoryOutput {
  id: number
  stage: {
    id: number
    name: string
  }
  resource_version_display: string
  created_time: string
  created_by: string
  source: string
  duration: number
  status: string
}

/**
 * GET /gateways/{gateway_id}/releases/histories/
 */
export interface IReleaseHistoryListOutput {
  id: number
  stage: {
    id: number
    name: string
  }
  resource_version_display: string
  created_time: string
  created_by: string
  source: string
  duration: number
  status: string
}

/**
 * GET /gateways/{gateway_id}/releases/histories/latest/
 */
export interface IReleaseHistoryLatestOutput {
  id: number
  stage: {
    id: number
    name: string
  }
  resource_version_display: string
  created_time: string
  created_by: string
  source: string
  duration: number
  status: string
}

/**
 * GET /gateways/{gateway_id}/releases/histories/{history_id}/events/
 */
export interface IReleaseHistoryEventRetrieveOutput {
  id: number
  stage: {
    id: number
    name: string
  }
  resource_version_display: string
  created_time: string
  created_by: string
  source: string
  duration: number
  status: string
  events: {
    id: number
    release_history_id: number
    name: string
    step: number
    status: string
    created_time: string
    detail: {
      [key: string]: string | null
    }
  }[]
  events_template: Array<{
    description: string
    name: string
    step: number
  }>
  data_plane: {
    description: string
    id: number
    name: string
  } | null
}

/**
 * GET /gateways/{gateway_id}/releases/programmable/deploy/histories/
 */
export interface IDeployHistoryListOutput {
  deploy_id: string
  history_id: number
  commit_id: string
  branch: string
  source: string
  stage: {
    id: number
    name: string
  }
  status: string
  created_time: string
  version: string
  created_by: string
}

/**
 * GET /gateways/{gateway_id}/releases/programmable/deploy/histories/{history_id}/events/
 */
export interface IGetDeployEventsByHistoryIdOutput {
  id: number
  stage: {
    id: number
    name: string
  }
  resource_version_display: string
  created_time: string
  created_by: string
  source: string
  duration: number
  status: string
  events: {
    id: number
    release_history_id: number
    name: string
    step: number
    status: string
    created_time: string
    detail: {
      [key: string]: string | null
    }
  }[]
  events_template: any
  paas_deploy_info: any
  data_plane: {
    description: string
    id: number
    name: string
  } | null
}

/**
 * GET /gateways/{gateway_id}/releases/programmable/deploy/{deploy_id}/histories/events/
 */
export interface IGetDeployEventsByDeployIdOutput {
  id: number
  stage: {
    id: number
    name: string
  }
  resource_version_display: string
  created_time: string
  created_by: string
  source: string
  duration: number
  status: string
  events: {
    id: number
    release_history_id: number
    name: string
    step: number
    status: string
    created_time: string
    detail: {
      [key: string]: string | null
    }
  }[]
  events_template: string
  paas_deploy_info: string
  data_plane: {
    description: string
    id: number
    name: string
  } | null
}

/**
 * GET /gateways/{gateway_id}/releases/stages/{stage_id}/resources/
 */
export interface IResourceListOutput {
  id: number
  name: string | null
  description: string | null
  method: string
  path: string
  created_time: string | null
  updated_time: string | null
  backend: string
  labels: string
  docs: string
  has_updated: string
  plugin_count: string
  auth_config: string
}

/**
 * GET /gateways/{gateway_id}/releases/stages/{stage_id}/resources/{resource_id}/schema/
 */
export interface IReleaseResourceSchemaOutput {
  resource_id: number
  body_schema: any
  body_example: any
  parameter_schema: any
  response_schema: any
}

/**
 * GET /gateways/{gateway_id}/releasing-status/
 */
export interface IGatewayReleasingStatusOutput {
  is_releasing: boolean
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
  released_stages: string
  sdk_count: string
}

/**
 * GET /gateways/{gateway_id}/resource-versions/diff/
 */
export interface IResourceVersionDiffOutput {
  add: {
    id: number
    name: string
    method: string
    path: string
    diff: {
      [key: string]: string | null
    } | null
  }[]
  delete: {
    id: number
    name: string
    method: string
    path: string
    diff: {
      [key: string]: string | null
    } | null
  }[]
  update: {
    source: Record<string, any>
    target: Record<string, any>
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
    description: string
    description_en: string
    method: string
    path: string
    match_subpath: boolean
    enable_websocket: boolean
    is_public: boolean
    allow_apply_permission: boolean
    doc_updated_time: string
    proxy: string
    contexts: {
      [key: string]: string | null
    }
    plugins: {
      binding_type: string
      config: Record<string, any>
      id: number
      name: string
      priority: number
      type: string
    }[]
    has_openapi_schema: boolean
    openapi_schema: string
  }[]
  created_time: string
  created_by: string
}

/**
 * GET /gateways/{gateway_id}/resources/
 */
export interface IResourceListPageOutput {
  id: number
  name: string | null
  description: string | null
  method: string
  path: string
  created_time: string | null
  updated_time: string | null
  backend: string
  labels: string
  docs: string
  has_updated: string
  plugin_count: string
  auth_config: string
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

/**
 * GET /gateways/{gateway_id}/resources/{id}/
 */
export interface IResourceRetrieveOutput {
  id: number
  name: string | null
  description: string | null
  description_en: string | null
  method: string
  path: string
  match_subpath: boolean
  enable_websocket: boolean
  is_public: boolean
  allow_apply_permission: boolean
  auth_config: string
  backend: string
  labels: string
  schema: string
}

/**
 * GET /gateways/{gateway_id}/resources/{resource_id}/docs/
 */
export interface IDocListOutput {
  id: number
  language: string
  content: string | null
}

/**
 * GET /gateways/{gateway_id}/resources/{resource_id}/docs/{id}/
 */
export interface IDocRetrieveOutput {
  id: number
  language: string
  content: string | null
}

/**
 * GET /gateways/{gateway_id}/sdks/
 */
export interface IGatewaySDKListOutput {
  download_url: string
  id: number
  language: string
  version_number: string
  created_time: string
  updated_time: string
  created_by: string
  name: string
  resource_version: {
    id: number
    version: string
  }
}

/**
 * GET /gateways/{gateway_id}/stages/
 */
export interface IStageListOutput {
  id: number
  name: string
  description: string | null
  description_en: string | null
  status: number
  created_time: string | null
  release: {
    status: string
    created_time: string
    created_by: string
  }
  resource_version: {
    id: number
    version: string
    schema_version: string
  }
  publish_id: number
  publish_version: string
  publish_validate_msg: string
  new_resource_version: string
}

/**
 * GET /gateways/{gateway_id}/stages/{id}/
 */
export interface IStageRetrieveOutput {
  id: number
  name: string
  description: string | null
  description_en: string | null
  status: number
  created_time: string | null
  release: {
    status: string
    created_time: string
    created_by: string
  }
  resource_version: {
    id: number
    version: string
    schema_version: string
  }
  publish_id: number
  publish_version: string
  publish_validate_msg: string
  new_resource_version: string
}

/**
 * GET /gateways/{gateway_id}/stages/{id}/backends/
 */
export interface IStageBackendListOutput {
  id: number
  name: string
  config: {
    type?: string
    timeout: number
    loadbalance: string
    hash_on?: string
    key?: string
    hosts: {
      scheme: string
      host: string
      weight?: number
    }[]
    checks?: {
      active?: {
        type?: string
        timeout?: number
        concurrency?: number
        http_path?: string
        https_verify_certificate?: boolean
        healthy?: {
          http_statuses?: number[]
          successes?: number
          interval?: number
        }
        unhealthy?: {
          http_statuses?: number[]
          http_failures?: number
          tcp_failures?: number
          timeouts?: number
          interval?: number
        }
      }
      passive?: {
        type?: string
        healthy?: {
          http_statuses?: number[]
          successes?: number
        }
        unhealthy?: {
          http_statuses?: number[]
          http_failures?: number
          tcp_failures?: number
          timeouts?: number
        }
      }
    }
  }
}

/**
 * GET /gateways/{gateway_id}/stages/{id}/backends/{backend_id}/
 */
export interface IStageBackendRetrieveOutput {
  id: string
  name: string
  config: string
}

/**
 * GET /gateways/{gateway_id}/stages/{id}/programmable/
 */
export interface IProgrammableStageDeployOutput {
  branch: string
  commit_id: string
  created_by: string | null
  created_time: string
  deploy_id: string
  latest_deployment: {
    branch: string
    commit_id: string
    deploy_id: string
    history_id: number
    status: string
    version: string
  }
  repo_info: {
    branch_commit_info: {
      [branch: string]: {
        commit_id: string
        extra: object
        last_update: string
        message: string
        type: string
      }
    }
    branch_list: string[]
    repo_url: string
  }
  status: string
  version: string
}

/**
 * GET /gateways/{gateway_id}/stages/{id}/vars/
 */
export interface IStageVarsOutput {
  vars: {
    [key: string]: string
  }
}

/**
 * GET /gateways/{gateway_id}/tenant-apps/
 */
export interface IGatewayTenantAppListOutput {
  bk_app_code: string
  name: string
  description: string
  bk_tenant: {
    mode: string
    id: string
  }
}

/**
 * GET /gateways/{gateway_id}/tests/
 */
export interface IAPITestOutput {
  status_code: number
  proxy_time: number
  size: number
  body: string
  headers: {
    [key: string]: string | null
  }
}

/**
 * GET /gateways/{gateway_id}/tests/histories/
 */
export interface IAPIDebugHistoriesListOutput {
  id: number
  created_time: string | null
  gateway_id: number
  resource_name: string
  request: any
  response: any
}

/**
 * GET /gateways/{gateway_id}/tests/histories/{id}/
 */
export interface IAPIDebugHistoriesRetrieveOutput {
  id: number
  created_time: string | null
  gateway_id: number
  resource_name: string
  request: any
  response: any
}
