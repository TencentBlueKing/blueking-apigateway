<template>
  <div class="navigation-main">
    <bk-navigation
      :class="[
        'navigation-main-content',
        'apigw-navigation',
        route.name === 'apigwResourceVersion' ? 'custom-height-navigation' : ''
      ]"
      :default-open="true"
      :need-menu="needMenu"
      navigation-type="left-right"
      @toggle="handleCollapse"
    >
      <template #menu>
        <bk-menu
          :collapse="collapse"
          :opened-keys="openedKeys"
          :active-key="activeMenuKey"
          :unique-open="false"
        >
          <template v-for="menu in menuData">
            <template v-if="menu.enabled">
              <template v-if="menu.children?.length">
                <bk-submenu
                  :key="menu.name"
                  :title="menu.title"
                >
                  <template #icon>
                    <i :class="['icon apigateway-icon', `icon-ag-${menu.icon}`]"></i>
                    <bk-badge
                      dot
                      theme="danger"
                      style="margin-left: 5px"
                      v-if="menu.name === 'apigwPermissionManage' && permission.count !== 0"
                    >
                    </bk-badge>
                  </template>
                  <template v-for="child in menu.children">
                    <bk-menu-item
                      v-if="child.enabled"
                      :key="child.name"
                      @click.stop="handleGoPage(child.name, apigwId)"
                    >
                      {{ child.title }}
                      <bk-badge
                        :count="permission.count"
                        :max="99"
                        theme="danger"
                        style="margin-left: 5px"
                        v-if="child.name === 'apigwPermissionApplys' && permission.count !== 0"
                      >
                      </bk-badge>
                    </bk-menu-item>
                  </template>
                </bk-submenu>
              </template>
              <template v-else>
                <bk-menu-item
                  :key="menu.name"
                  @click.stop="handleGoPage(menu.name, apigwId)"
                >
                  <template #icon>
                    <i :class="['icon apigateway-icon', `icon-ag-${menu.icon}`]"></i>
                  </template>
                  {{ menu.title }}
                </bk-menu-item>
              </template>
            </template>
          </template>
        </bk-menu>
      </template>
      <template #side-header>
        <bk-select
          ref="apigwSelect"
          class="header-select"
          filterable
          v-model="apigwId"
          @change="handleGoPage(activeMenuKey, apigwId)"
          :clearable="false">
          <bk-option
            v-for="item in gatewaysList" :key="item.id" :id="item.id" :name="item.name"
          />
        </bk-select>
      </template>
      <!-- 提示发布 -->
      <tips-publish-bar v-show="stage.getNotUpdatedStages?.length" />
      <div class="content-view" :style="stage.getNotUpdatedStages?.length ? 'padding-top: 42px' : 'padding-top: 0px'">
        <!-- 默认头部 -->
        <div class="flex-row align-items-center content-header" v-if="!route.meta.customHeader">
          <i
            class="icon apigateway-icon icon-ag-return-small"
            v-if="route.meta.showBackIcon"
            @click="handleBack"></i>
          {{ headerTitle }}
          <div class="title-name" v-if="route.meta.showPageName && pageName">
            <span></span>
            <div class="name">{{ pageName }}</div>
          </div>
        </div>
        <div :class="routerViewWrapperClass">
          <router-view
            :key="apigwId" :apigw-id="apigwId">
          </router-view>
        </div>
      </div>
    </bk-navigation>

    <version-release-note ref="versionReleaseNoteRef" />
  </div>
</template>

<script setup lang="ts">
import {
  ref,
  watch,
  onMounted,
  onBeforeUnmount,
  computed,
} from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { createMenuData } from '@/common/menu';
import { useGetApiList, useSidebar, useGetStageList } from '@/hooks';
import { useCommon, usePermission, useStage } from '@/store';
import { getPermissionApplyList, getGatewaysDetail } from '@/http';
import mitt from '@/common/event-bus';
import { cloneDeep } from 'lodash';
import versionReleaseNote from '@/components/version-release-note.vue';
import tipsPublishBar from '@/components/tips-publish-bar.vue';

const { initSidebarFormData, isSidebarClosed } = useSidebar();
const route = useRoute();
const router = useRouter();
// 全局公共字段存储
const common = useCommon();
const permission = usePermission();
const filterData = ref({ name: '' });
const apigwSelect = ref();

const stage = useStage();
const versionReleaseNoteRef = ref();
const { getStagesStatus } = useGetStageList();

// 获取网关数据方法
const {
  getGatewaysListData,
} = useGetApiList(filterData);
const collapse = ref(true);
// 选中的菜单
const activeMenuKey = ref('apigwOperateRecords');
const gatewaysList = ref<any>([]);
const openedKeys = ref<string[]>([]);

// 当前网关Id
const apigwId = ref(0);
const apigwIdBack = ref(0);

// 页面header名
const headerTitle = ref('');

// 当前离开页面的数据
const curLeavePageData = ref({});

const routerViewWrapperClass = computed(() => {
  if (route.meta.customHeader) {
    return 'custom-header-view';
  }
  if (stage.getNotUpdatedStages?.length) {
    return 'default-header-view has-notice';
  }
  return 'default-header-view';
});

const handleCollapse = (v: boolean) => {
  mitt.emit('side-toggle', v);
  collapse.value = !v;
};

// 设置网关名
const handleSetApigwName = () => {
  const apigwObj = gatewaysList.value.find((apigw: any) => apigw.id === apigwId.value) || {};
  common.setApigwName(apigwObj?.name);
};

// 将当前的网关详情存到全局pinia中
const handleSetApigwDeatail = async () => {
  const curApigwDataDetail = await getGatewaysDetail(apigwId.value);
  common.setCurApigwData(curApigwDataDetail);
};

const getStages = async () => {
  const res = await getStagesStatus();
  if (res?.notUpdatedStages?.length) {
    versionReleaseNoteRef.value?.show();
  }
};

const needMenu = ref(true);
const menuData = ref([]);
const pageName = ref<string>('');

// 监听当前路由
watch(
  () => route,
  (val: any) => {
    activeMenuKey.value = val.meta.matchRoute;
    apigwId.value = Number(val.params.id);
    apigwIdBack.value = cloneDeep(apigwId.value);
    headerTitle.value = val.meta.title;
    // 设置全局网关id
    common.setApigwId(apigwId.value);
    // 设置全局网关名称
    handleSetApigwName();
    // 设置当前网关详情
    handleSetApigwDeatail();

    if (val.meta.isMenu === false) {
      needMenu.value = false;
    }

    menuData.value = createMenuData();

    const curOpenedKeys = openedKeys.value;
    const menuDataLen = menuData.value.length;
    for (let i = 0; i < menuDataLen; i++) {
      const item = menuData.value[i];
      const finded = item.children?.find((child: any) => child.name === activeMenuKey.value);
      if (finded) {
        curOpenedKeys.push(item.name);
      }
    }
    openedKeys.value = curOpenedKeys;
  },
  { immediate: true, deep: true },
);

// 获取权限审批的数量
const getPermList = async () => {
  try {
    const res = await getPermissionApplyList(apigwId.value, { offset: 0, limit: 10 });
    permission.setCount(res.count);
  } catch (error) {
    console.log('error', error);
  }
};

const handleGoPage = async (routeName: string, id?: number) => {
  let result = true;
  if (Object.keys(curLeavePageData.value).length > 0) {
    result = await isSidebarClosed(JSON.stringify(curLeavePageData.value)) as boolean;
    if (result) {
      getRouteData(routeName, id);
      // apigwId.value = apigwIdBack.value;
    }
  } else {
    getRouteData(routeName, id);
  }
};

const getRouteData = (routeName: string, id?: number) => {
  curLeavePageData.value = {};
  common.setApigwId(id);
  router.push({
    name: routeName,
    params: {
      id,
    },
  });
  getPermList();
};

mitt.on('update-name', ({ name }) => {
  pageName.value = name;
});

onBeforeUnmount(() => {
  mitt.off('update-name');
});

const handleBack = () => {
  router.back();
};

watch(
  () => apigwId.value,
  (v) => {
    if (v) {
      setTimeout(() => {
        getStages();
      }, 200);
    }
  },
  { immediate: true },
);

onMounted(async () => {
  // 处理其他页面离开页面前是否会出现提示框的判断
  mitt.on('on-leave-page-change', (payload: Record<string, any>) => {
    curLeavePageData.value = payload;
    initSidebarFormData(payload);
  });
  gatewaysList.value = await getGatewaysListData();
  // 初始化设置一次
  handleSetApigwName();
  getPermList();
});
</script>

<style lang="scss" scoped>
.navigation-main {
  height: calc(100vh - 52px);
  &-radio {
    margin: 10px 0 20px 0;
  }

  :deep(.navigation-nav) {
    .nav-slider {
      background: #fff !important;
      border-right: 1px solid #dcdee5 !important;
      .bk-navigation-title {
        flex-basis: 51px !important;
      }
      .nav-slider-list {
        border-top: 1px solid #f0f1f5;
      }
    }
    .footer-icon {
      &.is-left {
        color: #63656e;
        &:hover {
          background: linear-gradient(270deg, #dee0ea, #eaecf2);
          color: #63656e;
          cursor: pointer;
        }
      }
    }
    .bk-menu{
      background: #fff !important;
      .bk-menu-item{
        color: rgb(99, 101, 110);
        margin: 0px;
        .item-icon{
          .default-icon{
            background-color: rgb(197, 199, 205);
          }
        }
        &:hover{
          background: #F0F1F5;
        }
      }
      .bk-menu-item.is-active {
        color: rgb(58, 132, 255);
        background: rgb(225, 236, 255);
        .item-icon{
          .default-icon{
            background-color: rgb(58, 132, 255);
          }
        }
      }
    }
    .submenu-header{
      position: relative;
      .bk-badge-main{
        position: absolute;
        left: 120px;
        top: 1px;
        .bk-badge{
          width: 6px;
          height: 6px;
          min-width: 6px;
          background-color: #ff5656;
        }
      }
    }
    .submenu-list{
      .bk-menu-item{
        .item-content{
          position: relative;
          .bk-badge-main{
            position: absolute;
            top: 6px;
            left: 56px;
            .bk-badge{
              background-color: #ff5656;
              height: 18px;
              padding: 0px 2px;
              font-size: 12px;
              line-height: 14px;
              min-width: 18px;
            }
          }
        }
      }
    }

    .submenu-header-icon{
      color: rgb(99, 101, 110);
    }
    .submenu-header-content{
      color: rgb(99, 101, 110);
    }
    .submenu-header-collapse {
      width: 22px;
      font-size: 22px;
    }
    .bk-menu-submenu.is-opened {
      background: #fff !important;
    }
    .bk-menu-submenu .submenu-header.is-collapse {
      color: rgb(58, 132, 255);
      background: rgb(225, 236, 255);
      .submenu-header-icon {
        color: rgb(58, 132, 255);
      }
    }
  }

  :deep(.navigation-container) {
    .container-header{
      height: 0px !important;
      flex-basis: 0px !important;
      border-bottom: 0px;
    }
  }

  &-content {
    border: 1px solid #ddd;

    .content-view {
      height: 100%;
      font-size: 14px;
      overflow: hidden;
      .content-header{
        display: flex;
        flex-basis: 52px;
        padding: 0 24px;
        background: #fff;
        border-bottom: 1px solid #dcdee5;
        // box-shadow: 0 3px 4px rgba(64,112,203,0.05882);
        box-shadow: 0 3px 4px 0 #0000000a;
        height: 52px;
        box-sizing: border-box;
        margin-right: auto;
        color: #313238;
        font-size: 16px;
        .icon-ag-return-small{
          font-size: 32px;
          color: #3a84ff;
          cursor: pointer;
        }
        .title-name {
          display: flex;
          align-items: center;
          margin-left: 8px;
          span {
            width: 1px;
            height: 14px;
            background: #DCDEE5;
            margin-right: 8px;
          }
          .name {
            font-size: 14px;
            color: #979BA5;
          }
        }
      }
      .default-header-view{
        height: calc(100vh - 105px);
        overflow: auto;

        &.has-notice {
          height: calc(100vh - 147px);
        }
      }
      .custom-header-view{
        margin-top: 52px;
        height: 100%;
        overflow: auto;
      }
    }
  }
  :deep(.header-select){
    width: 224px;
    .bk-input {
      border: none;
      background: #F5F7FA;
      border-radius: 2px;
      box-shadow: none;
      .bk-input--text{
        background: #F5F7FA;
        color: #63656E;
        font-size: 14px;
      }
    }
    &.is-focus {
      border: 1px solid #3a84ff;
    }
  }
}
</style>
<style lang="scss">
.custom-height-navigation {
  .content-header {
    border-bottom: none !important;
  }
}
.custom-side-header {
  display: flex;
  align-items: center;
  .title {
    font-size: 16px;
    font-weight: 400;
    color: #313238;
  }
  .subtitle {
    font-size: 14px;
    color: #979BA5;
  }
  span {
    width: 1px;
    height: 14px;
    background: #DCDEE5;
    margin: 0 8px;
  }
}
</style>
