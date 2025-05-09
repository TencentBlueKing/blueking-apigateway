// 搜索参数类型接口
export interface SearchParamsType {
  stage_id?: number; // 阶段ID，可选
  resource_id?: string; // 资源ID，可选
  bk_app_code?: string; // 蓝鲸应用代码，可选
  metrics?: string; // 指标，可选
  time_dimension?: string; // 时间维度，可选
  time_start?: number; // 起始时间，可选
  time_end?: number; // 结束时间，可选
  limit?: number; // 限制条数，可选
  offset?: number; // 偏移量，可选
}

// 系列项类型接口
export interface SeriesItemType {
  alias: string; // 别名
  datapoints: Array<Array<number>>; // 数据点数组
  dimensions: Object; // 维度对象
  metric_field: string; // 指标字段
  target: string; // 目标
  unit: string; // 单位
}

// 图表数据加载状态接口
export interface ChartDataLoading {
  requests_total?: boolean; // 总请求数加载状态，可选
  requests_failed_total?: boolean; // 失败请求数加载状态，可选
}
