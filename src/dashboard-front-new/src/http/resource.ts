import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

export const getResourceListData = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/?${json2Query(data)}`);

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
