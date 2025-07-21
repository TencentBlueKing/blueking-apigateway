import http from '../http';

const path = '/gateways';

/**
 *  获取AI解析结果
 * @param gatewayId 网关id
 * @param data 参数
 */
export const getAICompletion = (gatewayId: number, data: any) => http.post(`${path}/${gatewayId}/ai/completion/`, data);
