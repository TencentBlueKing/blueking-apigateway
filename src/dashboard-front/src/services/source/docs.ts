import http from '../http';

const path = '/docs/gateways';

// 获取网关文档详情
export const getGatewaysDetailsDocs = (gatewayName: string) => http.get(`${path}/${gatewayName}/`);

// 获取网关资源的文档
export const getApigwResourceDocDocs = (gatewayName: string, resourceName: string, data: any) => http.get(`${path}/${gatewayName}/resources/${resourceName}/doc/?${json2Query(data)}`);

// 获取网关 SDK 调用示例
export const getApigwResourceSDKDocs = (gatewayName: string, data: any) => http.get(`${path}/${gatewayName}/sdks/usage-example/?${json2Query(data)}`);

// 获取网关 SDK 列表
export const getApigwSDKDocs = (gatewayName: string, data: any) => http.get(`${path}/${gatewayName}/sdks/?${json2Query(data)}`);

// 获取网关环境下已发布的资源列表
export const getApigwResourcesDocs = (gatewayName: string, data: any) => http.get(`${path}/${gatewayName}/resources/?${json2Query(data)}`);
