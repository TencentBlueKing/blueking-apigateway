/*
* 可编程网关相关 API
*  */

import http from '../http';

const path = '/gateways';

/**
 * 获取某个环境或资源下，可配置的插件列表
 * @param apigwId 网关id
 * @param data 插件列表参数
 */
export const getPluginListData = (apigwId: number, data: any) => http.get(`${path}/${apigwId}/plugins/`, data);

/**
 * 获取插件绑定的环境列表和资源列表
 * @param apigwId 网关id
 * @param code 插件code
 */
export const getPluginBindingsList = (apigwId: number, code: string) => http.get(`${path}/${apigwId}/plugins/${code}/bindings/`);

/**
 * 获取插件类型对应的动态表单
 * @param apigwId 网关id
 * @param code 插件code
 */
export const getPluginForm = (apigwId: number, code: string) => http.get(`${path}/${apigwId}/plugins/${code}/form/`);

/**
 * 获取某个环境或资源绑定的插件列表 (插件类型 + 插件配置)
 * @param apigwId 网关id
 * @param scopeType 类型
 * @param scopeId 类型id
 */
export const getScopeBindingPluginList = (apigwId: number, scopeType: string, scopeId: number) =>
  http.get(`${path}/${apigwId}/plugins/${scopeType}/${scopeId}/`);

/**
 * 创建一个插件，并且绑定到对应的 scope_type + scope_id
 * @param apigwId 网关id
 * @param scopeType 类型
 * @param scopeId 类型id
 * @param code 插件code
 * @param data 插件的参数
 */
export const creatPlugin = (apigwId: number, scopeType: string, scopeId: number, code: string, data: any) =>
  http.post(`${path}/${apigwId}/plugins/${scopeType}/${scopeId}/${code}/configs/`, data);

/**
 * 获取插件的配置
 * @param apigwId 网关id
 * @param scopeType 类型
 * @param scopeId 类型id
 * @param code 插件code
 * @param id 插件id
 */
export const getPluginConfig = (apigwId: number, scopeType: string, scopeId: number, code: string, id: number) =>
  http.get(`${path}/${apigwId}/plugins/${scopeType}/${scopeId}/${code}/configs/${id}/`);

/**
 * 更新插件的配置
 * @param apigwId 网关id
 * @param scopeType 类型
 * @param scopeId 类型id
 * @param code 插件code
 * @param id 插件id
 * @param data 插件的参数
 */
export const updatePluginConfig = (
  apigwId: number,
  scopeType: string,
  scopeId: number,
  code: string,
  id: number,
  data: any,
) =>
  http.put(`${path}/${apigwId}/plugins/${scopeType}/${scopeId}/${code}/configs/${id}/`, data);

/**
 * 删除插件的配置
 * @param apigwId 网关id
 * @param scopeType 类型
 * @param scopeId 类型id
 * @param code 插件code
 * @param id 插件id
 */
export const deletePluginConfig = (apigwId: number, scopeType: string, scopeId: number, code: string, id: number) =>
  http.delete(`${path}/${apigwId}/plugins/${scopeType}/${scopeId}/${code}/configs/${id}/`);
