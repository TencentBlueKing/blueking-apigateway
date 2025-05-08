import fetch from './fetch';
import { json2Query, blobDownLoad } from '@/common/util';
import { SearchParamsType } from '@/views/operate-data/dashboard/type';

const { BK_DASHBOARD_URL } = window;

/**
 *  查询 metrics
 * @param apigwId 网关id
 */
export const getApigwMetrics = (apigwId: number, params: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/metrics/query-range/?${json2Query(params)}`);

/**
 *  请求总数健康率
 * @param apigwId 网关id
 */
export const getApigwMetricsInstant = (apigwId: number, params: SearchParamsType) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/metrics/query-instant/?${json2Query(params)}`);

/**
 *  获取流程日志列表
 * @param apigwId 网关id
 */
export const getApigwStages = (apigwId: number, params: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/?${json2Query(params)}`);

/**
 *  获取流程日志列表
 * @param apigwId 网关id
 */
export const getApigwResources = (apigwId: number, params: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/?${json2Query(params)}`);

/**
 *  日志导出
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const exportLogs = async (apigwId: number, data: any, extraStr?: string) => {
  const res = await fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/logs/export/?${json2Query(data)}${extraStr}`, {}, { responseType: 'blob' });
  return blobDownLoad(res);
};

/**
 *  查询请求总量/失败总量接口
 * @param apigwId 网关id
 */
export const getReportSummary = (apigwId: number, params: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/metrics/query-summary/?${json2Query(params)}`);

/**
 *  请求总量/失败请求总量导出接口
 * @param apigwId 网关id
 * @param data 导出参数
 */
export const exportReportSummary = async (apigwId: number, data: any) => {
  const res = await fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/metrics/query-summary/export/?${json2Query(data)}`, {}, { responseType: 'blob' });
  return blobDownLoad(res);
};

/**
 *  查询调用方接口
 * @param apigwId 网关id
 */
export const getCallers = (apigwId: number, params: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/metrics/query-summary/caller/?${json2Query(params)}`);
