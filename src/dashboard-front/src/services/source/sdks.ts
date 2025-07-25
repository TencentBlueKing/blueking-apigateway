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

const path = '/gateways';

export const getSDKList = (apigwId: number, data: any) => http.get(`${path}/${apigwId}/sdks/`, data);

export const createSDK = (apigwId: number, data: any) => http.post(`${path}/${apigwId}/sdks/`, data);

/**
 *  获取指定语言（python）的网关 SDK 说明文档
 * @param data 查询参数
 */
export const getGatewaySDKDoc = (data: any) => http.get('/docs/sdks/doc/', data);
