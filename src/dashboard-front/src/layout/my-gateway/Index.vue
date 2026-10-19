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
        <div>
          <BkSelect
            v-show="!isMenuCollapsed"
            v-model="gatewayId"
            class="gateway-select"
            filterable
            :clearable="false"
            :search-placeholder="t('请搜索网关')"
            :popover-options="{
              extCls: 'gateway-select-popover',
            }"
            @change="() => handleGoPage(activeMenuKey)"
          >
            <template #prefix>
              <div
                class="gateway-selector-prefix ml-8px my-4px"
                :class="[getGatewayKind.color, getGatewayKind.bgColor]"
              >
                <AgIcon
                  v-bk-tooltips="{
                    content: getGatewayKind.name,
                    placement: 'right',
                  }"
                  size="22"
                  :name="getGatewayKind.icon"
                  :class="[getGatewayKind.color, getGatewayKind.bgColor]"
                />
              </div>
            </template>
            <template #extension>
              <div class="m-auto cursor-pointer">
                <div
                  class="flex items-center color-#979ba5"
                  @click.stop="handleCreateGateway"
                >
                  <AgIcon
                    class="mr-8px color-#979ba5 b-rounded-2px"
                    name="plus-circle"
                    size="16"
                  />
                  <span class="text-12px color-#4d4f56">
                    {{ t('创建应用') }}
                  </span>
                </div>
              </div>
            </template>
            <BkOption
              v-for="item of gatewayList"
              :id="item.id"
              :key="item.id"
              :name="item.name"
            >
              <div class="w-full flex items-center justify-between">
                <div class="flex items-center justify-center">
                  <BkPopover
                    placement="right"
                    :content="getKindInfo(item.kind).name"
                    :popover-delay="0"
                  >
                    <AgIcon
                      :name="getKindInfo(item.kind).icon"
                      size="20"
                      class="mr-8px b-rounded-2px"
                      :class="[getKindInfo(item.kind).color, getKindInfo(item.kind).bgColor]"
                    />
                  </BkPopover>
                  <span class="max-w-180px color-#4d4f56 text-ov">
                    {{ item.name }}
                  </span>
                </div>
                <BkTag
                  v-if="!item.status || gatewayStore?.currentGateway?.status === 0 && gatewayId === item.id"
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
          <template v-for="menu in visibleMenuList">
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
            :key="(route.params.id as string)"
            :gateway-id="Number(route.params.id)"
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
  useGatewayRoleStore,
  usePermission,
  useStage,
  useUserInfo,
} from '@/stores';
import { getGatewayList } from '@/services/source/gateway';
import type { IExtractListApiResults } from '@/services/types/utils';
import type { IMenu } from '@/types/common';
import { getStageList } from '@/services/source/stage';
import { getPermissionApplyList } from '@/services/source/permission';
import Version113UpdateNotice from '@/components/version-113-update-notice/Index.vue';
import { useGatewayRole } from '@/hooks';
import { canAccessByRole } from '@/utils/gateway-permission';
import { isGatewayNavigationPending } from '@/router/gateway-role-guard';
import { getGatewayErrorRoute } from '@/utils/gateway-access-error';

type GatewayItemType = IExtractListApiResults<typeof getGatewayList>;

const { t, locale } = useI18n();
const route = useRoute();
const router = useRouter();

const gatewayStore = useGateway();
const featureFlagStore = useFeatureFlag();
const permissionStore = usePermission();
const stageStore = useStage();
const roleStore = useGatewayRoleStore();
const userStore = useUserInfo();
const { currentRole, roleStatus, roleError, canAccess } = useGatewayRole();

// 选中的菜单
const activeMenuKey = ref('StageOverview');
const gatewayList = ref<GatewayItemType[]>([]);
const openedKeys = ref<string[]>(['StageManagement', 'ResourceManagement']);
const needMenu = ref(true);
const pageName = ref('');
// 当前网关Id
const gatewayId = ref(0);
// 页面header名
const headerTitle = ref('');

const isMenuCollapsed = ref(false);
const version113UpdateNoticeRef = ref();

const isShowNoticeAlert = computed(() => featureFlagStore.isEnabledNotice);
const isAIGateway = computed(() => gatewayStore.isAIGateway);
const isProgrammableGateway = computed(() => gatewayStore.isProgrammableGateway);
// 只稳定当前网关的菜单展示；请求完成、身份变化或角色失效后立即采用新状态。
// 页面访问与操作权限仍使用 currentRole，由守卫等待最新角色后决定是否放行。
const menuRole = computed(() => {
  const state = roleStore.roles[Number(route.params.id)];
  return state?.status === 'loading' ? state.previousRole ?? '' : currentRole.value;
});
const menuList = computed<IMenu[]>(() => [
  {
    name: 'StageManagement',
    enabled: true,
    title: t('环境管理'),
    icon: 'setting',
    permission: 'stage',
    children: [
      {
        name: 'StageOverview',
        enabled: true,
        title: t('环境概览'),
        permission: 'stage',
      },
      {
        name: 'StageReleaseRecord',
        enabled: true,
        title: t('发布记录'),
        permission: 'stage',
      },
    ],
  },
  {
    name: 'BackendService',
    enabled: true,
    title: t('后端服务'),
    icon: 'backend',
    permission: 'backend',
  },
  {
    name: 'ModelService',
    title: t('模型服务'),
    icon: 'cube-1',
    enabled: isAIGateway.value,
    permission: 'model',
  },
  {
    name: 'ResourceManagement',
    enabled: true,
    title: t('资源管理'),
    icon: 'resources',
    permission: 'resource',
    children: [
      {
        name: 'ResourceSetting',
        enabled: true,
        title: t('资源配置'),
        // 是否在可编程网关中隐藏
        hideInProgrammable: true,
        permission: 'resource',
      },
      {
        name: 'ResourceVersion',
        enabled: true,
        title: t('资源版本'),
        permission: 'resource',
      },
    ],
  },
  {
    name: 'PermissionManage',
    enabled: true,
    title: t('权限管理'),
    icon: 'permission-2',
    permission: 'permission',
    children: [
      {
        name: 'PermissionApply',
        enabled: true,
        title: t('权限审批'),
        permission: 'permission',
      },
      {
        name: 'PermissionApp',
        enabled: true,
        title: t('应用权限'),
        permission: 'permission',
      },
    ],
  },
  {
    name: 'apigwOperatingData',
    enabled: featureFlagStore.flags.ENABLE_RUN_DATA,
    title: t('运行数据'),
    icon: 'runtime-data',
    permission: 'runtime',
    children: [
      {
        name: 'AccessLog',
        enabled: true,
        title: t('流水日志'),
        permission: 'runtime',
      },
      {
        name: 'Dashboard',
        enabled: featureFlagStore.flags.ENABLE_RUN_DATA_METRICS,
        title: t('仪表盘'),
        permission: 'runtime',
      },
      {
        name: 'Report',
        enabled: featureFlagStore.flags.ENABLE_RUN_DATA_METRICS,
        title: t('统计报表'),
        permission: 'runtime',
      },
    ],
  },
  {
    name: 'MonitorAlarm',
    title: t('监控告警'),
    icon: 'warning',
    enabled: featureFlagStore.flags.ENABLE_MONITOR,
    children: [
      {
        name: 'MonitorAlarmStrategy',
        title: t('告警策略'),
        enabled: true,
        permission: 'alarm-strategy',
      },
      {
        name: 'MonitorAlarmHistory',
        title: t('告警记录'),
        enabled: true,
        permission: 'alarm-history',
      },
    ],
  },
  {
    name: 'OnlineDebugging',
    enabled: true,
    title: t('在线调试'),
    icon: 'debugging',
    permission: 'debug',
  },
  {
    name: 'MCP',
    title: 'MCP',
    icon: 'mcp',
    enabled: true,
    children: [
      {
        name: 'MCPServer',
        enabled: true,
        title: 'MCP Server',
        permission: 'mcp-server',
      },
      {
        name: 'MCPServerPermission',
        title: t('MCP 权限管理'),
        enabled: true,
        permission: 'mcp-perm',
      },
      {
        name: 'MCPServerObservability',
        title: t('可观测'),
        enabled: featureFlagStore.flags.ENABLE_MCP_SERVER_OBSERVABILITY,
        permission: 'mcp-obs',
      },
    ],
  },
  {
    name: 'GatewaySettings',
    enabled: true,
    title: t('网关设置'),
    icon: 'gateway-settings',
    children: [
      {
        name: 'BasicInfo',
        enabled: true,
        title: t('基本信息'),
        permission: 'basic-view',
      },
      {
        name: 'MemberManagement',
        enabled: true,
        title: t('成员管理'),
        permission: 'member',
      },
      {
        name: 'AuditLog',
        enabled: true,
        title: t('操作记录'),
        permission: 'audit',
      },
    ],
  },
]);

const visibleMenuList = computed(() => menuList.value
  .map((menu) => {
    if (!menu.children?.length) {
      return menu;
    }
    return {
      ...menu,
      children: menu.children.filter(child => isMenuVisible(child)),
    };
  })
  .filter((menu) => {
    if (menu.children) {
      return menu.enabled && menu.children.length > 0;
    }
    return isMenuVisible(menu);
  }));

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
    'MemberManagement',
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

const getKindInfo = (kind?: number | null) => {
  if (kind === 1) {
    return {
      icon: 'wangguanleixing-biancheng',
      name: t('可编程网关'),
      color: 'color-#0e3377',
      bgColor: 'bg-#bdc2ce',
    };
  }

  if (kind === 2) {
    return {
      icon: 'wangguanleixing-ai',
      name: t('AI 网关'),
      color: 'color-#6228ff',
      bgColor: 'bg-#ece5ff',
    };
  }

  return {
    icon: 'wangguanleixing-wangguan',
    name: t('API 网关'),
    color: 'color-#3a84ff',
    bgColor: 'bg-#cddffe',
  };
};

// 左上角前缀图标跟随当前选中网关的类型
const getGatewayKind = computed(() => getKindInfo(gatewayStore.currentGateway?.kind));

const setBreadcrumbTitle = (payload: typeof route) => {
  const { title, aiTitle = '', standardTitle = '' } = payload?.meta ?? {};
  if (isAIGateway.value && aiTitle) {
    headerTitle.value = (payload.query?.kind === 'ai' ? aiTitle as string : standardTitle as string) ?? '';
  }
  else {
    headerTitle.value = (title as string) ?? '';
  }
};

// 检查网关下的环境 schema 版本
const checkStageVersion = async (id: number) => {
  const stageList = await getStageList(id);
  if (id === Number(route.params.id) && canAccess('stage')
    && stageList.some(item => item.status === 1 && item.resource_version?.schema_version === '1.0')) {
    version113UpdateNoticeRef.value?.show();
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
    // 网关详情与角色已由路由守卫加载，布局不再重复请求。
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
    }
  },
  { flush: 'post' },
);

// 身份变化后由布局补载当前网关；导航中的角色校验与缓存刷新仍交给守卫。
const refreshCurrentGateway = async () => {
  const currentRoute = router.currentRoute.value;
  const id = Number(currentRoute.params.id);
  if (
    !Number.isSafeInteger(id)
    || id <= 0
    || !userStore.info.username
    || currentRoute.meta.skipRoleCheck
    || isGatewayNavigationPending(router)
  ) {
    return;
  }
  try {
    const role = await roleStore.fetchGatewayRole(id);
    if (role && currentRoute === router.currentRoute.value && !isGatewayNavigationPending(router)) {
      await gatewayStore.ensureGatewayDetail(id);
    }
  }
  catch (error) {
    // 角色错误由下面的 watcher 统一处理；这里仅补上详情失败，且不能影响新导航。
    if (roleStatus.value !== 'error' && currentRoute === router.currentRoute.value
      && !isGatewayNavigationPending(router)) {
      await router.replace(getGatewayErrorRoute(error, id, currentRoute.fullPath));
    }
  }
};

watch(
  [() => userStore.info.username, () => userStore.info.tenant_id],
  (_identity, previousIdentity) => {
    if (previousIdentity.length) {
      // 详情同样属于旧身份的上下文，不能在重新登录后继续命中缓存。
      gatewayStore.clearCurrentGateway();
    }
    // 复用守卫已加载/正在加载的结果，也不自动重试失败请求。
    if (roleStatus.value !== 'idle') {
      return;
    }
    void refreshCurrentGateway();
  },
  // 覆盖守卫完成后、布局挂载前发生身份变化的情况。
  { immediate: true },
);

// 兜底防线：覆盖停留在页面上时角色被变更（如成员管理中移除了自己的角色）的场景
watch(
  [
    currentRole,
    roleStatus,
    () => route.meta.permission,
    () => route.params.id,
  ],
  () => {
    if (
      !route.params.id
      || route.meta.skipRoleCheck
      || isGatewayNavigationPending(router)
      || !['ready', 'error'].includes(roleStatus.value)
    ) {
      return;
    }
    if (roleStatus.value === 'error') {
      router.replace(getGatewayErrorRoute(roleError.value, Number(route.params.id), route.fullPath));
      return;
    }
    if (!canAccess(route.meta.permission)) {
      router.replace({
        name: 'GatewayNotFound',
        params: { id: route.params.id },
      });
    }
  },
);

const getGatewayData = async () => {
  const response = await getGatewayList({ limit: 10000 });
  gatewayList.value = response.results || [];
};

// 获取权限审批的数量
const getPermissionData = async (id: number) => {
  const res = await getPermissionApplyList(
    id,
    {
      offset: 0,
      limit: 10,
    },
  );
  if (id === Number(route.params.id) && canAccess('permission')) {
    permissionStore.setCount(res.count);
  }
};

// 附加数据只能在目标网关角色就绪后查询，运营者不调用管理员的环境接口。
watch(
  [() => route.params.id, currentRole, roleStatus],
  () => {
    permissionStore.setCount(0);
    const id = Number(route.params.id);
    if (!Number.isSafeInteger(id) || id <= 0 || roleStatus.value !== 'ready') {
      return;
    }
    const requests: Promise<void>[] = [];
    if (canAccess('stage')) {
      requests.push(checkStageVersion(id));
    }
    if (canAccess('permission')) {
      requests.push(getPermissionData(id));
    }
    Promise.all(requests).catch(() => {
      // 附加数据失败不影响导航，错误由统一 HTTP 封装提示。
    });
  },
  { immediate: true },
);

const isMenuVisible = (menu: IMenu) => {
  if (!menu.enabled) {
    return false;
  }
  if (menu.hideInProgrammable && isProgrammableGateway.value) {
    return false;
  }
  return canAccessByRole(menuRole.value, menu.permission);
};

const handleCollapse = (collapsed: boolean) => {
  isMenuCollapsed.value = !collapsed;
};

const handleGoPage = async (routeName: string) => {
  const targetGatewayId = gatewayId.value;
  const gatewayData = gatewayList.value.find(item => item.id === targetGatewayId);
  // 网关类型也会影响菜单可用性；不可用的菜单使用既有落点或基本信息。
  let nextRouteName = routeName;
  if (routeName === 'ResourceSetting' && gatewayData?.kind === 1) {
    nextRouteName = 'StageOverview';
  }
  if ((routeName === 'ModelService' && gatewayData?.kind !== 2)
    || ['GatewayNotFound', 'GatewayLoadError'].includes(routeName)) {
    nextRouteName = 'BasicInfo';
  }
  // 不能用当前网关角色判断目标网关权限；先保留菜单，再由守卫查询目标角色并决定是否回退。
  if (targetGatewayId !== Number(route.params.id)) {
    try {
      await router.push({
        name: nextRouteName,
        params: { id: targetGatewayId },
      });
    }
    finally {
      // 导航可能被取消，选择器始终跟随实际生效的路由；不提前修改全局 apigwId。
      gatewayId.value = Number(route.params.id);
    }
    return;
  }
  // 刷新期间仍可选择菜单；保留点击目标，由守卫等待角色结果，避免用暂时为空的角色误回退。
  await router.push({
    name: nextRouteName,
    params: { id: gatewayId.value },
  });
};

const handleCreateGateway = () => {
  const routeData = router.resolve({ name: 'CreateGateway' });
  window.open(routeData.href, '_blank');
};

const handleBack = () => {
  router.back();
};

onMounted(() => {
  getGatewayData();
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
        flex-basis: 52px;
        border-bottom: 1px solid #dcdee5;
        box-shadow: 0 3px 4px 0 #0000000a;
        box-sizing: border-box;

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

:deep(.gateway-select) {
  width: 224px;
  height: 32px;
  border: 1px solid transparent;
  border-radius: 2px;
  box-sizing: border-box;

  .bk-select-trigger {
    display: flex;
    height: 100%;
  }

  .bk-input {
    height: 100%;
    background-color: #f5f7fa;
    border: none;
    border-radius: 2px;
    box-shadow: none;
    box-sizing: border-box;

    .bk-input--text {
      font-size: 14px;
      color: #4d4f56;
      background-color: transparent;
      order: 1;
    }

    .gateway-selector-prefix {
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 2px;
    }

    &:hover {
      background-color: #eaebf0;
    }
  }

  &.is-focus {
    border-color: #699df4;
  }
}
</style>

<style lang="scss">
.bk-popover.bk-pop2-content.gateway-select-popover .bk-select-content-wrapper {

  .bk-select-option {

    &.is-hover {
      background-color: #f0f1f5;
    }

    &.is-selected {

      .icon-ag-wangguanleixing-wangguan {
        background-color: #a3c5fd;
        color: #1768ef;
      }
    }
  }

  .bk-select-extension {
    height: 48px;
  }
}

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
