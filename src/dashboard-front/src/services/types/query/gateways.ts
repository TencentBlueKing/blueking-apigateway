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

/** /gateways/monitors/alarm/records/summary/ [GET] */
export interface IGatewaysMonitorsAlarmRecordsSummaryListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 开始时间 */
  time_start?: number | null
  /** 结束时间 */
  time_end?: number | null
}

/** /gateways/{gateway_id}/audits/logs/ [GET] */
export interface IGatewaysAuditsLogsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 开始时间 */
  time_start?: number | null
  /** 结束时间 */
  time_end?: number | null
  /** 关键字 (模糊) */
  keyword?: string
  /** 操作对象 */
  op_object_type?: 'gateway' | 'stage' | 'backend' | 'stage_backend' | 'resource' | 'resource_version' | 'release' | 'gateway_label' | 'plugin' | 'resource_doc' | 'mcp_server' | 'permission'
  /** 操作类型 */
  op_type?: 'create' | 'delete' | 'modify' | 'query'
  /** 实例 */
  op_object?: string
  op_status?: string
  order_by?: string
  /** 操作人 */
  username?: string
}

/** /gateways/{gateway_id}/backends/ [GET] */
export interface IGatewaysBackendsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  name?: string
  type?: string
}

/** /gateways/{gateway_id}/labels/ [GET] */
export interface IGatewaysLabelsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/logs/ [GET] */
export interface IGatewaysLogsListQuery {
  offset?: number // 偏移量，可选
  limit?: number // 限制数量，可选
  query?: string // 查询字符串，可选
  time_range?: number // 时间范围，可选
  time_start?: string | number // 开始时间，可以是字符串或数字，可选
  time_end?: string | number // 结束时间，可以是字符串或数字，可选
  stage_id?: number
  resource_id?: string
  backend_name?: string
}

/** /gateways/{gateway_id}/logs/timechart/ [GET] */
export interface IGatewaysLogsTimechartReadQuery {
  /** 环境 ID */
  stage_id: number
  /** 资源 ID */
  resource_id?: number | null
  /** 后端服务名称 */
  backend_name?: string
  /** 查询条件 */
  query?: string
  /** 包含条件 */
  include?: (string)[]
  /** 排除条件 */
  exclude?: (string)[]
  /** 时间范围 */
  time_range?: number
  /** 起始时间 */
  time_start?: number
  /** 结束时间 */
  time_end?: number
  /** 偏移量 */
  offset?: number
  /** 限制条数 */
  limit?: number
}

/** /gateways/{gateway_id}/logs/{request_id}/ [GET] */
export interface IGatewaysLogsReadQuery {
  /** 随机数 */
  bk_nonce: number
  /** 时间戳 */
  bk_timestamp: number
  /** 签名 */
  bk_signature: string
  /** 分享人 */
  shared_by: string
}

/** /gateways/{gateway_id}/mcp-servers/ [GET] */
export interface IGatewaysMcpServersListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** MCPServer 筛选条件，支持模糊匹配 MCPServer 名称或描述 */
  keyword?: string
  /** MCPServer 状态筛选 */
  status?: 0 | 1
  /** 环境 ID 筛选 */
  stage_id?: number
  /** 标签筛选 */
  label?: string
  /** 分类筛选，支持单个或多个分类名称，多个分类以逗号分隔 */
  categories?: string
  /** 排序方式 */
  order_by?: 'updated_time' | '-updated_time' | 'created_time' | '-created_time' | 'name' | '-name' | '-status'
}

/** /gateways/{gateway_id}/mcp-servers/-/app-permission-apply/ [GET] */
export interface IGatewaysMcpServersAppPermissionApplyListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** MCPServer ID，不传则查询所有 */
  mcp_server_id?: number
  /** 蓝鲸应用 ID */
  bk_app_code?: string
  /** 申请人 */
  applied_by?: string
  /** 审批处理状态 */
  state: 'processed' | 'unprocessed'
}

/** /gateways/{gateway_id}/mcp-servers/-/categories/ [GET] */
export interface IGatewaysMcpServersCategoriesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/mcp-servers/-/filter-options/ [GET] */
export interface IGatewaysMcpServersFilterOptionsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/mcp-servers/-/remote-prompts/ [GET] */
export interface IGatewaysMcpServersRemotePromptsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 搜索关键字 */
  keyword?: string
}

/** /gateways/{gateway_id}/mcp-servers/-/stage-release-check/ [GET] */
export interface IGatewaysMcpServersStageReleaseCheckReadQuery {
  /** Stage ID */
  stage_id: number
  /** 资源版本 ID */
  resource_version_id: number
}

/** /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/ [GET] */
export interface IGatewaysMcpServersPermissionsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 蓝鲸应用 ID */
  bk_app_code?: string
  /** 授权类型 */
  grant_type?: 'grant' | 'apply'
}

/** /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/permissions/app-permission-apply/applicant/ [GET] */
export interface IGatewaysMcpServersPermissionsAppPermissionApplyApplicantListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/mcp-servers/{mcp_server_id}/tools/ [GET] */
export interface IGatewaysMcpServersToolsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/metrics/query-instant/ [GET] */
export interface IGatewaysMetricsQueryInstantListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 环境 id */
  stage_id: number
  /** 后端服务名称 */
  backend_name?: string
  /** 资源 id */
  resource_id?: number | null
  /** metric 类型 */
  metrics: 'requests_total' | 'health_rate'
  /** 时间范围 */
  time_range?: number
  /** 开始时间 */
  time_start?: number
  /** 结束时间 */
  time_end?: number
}

/** /gateways/{gateway_id}/metrics/query-range/ [GET] */
export interface IGatewaysMetricsQueryRangeListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 环境 id */
  stage_id: number
  /** 后端服务名称 */
  backend_name?: string
  /** 资源 id */
  resource_id?: number | null
  /** metric 类型 */
  metrics: 'requests' | 'non_20x_status' | 'app_requests' | 'resource_requests' | 'response_time_90th' | 'response_time_50th' | 'response_time_95th' | 'response_time_99th' | 'ingress' | 'egress'
  /** 时间范围 */
  time_range?: number
  /** 开始时间 */
  time_start?: number
  /** 结束时间 */
  time_end?: number
  /** 精度 */
  step?: 'auto' | '1m' | '5m' | '10m' | '30m' | '1h' | '3h' | '12h'
}

/** /gateways/{gateway_id}/metrics/query-summary/ [GET] */
export interface IGatewaysMetricsQuerySummaryListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 环境 id */
  stage_id: number
  /** 资源 id */
  resource_id?: number | null
  /** app code */
  bk_app_code?: string
  /** metric 类型 */
  metrics: 'requests_total' | 'requests_failed_total'
  /** 时间维度 */
  time_dimension: 'day' | 'week' | 'month'
  /** 开始时间 */
  time_start?: number
  /** 结束时间 */
  time_end?: number
}

/** /gateways/{gateway_id}/metrics/query-summary/caller/ [GET] */
export interface IGatewaysMetricsQuerySummaryCallerListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 环境 id */
  stage_id: number
  /** 开始时间 */
  time_start?: number
  /** 结束时间 */
  time_end?: number
}

/** /gateways/{gateway_id}/metrics/query-summary/export/ [GET] */
export interface IGatewaysMetricsQuerySummaryExportListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/monitors/alarm/records/ [GET] */
export interface IGatewaysMonitorsAlarmRecordsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 开始时间 */
  time_start?: number | null
  /** 结束时间 */
  time_end?: number | null
  /** 告警策略 id */
  alarm_strategy_id?: number | null
  /** 告警状态 */
  status?: 'received' | 'skipped' | 'success' | 'failure'
}

/** /gateways/{gateway_id}/monitors/alarm/strategies/ [GET] */
export interface IGatewaysMonitorsAlarmStrategiesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 查询关键字 */
  keyword?: string
  /** 网关标签 id */
  gateway_label_id?: number | null
  /** 排序字段 */
  order_by?: 'name' | '-name' | 'updated_time' | '-updated_time'
}

/** /gateways/{gateway_id}/permissions/app-permission-apply/ [GET] */
export interface IGatewaysPermissionsAppPermissionApplyListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  bk_app_code?: string
  applied_by?: string
  grant_dimension?: string
}

/** /gateways/{gateway_id}/permissions/app-permission-records/ [GET] */
export interface IGatewaysPermissionsAppPermissionRecordsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/permissions/app-permissions/ [GET] */
export interface IGatewaysPermissionsAppPermissionsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 应用ID */
  bk_app_code?: string
  /** 查询关键字 */
  keyword?: string
  /** 请求路径 */
  resource_path?: string
  grant_type?: 'initialize' | 'apply' | 'renew' | 'auto_renew' | 'sync'
  /** 资源id */
  resource_id?: number
  /** 排序 */
  order_by?: 'bk_app_code' | '-bk_app_code' | 'expires' | '-expires'
  /** 授权维度 */
  grant_dimension?: 'api' | 'resource'
  /** 申请人 */
  applied_by?: string
}

/** /gateways/{gateway_id}/permissions/app-permissions/bk-app-codes/ [GET] */
export interface IGatewaysPermissionsAppPermissionsBkAppCodesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/plugins/ [GET] */
export interface IGatewaysPluginsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 名称关键字 */
  keyword?: string
  /** 范围类型：stage or resource */
  scope_type: 'stage' | 'resource'
  /** 范围 id: stage_id or resource_id */
  scope_id: number
  /** 标签 */
  tag?: string
}

/** /gateways/{gateway_id}/plugins/-/tags/ [GET] */
export interface IGatewaysPluginsTagsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/plugins/{code}/bindings/ [GET] */
export interface IGatewaysPluginsBindingsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/plugins/{scope_type}/{scope_id}/ [GET] */
export interface IGatewaysPluginsReadQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/releases/histories/ [GET] */
export interface IGatewaysReleasesHistoriesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 查询参数关键字 */
  keyword?: string
  /** 环境 id */
  stage_id?: number | null
  /** 创建者 */
  created_by?: string
  /** 开始时间 */
  time_start?: number | null
  /** 结束时间 */
  time_end?: number | null
}

/** /gateways/{gateway_id}/releases/programmable/deploy/histories/ [GET] */
export interface IGatewaysReleasesProgrammableDeployHistoriesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 查询参数关键字 */
  keyword?: string
  /** 环境 id */
  stage_id?: number | null
  /** 创建者 */
  created_by?: string
  /** 开始时间 */
  time_start?: number | null
  /** 结束时间 */
  time_end?: number | null
}

/** /gateways/{gateway_id}/releases/stages/{stage_id}/resources/ [GET] */
export interface IGatewaysReleasesStagesResourcesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/resource-versions/ [GET] */
export interface IGatewaysResourceVersionsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** 资源版本筛选条件，支持模糊匹配 */
  keyword?: string
}

/** /gateways/{gateway_id}/resource-versions/diff/ [GET] */
export interface IGatewaysResourceVersionsDiffReadQuery {
  /** 对比源的版本号id */
  source_resource_version_id: number | null
  /** 对比目标的版本号id */
  target_resource_version_id: number | null
}

/** /gateways/{gateway_id}/resource-versions/programmable/next-deploy-version/ [GET] */
export interface IGatewaysResourceVersionsProgrammableNextDeployVersionReadQuery {
  /** 环境name */
  stage_name: string
  /** 版本类型：major/minor/patch */
  version_type: 'major' | 'minor' | 'patch'
}

/** /gateways/{gateway_id}/resource-versions/{id}/ [GET] */
export interface IGatewaysResourceVersionsReadQuery {
  /** stage_id */
  stage_id?: number
}

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
  /** 标签 ID，多个以逗号 , 分割 */
  label_ids?: string
  /** 后端服务 ID */
  backend_id?: number | null
  /** 后端服务名称，完整匹配 */
  backend_name?: string
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

/** /gateways/{gateway_id}/resources/{resource_id}/docs/ [GET] */
export interface IGatewaysResourcesDocsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/sdks/ [GET] */
export interface IGatewaysSdksListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
  /** sdk语言 */
  language?: 'unknown' | 'python' | 'golang' | 'java'
  /** sdk版本号 */
  version_number?: string
  /** 资源版本号id */
  resource_version_id?: number | null
  /** 查询关键字，支持模糊匹配 */
  keyword?: string
}

/** /gateways/{gateway_id}/stages/ [GET] */
export interface IGatewaysStagesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/stages/{id}/backends/ [GET] */
export interface IGatewaysStagesBackendsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/tenant-apps/ [GET] */
export interface IGatewaysTenantAppsListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}

/** /gateways/{gateway_id}/tests/histories/ [GET] */
export interface IGatewaysTestsHistoriesListQuery {
  /** Number of results to return per page. */
  limit?: number
  /** The initial index from which to return the results. */
  offset?: number
}
