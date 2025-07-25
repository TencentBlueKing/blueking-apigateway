import http from '../http';

const path = '/gateways';

// 定义搜索参数类型
export interface ISearchParamsType {
  stage_id?: number // 阶段ID，可选
  resource_id?: string // 资源ID，可选
  metrics?: string // 指标，可选
  time_start?: number // 开始时间，可选
  time_end?: number // 结束时间，可选
  time_range?: string // 时间范围，可选
  limit?: number // 限制数量，可选
  offset?: number // 偏移量，可选
}

// 定义瞬时类型
type InstantType = { instant: number };

// 定义统计数据类型
export interface IStatisticsType {
  requests_total?: InstantType // 总请求数，可选
  health_rate?: InstantType // 健康率，可选
}

// 定义系列项类型
export interface ISeriesItemType {
  alias: string // 别名
  datapoints: Array<Array<number>> // 数据点数组
  dimensions: object // 维度
  metric_field: string // 指标字段
  target: string // 目标
  unit: string // 单位
}

// 定义图表系列类型
type IChartsSires = {
  metrics?: Array<unknown> // 指标数组，可选
  series?: Array<ISeriesItemType> // 系列项数组，可选
};

// 定义图表数据类型
export interface IChartDataType {
  requests_total?: IChartsSires // 总请求数图表系列，可选
  requests?: IChartsSires // 请求图表系列，可选
  non_20x_status?: IChartsSires // 非20x状态图表系列，可选
  app_requests?: IChartsSires // 应用请求图表系列，可选
  resource_requests?: IChartsSires // 资源请求图表系列，可选
  ingress?: IChartsSires // 入口图表系列，可选
  egress?: IChartsSires // 出口图表系列，可选
  failed_500_requests?: IChartsSires // 失败的500请求图表系列，可选
  response_time?: IChartsSires // 响应时间图表系列，可选
  response_time_90th?: IChartsSires // 响应时间90百分位图表系列，可选
}

// 定义图表数据加载状态类型
export interface IChartDataLoading {
  requests_total?: boolean // 总请求数加载状态，可选
  health_rate?: boolean // 健康率加载状态，可选
  requests?: boolean // 请求加载状态，可选
  non_20x_status?: boolean // 非20x状态加载状态，可选
  app_requests?: boolean // 应用请求加载状态，可选
  resource_requests?: boolean // 资源请求加载状态，可选
  ingress?: boolean // 入口加载状态，可选
  egress?: boolean // 出口加载状态，可选
  response_time_90th?: boolean // 响应时间90百分位加载状态，可选
}

/**
 *  查询 metrics
 * @param apigwId 网关id
 */
export const getApigwMetrics = (apigwId: number, params: any) => http.get(`${path}/${apigwId}/metrics/query-range/`, params);

/**
 *  请求总数健康率
 * @param apigwId 网关id
 */
export const getApigwMetricsInstant = (apigwId: number, params: ISearchParamsType) => http.get(`${path}/${apigwId}/metrics/query-instant/`, params);

/**
 *  获取流程日志列表
 * @param apigwId 网关id
 */
export const getApigwResources = (apigwId: number, params: any) => http.get(`${path}/${apigwId}/resources/`, params);

/**
 *  获取流程日志列表
 * @param apigwId 网关id
 */
export const getApigwStages = (apigwId: number, params: any) => http.get(`${path}/${apigwId}/stages/`, params);
