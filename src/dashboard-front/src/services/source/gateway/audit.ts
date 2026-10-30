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
import type { IAuditEventLogOutput } from '@/services/types/responses/gateways.ts';
import type { IGatewaysAuditsLogsListQuery } from '@/services/types/query/gateways.ts';

const path = '/gateways';

/**
 *  查询操作记录
 * @param gatewayId 网关id
 * @param params 查询参数
 */
export const getAuditLogList = (gatewayId: number, params: IGatewaysAuditsLogsListQuery) =>
  http.get<ICountAndResults<IAuditEventLogOutput>>(`${path}/${gatewayId}/audits/logs/`, params);
