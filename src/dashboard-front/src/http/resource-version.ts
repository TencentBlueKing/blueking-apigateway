import fetch from './fetch';

const { BK_DASHBOARD_URL } = window;


/**
 * 生成资源版本
 * @param apigwId 网关id
 * @param data 资源版本信息
 */
export const createResourceVersion = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resource-versions/`, data);
