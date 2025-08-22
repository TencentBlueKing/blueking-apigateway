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

import { type IStageListItem } from '@/services/source/stage';

interface IState {
  stageList: IStageListItem[]
  notUpdatedStages: IStageListItem[]
  curStageData: IStageListItem | {
    id: null
    name: string
  }
  curStageId: number
  stageMainLoading: boolean
  exist2: boolean
  isDoing: boolean
}

export const useStage = defineStore('useStage', {
  // state 定义了 store 的状态
  state: (): IState => ({
    stageList: [], // 环境列表
    curStageData: {
      id: null, // 当前环境的 ID
      name: '', // 当前环境的名称
    },
    curStageId: -1, // 当前环境的 ID
    stageMainLoading: false, // 环境主加载状态
    notUpdatedStages: [], // 当前网关下未更新的环境列表
    exist2: false, // 当前网关下是否有 schema_version = 2.0 的资源
    isDoing: false, // stage发布是否是doing态
  }),
  // getters 定义了 store 的计算属性
  getters: {
    // 获取默认环境
    defaultStage(state) {
      return state.stageList[0] || {};
    },
    // 获取环境主加载状态
    realStageMainLoading(state) {
      return state.stageMainLoading;
    },
    // 获取未更新的环境列表
    getNotUpdatedStages(state) {
      return state.notUpdatedStages;
    },
    // 获取是否存在 schema_version = 2.0 的资源
    getExist2(state) {
      return state.exist2;
    },
    // 获取doing态
    getDoing(state) {
      return state.isDoing;
    },
  },
  actions: {
    // 设置环境列表
    setStageList(data: any[]) {
      this.stageList = data;
    },
    // 设置环境主加载状态
    setStageMainLoading(loading: boolean) {
      this.stageMainLoading = loading;
    },
    // 设置未更新的环境列表
    setNotUpdatedStages(data: any[]) {
      this.notUpdatedStages = data;
    },
    // 设置是否存在 schema_version = 2.0 的资源
    setExist2(data: boolean) {
      this.exist2 = data;
    },
    // 设置发布资源doing态
    setDoing(data: boolean) {
      this.isDoing = data;
    },
  },
});
