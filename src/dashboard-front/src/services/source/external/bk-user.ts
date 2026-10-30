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
* 蓝鲸用户管理（外部系统）相关 API
*  */

import http from '@/services/http';
import { useEnv } from '@/stores';

/**
 * 搜索多租户人员
 * @param params.keyword 搜索关键字
 * @param tenant_id 租户id，为空时使用 default
 */
export const getTenantUsers = (
  params: { keyword: string },
  tenant_id: string,
) => {
  const envStore = useEnv();
  return http.get<{
    bk_username: string
    display_name: string
  }[]>(
    `${envStore.env.BK_USER_WEB_API_URL}/api/v3/open-web/tenant/users/-/search/`,
    params,
    { headers: { 'X-Bk-Tenant-Id': tenant_id || 'default' } },
  );
};

/**
 * 将国际化语言设置保存到用户管理中
 * @param url 用户管理的语言设置接口地址
 * @param params.language 语言
 * @param tenant_id 租户id，非多租户环境为 null
 */
export const updateUserLanguage = (
  url: string,
  params: { language: string },
  tenant_id: string | null,
) =>
  http.put(url, params, tenant_id ? { headers: { 'X-Bk-Tenant-Id': tenant_id || '' } } : {});
