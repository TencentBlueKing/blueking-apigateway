import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

/**
 *  获取环境下可用的资源列表接口(在线调试)
 * @param apigwId 网关id
 * @returns
 */
export const getReleaseResources = (apigwId: number, stageId: string) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/releases/stages/${stageId}/resources/`);

/**
 *  获取环境列表
 * @param apigwId 网关id
 * @returns
 */
export const getStages = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/?${json2Query(data)}`);

/**
 *  在线调试发起请求
 * @param apigwId 网关id
 * @param data 请求数据
 * @returns
 */
export const postAPITest = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/tests/`, data);

/**
 *  获取指定网关的信息
 * @param apigwId 网关id
 * @returns
 */
export const getApiDetail = (apigwId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/`);

/**
 *  获取 user_auth_type
 * @returns
 */
export const getUserAuthType = () => fetch.get(`${BK_DASHBOARD_URL}/settings/user_auth_type/`);

/**
 * 获取环境下可用的某个资源接口schema(在线调试)
 * @param gatewayId 网关id
 * @param stageId 环境id
 * @param resourceId 资源id
 * @returns
 */
export const resourceSchema = (gatewayId: number, stageId: number, resourceId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${gatewayId}/releases/stages/${stageId}/resources/${resourceId}/schema/`);
