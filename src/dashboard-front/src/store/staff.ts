// @ts-check
import { defineStore } from 'pinia';
import QueryString from 'qs';
import { shallowRef } from 'vue';
import _ from 'lodash';

const { BK_LIST_USERS_API_URL } = window;

/**
 * 使用 Pinia 定义一个名为 useStaffStore 的 store
 */
export const useStaffStore = defineStore({
  id: 'staffStore', // store 的唯一标识符
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
      if (this.fetching) return; // 如果正在获取数据，则直接返回
      this.fetching = true; // 设置 fetching 为 true，表示开始获取数据
      const usersListPath = `${BK_LIST_USERS_API_URL}`; // 获取员工列表的 API URL
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
      scriptTag.setAttribute('src', `${usersListPath}?${QueryString.stringify(params)}`); // 设置 script 标签的 src 属性

      const headTag = document.getElementsByTagName('head')[0]; // 获取 head 标签
      // @ts-ignore
      window[params.callback] = ({ data, result }: { data: any, result: boolean }) => {
        if (result) {
          this.fetching = false; // 设置 fetching 为 false，表示数据获取完成
          this.list = _.unionBy(this.list, data.results, 'id'); // 合并新获取的数据到列表中
          console.log('staffs', this.list.length); // 打印员工列表的长度
        }
        headTag.removeChild(scriptTag); // 移除 script 标签
        // @ts-ignore
        delete window[params.callback]; // 删除回调函数
      };
      headTag.appendChild(scriptTag); // 将 script 标签添加到 head 标签中
    },
  },
});
