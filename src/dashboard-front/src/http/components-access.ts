import fetch from './fetch';
import { json2Query } from '@/common/util';

const { BK_DASHBOARD_URL } = window;

export const getEsbComponents = (data?: any) => fetch.get(`${BK_DASHBOARD_URL}/esb/components/?${json2Query(data)}`);

export const checkEsbNeedNewVersion = () => fetch.get(`${BK_DASHBOARD_URL}/esb/components/sync/need-new-release/`);

export const addComponent = (data: any) => fetch.post(`${BK_DASHBOARD_URL}/esb/components/`, data);

export const updateComponent = (id: number, data: any) => fetch.put(`${BK_DASHBOARD_URL}/esb/components/${id}/`, data);

export const getComponentsDetail = (id: number) => fetch.get(`${BK_DASHBOARD_URL}/esb/components/${id}/`);

export const deleteComponentByBatch = (data: any) => fetch.delete(`${BK_DASHBOARD_URL}/esb/components/batch/`, data);

export const getReleaseStatus = () => fetch.get(`${BK_DASHBOARD_URL}/esb/components/sync/release/status/`);

export const getSyncHistory = (data: any) => fetch.get(`${BK_DASHBOARD_URL}/esb/components/sync/release/histories/?${json2Query(data)}`);

export const checkSyncComponent = () => fetch.post(`${BK_DASHBOARD_URL}/esb/components/sync/check/`);

export const syncReleaseData = () => fetch.post(`${BK_DASHBOARD_URL}/esb/components/sync/release/`);

/**
 * 组件同步网关及发布历史.
 * @param id
 * @returns
 */
export const getSyncVersion = (id: any) => fetch.get(`${BK_DASHBOARD_URL}/esb/components/sync/release/histories/${id}/`);

/**
 * 获取 feature flag 全局特性开关列表
 * @param data 分页参数
 * @returns
 */
export const getFeatures = (data?: any) => fetch.get(`${BK_DASHBOARD_URL}/settings/feature_flags/?${json2Query(data)}`);
