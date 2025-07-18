import http from '../http';

export interface IAuditLog {
  // 操作类型
  op_type: string
  // 操作状态
  op_status: string
  // 操作对象
  op_object?: string
  // 操作对象类型
  op_object_type: string
  // 用户名
  username?: string
  // 开始时间（可选）
  time_start?: string
  // 结束时间（可选）
  time_end?: string
  // 关键词（可选）
  keyword?: string
  // 排序字段（可选）
  order_by?: string
}

/**
 *  查询操作记录
 * @param apigwId 网关id
 * @param params
 * @returns
 */
export async function getAuditLogList(apigwId: number, params: IAuditLog) {
  return http.get(`/gateways/${apigwId}/audits/logs/`, params);
}
