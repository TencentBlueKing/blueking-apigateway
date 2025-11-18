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

/**
 *  获取AI解析结果
 * @param gatewayId 网关id
 * @param data 参数
 */
export const getAICompletion = (gatewayId: number, data: any) => http.post(`${path}/${gatewayId}/ai/completion/`, data);

/**
 *  批量AI翻译资源文档
 * @param gatewayId 网关id
 * @param data 参数
 */
export const batchResourceDocAITranslate = (gatewayId: number, data: {
  doc_ids?: number[]
  target_language?: string
}) => http.post(`${path}/${gatewayId}/ai/batch-translate/`, data);
