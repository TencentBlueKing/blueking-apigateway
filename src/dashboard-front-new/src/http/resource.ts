import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

/**
 *  资源列表数据
 * @param apigwId 网关id
 * @returns
 */
export const getResourceListData = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/?${json2Query(data)}`);

/**
 *  创建资源
 * @param apigwId 网关id
 * @param data 网关资源数据
 * @returns
 */
export const createResources = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/`, data);

// 校验资源后端地址
export const backendsPathCheck = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/backend-path/check/?${json2Query(data)}`);
/**
 *
 * @param apigwId 网关id
 * @returns
 */
export const getResourceVersionsList = (apigwId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resource_versions/`);

/**
 *
 * @param apigwId 网关id
 * @param versionId 版本id
 * @returns
 */
export const getResourceVersionsInfo = (apigwId: number, id: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resource_versions/${id}`);
