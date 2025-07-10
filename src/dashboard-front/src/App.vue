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
          class="h-28px cursor-pointer"
        >
      </template>
      <template #header>
        <div class="header">
          <div class="header-nav">
            <template v-for="(item, index) in tabList">
              <div
                v-if="item.enabled"
                :key="item.id"
                class="header-nav-item"
                :class="{ 'item-active': index === activeIndex }"
                @click="handleNavClick(item.url, index, item.link)"
              >
                <span class="text">{{ item.name }}</span>
              </div>
            </template>
          </div>
          <div class="header-aside-wrap" />
        </div>
      </template>
      <div class="content">
        <RouterView v-if="userLoaded" />
      </div>
    </BkNavigation>
  </BkConfigProvider>
</template>

<script lang="ts" setup>
import LogoWithoutTitle from '@/images/APIgateway-logo.png';
import En from '../node_modules/bkui-vue/dist/locale/en.esm.js';
import ZhCn from '../node_modules/bkui-vue/dist/locale/zh-cn.esm.js';
import { useFeatureFlag, useUserInfo } from '@/stores';
import { getMyGateWayMenu } from '@/constants';

const route = useRoute();
const router = useRouter();
const userInfoStore = useUserInfo();
const featureFlagStore = useFeatureFlag();

userInfoStore.fetchUserInfo();
featureFlagStore.fetchFlags();

const locale = ref('zh-cn');
const activeIndex = ref(0);
const userLoaded = ref(false);
const curLeavePageData = ref({});

const tabList = computed(() => {
  return getMyGateWayMenu();
});

const bkuiLocale = computed(() => {
  if (locale.value === 'zh-cn') {
    return ZhCn;
  }
  return En;
});

const apigwId = computed(() => {
  return route.params.id;
});

watch(
  () => route.path,
  (newVal, oldVal) => {
    if (newVal === oldVal) {
      return;
    }
    const { meta } = route;
    activeIndex.value = tabList.value.findIndex(v => v.url === meta?.topMenu);
    if (activeIndex.value === -1) {
      activeIndex.value = 0;
    }
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

const handleNavClick = (url: string, index: number, link: string) => {
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
  font-family: "PingFang SC","Microsoft Yahei",Helvetica,Aria,sans-serif;
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
