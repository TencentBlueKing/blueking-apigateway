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

/**
 * @description 配置 BkUserDisplayName 组件
 * @param {string} tenantId 要覆盖的租户 id
 */
import BkUserDisplayName from '@blueking/bk-user-display-name';
import {
  useEnv,
  useUserInfo,
} from '@/stores';

export function useBkUserDisplayName() {
  const userStore = useUserInfo();
  const envStore = useEnv();

  return {
    configure: (tenantId?: string) => BkUserDisplayName.configure({
      tenantId: tenantId || userStore.info.tenant_id || '',
      apiBaseUrl: envStore.tenantUserDisplayAPI,
    }),
  };
}
