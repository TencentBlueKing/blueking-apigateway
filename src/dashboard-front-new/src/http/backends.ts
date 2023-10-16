import fetch from './fetch';
// import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

// 获取后端服务列表
export const getBackendsListData = (id: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${id}/backends/`);
