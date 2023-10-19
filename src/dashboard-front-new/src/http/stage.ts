import fetch from './fetch';
// import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

// 获取环境列表
export const getStageList = (apigwId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/`);

// 创建环境
export const createStage = (apigwId: number, data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/`, data);

// 获取环境详情
export const getStageDetail = (apigwId: number, stageId: number) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/${stageId}`);

// 删除环境
export const deleteStage = (apigwId: number, stageId: number) => fetch.delete(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/${stageId}`);

// 获取后端服务列表
export const getStageBackends = (apigwId: number, stageId: number) => fetch.post(`${BK_DASHBOARD_URL}/gateways/${apigwId}/stages/${stageId}/backends`);
