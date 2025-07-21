import http from '../http';

const path = '/gateways';

interface IMetricInstantParams {
  stage_id?: number // 阶段ID，可选
  resource_id?: string // 资源ID，可选
  metrics?: string // 指标，可选
  time_start?: number // 开始时间，可选
  time_end?: number // 结束时间，可选
  time_range?: string // 时间范围，可选
  limit?: number // 限制数量，可选
  offset?: number // 偏移量，可选
}

export const getGatewayMetrics = (apigwId: number, params: any) => http.get(`${path}/${apigwId}/metrics/query-range/`, params);

export const getGatewayMetricsInstant = (apigwId: number, params: IMetricInstantParams) =>
  http.get(`${path}/${apigwId}/metrics/query-instant/`, params);
