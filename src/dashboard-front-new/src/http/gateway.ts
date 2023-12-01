import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

// 获取网关列表
export const getGatewaysList = (data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/?${json2Query(data)}`);

// 新建网关
export const createGateway = (data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/`, data);

// 获取网关标签
export const getGatewayLabels = (apigwId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/labels/`);

// 网关api文档
export const getGatewaysDocs = (apigwId: any, data: any) => fetch.get(`${BK_DASHBOARD_URL}/docs/gateways/?${json2Query(data)}`);

// 获取网关详情
export const getGatewaysDetailsDocs = (gatewayName: string) => fetch.get(`${BK_DASHBOARD_URL}/docs/gateways/${gatewayName}/`);

// 获取网关公开、可用的环境列表
export const getApigwStagesDocs = (gatewayName: string, data: any) => fetch.get(`${BK_DASHBOARD_URL}/docs/gateways/${gatewayName}/stages/?${json2Query(data)}`);

// 获取网关环境下已发布的资源列表
export const getApigwResourcesDocs = (gatewayName: string, data: any) => fetch.get(`${BK_DASHBOARD_URL}/docs/gateways/${gatewayName}/resources/?${json2Query(data)}`);

// 获取网关 SDK 列表
export const getApigwSDKDocs = (gatewayName: string, data: any) => fetch.get(`${BK_DASHBOARD_URL}/docs/gateways/${gatewayName}/sdks/?${json2Query(data)}`);

// 获取网关 SDK 调用示例
export const getApigwResourceSDKDocs = (gatewayName: string, data: any) => fetch.get(`${BK_DASHBOARD_URL}/docs/gateways/${gatewayName}/sdks/usage-example/?${json2Query(data)}`);

// 获取网关资源的文档
export const getApigwResourceDocDocs = (gatewayName: string, resourceName: string, data: any) => fetch.get(`${BK_DASHBOARD_URL}/docs/gateways/${gatewayName}/resources/${resourceName}/doc/?${json2Query(data)}`);

