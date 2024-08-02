import fetch from './fetch';
import { json2Query, blobDownLoad } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

/**
 *  查询 metrics
 * @param apigwId 网关id
 */
export const getApigwMetrics = (apigwId: number, params: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/metrics/query-range/?${json2Query(params)}`);

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
export const exportLogs = async (apigwId: number, data: any) => {
  const res = await fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/logs/export/`, data, { responseType: 'blob' });
  return blobDownLoad(res);
};
