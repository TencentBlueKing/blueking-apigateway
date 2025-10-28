/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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

const path = '/docs/gateways';

// 网关api文档列表
export const getGatewaysDocs = (data: any) => http.get(`${path}/`, data);

// 获取网关文档详情
export const getGatewaysDetailsDocs = (gatewayName: string, data: any) => http.get(`${path}/${gatewayName}/`, data);

// 获取网关资源的文档
export const getApigwResourceDocDocs = (gatewayName: string, resourceName: string, data: any) => http.get(`${path}/${gatewayName}/resources/${resourceName}/doc/`, data);

// 获取网关 SDK 调用示例
export const getApigwResourceSDKDocs = (gatewayName: string, data: any) => http.get(`${path}/${gatewayName}/sdks/usage-example/`, data);

// 获取网关 SDK 列表
export const getApigwSDKDocs = (gatewayName: string, data: any) => http.get(`${path}/${gatewayName}/sdks/`, data);

// 获取网关环境下已发布的资源列表
export const getApigwResourcesDocs = (gatewayName: string, data: any) => http.get(`${path}/${gatewayName}/resources/`, data);

// 获取网关公开、可用的环境列表
export const getApigwStagesDocs = (gatewayName: string, data: any) =>
  http.get(`${path}/${gatewayName}/stages/`, data);
