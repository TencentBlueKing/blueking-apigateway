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
 * @file docCategory store
 * @author
 */

import http from '@/api'

export default {
  namespaced: true,
  state: {},
  mutations: {},
  actions: {
    getDocCategorys (context, params, config = {}) {
      const url = `${DASHBOARD_URL}/esb/doc_categories/`
      return http.get(url, params, config)
    },

    getDocCategoryDetail (context, { docCategoryId }, config = {}) {
      const url = `${DASHBOARD_URL}/esb/doc_categories/${docCategoryId}/`
      return http.get(url, {}, config)
    },

    addDocCategory (context, params, config = {}) {
      const url = `${DASHBOARD_URL}/esb/doc_categories/`
      return http.post(url, params, config)
    },

    updateDocCategory (context, { docCategoryId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/esb/doc_categories/${docCategoryId}/`
      return http.put(url, data, config)
    },

    deleteDocCategory (context, { docCategoryId }, config = {}) {
      const url = `${DASHBOARD_URL}/esb/doc_categories/${docCategoryId}/`
      return http.delete(url, {}, config)
    }
  }
}
