import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

// 获取网关列表
export const getGatewaysList = (data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/?${json2Query(data)}`);

// 新建网关
export const createGateway = (data: any) => fetch.post(`${BK_DASHBOARD_URL}/gateways/`, data);

// 获取网关标签
export const getGatewayLabels = (apigwId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/labels/`);
