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

// 定义一个名为useResourceVersion的Pinia store
export const useResourceVersion = defineStore('useResourceVersion', {
  // state定义了store的初始状态
  state: () => ({
    tabActive: 'edition', // 当前激活的标签页
    resourceFilter: {}, // 资源过滤器
    pageStatus: {
      isDetail: false, // 是否显示详情
      isShowLeft: true, // 是否显示左侧栏
    },
  }),
  // getters定义了获取state的方法
  getters: {
    // 获取当前激活的标签页
    getTabActive(state) {
      return state.tabActive;
    },
    // 获取资源过滤器
    getResourceFilter(state) {
      return state.resourceFilter;
    },
    // 获取页面状态
    getPageStatus(state) {
      return state.pageStatus;
    },
  },
  // actions定义了修改state的方法
  actions: {
    // 设置当前激活的标签页
    setTabActive(key: string) {
      this.tabActive = key;
    },
    // 设置资源过滤器
    setResourceFilter(value: any) {
      this.resourceFilter = value;
    },
    // 设置页面状态
    setPageStatus(value: any) {
      this.pageStatus = value;
    },
  },
});
