/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
  <div class="navigation-main">
    <BkNavigation
      class="navigation-main-content apigw-navigation"
      :class="{ 'custom-height-navigation': route.meta?.hideHeaderBorder }"
      default-open
      :need-menu="needMenu"
      navigation-type="left-right"
      @toggle="handleCollapse"
    >
      <!-- 左上角的网关选择器 -->
      <template #side-header>
        <div class="h-34px">
          <BkSelect
            v-show="!isMenuCollapsed"
            v-model="gatewayId"
            :clearable="false"
            class="header-select h-full"
            filterable
            @change="() => handleGoPage(activeMenuKey)"
          >
            <template #prefix>
              <div
                v-if="isProgrammableGateway || isAIGateway"
                class="gateway-selector-prefix"
                :style="{ left: `${iconLeft}px` }"
              >
                <AgIcon
                  v-bk-tooltips="{
                    content: isAIGateway ? t('AI 网关') : t('可编程网关'),
                    placement: 'right',
                  }"
                  :name="isAIGateway ? 'AIwangguan' : 'square-program'"
                  size="16"
                />
              </div>
            </template>
            <BkOption
              v-for="item in gatewayList"
              :id="item.id"
              :key="item.id"
              :name="item.name"
            >
              <div class="w-full flex items-center justify-between">
                <div class="flex items-center justify-center">
                  <span
                    class="text-ov"
                    :style="{ maxWidth: getOptionTextWidth(item) }"
                  >
                    {{ item.name }}
                  </span>
                  <BkPopover
                    v-if="[1, 2].includes(item.kind)"
                    placement="right"
                    :content="item.kind === 1 ? t('可编程网关') : t('AI 网关')"
                    :popover-delay="0"
                  >
                    <AgIcon
                      :name="item.kind === 1 ? 'square-program' : 'AIwangguan'"
                      size="16"
                      class="ml-6px color-#3a84ff"
                      :class="[
                        {
                          'mr-4px': !item.status
                        }
                      ]"
                    />
                  </BkPopover>
                </div>
                <BkTag
                  v-if="!item.status
                    || gatewayStore?.currentGateway?.status === 0 && gatewayId === item.id"
                >
                  {{ t('已停用') }}
                </BkTag>
              </div>
            </BkOption>
          </BkSelect>
        </div>
      </template>
      <template #menu>
        <BkMenu
          :collapse="isMenuCollapsed"
          :opened-keys="openedKeys"
          :active-key="activeMenuKey"
          :unique-open="false"
        >
          <template v-for="menu in menuList">
            <template v-if="menu.enabled">
              <template v-if="menu.children?.length">
                <BkSubmenu
                  :key="menu.name"
                  :title="menu.title"
                >
                  <template #icon>
                    <AgIcon
                      :name="menu.icon || ''"
                      size="18"
                    />
                    <BkBadge
                      v-if="['PermissionManage'].includes(menu.name) && permissionStore.count > 0"
                      dot
                      theme="danger"
                      :class="{'en': locale !== 'zh-cn'}"
                    />
                  </template>
                  <template v-for="child in menu.children">
                    <BkMenuItem
                      v-if="child.enabled && !(child.hideInProgrammable && isProgrammableGateway)"
                      :key="child.name"
                      @click.stop="() => handleGoPage(child.name)"
                    >
                      {{ child.title }}
                      <BkBadge
                        v-if="['PermissionApply'].includes(child.name ) && permissionStore.count > 0"
                        :count="permissionStore.count"
                        :max="99"
                        theme="danger"
                        :class="{'en': locale !== 'zh-cn'}"
                      />
                    </BkMenuItem>
                  </template>
                </BkSubmenu>
              </template>
              <template v-else>
                <BkMenuItem
                  v-if="!(menu.hideInProgrammable && isProgrammableGateway)"
                  :key="menu.name"
                  @click.stop="() => handleGoPage(menu.name)"
                >
                  <template #icon>
                    <AgIcon
                      :name="menu.icon || ''"
                      size="18"
                    />
                  </template>
                  {{ menu.title }}
                </BkMenuItem>
              </template>
            </template>
          </template>
        </BkMenu>
      </template>
      <div
        class="content-view"
        style="padding-top: 0;"
      >
        <!-- 默认头部 -->
        <div
          v-if="!route.meta.customHeader"
          class="content-header"
        >
          <AgIcon
            v-if="route.meta.showBackIcon"
            name="return-small"
            size="32"
            @click="handleBack"
          />
          {{ headerTitle }}
          <div
            v-if="route.meta.showPageName && pageName"
            class="title-name"
          >
            <span />
            <div class="name">
              {{ pageName }}
            </div>
          </div>
        </div>
        <div :class="routerViewWrapperClass">
          <RouterView
            :key="gatewayId"
            :gateway-id="gatewayId"
          />
        </div>
      </div>
    </BkNavigation>
    <!-- 1.13 版本升级提示 -->
    <Version113UpdateNotice ref="version113UpdateNoticeRef" />
  </div>
</template>

<script setup lang="ts">
import {
  useFeatureFlag,
  useGateway,
  usePermission,
  useStage,
} from '@/stores';
import { getGatewayList } from '@/services/source/gateway';
import type { IExtractListApiResults } from '@/services/types/utils';
import type { IMenu } from '@/types/common';
import { getStageList } from '@/services/source/stage';
import { getPermissionApplyList } from '@/services/source/permission';
import Version113UpdateNotice from '@/components/version-113-update-notice/Index.vue';

type GatewayItemType = IExtractListApiResults<typeof getGatewayList>;

const { t, locale } = useI18n();
const route = useRoute();
const router = useRouter();

const gatewayStore = useGateway();
const featureFlagStore = useFeatureFlag();
const permissionStore = usePermission();
const stageStore = useStage();

// 选中的菜单
const activeMenuKey = ref('StageOverview');
const gatewayList = ref<GatewayItemType[]>([]);
const openedKeys = ref<string[]>(['StageManagement', 'ResourceManagement']);
const needMenu = ref(true);
const pageName = ref('');
// 当前网关Id
const gatewayId = ref(0);
const iconLeft = ref(6);
// 页面header名
const headerTitle = ref('');

const isMenuCollapsed = ref(false);
const version113UpdateNoticeRef = ref();

const isShowNoticeAlert = computed(() => featureFlagStore.isEnabledNotice);
const isAIGateway = computed(() => gatewayStore.isAIGateway);
const isProgrammableGateway = computed(() => gatewayStore.isProgrammableGateway);
const menuList = computed<IMenu[]>(() => [
  {
    name: 'StageManagement',
    enabled: true,
    title: t('环境管理'),
    icon: 'resource',
    children: [
      {
        name: 'StageOverview',
        enabled: true,
        title: t('环境概览'),
      },
      {
        name: 'StageReleaseRecord',
        enabled: true,
        title: t('发布记录'),
      },
    ],
  },
  {
    name: 'BackendService',
    enabled: true,
    title: t('后端服务'),
    icon: 'fuwuguanli',
  },
  {
    name: 'ModelService',
    title: t('模型服务'),
    icon: 'cube-1',
    enabled: isAIGateway.value,
  },
  {
    name: 'ResourceManagement',
    enabled: true,
    title: t('资源管理'),
    icon: 'ziyuanguanli',
    children: [
      {
        name: 'ResourceSetting',
        enabled: true,
        title: t('资源配置'),
        // 是否在可编程网关中隐藏
        hideInProgrammable: true,
      },
      {
        name: 'ResourceVersion',
        enabled: true,
        title: t('资源版本'),
      },
    ],
  },
  {
    name: 'PermissionManage',
    enabled: true,
    title: t('权限管理'),
    icon: 'quanxianguanli',
    children: [
      {
        name: 'PermissionApply',
        enabled: true,
        title: t('权限审批'),
      },
      {
        name: 'PermissionApp',
        enabled: true,
        title: t('应用权限'),
      },
    ],
  },
  {
    name: 'apigwOperatingData',
    enabled: featureFlagStore.flags.ENABLE_RUN_DATA,
    title: t('运行数据'),
    icon: 'keguancexing',
    children: [
      {
        name: 'AccessLog',
        enabled: true,
        title: t('流水日志'),
      },
      {
        name: 'Dashboard',
        enabled: featureFlagStore.flags.ENABLE_RUN_DATA_METRICS,
        title: t('仪表盘'),
      },
      {
        name: 'Report',
        enabled: featureFlagStore.flags.ENABLE_RUN_DATA_METRICS,
        title: t('统计报表'),
      },
    ],
  },
  {
    name: 'MonitorAlarm',
    title: t('监控告警'),
    icon: 'gaojingjilu',
    enabled: featureFlagStore.flags.ENABLE_MONITOR,
    children: [
      {
        name: 'MonitorAlarmStrategy',
        title: t('告警策略'),
        enabled: true,
      },
      {
        name: 'MonitorAlarmHistory',
        title: t('告警记录'),
        enabled: true,
      },
    ],
  },
  {
    name: 'OnlineDebugging',
    enabled: true,
    title: t('在线调试'),
    icon: 'zaixiandiaoshi',
  },
  {
    name: 'MCP',
    title: 'MCP',
    icon: 'mcp-server',
    enabled: true,
    children: [
      {
        name: 'MCPServer',
        enabled: true,
        title: 'MCP Server',
      },
      {
        name: 'MCPServerPermission',
        title: t('MCP 权限管理'),
        enabled: true,
      },
      {
        name: 'MCPServerObservability',
        title: t('可观测'),
        enabled: featureFlagStore.flags.ENABLE_MCP_SERVER_OBSERVABILITY,
      },
    ],
  },
  {
    name: 'BasicInfo',
    enabled: true,
    title: t('基本信息'),
    icon: 'jibenxinxi',
  },
  {
    name: 'AuditLog',
    enabled: true,
    title: t('操作记录'),
    icon: 'history',
  },
]);

// 表格需要兼容的页面模块
const needBkuiTablePage = computed(() => {
  return [
    'BackendService',
    'ModelService',
    'PermissionApply',
    'PermissionRecord',
    'PermissionApp',
    'AuditLog',
    'MonitorAlarmStrategy',
    'MonitorAlarmHistory',
  ];
});

const routerViewWrapperClass = computed(() => {
  const initClass = 'default-header-view';
  const displayBkuiTable = needBkuiTablePage.value.includes(route.name as string) ? 'need-bkui-table-wrapper' : '';
  if (route.meta.customHeader) {
    return `custom-header-view ${displayBkuiTable}`;
  }
  if (stageStore.getNotUpdatedStages?.length > 0 && isShowNoticeAlert.value) {
    return `${initClass} has-stage-bar-show-notice ${displayBkuiTable}`;
  }
  if (isShowNoticeAlert.value) {
    return `${initClass} show-notice ${displayBkuiTable}`;
  }
  if (stageStore.getNotUpdatedStages?.length > 0 || isShowNoticeAlert.value) {
    return `${initClass} has-stage-bar`;
  }
  return `${initClass} ${displayBkuiTable}`;
});

const setBreadcrumbTitle = (payload: typeof route) => {
  const { title, aiTitle = '', standardTitle = '' } = payload?.meta ?? {};
  if (isAIGateway.value && aiTitle) {
    headerTitle.value = (payload.query?.kind === 'ai' ? aiTitle as string : standardTitle as string) ?? '';
  }
  else {
    headerTitle.value = (title as string) ?? '';
  }
};

// 监听当前路由
watch(
  [
    () => route.meta,
    () => route.params,
    () => route.name,
  ],
  () => {
    activeMenuKey.value = (route.meta?.matchRoute || route.name) as string;
    gatewayId.value = Number(route.params.id || 0);
    // 设置全局网关
    gatewayStore.fetchGatewayDetail(gatewayId.value);
    // if (!route.meta?.isMenu) {
    //   needMenu.value = false;
    // }
    // 设置面包屑标题
    setBreadcrumbTitle(route);

    // 设置一下默认展开的菜单项
    for (let i = 0; i < menuList.value.length; i++) {
      const item = menuList.value[i];
      const menuItem = item.children?.find((child: any) => child.name === activeMenuKey.value);
      if (menuItem) {
        openedKeys.value.push(item.name);
      }
    }

    if (gatewayId.value) {
      checkStageVersion();
    }
  },
  {
    immediate: true,
    deep: true,
  },
);

watch(
  () => gatewayStore.currentGateway,
  (newGateway) => {
    // 仅当网关数据存在，并且和当前页面网关id一致，才刷新标题
    if (newGateway && newGateway?.id === gatewayId.value) {
      setBreadcrumbTitle(route);
      nextTick(() => {
        getGatewayIconDistance(newGateway?.name ?? '');
      });
    }
  },
  { flush: 'post' },
);

const getGatewayData = async () => {
  const response = await getGatewayList({ limit: 10000 });
  gatewayList.value = response.results || [];
  const name = gatewayList.value.find(gw => gw.id === gatewayId.value)?.name ?? '';
  getGatewayIconDistance(name);
};

// 获取权限审批的数量
const getPermissionData = async () => {
  const res = await getPermissionApplyList(
    gatewayId.value,
    {
      offset: 0,
      limit: 10,
    },
  );
  permissionStore.setCount(res.count);
};

// 检查网关下的环境 schema 版本
async function checkStageVersion() {
  const stageList = await getStageList(gatewayId.value);
  if (stageList.some(item => item.status === 1 && item.resource_version?.schema_version === '1.0')) {
    version113UpdateNoticeRef.value?.show();
  }
}
// 根据网关不同状态展示文案最大宽度
const getOptionTextWidth = (gateway: GatewayItemType) => {
  // 如果当前网关既是编辑网关且已停用
  if (gateway.kind === 1) {
    if (!gateway.status) {
      return '100px';
    }
    return '180px';
  }

  // 如果当前网关既已停用
  if (!gateway.status) {
    return '120px';
  }

  return '200px';
};

const getGatewayTextWidth = (text: string) => {
  const ctx = document.createElement('canvas').getContext('2d');
  if (!ctx) return 0;
  const platform = window.navigator.platform.toLowerCase();
  const realFontFamily = platform.indexOf('win') === 0
    ? 'Microsoft Yahei,Helvetica,Aria'
    : getComputedStyle(document.body).fontFamily;
  // 14px 和页面select输入框字号保持一致
  ctx.font = `14px ${realFontFamily}`;
  return ctx.measureText(text).width;
};

// 动态获取网关icon的边距
const getGatewayIconDistance = (name: string) => {
  if (name) {
    const calcValue = getGatewayTextWidth(name) + 20;
    // 最小不能小于 24px，防止canvas测不准得到很小的值，图标盖住文字
    iconLeft.value = Math.max(calcValue, 24);
    // 防止图标跑到输入框外面
    iconLeft.value = Math.min(iconLeft.value, 176);
  }
};

const handleCollapse = (collapsed: boolean) => {
  isMenuCollapsed.value = !collapsed;
};

const handleGoPage = (routeName: string) => {
  gatewayStore.setApigwId(gatewayId.value);
  // 如果是可编程网关，则不展示资源配置，需要跳转到环境概览
  const gatewayData = gatewayList.value.find((item: GatewayItemType) => item.id === gatewayId.value);
  const isEditGateway = gatewayData?.kind === 1;
  router.push({
    name: ['ResourceSetting'].includes(routeName) && isEditGateway ? 'StageOverview' : routeName,
    params: { id: gatewayId.value },
  });
  getGatewayIconDistance(gatewayData?.name ?? '');
  getPermissionData();
};

const handleBack = () => {
  router.back();
};

onMounted(() => {
  Promise.all([getGatewayData(), getPermissionData()]);
});
</script>

<style lang="scss" scoped>
.navigation-main {
  height: calc(100vh - 52px);

  .navigation-main-radio {
    margin: 10px 0 20px;
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
          color: #63656e;
          cursor: pointer;
          background: linear-gradient(270deg, #dee0ea, #eaecf2);
        }
      }
    }

    .bk-menu {
      background: #fff !important;

      .bk-menu-item {
        margin: 0;
        color: rgb(99 101 110);

        .item-icon {

          .default-icon {
            background-color: rgb(197 199 205);
          }
        }

        &:hover {
          background: #f0f1f5;
        }
      }

      .bk-menu-item.is-active {
        color: rgb(58 132 255);
        background: rgb(225 236 255);

        .item-icon {

          .default-icon {
            background-color: rgb(58 132 255);
          }
        }
      }
    }

    .submenu-header {
      position: relative;

      .bk-badge-main {
        position: absolute;
        top: 1px;
        left: 120px;

        &.en {
          left: 142px;
        }

        .bk-badge {
          width: 6px;
          height: 6px;
          min-width: 6px;
          background-color: #ff5656;
        }
      }
    }

    .submenu-list {

      .bk-menu-item {

        .item-content {
          position: relative;

          .bk-badge-main {
            position: absolute;
            top: 6px;
            left: 58px;

             &.en {
              left: 130px;
            }

            .bk-badge {
              height: 18px;
              min-width: 18px;
              padding: 0 2px;
              font-size: 12px;
              line-height: 14px;
              background-color: #ff5656;
            }
          }
        }
      }
    }

    .submenu-header-icon {
      color: rgb(99 101 110);
    }

    .submenu-header-content {
      color: rgb(99 101 110);
    }

    .submenu-header-collapse {
      width: 22px;
      font-size: 22px;
    }

    .bk-menu-submenu.is-opened {
      background: #fff !important;
    }

    .bk-menu-submenu .submenu-header.is-collapse {
      color: rgb(58 132 255);
      background: rgb(225 236 255);

      .submenu-header-icon {
        color: rgb(58 132 255);
      }
    }
  }

  :deep(.navigation-container) {

    .container-header {
      height: 0 !important;
      flex-basis: 0 !important;
      border-bottom: 0;
    }
  }

  .navigation-main-content {
    border: 1px solid #ddd;

    .content-view {
      height: 100%;
      overflow: hidden;
      font-size: 14px;

      .content-header {
        display: flex;
        align-items: center;
        height: 52px;
        padding: 0 24px;
        margin-right: auto;
        font-size: 16px;
        color: #313238;
        background: #fff;
        border-bottom: 1px solid #dcdee5;
        box-shadow: 0 3px 4px 0 #0000000a;
        box-sizing: border-box;
        flex-basis: 52px;

        .icon-ag-return-small {
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
            margin-right: 8px;
            background: #dcdee5;
          }

          .name {
            font-size: 14px;
            color: #979ba5;
          }
        }
      }

      .default-header-view {
        height: calc(100vh - 105px);
        overflow: hidden auto;

        &.custom-header-view {
          height: 100%;
          margin-top: 52px;
          overflow: auto;
        }

        &.has-stage-bar {
          height: calc(100vh - 147px);
        }

        &.show-notice {
          height: calc(100vh - 145px);
        }

        &.has-stage-bar-show-notice {
          height: calc(100vh - 187px);
        }
      }

      .need-bkui-table-wrapper {
        overflow-y: hidden;

        :deep(.bk-table-body) {

          &.bk-scrollbar {

            .bk__rail-x,
            .bk__rail-y {
              display: none !important;
            }
          }
        }
      }
    }
  }
}

:deep(.header-select) {
  width: 224px;

  .bk-input {
    display: flex;
    align-items: center;
    background-color: #f5f7fa;
    border: none;
    border-radius: 2px;
    box-shadow: none;
    position: relative;

    .bk-input--text {
      font-size: 14px;
      color: #63656e;
      background-color: transparent;
      max-width: fit-content;
      margin-left: 6px;
      padding-right: 24px;
      order: 1;
    }

    .gateway-selector-prefix {
      width: 16px;
      flex-shrink: 0;
      color: #3a84ff;
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      order: 2;
    }
  }

  &.is-focus {
    border: 1px solid #3a84ff;
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
    margin: 0 8px;
    background: #DCDEE5;
  }
}
</style>
