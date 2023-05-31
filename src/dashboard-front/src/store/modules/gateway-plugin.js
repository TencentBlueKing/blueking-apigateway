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
import { json2Query } from '@/common/util.js'
  
export default {
  namespaced: true,
  state: {
  },
  mutations: {
  },
  actions: {
    getPlugins (context, { apigwId, pageParams }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/plugins/configs/?${json2Query(pageParams)}`
      return http.get(url, {}, config)
    },
        
    getIdPlugin (context, { apigwId, id }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/plugins/configs/${id}/`
      return http.get(url, {}, config)
    },

    getPluginType (context, { apigwId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/plugins/types/`
      return http.get(url, {}, config)
    },

    getResources (context, { apigwId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/resources/verified-user-required/`
      return http.get(url, {}, config)
    },

    updatePlugin (context, { apigwId, id, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/plugins/configs/${id}/`
      return http.put(url, data, config)
    },
        
    createPlugin (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/plugins/configs/`
      return http.post(url, data, config)
    },

    // 删除插件
    deletePlugin (context, { apigwId, id }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/plugins/configs/${id}/`
      return http.delete(url, {}, config)
    },

    // 获取绑定列表（资源/环境）
    getPluginBinding (context, { apigwId, id }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/plugins/configs/${id}/bindings/`
      return http.get(url, {}, config)
    },

    // 绑定环境/资源
    createPluginBinding (context, { apigwId, id, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/plugins/configs/${id}/bindings/`
      return http.post(url, data, config)
    },

    // 解绑环境/资源
    deletePluginBinding (context, { apigwId, id, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/plugins/configs/${id}/bindings/`
      return http.delete(url, { data }, config)
    },

    getDynamicForm (context, { apigwId, formId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/plugins/forms/${formId}/`
      return http.get(url, {}, config)
    }
  }
}
