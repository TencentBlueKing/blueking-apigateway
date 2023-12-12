import fetch from './fetch';

const { BK_DASHBOARD_URL } = window;
/**
 *  获取系统管理列表
 */
export const getSystems = () => fetch.get(`${BK_DASHBOARD_URL}/esb/systems/`);

/**
 *  获取系统管理详情
 */
export const getSystemDetail = (systemId: number) => fetch.get(`${BK_DASHBOARD_URL}/esb/systems/${systemId}/`);

/**
 *  新增系统管理
 */
export const addSystem = (data: any) => fetch.post(`${BK_DASHBOARD_URL}/esb/systems/`, data);

/**
 *  更新系统管理
 */
export const updateSystem = (systemId: number, data: any) => fetch.put(`${BK_DASHBOARD_URL}/esb/systems/${systemId}/`, data);


/**
 *  删除系统管理
 */
export const deleteSystem = (systemId: number) => fetch.delete(`${BK_DASHBOARD_URL}/esb/systems/${systemId}/`);

/**
 *  获取 Esb 网关
 */
export const getEsbGateway = () => fetch.get(`${BK_DASHBOARD_URL}/esb/components/gateway/`);
