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
<template>
  <BkConfigProvider :locale="bkuiLocale">
    <BkNavigation
      class="navigation-content"
      navigation-type="top-bottom"
      :need-menu="false"
      default-open
      side-title="蓝鲸 API 网关"
    >
      <template #side-icon>
        <img
          :src="LogoWithoutTitle"
          alt="API Gateway"
          class="max-w-none h-28px cursor-pointer"
        >
      </template>
      <template #header>
        <div class="header">
          <div class="header-nav">
            <template v-for="(item, index) in menuList">
              <div
                v-if="item.enabled"
                :key="item.id"
                class="header-nav-item"
                :class="{ 'item-active': index === activeIndex }"
                @click="() => handleNavClick(item.url, index, item.link)"
              >
                <span class="text">{{ item.name }}</span>
              </div>
            </template>
          </div>
          <div class="header-aside-wrap">
            <LanguageToggle />
            <UserInfo v-if="userInfoStore.info.display_name || userInfoStore.info.username" />
          </div>
        </div>
      </template>
      <div class="content">
        <RouterView v-if="userLoaded" />
      </div>
    </BkNavigation>
  </BkConfigProvider>
</template>

<script lang="ts" setup>
import LanguageToggle from '@/components/language-toggle/Index.vue';
import UserInfo from '@/components/user-info/Index.vue';
import LogoWithoutTitle from '@/images/APIgateway-logo.png';
import En from '../node_modules/bkui-vue/dist/locale/en.esm.js';
import ZhCn from '../node_modules/bkui-vue/dist/locale/zh-cn.esm.js';
import {
  useEnv,
  useFeatureFlag,
  useGateway,
  useUserInfo,
} from '@/stores';
import { useBkUserDisplayName } from '@/hooks';
import type { IHeaderNav } from '@/types/common';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const userInfoStore = useUserInfo();
const featureFlagStore = useFeatureFlag();
const envStore = useEnv();
const { configure: configureDisplayName } = useBkUserDisplayName();
const gateway = useGateway();

userInfoStore.fetchUserInfo();
featureFlagStore.fetchFlags();
envStore.fetchEnv();

const locale = ref('zh-cn');
const activeIndex = ref(0);
const userLoaded = ref(false);
const curLeavePageData = ref({});

const menuList: IHeaderNav[] = [
  {
    name: t('我的网关'),
    id: 1,
    url: 'Home',
    enabled: true,
    link: '',
  },
  {
    name: t('组件管理'),
    id: 2,
    url: 'ComponentsMain',
    enabled: true,
    link: '',
  },
  {
    name: t('API 文档'),
    id: 3,
    url: 'Docs',
    enabled: true,
    link: '',
  },
  {
    name: t('平台工具'),
    id: 4,
    url: 'PlatformTools',
    enabled: true,
    link: '',
  },
  {
    name: t('MCP 市场'),
    id: 5,
    url: 'McpMarket',
    enabled: true,
    link: '',
  },
];

const bkuiLocale = computed(() => {
  if (locale.value === 'zh-cn') {
    return ZhCn;
  }
  return En;
});

const apigwId = computed(() => {
  return route.params.id;
});

configureDisplayName();

watch(
  () => route.path,
  (newVal, oldVal) => {
    if (newVal === oldVal) {
      return;
    }
    const { meta } = route;
    activeIndex.value = menuList.findIndex(menu => menu.url === meta?.topMenu);
    if (activeIndex.value === -1) {
      activeIndex.value = 0;
    }
    gateway.setApigwId(apigwId.value);
    userLoaded.value = true;
  },
  {
    immediate: true,
    deep: true,
  },
);

const goPage = (routeName: string): void => {
  const id = ['home', 'apigwDoc', 'apiDocs'].includes(routeName) ? '' : apigwId.value;
  router.push({
    name: routeName,
    params: { id },
  });
};

const getRouteData = (routeName: string, index: number, link: string) => {
  curLeavePageData.value = {};
  activeIndex.value = index;
  // 常用工具
  if (link) {
    window.open(routeName);
    return;
  }
  if (['apigwSystem'].includes(routeName)) {
    router.push({ name: routeName });
    return;
  }
  goPage(routeName);
};

const handleNavClick = (url: string, index: number, link: string = '') => {
  // 禁止重复点击
  if (index === activeIndex.value) {
    return;
  }
  getRouteData(url, index, link);
};
</script>

<style lang="scss">
#app {
  width: 100%;
  height: 100vh;
  min-width: 1280px;
  overflow: auto;
  font-size: 14px;
  color: #63656e;
  text-align: left;
  background: #f5f7fb;
}
</style>

<style lang="scss" scoped>
.navigation-content {

  :deep(.bk-navigation-wrapper) {

    .container-content {
      // 最小宽度应为 1280px 减去左侧菜单栏展开时的宽度 260px，即为 1020px
      min-width: 1020px;
      padding: 0 !important;
    }
  }

  .content {
    height: 100%;
    font-size: 14px;
  }

  :deep(.title-desc) {
    color: #eaebf0;
    cursor: pointer;
  }

  .header {
    display: flex;
    width: 100%;
    font-size: 14px;
    color: #96A2B9;
    align-items: center;
    justify-content: space-between;

    .header-nav {
      display: flex;
      flex: 1;
      padding: 0;
      margin: 0;

      .header-nav-item {
        margin-right: 40px;
        color: #96A2B9;
        list-style: none;

        &.item-active {
          color: #FFF !important;
        }

        &:hover {
          color: #D3D9E4;
          cursor: pointer;
        }

        text {
          color: #96A2B9;

          &:hover {
            color: #D3D9E4;
          }
        }
      }
    }

    .header-aside-wrap {
      display: flex;
      align-items: center;
      gap: 14px;
    }
  }
}
</style>
