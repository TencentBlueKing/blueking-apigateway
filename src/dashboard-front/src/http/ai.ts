import fetch from './fetch';

const { BK_DASHBOARD_URL } = window;

/**
 *  获取AI解析结果
 * @param apigwId 网关id
 * @param data 参数
 */
export const getAICompletion = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/ai/completion/`, data);
