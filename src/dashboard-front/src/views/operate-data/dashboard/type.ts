// 定义搜索参数类型
export interface SearchParamsType {
  stage_id?: number; // 阶段ID，可选
  resource_id?: string; // 资源ID，可选
  metrics?: string; // 指标，可选
  time_start?: number; // 开始时间，可选
  time_end?: number; // 结束时间，可选
  time_range?: string; // 时间范围，可选
  limit?: number; // 限制数量，可选
  offset?: number; // 偏移量，可选
}

// 定义瞬时类型
type InstantType = {
  instant: number; // 瞬时值
};

// 定义统计数据类型
export interface StatisticsType {
  requests_total?: InstantType; // 总请求数，可选
  health_rate?: InstantType; // 健康率，可选
}

// 定义系列项类型
export interface SeriesItemType {
  alias: string; // 别名
  datapoints: Array<Array<number>>; // 数据点数组
  dimensions: Object; // 维度
  metric_field: string; // 指标字段
  target: string; // 目标
  unit: string; // 单位
}

// 定义图表系列类型
type ChartsSires = {
  metrics?: Array<unknown>; // 指标数组，可选
  series?: Array<SeriesItemType>; // 系列项数组，可选
};

// 定义图表数据类型
export interface ChartDataType {
  requests_total?: ChartsSires; // 总请求数图表系列，可选
  requests?: ChartsSires; // 请求图表系列，可选
  non_20x_status?: ChartsSires; // 非20x状态图表系列，可选
  app_requests?: ChartsSires; // 应用请求图表系列，可选
  resource_requests?: ChartsSires; // 资源请求图表系列，可选
  ingress?: ChartsSires; // 入口图表系列，可选
  egress?: ChartsSires; // 出口图表系列，可选
  failed_500_requests?: ChartsSires; // 失败的500请求图表系列，可选
  response_time?: ChartsSires; // 响应时间图表系列，可选
  response_time_90th?: ChartsSires; // 响应时间90百分位图表系列，可选
}

// 定义图表数据加载状态类型
export interface ChartDataLoading {
  requests_total?: boolean; // 总请求数加载状态，可选
  health_rate?: boolean; // 健康率加载状态，可选
  requests?: boolean; // 请求加载状态，可选
  non_20x_status?: boolean; // 非20x状态加载状态，可选
  app_requests?: boolean; // 应用请求加载状态，可选
  resource_requests?: boolean; // 资源请求加载状态，可选
  ingress?: boolean; // 入口加载状态，可选
  egress?: boolean; // 出口加载状态，可选
  response_time_90th?: boolean; // 响应时间90百分位加载状态，可选
}
