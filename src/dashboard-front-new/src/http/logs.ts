import fetch from './fetch';

const { BK_DASHBOARD_URL } = window;

/**
 *  查询发布事件(日志)
 * @param apigwId 网关id
 * @returns
 */
export const getLogs = (apigwId: number, historyId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/releases/histories/${historyId}/events/`);

/**
 *  版本发布接口
 * @param apigwId 网关id
 * @param data 数据
 * @returns
 */
export const createReleases = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/releases/`, data);
