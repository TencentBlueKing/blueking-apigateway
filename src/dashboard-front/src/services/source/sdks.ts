import http from '../http';

const path = '/gateways';

export const getSDKList = (apigwId: number, data: any) => http.get(`${path}/${apigwId}/sdks/`, data);

export const createSDK = (apigwId: number, data: any) => http.post(`${path}/${apigwId}/sdks/`, data);

/**
 *  获取指定语言（python）的网关 SDK 说明文档
 * @param data 查询参数
 */
export const getGatewaySDKDoc = (data: any) => http.get('/docs/sdks/doc/', data);
