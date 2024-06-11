import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

// 获取后端服务列表
export const getBackendsListData = (apigwId: number, data = {}) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/backends/?${json2Query(data)}`);

// 获取后端服务详情
export const getBackendsDetailData = (apigwId: number, backendId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/backends/${backendId}/`);
