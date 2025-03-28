<template>
  <BkConfigProvider :locale="bkuiLocale">
    <div id="app" :class="[systemCls]">
      <NoticeComponent
        v-if="showNoticeAlert && enableShowNotice"
        :api-url="noticeApi"
        @show-alert-change="handleShowAlertChange"
      />
      <bk-navigation
        class="navigation-content"
        navigation-type="top-bottom"
        :need-menu="false"
        :default-open="true"
        :side-title="sideTitle"
      >
        <template #side-icon>
          <img :src="appLogo" class="api-logo" />
        </template>
        <div class="content">
          <router-view v-if="userLoaded"></router-view>
        </div>
        <template #header>
          <div class="header">
            <div class="header-nav">
              <template v-for="(item, index) in headerList">
                <div
                  :key="item.id"
                  class="header-nav-item"
                  :class="{ 'item-active': index === activeIndex }"
                  v-if="item.enabled">
                  <span
                    v-if="!isExternalLink(item.url)"
                    @click="handleToPage(item.url, index, item.link)">{{item.name}}</span>
                  <a :href="item.url" target="_blank" v-else>{{item.name}}</a>
                </div>
              </template>
            </div>
            <div class="header-aside-wrap">
              <language-toggle></language-toggle>
              <product-info></product-info>
              <user-info v-if="userLoaded" />
            </div>
          </div>
        </template>
      </bk-navigation>

      <!-- <AppAuth ref="authRef" /> -->
    </div>
  </BkConfigProvider>
</template>

<script setup lang="ts">
import {
  computed,
  onMounted,
  ref,
  watch,
} from 'vue';
import { useI18n } from 'vue-i18n';
import {
  useRoute,
  useRouter,
} from 'vue-router';
import {
  ConfigProvider as BkConfigProvider,
  Message,
} from 'bkui-vue';
// @ts-ignore
import zhCn from 'bkui-vue/dist/locale/zh-cn.esm';
// @ts-ignore
import en from 'bkui-vue/dist/locale/en.esm';

// @ts-ignore
import NoticeComponent from '@blueking/notice-component';
import '@blueking/notice-component/dist/style.css';

import UserInfo from '@/components/user-info.vue';
import ProductInfo from '@/components/product-info.vue';
import LanguageToggle from '@/components/language-toggle.vue';
// import AppAuth from '@/components/auth/index.vue';
import mitt from '@/common/event-bus';
import {
  useCommon,
  useUser,
} from '@/store';
import {
  getFeatureFlags,
  getUser,
} from '@/http';
// import { ILoginData } from '@/common/auth';
import { useSidebar } from '@/hooks';
// @ts-ignore
import {
  getPlatformConfig,
  setDocumentTitle,
  setShortcutIcon,
} from '@blueking/platform-config';
// @ts-ignore
import logoWithoutName from '@/images/APIgateway-logo.png';
import { isChinese } from '@/language/i18n';
import constantConfig from '@/constant/config';
import { useScriptTag } from '@vueuse/core';
import BkUserDisplayName from '@blueking/bk-user-display-name';

const { initSidebarFormData, isSidebarClosed } = useSidebar();
const { t, locale } = useI18n();
const router = useRouter();
const route = useRoute();
const common = useCommon();
// 获取用户数据
const user = useUser();

const { BK_DASHBOARD_URL } = window;

// 接入访问统计逻辑，只在上云版执行
if (constantConfig.BK_ANALYSIS_SCRIPT_SRC) {
  try {
    const { BK_ANALYSIS_SCRIPT_SRC } = constantConfig;
    if (BK_ANALYSIS_SCRIPT_SRC) {
      useScriptTag(
        BK_ANALYSIS_SCRIPT_SRC,
        // script loaded 后的回调
        () => {
          window.BKANALYSIS.init({ siteName: 'custom:bk-apigateway:default:default' });
          console.log('BKANALYSIS init success');
        },
        // script 标签的 attrs
        {
          attrs: { charset: 'utf-8' },
        },
      );
    } else {
      console.log('BKANALYSIS script not found');
    }
  } catch {
    console.log('BKANALYSIS init fail');
  }
}

const bkuiLocaleData = {
  zhCn,
  en,
};

const bkuiLocale = computed(() => {
  if (locale.value === 'zh-cn') {
    return bkuiLocaleData.zhCn;
  }
  return bkuiLocaleData.en;
});

// t()方法的 | 符号有特殊含义，需要用插值才能正确显示
const sideTitle = computed(() => {
  // return t("蓝鲸 {pipe} API 网关", { pipe: '|'});
  return t('蓝鲸 API 网关');
});

const websiteConfig = ref<any>({});

const getWebsiteConfig = async () => {
  const bkSharedResUrl = window.BK_NODE_ENV === 'development'
    ? window.BK_DASHBOARD_FE_URL
    : window.BK_SHARED_RES_URL;

  if (bkSharedResUrl) {
    const url = bkSharedResUrl?.endsWith('/') ? bkSharedResUrl : `${bkSharedResUrl}/`;
    websiteConfig.value = await getPlatformConfig(`${url}${window.BK_APP_CODE || 'bk_apigateway'}/base.js`, constantConfig.SITE_CONFIG);
  } else {
    websiteConfig.value = await getPlatformConfig(constantConfig.SITE_CONFIG);
  }

  if (websiteConfig.value.i18n) {
    websiteConfig.value.i18n.appLogo = websiteConfig.value[isChinese ? 'appLogo' : 'appLogoEn'];
  }

  setShortcutIcon(websiteConfig.value?.favicon);
  setDocumentTitle(websiteConfig.value?.i18n);
  common.setWebsiteConfig(websiteConfig.value);
};
getWebsiteConfig();

const appLogo = computed(() => {
  return logoWithoutName;
});

// 加载完用户数据才会展示页面
const userLoaded = ref(false);
const activeIndex = ref(0);
// 跑马灯数据
const showNoticeAlert = ref(true);
const enableShowNotice = ref(false);
const noticeApi = ref(`${BK_DASHBOARD_URL}/notice/announcements/`);
const curLeavePageData = ref({});

// getUser()
//   .then((data) => {
//     user.setUser(data);
//     userLoaded.value = true;
//   })
//   .catch(() => {
//     Message('获取用户信息失败，请检查后再试');
//   });

// getFeatureFlags({ limit: 10000, offset: 0 }).then((data) => {
//   console.log(data);
//   user.setFeatureFlags(data);
// })
//   .catch(() => {
//     Message('获取功能权限失败，请检查后再试');
//   });

const headerList = computed(() => ([
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
    url: 'componentsMain',
    enabled: user.featureFlags?.MENU_ITEM_ESB_API && !user.featureFlags?.ENABLE_MULTI_TENANT_MODE,
    link: '',
  },
  {
    name: t('API 文档'),
    id: 3,
    url: 'apiDocs',
    enabled: true,
    link: '',
  },
  // {
  //   name: t('网关API文档'),
  //   id: 3,
  //   url: 'apigwDoc',
  //   enabled: true,
  //   link: '',
  // },
  // {
  //   name: t('组件API文档'),
  //   id: 4,
  //   url: 'componentDoc',
  //   enabled: user.featureFlags?.MENU_ITEM_ESB_API_DOC,
  //   link: '',
  // },
  // {
  //   name: t('网关API SDK'),
  //   id: 5,
  //   params: {
  //     type: 'apigateway',
  //   },
  //   url: 'apigwSDK',
  //   enabled: user.featureFlags?.ENABLE_SDK,
  //   link: '',
  // },
  // {
  //   name: t('组件API SDK'),
  //   id: 6,
  //   params: {
  //     type: 'esb',
  //   },
  //   url: 'esbSDK',
  //   enabled: user.featureFlags?.ENABLE_SDK,
  //   link: '',
  // },
]));

const systemCls = ref('mac');
// const authRef = ref();

const apigwId = computed(() => {
  if (route.params.id !== undefined) {
    return route.params.id;
  }
  return undefined;
});

const handleShowAlertChange = (payload: boolean) => {
  showNoticeAlert.value = payload;
};

// const fetchUserInfo = async () => {
//   try {
//     const res = await getUser();
//     user.setUser(res);
//     userLoaded.value = true;
//   } catch (e: any) {
//     console.error(e);
//     if (e?.code !== 'UNAUTHENTICATED') {
//       Message('获取用户信息失败，请检查后再试');
//     }
//   }
// };

// const fetchFeatureFlags = async () => {
//   try {
//     const res = await getFeatureFlags({ limit: 10000, offset: 0 });
//     enableShowNotice.value = res?.ENABLE_BK_NOTICE || false;
//     user.setFeatureFlags(res);
//   } catch (e: any) {
//     console.error(e);
//     if (e?.code !== 'UNAUTHENTICATED') {
//       Message('获取功能权限失败，请检查后再试');
//     }
//   };
// };

watch(
  // () => route.fullPath,
  () => route.path,
  async (val, prevVal) => {
    if (val === prevVal) {
      return;
    }
    const { meta } = route;
    let index = 0;
    for (let i = 0; i < headerList.value.length; i++) {
      const item = headerList.value[i];
      if (item.url === meta?.topMenu) {
        index = i;
        break;
      }
    }
    activeIndex.value = index;
    const platform = window.navigator.platform.toLowerCase();
    if (platform.indexOf('win') === 0) {
      systemCls.value = 'win';
    }

    try {
      const [useRes, flagsRes] = await Promise.all([
        getUser(),
        getFeatureFlags({ limit: 10000, offset: 0 }),
      ]);

      user.setUser(useRes);

      enableShowNotice.value = flagsRes?.ENABLE_BK_NOTICE || false;
      user.setFeatureFlags(flagsRes);

      // 多租户 display_name 组件展示配置
      // 在 template 中使用时，不需再 import，否则报错
      if (user.featureFlags?.ENABLE_MULTI_TENANT_MODE) {
        BkUserDisplayName.configure({
          tenantId: user.user.tenant_id,
          apiBaseUrl: user.apiBaseUrl,
        });
      }

      userLoaded.value = true;
    } catch (e: any) {
      console.error(e);
      if (e?.code !== 'UNAUTHENTICATED') {
        Message('获取用户信息或功能权限失败，请检查后再试');
      }
    }
  },
  {
    immediate: true,
    deep: true,
  },
);

const isExternalLink  = (url?: string) => /^https?:\/\//.test(url);

const handleToPage = async (routeName: string, index: number, link: string) => {
  let result = true;
  console.log(curLeavePageData.value);
  if (Object.keys(curLeavePageData.value).length > 0) {
    result = await isSidebarClosed(JSON.stringify(curLeavePageData.value)) as boolean;
    if (result) {
      getRouteData(routeName, index, link);
    }
  } else {
    getRouteData(routeName, index, link);
  }
};

const getRouteData = (routeName: string, index: number, link: string) => {
  curLeavePageData.value = {};
  activeIndex.value = index;
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
        id: ['home', 'apigwDoc', 'apiDocs'].includes(routeName) ? '' : apigwId.value,
      },
    });
  }
};

onMounted(() => {
  // 处理其他页面离开页面前是否会出现提示框的判断
  mitt.on('on-leave-page-change', (payload: Record<string, any>) => {
    curLeavePageData.value = payload;
    initSidebarFormData(payload);
  });
  // mitt.on('show-login-modal', (payload: ILoginData) => {
  //   authRef.value.showLoginModal(payload);
  // });
  // mitt.on('close-login-modal', () => {
  //   authRef.value.hideLoginModal();
  //   setTimeout(() => {
  //     window.location.reload();
  //   }, 0);
  // });
});

// onBeforeMount(() => {
//   mitt.off('show-login-modal');
//   mitt.off('close-login-modal');
// });
</script>

<style lang="scss">
@import './css/app.css';

// 多租户人员选择器样式
.multiple-selector .tags-container:not(.focused) {
  border-color: #c4c6cc !important;
}
</style>
<style lang="scss" scoped>
.navigation-content {
  // :deep(.bk-navigation-header) {
  //   min-width: 1280px;
  // }

  :deep(.bk-navigation-wrapper) {
    .container-content{
      padding: 0 !important;
      // 最小宽度应为 1280px 减去左侧菜单栏展开时的宽度 260px，即为 1020px
      min-width: 1020px;
    }
  }

  .content {
    font-size: 14px;
    height: 100%;
  }

  :deep(.title-desc) {
    color: #eaebf0;
    cursor: pointer;
  }

  .api-logo {
    height: 28px;
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
      flex: 1;
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

    .header-aside-wrap {
      display: flex;
      align-items: center;
      gap: 14px;
    }
  }
}
</style>
