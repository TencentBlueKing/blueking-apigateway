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
import type { IEnvVarsOutput, IFeatureFlagsOutput, IFeatureFlagsQuery } from '@/services/types/platform/setting.ts';

const path = '/settings';

/**
 * 当前环境的功能开关
 * @param params 分页参数
 */
export const getFeatureFlags = (params: IFeatureFlagsQuery) =>
  http.get<IFeatureFlagsOutput>(`${path}/feature-flags/`, params);

/**
 * 当前环境的环境变量配置
 */
export const getEnvVars = () =>
  http.get<IEnvVarsOutput>(`${path}/env-vars/`);
