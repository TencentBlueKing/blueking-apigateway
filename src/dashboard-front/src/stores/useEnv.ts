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
import { defineStore } from 'pinia';

import { getEnv } from '@/services/source/basic';

export const useEnv = defineStore('useEnv', {
  state: () => ({
    env: {
      BK_API_RESOURCE_URL_TMPL: '',
      BK_APP_CODE: '',
      BK_COMPONENT_API_URL: '',
      BK_DASHBOARD_CSRF_COOKIE_NAME: '',
      BK_DASHBOARD_FE_URL: '',
      BK_DASHBOARD_URL: '',
      BK_DEFAULT_TEST_APP_CODE: '',
      BK_PAAS_APP_REPO_URL_TMPL: '',
      EDITION: '',
    },
  }),
  actions: {
    /**
     * 查询环境变量信息
     */
    fetchEnv() {
      getEnv().then((result) => {
        Object.assign(this.env, result);
      });
    },
  },
});
