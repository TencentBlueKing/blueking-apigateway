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
import QueryString from 'qs';
import { unionBy } from 'lodash-es';
import { useEnv } from '@/stores/useEnv.ts';

/**
 * 使用 Pinia 定义一个名为 useStaffStore 的 store
 */
export const useStaff = defineStore('useStaff', {
  state: () => ({
    fetching: false, // 标识是否正在获取数据
    list: shallowRef([]), // 存储员工列表数据
  }),
  actions: {
    /**
     * 异步获取员工数据
     * @param {string} [name] - 可选参数，员工姓名，用于模糊查询
     */
    async fetchStaffs(name?: string) {
      const envStore = useEnv();

      if (this.fetching) return; // 如果正在获取数据，则直接返回

      this.fetching = true; // 设置 fetching 为 true，表示开始获取数据
      // 获取员工列表的 API URL
      const usersListPath = `${envStore.env.BK_COMPONENT_API_URL}/api/c/compapi/v2/usermanage/fs_list_users/`;
      const params: any = {
        app_code: 'bk-magicbox', // 应用代码
        page: 1, // 页码
        page_size: 200, // 每页数据量
        callback: 'callbackStaff', // 回调函数名称
      };
      if (name) {
        params.fuzzy_lookups = name; // 如果传入了 name 参数，则进行模糊查询
      }
      const scriptTag = document.createElement('script'); // 创建 script 标签
      scriptTag.setAttribute('type', 'text/javascript'); // 设置 script 标签类型
      // 设置 script 标签的 src 属性
      scriptTag.setAttribute('src', `${usersListPath}?${QueryString.stringify(params)}`);

      const headTag = document.getElementsByTagName('head')[0]; // 获取 head 标签
      // @ts-expect-error ignore
      window[params.callback] = ({ data, result }: {
        data: any
        result: boolean
      }) => {
        if (result) {
          this.fetching = false; // 设置 fetching 为 false，表示数据获取完成
          this.list = unionBy(this.list, data.results, 'id'); // 合并新获取的数据到列表中
        }
        headTag.removeChild(scriptTag); // 移除 script 标签
        delete window[params.callback]; // 删除回调函数
      };
      headTag.appendChild(scriptTag); // 将 script 标签添加到 head 标签中
    },
  },
});
