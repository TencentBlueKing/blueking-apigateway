/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

/*
* 插件管理相关 API
*  */

import http from '@/services/http';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IPluginBindingListOutput,
  IPluginConfigRetrieveOutput,
  IPluginTypeListOutput,
  IPluginTypeTagsOutput,
  IScopePluginConfigListOutput,
} from '@/services/types/responses/gateways.ts';
import type {
  IGatewaysPluginsBindingsListQuery,
  IGatewaysPluginsListQuery,
  IGatewaysPluginsReadQuery,
  IGatewaysPluginsTagsListQuery,
} from '@/services/types/query/gateways.ts';
import type { IPluginConfigBaseSLZ } from '@/services/types/body/post/gateways.ts';

const path = '/gateways';

/**
 * 获取某个环境或资源下，可配置的插件列表
 * @param gatewayId 网关id
 * @param data 插件列表参数
 */
export const getPluginListData = (gatewayId: number, data: IGatewaysPluginsListQuery) =>
  http.get<ICountAndResults<IPluginTypeListOutput>>(`${path}/${gatewayId}/plugins/`, data);

/**
 * 获取某个环境或资源下的插件标签
 * @param gatewayId 网关id
 */
export const getPluginTags = (gatewayId: number, query: IGatewaysPluginsTagsListQuery = {}) =>
  http.get<IPluginTypeTagsOutput>(`${path}/${gatewayId}/plugins/-/tags/`, query);

/**
 * 获取插件绑定的环境列表和资源列表
 * @param gatewayId 网关id
 * @param code 插件code
 */
export const getPluginBindingsList = (gatewayId: number, code: string, query: IGatewaysPluginsBindingsListQuery = {}) => http.get<IPluginBindingListOutput>(`${path}/${gatewayId}/plugins/${code}/bindings/`, query);

/**
 * 获取某个环境或资源绑定的插件列表 (插件类型 + 插件配置)
 * @param gatewayId 网关id
 * @param scopeType 类型
 * @param scopeId 类型id
 */
export const getScopeBindingPluginList = (
  gatewayId: number,
  scopeType: string,
  scopeId: number,
  query: IGatewaysPluginsReadQuery = {},
) =>
  http.get<IScopePluginConfigListOutput[]>(`${path}/${gatewayId}/plugins/${scopeType}/${scopeId}/`, query);

/**
 * 创建一个插件，并且绑定到对应的 scope_type + scope_id
 * @param gatewayId 网关id
 * @param scopeType 类型
 * @param scopeId 类型id
 * @param code 插件code
 * @param data 插件的参数
 */
export const createPlugin = (
  gatewayId: number,
  scopeType: string,
  scopeId: number,
  code: string,
  data: IPluginConfigBaseSLZ,
) =>
  http.post(`${path}/${gatewayId}/plugins/${scopeType}/${scopeId}/${code}/configs/`, data);

/**
 * 获取插件的配置
 * @param gatewayId 网关id
 * @param scopeType 类型
 * @param scopeId 类型id
 * @param code 插件code
 * @param id 插件id
 */
export const getPluginConfig = (gatewayId: number, scopeType: string, scopeId: number, code: string, id: number) =>
  http.get<IPluginConfigRetrieveOutput>(`${path}/${gatewayId}/plugins/${scopeType}/${scopeId}/${code}/configs/${id}/`);

/**
 * 更新插件的配置
 * @param gatewayId 网关id
 * @param scopeType 类型
 * @param scopeId 类型id
 * @param code 插件code
 * @param id 插件id
 * @param data 插件的参数
 */
export const updatePluginConfig = (
  gatewayId: number,
  scopeType: string,
  scopeId: number,
  code: string,
  id: number,
  data: IPluginConfigBaseSLZ,
) =>
  http.put(`${path}/${gatewayId}/plugins/${scopeType}/${scopeId}/${code}/configs/${id}/`, data);

/**
 * 删除插件的配置
 * @param gatewayId 网关id
 * @param scopeType 类型
 * @param scopeId 类型id
 * @param code 插件code
 * @param id 插件id
 */
export const deletePluginConfig = (gatewayId: number, scopeType: string, scopeId: number, code: string, id: number) =>
  http.delete(`${path}/${gatewayId}/plugins/${scopeType}/${scopeId}/${code}/configs/${id}/`);
