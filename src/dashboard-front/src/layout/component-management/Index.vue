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
      class="navigation-main-content"
      :default-open="collapse"
      navigation-type="left-right"
      @toggle="handleCollapse"
    >
      <template #menu>
        <BkMenu
          :collapse="collapse"
          :opened-keys="openedKeys"
          :active-key="activeMenuKey"
        >
          <template v-for="menu in componentsMenu">
            <template v-if="menu?.children?.length">
              <BkSubmenu
                :key="menu.name"
                :title="menu.title"
              >
                <template #icon>
                  <i
                    class="icon apigateway-icon"
                    :class="[`icon-ag-${menu.icon}`]"
                  />
                </template>
                <BkMenuItem
                  v-for="child in menu.children"
                  :key="child.name"
                  @click="handleGoPage(child.name, apigwId)"
                >
                  {{ child.title }}
                </BkMenuItem>
              </BkSubmenu>
            </template>
            <template v-else>
              <BkMenuItem
                :key="menu.name"
                @click="handleGoPage(menu.name, apigwId)"
              >
                <template #icon>
                  <i
                    class="icon apigateway-icon"
                    :class="[`icon-ag-${menu.icon}`]"
                  />
                </template>
                {{ menu.title }}
              </BkMenuItem>
            </template>
          </template>
        </BkMenu>
      </template>

      <div class="content-view">
        <!-- 默认头部 -->
        <div
          v-if="!route.meta.customHeader"
          class="content-header"
        >
          <i
            v-if="route.meta.showBackIcon"
            class="icon apigateway-icon icon-ag-return-small"
            @click="handleBack"
          />
          {{ headerTitle }}
        </div>
        <div :class="routerViewWrapperClass">
          <RouterView :key="apigwId" />
        </div>
      </div>
    </BkNavigation>
  </div>
</template>

<script setup lang="ts">
import { useGateway } from '@/stores';
import { useGatewaysList } from '@/hooks';
import type { IMenu } from '@/types/common';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
// 全局公共字段存储
const gatewayStore = useGateway();

const filterData = ref({ name: '' });
const collapse = ref(true);
const activeMenuKey = ref('');
const gatewaysList = ref([]);
const apigwId = ref(0);
const headerTitle = ref('');
const componentsMenu = shallowRef<IMenu>([
  {
    name: 'ComponentsIntro',
    title: t('简介'),
    icon: 'component-intro',
  },
  {
    name: 'ComponentsSystem',
    title: t('系统管理'),
    icon: 'system-mgr',
  },
  {
    name: 'ComponentsManage',
    title: t('组件管理'),
    icon: 'components',
  },
  {
    name: 'ComponentsCategory',
    title: t('文档分类'),
    icon: 'document',
  },
  {
    name: 'ComponentsRuntimeData',
    title: t('实时运行数据'),
    icon: 'runtime',
  },
]);

// 获取网关数据方法
const { getGatewaysListData } = useGatewaysList(filterData);

const openedKeys = computed(() => componentsMenu.value.map(item => item.name));
// 表格需要兼容的页面模块
const needBkuiTablePage = computed(() => {
  return [
    'ComponentsSystem',
    'ComponentsManage',
    'ComponentsCategory',
    'ComponentsPermission',
    'ComponentsRuntimeData',
    'SyncApigwAccess',
    'SyncHistory',
    'SyncVersion',
  ];
});
const routerViewWrapperClass = computed(() => {
  const displayBkuiTable = needBkuiTablePage.value.includes(route.name) ? 'need-bkui-table-wrapper' : '';
  if (route.meta.customHeader) {
    return `custom-header-view ${displayBkuiTable}`;
  }
  return `default-header-view ${displayBkuiTable}`;
});

// 设置网关名
const handleSetApigwName = () => {
  const apigwObj = gatewaysList.value.find(apigw => apigw.id === apigwId.value) || {};
  gatewayStore.setApigwName(apigwObj?.name);
};

// 监听当前路由
watch(
  [
    () => route.meta,
    () => route.params,
  ],
  () => {
    const { title, matchRoute } = route.meta ?? {};
    activeMenuKey.value = matchRoute;
    headerTitle.value = title;
    if (route.params.id) {
      apigwId.value = Number(route.params.id);
      handleSetApigwName();
      // 设置全局网关
      gatewayStore.fetchGatewayDetail(apigwId.value);
    }
  },
  {
    immediate: true,
    deep: true,
  },
);

const handleCollapse = (isCollapse: boolean) => {
  collapse.value = !isCollapse;
};

const handleGoPage = (routeName: string, apigwId?: number) => {
  gatewayStore.setApigwId(apigwId);
  router.push({
    name: routeName,
    params: { id: apigwId },
  });
};

const handleBack = () => {
  router.back();
};

onMounted(async () => {
  gatewaysList.value = await getGatewaysListData();
  // 初始化设置一次
  handleSetApigwName();
});
</script>

<style lang="scss" scoped>
.navigation-main {
  height: calc(100vh - 52px);

  .navigation-main-radio {
    margin: 10px 0 20px 0;
  }

  :deep(.navigation-nav) {
    .nav-slider {
      background: #ffffff !important;

      .bk-navigation-title {
        display: none !important;
      }

      .nav-slider-list {
        border-top: 1px solid #f0f1f5;
      }
    }

    .bk-menu {
      background: #ffffff !important;

      .bk-menu-item {
        color: rgb(99, 101, 110);
        margin: 0px;

        .item-icon {
          .default-icon {
            background-color: rgb(197, 199, 205);
          }
        }

        &:hover {
          background-color: #f0f1f5;
        }

        &.is-active {
          color: rgb(58, 132, 255);
          background: rgb(225, 236, 255);

          .item-icon {
            .default-icon {
              background-color: rgb(58, 132, 255);
            }
          }
        }
      }
    }

    .submenu-header {
      position: relative;

      .bk-badge-main {
        position: absolute;
        left: 120px;
        top: 1px;

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
            left: 56px;

            .bk-badge {
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

    .submenu-header-icon {
      color: rgb(99, 101, 110);
    }

    .submenu-header-content {
      color: rgb(99, 101, 110);
    }

    .bk-menu-submenu.is-opened {
      background: #fff !important;
    }
  }

  :deep(.navigation-container) {
    .container-header {
      height: 0px !important;
      flex-basis: 0px !important;
      border-bottom: 0px;
    }
  }

  .navigation-main-content {
    border: 1px solid #ddd;

    .content-view {
      height: 100%;
      font-size: 14px;
      overflow: hidden;

      .content-header {
        display: flex;
        align-items: center;
        flex-basis: 51px;
        padding: 0 24px;
        background: #fff;
        border-bottom: 1px solid #dcdee5;
        box-shadow: 0 3px 4px rgba(64, 112, 203, 0.05882);
        height: 51px;
        margin-right: auto;
        color: #313238;
        font-size: 16px;

        .icon-ag-return-small {
          font-size: 32px;
          color: #3a84ff;
          cursor: pointer;
        }
      }

      .default-header-view {
        height: calc(100vh - 105px);
        overflow: auto;

        &.custom-header-view {
          margin-top: 52px;
          height: 100%;
          overflow: auto;
        }

        &.need-bkui-table-wrapper {
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
    width: 240px;

    .bk-input--text {
      background: rgb(245, 247, 250);
    }
  }
}
</style>
