import http from '../http';

const path = '/gateways';

/**
 *  获取环境下可用的资源列表接口(在线调试)
 * @param gatewayId 网关id
 * @returns
 */
export const getReleaseResources = (gatewayId: number, stageId: string) => http.get(`${path}/${gatewayId}/releases/stages/${stageId}/resources/`);

/**
 *  获取环境列表
 * @param gatewayId 网关id
 * @returns
 */
export const getStages = (gatewayId: number, data: any) => http.get(`${path}/${gatewayId}/stages/?${json2Query(data)}`);

/**
 *  获取环境下可用的资源列表接口(在线调试)
 * @param gatewayId 网关id
 * @returns
 */
export const getResourcesOnline = (gatewayId: number, stageId: number, data: any) => http.get(`${path}/${gatewayId}/releases/stages/${stageId}/resources/?${json2Query(data)}`);

/**
 *  在线调试发起请求
 * @param gatewayId 网关id
 * @param data 请求数据
 * @returns
 */
export const postAPITest = (gatewayId: number, data: any) => http.post(`${path}/${gatewayId}/tests/`, data);

/**
 *  获取指定网关的信息
 * @param gatewayId 网关id
 * @returns
 */
export const getApiDetail = (gatewayId: number) => http.get(`${path}/${gatewayId}/`);

/**
 *  获取 user_auth_type
 * @returns
 */
export const getUserAuthType = () => http.get('/settings/user_auth_type/');

/**
 * 获取环境下可用的某个资源接口schema(在线调试)
 * @param gatewayId 网关id
 * @param stageId 环境id
 * @param resourceId 资源id
 * @returns
 */
export const resourceSchema = (gatewayId: number, stageId: number, resourceId: number) => http.get(`${path}/${gatewayId}/releases/stages/${stageId}/resources/${resourceId}/schema/`);

/**
 *  在线调试历史记录列表
 * @param gatewayId 网关id
 * @returns
 */
export const getTestHistories = (gatewayId: number, data: any) => http.get(`${path}/${gatewayId}/tests/histories/?${json2Query(data)}`);

/**
 *  获取调用历史详情
 * @param gatewayId 网关id
 * @returns
 */
export const getTestHistoriesDetails = (gatewayId: number, id: number) => http.get(`${path}/${gatewayId}/tests/histories/${id}/`);
