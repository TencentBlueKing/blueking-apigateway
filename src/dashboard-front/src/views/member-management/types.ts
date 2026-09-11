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

/**
 * 成员管理的类型声明
 */

import type { IGatewayMemberOutput } from '@/services/types/responses/gateway-members';
import type { GatewayPermissionKey } from '@/constants/gateway-permission';

export type IMember = IGatewayMemberOutput;

// 权限矩阵表格的一行：授权策略（administrator/operator/aiOnly）与展示文案（label/tip）的合体
export interface IPermissionItem {
  key: GatewayPermissionKey
  label: string
  administrator: boolean
  operator: boolean
  aiOnly?: boolean
  tip?: string
}
