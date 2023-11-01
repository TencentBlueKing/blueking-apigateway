import fetch from './fetch';

const { BK_DASHBOARD_URL } = window;

/**
 * 获取某个环境或资源下，可配置的插件列表
 * @param apigwId 网关id
 * @param data 插件列表参数
 */
export const getPluginListData = (apigwId: number, data: any) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/plugins/`, data);

/**
 * 获取插件绑定的环境列表和资源列表
 * @param apigwId 网关id
 * @param code 插件code
 */
export const getPluginBindingsList = (apigwId: number, code: string) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/plugins/${code}/bindings`);

/**
 * 获取插件类型对应的动态表单
 * @param apigwId 网关id
 * @param code 插件code
 */
export const getPluginForm = (apigwId: number, code: string) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/plugins/${code}/form`);

/**
 * 获取某个环境或资源绑定的插件列表 (插件类型 + 插件配置)
 * @param apigwId 网关id
 * @param scopeType 类型
 * @param scopeId 类型id
 */
export const getScopeBindingPluginList = (apigwId: number, scopeType: string, scopeId: number) => fetch.get(`${BK_DASHBOARD_URL}/gateways/${apigwId}/plugins/${scopeType}/${scopeId}`);

