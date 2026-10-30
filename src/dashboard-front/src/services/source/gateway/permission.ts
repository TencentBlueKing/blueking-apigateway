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
import http from '@/services/http';
import type { ICountAndResults } from '@/services/types/utils.ts';
import type {
  IAppPermissionApplyListOutput,
  IAppPermissionListOutput,
  IAppPermissionRecordListOutput,
} from '@/services/types/responses/gateways.ts';
import type {
  IGatewaysPermissionsAppPermissionApplyListQuery,
  IGatewaysPermissionsAppPermissionRecordsListQuery,
  IGatewaysPermissionsAppPermissionsBkAppCodesListQuery,
  IGatewaysPermissionsAppPermissionsListQuery,
} from '@/services/types/query/gateways.ts';
import type {
  IAppPermissionApplyApprovalInputSLZ,
  IAppPermissionExportInputSLZ,
  IAppPermissionInputSLZ,
  IAppPermissionRenewInputSLZ,
} from '@/services/types/body/post/gateways.ts';

const path = '/gateways';

export interface IAuthData {
  bk_app_code: string
  expire_type: string
  expire_days: number | null
  resource_ids: number[]
  dimension: string
}

/**
 *  获取权限申请单列表
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const getPermissionApplyList = (
  gatewayId: number,
  params: IGatewaysPermissionsAppPermissionApplyListQuery = {
    offset: 0,
    limit: 10,
  },
) =>
  http.get<ICountAndResults<IAppPermissionApplyListOutput>>(`${path}/${gatewayId}/permissions/app-permission-apply/`, params);

/**
 *  审批权限申请（通过 / 部分通过 / 驳回）
 * @param gatewayId 网关id
 * @param params 审批参数
 */
export const updatePermissionStatus = (gatewayId: number, params: IAppPermissionApplyApprovalInputSLZ) =>
  http.post(`${path}/${gatewayId}/permissions/app-permission-apply/approval/`, params);

/**
 *  获取权限审批记录列表
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const getPermissionRecordList = (
  gatewayId: number,
  params: IGatewaysPermissionsAppPermissionRecordsListQuery = {
    offset: 0,
    limit: 10,
  },
) =>
  http.get<ICountAndResults<IAppPermissionRecordListOutput>>(`${path}/${gatewayId}/permissions/app-permission-records/`, params);

/**
 *  网关权限主动授权
 * @param gatewayId 网关id
 * @param params 授权参数
 */
export const authApiPermission = (gatewayId: number, params: IAppPermissionInputSLZ) =>
  http.post(`${path}/${gatewayId}/permissions/app-gateway-permissions/`, params);

/**
 *  删除网关权限
 *  后端从查询串读取 ids，而 http.delete 会把 params 放进请求体，所以这里把 ids 拼在 URL 上
 * @param gatewayId 网关id
 * @param params.ids 网关权限id列表
 */
export const deleteApiPermission = (gatewayId: number, params: { ids: number[] }) =>
  http.delete(`${path}/${gatewayId}/permissions/app-gateway-permissions/delete/?ids=${params.ids}`);

/**
 *  获取权限列表
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const getPermissionList = (gatewayId: number, params: IGatewaysPermissionsAppPermissionsListQuery = {}) =>
  http.get<ICountAndResults<IAppPermissionListOutput>>(`${path}/${gatewayId}/permissions/app-permissions/`, params);

/**
 *  资源权限主动授权
 * @param gatewayId 网关id
 * @param params 授权参数
 */
export const authResourcePermission = (gatewayId: number, params: IAuthData) =>
  http.post(`${path}/${gatewayId}/permissions/app-resource-permissions/`, params);

/**
 *  获取有资源权限的应用列表
 * @param gatewayId 网关id
 * @param query 查询参数
 */
export const getResourcePermissionAppList = (
  gatewayId: number,
  query: IGatewaysPermissionsAppPermissionsBkAppCodesListQuery = {},
) =>
  http.get<string[]>(`${path}/${gatewayId}/permissions/app-permissions/bk-app-codes/`, query);

/**
 *  删除资源权限
 *  后端从查询串读取 ids，而 http.delete 会把 params 放进请求体，所以这里把 ids 拼在 URL 上
 * @param gatewayId 网关id
 * @param params.ids 资源权限id列表
 */
export const deleteResourcePermission = (gatewayId: number, params: { ids: number[] }) =>
  http.delete(`${path}/${gatewayId}/permissions/app-resource-permissions/delete/?ids=${params.ids}`);

/**
 *  导出应用权限
 * @param gatewayId 网关id
 * @param params 导出参数
 */
export const exportPermissionList = (gatewayId: number, params: IAppPermissionExportInputSLZ) =>
  http.post(`${path}/${gatewayId}/permissions/app-permissions/export/`, params, {
    responseType: 'blob',
    catchError: true,
  });

/**
 *  批量权限续期
 * @param gatewayId 网关id
 * @param params 续期参数
 */
export const batchUpdatePermission = (gatewayId: number, params: IAppPermissionRenewInputSLZ) =>
  http.post(`${path}/${gatewayId}/permissions/app-permissions/renew/`, params);

/**
 *  批量删除权限
 * @param gatewayId 网关id
 * @param params 删除参数，按资源维度、网关维度分别传权限id
 */
export const batchDeletePermission = (gatewayId: number, params: {
  resource_dimension_ids?: number[]
  gateway_dimension_ids?: number[]
}) =>
  http.delete(`${path}/${gatewayId}/permissions/app-permissions/batch/`, params);
