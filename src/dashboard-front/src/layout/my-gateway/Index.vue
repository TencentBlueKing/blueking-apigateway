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
        <BkSelect
          v-model="gatewayId"
          :clearable="false"
          class="header-select"
          filterable
          @change="() => handleGoPage(activeMenuKey)"
        >
          <template #prefix>
            <div class="gateway-selector-prefix">
              <AgIcon
                v-if="gatewayStore.isProgrammableGateway"
                name="square-program"
                size="20"
              />
            </div>
          </template>
          <BkOption
            v-for="item in gatewayList"
            :id="item.id"
            :key="item.id"
            :name="item.name"
          >
            <div class="gateway-select-option">
              <AgIcon
                v-if="item.kind === 1"
                name="square-program"
                class="mr-6px color-#3a84ff"
              />
              <div
                v-else
                class="w-14px mr-6px"
              />
              <span>{{ item.name }}</span>
            </div>
          </BkOption>
        </BkSelect>
      </template>
      <template #menu>
        <BkMenu
          :collapse="collapse"
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
                      class="m-l-5px"
                    />
                  </template>
                  <template v-for="child in menu.children">
                    <BkMenuItem
                      v-if="child.enabled && !(child.hideInProgrammable && gatewayStore.isProgrammableGateway)"
                      :key="child.name"
                      @click.stop="() => handleGoPage(child.name)"
                    >
                      {{ child.title }}
                      <BkBadge
                        v-if="['PermissionApply'].includes(child.name ) && permissionStore.count > 0"
                        :count="permissionStore.count"
                        :max="99"
                        theme="danger"
                        class="m-l-5px"
                      />
                    </BkMenuItem>
                  </template>
                </BkSubmenu>
              </template>
              <template v-else>
                <BkMenuItem
                  v-if="!(menu.hideInProgrammable && gatewayStore.isProgrammableGateway)"
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
  </div>
</template>

<script setup lang="ts">
import { useFeatureFlag, useGateway, usePermission } from '@/stores';
import { getGatewayList } from '@/services/source/gateway.ts';
import { getPermissionApplyList } from '@/services/source/permission';
interface IMenu {
  name: string
  title: string
  icon?: string
  enabled?: boolean
  children?: IMenu[]
  // 是否在可编程网关中隐藏，默认 false
  hideInProgrammable?: boolean
}

type GatewayItemType = Awaited<ReturnType<typeof getGatewayList>>['results'][number];

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const gatewayStore = useGateway();
const featureFlagStore = useFeatureFlag();
const permissionStore = usePermission();

const collapse = ref(true);
// 选中的菜单
const activeMenuKey = ref('StageOverview');
const gatewayList = ref<GatewayItemType[]>([]);
const openedKeys = ref<string[]>([]);
const needMenu = ref(true);
const pageName = ref('');

// 当前网关Id
const gatewayId = ref(0);

// 页面header名
const headerTitle = ref('');

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
    // enabled: featureFlagStore.flags.ENABLE_RUN_DATA,
    enabled: true,
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
        // enabled: featureFlagStore.flags.ENABLE_RUN_DATA_METRICS,
        enabled: true,
        title: t('仪表盘'),
      },
      {
        name: 'Report',
        // enabled: featureFlagStore.flags.ENABLE_RUN_DATA_METRICS,
        enabled: true,
        title: t('统计报表'),
      },
    ],
  },
  {
    name: 'MonitorAlarm',
    title: t('监控告警'),
    icon: 'notification',
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
    name: 'apigwOnlineTest',
    enabled: true,
    title: t('在线调试'),
    icon: 'zaixiandiaoshi',
  },
  {
    name: 'BasicInfo',
    enabled: true,
    title: t('基本信息'),
    icon: 'jibenxinxi',
  },
  {
    name: 'mcpServer',
    enabled: true,
    title: 'MCP Server',
    icon: 'cardd',
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
    'PermissionApply',
    'PermissionRecord',
    'PermissionApp',
    'AuditLog',
    'MonitorAlarmStrategy',
    'MonitorAlarmHistory',
  ];
});

const routerViewWrapperClass = computed(() => {
  const displayBkuiTable = needBkuiTablePage.value.includes(route.name) ? 'need-bkui-table-wrapper' : '';
  if (route.meta.customHeader) {
    return `custom-header-view ${displayBkuiTable}`;
  }
  return `default-header-view ${displayBkuiTable}`;
});

// 监听当前路由
watch(
  [
    () => route.meta,
    () => route.params,
  ],
  () => {
    activeMenuKey.value = route.meta.matchRoute as string;
    gatewayId.value = Number(route.params.id || 0);
    headerTitle.value = route.meta.title as string;
    // 设置全局网关
    gatewayStore.fetchGatewayDetail(gatewayId.value);

    if (route.meta.isMenu === false) {
      needMenu.value = false;
    }
  },
  {
    immediate: true,
    deep: true,
  },
);

const getGatewayData = async () => {
  const response = await getGatewayList({ limit: 10000 });
  gatewayList.value = response.results || [];
};

// 获取权限审批的数量
const getPermissionData = async () => {
  const res = await getPermissionApplyList(
    gatewayId.value, {
      offset: 0,
      limit: 10,
    });
  permissionStore.setCount(res.count);
};

const handleCollapse = (v: boolean) => {
  collapse.value = !v;
};

const handleGoPage = (routeName: string) => {
  gatewayStore.setApigwId(gatewayId.value);
  router.push({
    name: routeName,
    params: { id: gatewayId.value },
  });
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

    .bk-menu{
      background: #fff !important;

      .bk-menu-item{
        margin: 0;
        color: rgb(99 101 110);

        .item-icon{

          .default-icon{
            background-color: rgb(197 199 205);
          }
        }

        &:hover{
          background: #F0F1F5;
        }
      }

      .bk-menu-item.is-active {
        color: rgb(58 132 255);
        background: rgb(225 236 255);

        .item-icon{

          .default-icon{
            background-color: rgb(58 132 255);
          }
        }
      }
    }

    .submenu-header{
      position: relative;

      .bk-badge-main{
        position: absolute;
        top: 1px;
        left: 120px;

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

    .submenu-header-icon{
      color: rgb(99 101 110);
    }

    .submenu-header-content{
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

    .container-header{
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
            background: #DCDEE5;
          }

          .name {
            font-size: 14px;
            color: #979BA5;
          }
        }
      }

      .default-header-view {
        height: calc(100vh - 105px);
        overflow: auto;

        &.custom-header-view {
          height: 100%;
          margin-top: 52px;
          overflow: auto;
        }

        &.has-notice {
          height: calc(100vh - 147px);
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

  :deep(.header-select) {
    width: 224px;

    .bk-input {
      background: #F5F7FA;
      border: none;
      border-radius: 2px;
      box-shadow: none;

      .bk-input--text{
        font-size: 14px;
        color: #63656E;
        background: #F5F7FA;
      }
    }

    &.is-focus {
      border: 1px solid #3a84ff;
    }
  }
}

.gateway-selector-prefix {
  display: flex;
  width: 20px;
  margin-left: 6px;
  color: #3a84ff;
  justify-content: center;
  align-items: center;
}

.gateway-select-option {
  display: flex;
  justify-content: center;
  align-items: center;
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
