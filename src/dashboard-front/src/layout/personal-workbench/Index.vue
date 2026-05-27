/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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
      navigation-type="left-right"
      :default-open="collapse"
      :class="{ 'custom-height-navigation': route.meta?.hideHeaderBorder }"
      @toggle="handleCollapse"
    >
      <template #menu>
        <BkMenu
          :collapse="collapse"
          :opened-keys="openedKeys"
          :active-key="activeMenuKey"
        >
          <BkMenuGroup
            v-for="menu of personalWorkbenchMenu"
            :key="menu.name"
            :fold-name="menu.name"
            :name="menu.title"
          >
            <template v-if="menu.enabled && menu.children?.length">
              <BkMenuItem
                v-for="subMenu of menu.children"
                :key="subMenu.name"
                @click.stop="() => handleGoPage(subMenu.name)"
              >
                <template #icon>
                  <AgIcon
                    :name="subMenu.icon || ''"
                    size="18"
                  />
                </template>
                {{ subMenu.title }}
                <BkBadge
                  v-if="['MyPending'].includes(subMenu.name) && isExistApplied"
                  dot
                  theme="danger"
                  :class="{ 'en': locale.indexOf('zh-cn') === -1 }"
                />
              </BkMenuItem>
            </template>
          </BkMenuGroup>
        </BkMenu>
      </template>

      <div class="content-view">
        <!-- 默认头部 -->
        <div
          v-if="!route.meta.customHeader"
          class="flex items-center border-none! content-header"
        >
          <AgIcon
            v-if="route.meta.showBackIcon"
            name="return-small"
            @click="handleBack"
          />
          {{ headerTitle }}
        </div>
        <div :class="routerViewWrapperClass">
          <RouterView />
        </div>
      </div>
    </BkNavigation>
  </div>
</template>

<script setup lang="ts">
import { locale, t } from '@/locales';
import { useFeatureFlag } from '@/stores';
import type { IMenu } from '@/types/common';
import { usePersonalWorkbench } from '@/hooks';
import AgIcon from '@/components/ag-icon/Index.vue';

const route = useRoute();
const router = useRouter();
const featureFlagStore = useFeatureFlag();
const {
  isExistApplied,
  getMyAppliedData,
} = usePersonalWorkbench();

const collapse = ref(true);
const activeMenuKey = ref('');
const headerTitle = ref('');

const personalWorkbenchMenu = computed<IMenu[]>(() => [
  {
    name: 'ApplicationDeveloper',
    title: t('应用开发者'),
    icon: '',
    enabled: true,
    children: [
      {
        name: 'MyApply',
        title: t('我的申请'),
        icon: 'wodeshenqing',
        enabled: true,
      },
    ],
  },
  {
    name: 'GatewayAdministrator',
    title: t('网关管理员'),
    icon: '',
    enabled: true,
    children: [
      {
        name: 'MyPending',
        title: t('我的待办'),
        icon: 'wodedaiban',
        enabled: true,
      },
      {
        name: 'MyHandled',
        title: t('我的已办'),
        icon: 'wodeyiban',
        enabled: true,
      },
    ],
  },
]);

const openedKeys = computed(() => personalWorkbenchMenu.value.map((menu: IMenu) => menu.name));
const isShowNoticeAlert = computed(() => featureFlagStore.isEnabledNotice);
const routerViewWrapperClass = computed(() => {
  const initClass = 'default-header-view';
  if (route.meta.customHeader) {
    return 'custom-header-view';
  }
  if (isShowNoticeAlert.value) {
    return `${initClass} show-notice`;
  }
  return `${initClass}`;
});

const handleCollapse = (value: boolean) => {
  collapse.value = !value;
};

const handleGoPage = (routeName: string) => {
  router.push({ name: routeName });
};

const handleBack = () => {
  router.back();
};

getMyAppliedData();

watch(
  () => route.meta,
  (meta: typeof route.meta) => {
    activeMenuKey.value = meta.matchRoute as string;
    headerTitle.value = meta.title as string;
    getMyAppliedData();
  },
  {
    immediate: true,
    deep: true,
  },
);
</script>

<style lang="scss" scoped>
.navigation-main {
  height: calc(100vh - 52px);

  :deep(.navigation-nav) {

    .nav-slider {
      background-color: #ffffff;
      border-right: 1px solid #dcdee5 !important;

      .bk-navigation-title {
        display: none !important;
      }

      .nav-slider-list {
        padding-top: 4px;
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
      background-color: #ffffff !important;

      .bk-menu-group {

        .group-name {
          margin: 0 22px;
          color: #7f889b;
        }

        .bk-menu-item {
          margin: 0;
          color: rgb(99 101 110);

          .item-icon {

            .default-icon {
              background-color: rgb(197 199 205);
            }
          }

          .item-content {
            position: relative;

            .bk-badge-main {
              position: absolute;
              top: 8px;
              left: 60px;

              &.en {
                left: 84px;
              }
            }
          }

          &:hover {
            background-color: #f0f1f5;
          }

          &.is-active {
            color: rgb(58 132 255);
            background: rgb(225 236 255);

            .item-icon {

              .default-icon {
                background-color: rgb(58 132 255);
              }
            }
          }
        }
      }
    }

    .bk-menu-submenu.is-opened {
      background-color: #ffffff !important;
    }
  }

  :deep(.navigation-container) {

    .container-header {
      height: 0 !important;
      flex-basis: 0 !important;
    }
  }

  .navigation-main-content {
    border: 1px solid #dddddd;

    .content-view {
      height: 100%;
      overflow: hidden;
      font-size: 14px;

      .content-header {
        display: flex;
        height: 51px;
        padding: 0 24px;
        margin-right: auto;
        font-size: 16px;
        color: #313238;
        background-color: #ffffff;
        border-bottom: 1px solid #dcdee5;
        box-shadow: 0 3px 4px rgb(64 112 203 / 5.88%);
        align-items: center;
        flex-basis: 51px;

        .icon-ag-return-small {
          font-size: 32px;
          color: #3a84ff;
          cursor: pointer;
        }
      }

      .default-header-view {
        height: calc(100vh - 105px);
        overflow: auto;
        scrollbar-gutter: stable;

        &.custom-header-view {
          height: 100%;
          margin-top: 52px;
          overflow: auto;
        }

        &.show-notice {
          height: calc(100vh - 145px);
        }
      }
    }
  }
}
</style>
