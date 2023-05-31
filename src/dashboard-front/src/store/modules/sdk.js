/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
 * @file api store
 * @author
 */

import http from '@/api'
import cookie from 'cookie'

export default {
  namespaced: true,
  state: {
  },
  mutations: {
  },
  actions: {
    getApigwSDKs (context, { apigwId, params }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/support/sdks/`
      return http.get(url, { params })
    },
    buildApigwSDK (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/support/sdks/`
      const CSRFToken = cookie.parse(document.cookie)[DASHBOARD_CSRF_COOKIE_NAME || `${window.PROJECT_CONFIG.BKPAAS_APP_ID}_csrftoken`]
      if (data.is_public === false) {
        return fetch(url, {
          credentials: 'include',
          method: 'POST',
          body: JSON.stringify(data),
          headers: new Headers({
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRFToken
          })
        })
      } else {
        return http.post(url, data, config)
      }
    }
  }
}
