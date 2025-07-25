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

// 定义分页接口
interface IPagination {
  current: number // 当前页码
  offset: number // 偏移量
}

// 定义一个名为 useResourceSetting 的 store
export const useResourceSetting = defineStore('useResourceSetting', {
  state: () => ({
    // 存储上一次的分页信息
    previousPagination: null as IPagination | null,
  }),
  actions: {
    // 设置分页信息
    setPagination(pagination: IPagination) {
      this.previousPagination = pagination;
    },
  },
});
