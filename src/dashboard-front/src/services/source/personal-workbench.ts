/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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

import http from '../http';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type { IPersonalWorkbenchFilterOptionQuery, IPersonalWorkbenchListQuery } from '@/services/types/query/personal-workbench.ts';
import type { IPersonalWorkbenchFilterOptionResponse, IPersonalWorkbenchListResponse } from '@/services/types/responses/personal-workbench.ts';

const path = '/me/workbench';

/**
 * 个人工作台 - 我的待办 - API 网关权限申请列表
 * @param params 参数
 */
export const getGatewayPendingList = (params?: IPersonalWorkbenchListQuery) =>
  http.get<ICountAndResults<IPersonalWorkbenchListResponse>>(`${path}/permissions/gateway/pending/`, params);

/**
 * 个人工作台 - 我的申请 - API 网关权限申请列表
 * @param params 参数
 */
export const getGatewayAppliedList = (params: IPersonalWorkbenchListQuery) =>
  http.get<ICountAndResults<IPersonalWorkbenchListResponse>>(`${path}/permissions/gateway/applied/`, params);

/**
 * 个人工作台 - 我的已办 - API 网关权限申请列表
 * @param params 参数
 */
export const getGatewayHandledList = (params: IPersonalWorkbenchListQuery) =>
  http.get(`${path}/permissions/gateway/handled/`, params);

/**
 * 个人工作台 - 我的待办 - API 网关权限申请列表
 * @param params 参数
 */
export const getMcpPendingList = (params?: IPersonalWorkbenchListQuery) =>
  http.get<ICountAndResults<IPersonalWorkbenchListResponse>>(`${path}/permissions/mcp/pending/`, params);

/**
 * 个人工作台 - 我的申请 - MCP Server 权限申请列表
 * @param params 参数
 */
export const getMcpAppliedList = (params: IPersonalWorkbenchListQuery) =>
  http.get<ICountAndResults<IPersonalWorkbenchListResponse>>(`${path}/permissions/mcp/applied/`, params);

/**
 * 个人工作台 - 我的待办 - MCP Server 权限申请列表
 * @param params 参数
 */
export const getMcpHandledList = (params: IPersonalWorkbenchListQuery) =>
  http.get<ICountAndResults<IPersonalWorkbenchListResponse>>(`${path}/permissions/mcp/handled/`, params);

/**
 * 个人工作台 - 网关下拉筛选选项列表
 * @param params 参数
 */
export const getGatewayFilterOptions = (params: IPersonalWorkbenchFilterOptionQuery) =>
  http.get<IPersonalWorkbenchFilterOptionResponse[]>(`${path}/filter-options/gateways/`, params);

/**
 * 个人工作台 - MCP Server 维度网关下拉筛选选项列表
 * @param params 参数
 */
export const getMcpGatewayFilterOptions = (params: IPersonalWorkbenchFilterOptionQuery) =>
  http.get<IPersonalWorkbenchFilterOptionResponse[]>(`${path}/filter-options/mcp-gateways/`, params);

/**
 * 个人工作台 - MCP Server 下拉筛选选项列表
 * @param params 参数
 */
export const getMcpServerFilterOptions = (params: IPersonalWorkbenchFilterOptionQuery) =>
  http.get<IPersonalWorkbenchFilterOptionResponse[]>(`${path}/filter-options/mcp-servers/`, params);
