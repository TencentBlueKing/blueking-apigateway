import fetch from './fetch';

const { BK_DASHBOARD_URL } = window;

/**
 * 获取环境列表
 * @param apigwId 网关id
 */
export const getStageList = (apigwId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/`);

/**
 * 创建环境
 * @param apigwId 网关id
 * @param data 新建环境参数
 */
export const createStage = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/`, data);

/**
 * 更新环境
 * @param apigwId 网关id
 * @param stageId 环境id
 * @param data 更新环境参数
 */
export const updateStage = (apigwId: number, stageId: number, data: any) => fetch.put(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/${stageId}/`, data);

/**
 * 获取环境详情
 * @param apigwId 网关id
 * @param stageId 环境id
 */
export const getStageDetail = (apigwId: number, stageId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/${stageId}/`);

/**
 * 下架环境
 * @param apigwId 网关id
 * @param stageId 环境id
 */
export const removalStage = (apigwId: number, stageId: number, data: { status: number }) => fetch.put(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/${stageId}/status/`, data);

/**
 * 删除环境
 * @param apigwId 网关id
 * @param stageId 环境id
 */
export const deleteStage = (apigwId: number, stageId: number) => fetch.delete(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/${stageId}/`);

/**
 * 获取环境的后端服务列表
 * @param apigwId 网关id
 * @param stageId 环境id
 */
export const getStageBackends = (apigwId: number, stageId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/${stageId}/backends/`);

/**
 * 获取环境变量
 * @param apigwId 网关id
 * @param stageId 环境id
 */
export const getStageVars = (apigwId: number, stageId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/${stageId}/vars/`);

/**
 * 更新环境变量
 * @param apigwId 网关id
 * @param stageId 环境id
 * @param data 更新环境变量
 */
export const updateStageVars = (apigwId: number, stageId: number, data: any) => fetch.put(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/${stageId}/vars/`, data);
