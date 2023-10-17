import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

// 资源列表数据
export const getResourceListData = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/?${json2Query(data)}`);

// 校验资源后端地址
export const backendsPathCheck = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/resources/backend-path/check/?${json2Query(data)}`);
