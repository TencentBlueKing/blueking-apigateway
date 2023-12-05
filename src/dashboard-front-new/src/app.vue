<script setup lang="ts">
import {
  ref,
  computed,
  watch,
} from 'vue';
import * as UserInfo from '@/components/user-info.vue';
import { useI18n } from 'vue-i18n';
import { useRouter, useRoute } from 'vue-router';
import { useUser } from '@/store';
import { getUser } from '@/http';
import { Message } from 'bkui-vue';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const { BK_PAAS2_ESB_DOC_URL } = window;

// 加载完用户数据才会展示页面
const userLoading = ref(false);
const activeIndex = ref(0);
// 获取用户数据
const user = useUser();
getUser()
  .then((data) => {
    user.setUser(data);
    userLoading.value = true;
  })
  .catch(() => {
    Message('获取用户信息失败，请检查后再试');
  });

const headerList = ref([
  {
    name: t('我的网关'),
    id: 1,
    url: 'home',
    enabled: true,
    link: '',
  },
  {
    name: t('组件管理'),
    id: 2,
    url: 'apigwAccess',
    enabled: true,
    link: '',
  },
  {
    name: t('网关API文档'),
    id: 3,
    url: 'apigwDoc',
    enabled: true,
    link: '',
  },
  {
    name: t('组件API文档'),
    id: 4,
    url: 'componentDoc',
    enabled: true,
    link: '',
  },
  {
    name: t('网关API SDK'),
    id: 5,
    params: {
      type: 'apigateway',
    },
    url: 'apigwSDK',
    enabled: true,
    link: '',
  },
  {
    name: t('组件API SDK'),
    id: 6,
    params: {
      type: 'esb',
    },
    url: 'esbSDK',
    enabled: true,
    link: '',
  },

]);

const apigwId = computed(() => {
  if (route.params.id !== undefined) {
    return route.params.id;
  }
  return undefined;
});

watch(
  () => route.fullPath,
  () => {
    const { name } = route;

    let index = 0;
    for (let i = 0; i < headerList.value.length; i++) {
      const item = headerList.value[i];
      if (item.url === name) {
        index = i;
        break;
      }
    }
    activeIndex.value = index;
  },
);

const isExternalLink  = (url?: string) => /^https?:\/\//.test(url);

const handleToPage = (routeName: string, index: number, link: string) => {
  activeIndex.value = index;
  // 文档组件API
  if (routeName === 'componentAPI') {
    if (BK_PAAS2_ESB_DOC_URL) {
      window.open(BK_PAAS2_ESB_DOC_URL);
      return;
    }
  }
  // 常用工具
  if (!!link) {
    window.open(routeName);
    return;
  }
  if (routeName === 'apigwSystem') {
    router.push({
      name: 'apigwSystem',
    });
    return;
  }
  goPage(routeName);
};

const goPage = (routeName: string) => {
  if (routeName) {
    router.push({
      name: routeName,
      params: {
        id: ['home', 'apigwDoc'].includes(routeName) ? '' : apigwId.value,
      },
    });
  }
};

</script>

<template>
  <bk-navigation
    class="navigation-content"
    navigation-type="top-bottom"
    :need-menu="false"
    :default-open="true"
  >
    <template #side-icon>
      <!-- v-if="localLanguage === 'en'" -->
      <img src="@/images/APIgataway-c.png" class="api-logo">
      <!-- <img v-else src="@/images/APIgataway-c.png" class="api-logo"> -->
    </template>
    <div class="content">
      <router-view v-if="userLoading"></router-view>
    </div>
    <template #header>
      <div
        class="header"
      >
        <div class="header-nav">
          <div
            v-for="(item, index) in headerList"
            :key="item.id"
            class="header-nav-item"
            :class="{ 'item-active': index === activeIndex }"
          >
            <span
              v-if="!isExternalLink(item.url)"
              @click="handleToPage(item.url, index, item.link)">{{item.name}}</span>
            <a :href="item.url" target="_blank" v-else>{{item.name}}</a>
          </div>
        </div>
        <user-info v-if="userLoading" />
      </div>
    </template>
  </bk-navigation>
</template>

<style>
@import './css/app.css';
</style>
<style lang="scss" scoped>
.navigation-content {
  :deep(.bk-navigation-wrapper) {
    .container-content{
      padding: 0px !important;
    }
  }

  .content {
    font-size: 14px;
    height: 100%;
  }

  .api-logo{
    height: 22px;
    cursor: pointer;
  }

  .header{
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 14px;
    color: #96A2B9;
    .header-nav {
      display: flex;
      padding: 0;
      margin: 0;
      &-item {
          list-style: none;
          margin-right: 40px;
          color: #96A2B9;
          &.item-active {
              color: #FFFFFF !important;
          }
          &:hover {
              cursor: pointer;
              color: #D3D9E4;
          }
          a {
              color: #96A2B9;
              &:hover {
                  color: #D3D9E4;
              }
          }
      }
    }
  }
}
</style>
