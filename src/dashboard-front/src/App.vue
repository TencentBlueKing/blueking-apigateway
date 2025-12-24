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
    <div
      id="app"
      :class="[
        systemCls,
        { 'show-notice-wrapper': enableShowNotice && showNoticeAlert}
      ]"
    >
      <NoticeComponent
        v-if="enableShowNotice"
        :api-url="noticeApi"
        @show-alert-change="handleShowAlertChange"
      />
      <BkNavigation
        class="navigation-content"
        :class="[`${route.name}-navigation-content`]"
        navigation-type="top-bottom"
        :need-menu="false"
        default-open
      >
        <template #side-header>
          <div
            class="flex items-center gap-16px"
            @click="handleLogoClick"
          >
            <div>
              <img
                :src="LogoWithoutTitle"
                alt="API Gateway"
                class="max-w-none h-28px cursor-pointer"
              >
            </div>
            <div class="text-16px font-bold color-#eaebf0 cursor-pointer">
              {{ t('蓝鲸 API 网关') }}
            </div>
          </div>
        </template>
        <template #header>
          <div class="flex items-center justify-between header">
            <div class="flex flex-1 header-nav">
              <template v-for="(item, index) in menuList">
                <div
                  v-if="item.enabled"
                  :key="item.id"
                  class="mr-40px header-nav-item"
                  :class="{ 'item-active': index === activeIndex }"
                  @click="() => handleNavClick(item.url, index, item.link)"
                >
                  <span class="text">{{ item.name }}</span>
                </div>
              </template>
            </div>
            <div class="header-aside-wrap">
              <LanguageToggle />
              <ProductInfo />
              <UserInfo />
            </div>
          </div>
        </template>
        <div class="content">
          <RouterView v-if="userLoaded" />
        </div>
      </BkNavigation>
    </div>
  </BkConfigProvider>
</template>

<script lang="ts" setup>
import LanguageToggle from '@/components/language-toggle/Index.vue';
import ProductInfo from '@/components/product-info/Index.vue';
import UserInfo from '@/components/user-info/Index.vue';
import LogoWithoutTitle from '@/images/APIgateway-logo.png';
// @ts-expect-error missing module type
import En from '../node_modules/bkui-vue/dist/locale/en.esm.js';
// @ts-expect-error missing module type
import ZhCn from '../node_modules/bkui-vue/dist/locale/zh-cn.esm.js';
// @ts-expect-error missing module type
import NoticeComponent from '@blueking/notice-component';

import {
  useEnv,
  useFeatureFlag,
  useGateway,
  useUserInfo,
} from '@/stores';
import { useBkUserDisplayName } from '@/hooks';
import type { IHeaderNav } from '@/types/common';
import { useScriptTag, useTitle } from '@vueuse/core';

const { t, locale } = useI18n();
const route = useRoute();
const router = useRouter();
const userInfoStore = useUserInfo();
const featureFlagStore = useFeatureFlag();
const envStore = useEnv();
const { configure: configureDisplayName } = useBkUserDisplayName();
const gateway = useGateway();

// 接入访问统计逻辑，只在上云版执行
if (envStore.env.BK_ANALYSIS_SCRIPT_SRC) {
  try {
    const src = envStore.env.BK_ANALYSIS_SCRIPT_SRC;
    if (src) {
      useScriptTag(
        src,
        // script loaded 后的回调
        () => {
          window.BKANALYSIS?.init({ siteName: 'custom:bk-apigateway:default:default' });
        },
        // script 标签的 attrs
        { attrs: { charset: 'utf-8' } },
      );
    }
    else {
      console.log('BKANALYSIS script not found');
    }
  }
  catch {
    console.log('BKANALYSIS init fail');
  }
}

const systemCls = ref('mac');
const activeIndex = ref(0);
const userLoaded = ref(false);
const showNoticeAlert = ref(false);
const enableShowNotice = ref(false);
const noticeApi = ref(`${envStore.env.BK_DASHBOARD_URL}/backend/notice/announcements/`);
const curLeavePageData = ref({});

const bkuiLocale = computed(() => {
  if (locale.value === 'zh-cn') {
    return ZhCn;
  }
  return En;
});

const apigwId = computed(() => {
  return route.params.id;
});

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
    enabled: false,
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
  {
    name: t('微网关'),
    id: 6,
    url: envStore.env.BK_APISIX_URL,
    enabled: envStore.env.EDITION === 'te',
    link: envStore.env.BK_APISIX_URL,
  },
];

const fetchInitData = async () => {
  await getUserInfo();
  await getFlagList();
};

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
    const platform = window.navigator.platform.toLowerCase();
    if (platform.indexOf('win') === 0) {
      systemCls.value = 'win';
    }
    gateway.setApigwId(apigwId.value);
    // 需要在不同页面实时查询以下接口最新状态
    fetchInitData();
  },
  {
    immediate: true,
    deep: true,
  },
);

watch(locale, () => {
  const docTitle = useTitle();
  docTitle.value = t('API Gateway | 腾讯蓝鲸智云');
}, { immediate: true });

// flag需要是实时的，确保不同页面组件执行顺序需要监听下
async function getFlagList() {
  try {
    await featureFlagStore.fetchFlags();
    enableShowNotice.value = featureFlagStore.flags.ENABLE_BK_NOTICE;
    const isEnabledComManagement = featureFlagStore.flags?.MENU_ITEM_ESB_API
      && !featureFlagStore.flags?.ENABLE_MULTI_TENANT_MODE;

    featureFlagStore.setNoticeAlert(enableShowNotice.value && showNoticeAlert.value);
    featureFlagStore.setDisplayComManagement(isEnabledComManagement);

    const comNav = menuList.find(item => ['ComponentsMain'].includes(item.url));
    if (comNav) {
      comNav.enabled = isEnabledComManagement;
    }
  }
  finally {
    userLoaded.value = true;
  }
}

// 这里需要取user和env的接口数据处理多租户配置信息
async function getUserInfo() {
  try {
    const userData = await userInfoStore.fetchUserInfo();
    const envData = await envStore.fetchEnv();
    const tenantId = userData?.tenant_id ?? '';
    const apiBaseUrl = envData?.env?.BK_USER_WEB_API_URL ?? '';

    configureDisplayName({
      tenantId,
      apiBaseUrl,
    });
  }
  catch (error) {
    console.error('getUserInfo 执行失败：', error);
  }
};

const goPage = (routeName: string): void => {
  const id = ['Home', 'ApiDocs'].includes(routeName) ? '' : apigwId.value;
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
  if (index === activeIndex.value && !['Home', 'McpMarket'].includes(url)) {
    return;
  }
  getRouteData(url, index, link);
};

const handleLogoClick = () => {
  router.replace({ name: 'Home' });
};

const handleShowAlertChange = (isShowNotice: boolean) => {
  showNoticeAlert.value = isShowNotice;
  featureFlagStore.setNoticeAlert(enableShowNotice.value && showNoticeAlert.value);
};

</script>

<style lang="scss" scoped>
#app {
  width: 100%;
  height: 100vh;
  min-width: 1280px;
  overflow: hidden;
  font-size: 14px;
  color: #63656e;
  text-align: left;
  background: #f5f7fb;

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
      width: 100%;
      font-size: 14px;
      color: #96A2B9;

      .header-nav {
        padding: 0;
        margin: 0;

        .header-nav-item {
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

    &.ApiDocs-navigation-content {

      :deep(.bk-navigation-wrapper) {

        .container-content {
          overflow: hidden;
        }
      }
    }

    &.PlatformToolsToolbox-navigation-content,
    &.McpMarketDetails-navigation-content {
      :deep(.bk-navigation-wrapper) {

        .container-content,
        .default-header-view {
          overflow: hidden;
        }
      }
    }
  }

  &.show-notice-wrapper {

    .Home-navigation-content {

      :deep(.bk-navigation-wrapper) {

        .container-content {
          max-height: calc(100vh - 92px) !important;
        }
      }
    }
  }
}
</style>
