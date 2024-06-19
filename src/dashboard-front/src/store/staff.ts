// @ts-check
import { defineStore } from 'pinia';
import QueryString from 'qs';
import { shallowRef } from 'vue';
import _ from 'lodash';
const { BK_LIST_USERS_API_URL } = window;


export const useStaffStore = defineStore({
  id: 'staffStore',
  state: () => ({
    fetching: false,
    list: shallowRef([]),
  }),
  actions: {
    async fetchStaffs(name?: string) {
      if (this.fetching) return;
      this.fetching = true;
      const usersListPath = `${BK_LIST_USERS_API_URL}`;
      const params: any = {
        app_code: 'bk-magicbox',
        page: 1,
        page_size: 200,
        callback: 'callbackStaff',
      };
      if (name) {
        params.fuzzy_lookups = name;
      }
      const scriptTag = document.createElement('script');
      scriptTag.setAttribute('type', 'text/javascript');
      scriptTag.setAttribute('src', `${usersListPath}?${QueryString.stringify(params)}`);

      const headTag = document.getElementsByTagName('head')[0];
      // @ts-ignore
      window[params.callback] = ({ data, result }: { data: any, result: boolean }) => {
        if (result) {
          this.fetching = false;
          this.list = _.unionBy(this.list, data.results, 'id');
          console.log('staffs', this.list.length);
        }
        headTag.removeChild(scriptTag);
        // @ts-ignore
        delete window[params.callback];
      };
      headTag.appendChild(scriptTag);
    },
  },
});
