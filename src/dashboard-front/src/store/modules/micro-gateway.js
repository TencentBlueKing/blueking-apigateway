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
    getMicroApigwList (context, { apigwId, pageParams }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/micro-gateways/?${json2Query(pageParams)}`
      return http.get(url, {}, config)
    },
 
    addApigwStage (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/stages/`
      return http.post(url, data, config)
    },
 
    getApigwStageDetail (context, { apigwId, stageId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/stages/${stageId}/`
      return http.get(url, {}, config)
    },
 
    updateApigwStage (context, { apigwId, stageId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/stages/${stageId}/`
      return http.put(url, data, config)
    },
 
    updateApigwStageStatus (context, { apigwId, stageId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/stages/${stageId}/status/`
      return http.put(url, data, config)
    },
 
    deleteApigwStage (context, { apigwId, stageId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/stages/${stageId}/`
      return http.delete(url, {}, config)
    },

    getClusters (context, { apigwId, projectId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/micro-gateways/bcs/clusters/?project_id=${projectId}`
      return http.get(url, {}, config)
    },

    getNamespaces (context, { apigwId, projectId, cluster }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/micro-gateways/bcs/namespaces/?project_id=${projectId}&cluster_id=${cluster}`
      return http.get(url, {}, config)
    },

    getProjects (context, { apigwId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/micro-gateways/bcs/projects/`
      return http.get(url, {}, config)
    },

    getReleases (context, { apigwId, projectId, clusterName, namespace }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/micro-gateways/bcs/releases/?project_id=${projectId}&cluster_id=${clusterName}&namespace=${namespace}`
      return http.get(url, {}, config)
    },

    getMicrogateway (context, { apigwId, id }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/micro-gateways/${id}/`
      return http.get(url, {}, config)
    },

    getMicrogatewayList (context, { apigwId }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/micro-gateways/`
      return http.get(url, {}, config)
    },

    createMicrogateway (context, { apigwId, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/micro-gateways/`
      return http.post(url, data, config)
    },

    deleteMicrogateway (context, { apigwId, id }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/micro-gateways/${id}/`
      return http.delete(url, {}, config)
    },
        
    updateMicrogateway (context, { apigwId, id, data }, config = {}) {
      const url = `${DASHBOARD_URL}/apis/${apigwId}/micro-gateways/${id}/`
      return http.put(url, data, config)
    }
  }
}
