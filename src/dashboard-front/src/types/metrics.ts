/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

/*
* 指标图表相关类型：图表基础结构（网关与 MCP Server 共用），以及网关仪表盘、统计报表的类型
*  */

// 瞬时值
export interface IInstantValue {
  instant: number
}

// 图表系列项
export interface ISeriesItemType {
  alias: string // 别名
  datapoints: Array<Array<number>> // 数据点数组
  dimensions: Record<string, any> // 维度
  dimensions_translation?: Record<string, any> // 维度翻译
  metric_field: string // 指标字段
  target: string // 目标
  unit: string // 单位
}

// 单个图表的数据
export interface IChartSeries {
  metrics?: Array<unknown> // 指标数组，可选
  series?: Array<ISeriesItemType> // 系列项数组，可选
}

// 网关仪表盘搜索参数
export interface ISearchParamsType {
  stage_id?: number // 阶段ID，可选
  resource_id?: string // 资源ID，可选
  metrics?: string // 指标，可选
  time_start?: number // 开始时间，可选
  time_end?: number // 结束时间，可选
  time_range?: number // 最近 N 秒，可选；与起止同时传时后端以起止为准
  limit?: number // 限制数量，可选
  offset?: number // 偏移量，可选
  backend_name?: string // 后端服务名称，可选
}

// 统计报表搜索参数
export interface ISummarySearchParams {
  stage_id?: number // 阶段ID，可选
  resource_id?: number | string // 资源ID，可选；未选择时为空字符串
  bk_app_code?: string // 蓝鲸应用代码，可选
  metrics?: string // 指标，可选
  time_dimension?: string // 时间维度，可选
  time_start?: number // 起始时间，可选
  time_end?: number // 结束时间，可选
  limit?: number // 限制条数，可选
  offset?: number // 偏移量，可选
}

// 网关仪表盘统计数据
export interface IStatisticsType {
  requests_total?: IInstantValue // 总请求数，可选
  health_rate?: IInstantValue // 健康率，可选
}

// 网关仪表盘图表数据
export interface IChartDataType {
  requests_total?: IChartSeries // 总请求数图表系列，可选
  requests?: IChartSeries // 请求图表系列，可选
  non_20x_status?: IChartSeries // 非20x状态图表系列，可选
  app_requests?: IChartSeries // 应用请求图表系列，可选
  resource_requests?: IChartSeries // 资源请求图表系列，可选
  ingress?: IChartSeries // 入口图表系列，可选
  egress?: IChartSeries // 出口图表系列，可选
  failed_500_requests?: IChartSeries // 失败的500请求图表系列，可选
  response_time?: IChartSeries // 响应时间图表系列，可选
  response_time_90th?: IChartSeries // 响应时间90百分位图表系列，可选
  response_time_50th?: IChartSeries // 响应时间50百分位图表系列，可选
  response_time_95th?: IChartSeries // 响应时间95百分位图表系列，可选
  response_time_99th?: IChartSeries // 响应时间99百分位图表系列，可选
  llm_latency_avg?: IChartSeries // LLM 平均耗时图表系列，可选
  llm_latency_95th?: IChartSeries // LLM P95 延迟图表系列，可选
  llm_token_usage?: IChartSeries // LLM Token 消耗图表系列，可选
  llm_token_95th?: IChartSeries // 单请求 Token P95 图表系列，可选
  llm_active_connections?: IChartSeries // LLM 活跃连接数图表系列，可选
}

// 网关仪表盘图表加载状态
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
  response_time_50th?: boolean // 响应时间50百分位加载状态，可选
  response_time_95th?: boolean // 响应时间95百分位加载状态，可选
  response_time_99th?: boolean // 响应时间99百分位加载状态，可选
  llm_latency_avg?: boolean // LLM 平均耗时加载状态，可选
  llm_latency_95th?: boolean // LLM P95 延迟加载状态，可选
  llm_token_usage?: boolean // LLM Token 消耗加载状态，可选
  llm_token_95th?: boolean // 单请求 Token P95 加载状态，可选
  llm_active_connections?: boolean // LLM 活跃连接数加载状态，可选
}
