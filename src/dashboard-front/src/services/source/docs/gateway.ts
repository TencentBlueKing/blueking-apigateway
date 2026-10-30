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
* API 文档中心 - 网关文档相关 API（按网关名称访问已发布的文档）
*  */

import http from '@/services/http';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IDocsGatewaysListResponse,
  IDocsGatewaysPermissionApplyResponse,
  IDocsGatewaysReadResponse,
  IDocsGatewaysResourcesDocReadResponse,
  IDocsGatewaysResourcesListResponse,
  IDocsGatewaysSdksUsageExampleReadResponse,
  IDocsGatewaysStagesListResponse,
  IDocsSdksDocReadResponse,
} from '@/services/types/responses/docs.ts';
import type {
  IDocsGatewaysListQuery,
  IDocsGatewaysResourcesDocReadQuery,
  IDocsGatewaysResourcesListQuery,
  IDocsGatewaysSdksUsageExampleReadQuery,
  IDocsGatewaysStagesListQuery,
  IDocsSdksDocReadQuery,
} from '@/services/types/query/docs.ts';

const path = '/docs/gateways';

export interface IDocsPermissionApplyInput {
  bk_app_code: string
  reason: string
  resource_name: string
}

/**
 * 获取有公开文档的网关列表
 * @param data 查询参数
 */
export const getDocsGatewayList = (data: IDocsGatewaysListQuery = {}) =>
  http.get<ICountAndResults<IDocsGatewaysListResponse>>(`${path}/`, data);

/**
 * 获取网关文档详情
 * @param gatewayName 网关名称
 * @param data.source 访问来源，如 api_debug（在线调试）
 */
export const getDocsGatewayDetail = (gatewayName: string, data: { source?: string } = {}) =>
  http.get<IDocsGatewaysReadResponse>(`${path}/${gatewayName}/`, data);

/**
 * 获取网关环境下已发布的资源列表
 * @param gatewayName 网关名称
 * @param data 查询参数
 */
export const getDocsResourceList = (gatewayName: string, data: IDocsGatewaysResourcesListQuery) =>
  http.get<IDocsGatewaysResourcesListResponse[]>(`${path}/${gatewayName}/resources/`, data);

/**
 * 获取网关资源的文档
 * @param gatewayName 网关名称
 * @param resourceName 资源名称
 * @param data 查询参数
 */
export const getDocsResourceDoc = (
  gatewayName: string,
  resourceName: string,
  data: IDocsGatewaysResourcesDocReadQuery,
) =>
  http.get<IDocsGatewaysResourcesDocReadResponse>(`${path}/${gatewayName}/resources/${resourceName}/doc/`, data);

/**
 * 获取网关公开、可用的环境列表
 * @param gatewayName 网关名称
 * @param data 查询参数
 */
export const getDocsStageList = (gatewayName: string, data: IDocsGatewaysStagesListQuery = {}) =>
  http.get<IDocsGatewaysStagesListResponse[]>(`${path}/${gatewayName}/stages/`, data);

/**
 * 获取网关 SDK 的调用示例
 * @param gatewayName 网关名称
 * @param data 查询参数
 */
export const getDocsSDKUsageExample = (gatewayName: string, data: IDocsGatewaysSdksUsageExampleReadQuery) =>
  http.get<IDocsGatewaysSdksUsageExampleReadResponse>(`${path}/${gatewayName}/sdks/usage-example/`, data);

/**
 * 从文档页申请当前资源的调用权限
 * @param gatewayName 网关名称
 * @param data 申请参数
 */
export const applyDocsResourcePermission = (
  gatewayName: string,
  data: IDocsPermissionApplyInput,
) =>
  http.post<IDocsGatewaysPermissionApplyResponse>(`${path}/${gatewayName}/permissions/apply/`, data);

/**
 * 获取指定语言（python）的网关 SDK 说明文档
 * @param data 查询参数
 */
export const getGatewaySDKDoc = (data: IDocsSdksDocReadQuery) =>
  http.get<IDocsSdksDocReadResponse>('/docs/sdks/doc/', data);
