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
          <template
            v-for="menu in platformToolsMenu"
            :key="menu.name"
          >
            <BkMenuItem @click="() => handleGoPage(menu.name)">
              <template #icon>
                <AgIcon
                  :name="menu.icon"
                  size="18"
                />
              </template>
              {{ menu.title }}
            </BkMenuItem>
          </template>
        </BkMenu>
      </template>

      <div class="content-view">
        <!-- 默认头部 -->
        <div
          v-if="!route.meta.customHeader"
          class="flex items-center content-header"
        >
          <AgIcon
            v-if="route.meta.showBackIcon"
            name="return-small"
            @click="handleBack"
          />
          {{ headerTitle }}
        </div>
        <div :class="route.meta.customHeader ? 'custom-header-view' : 'default-header-view'">
          <RouterView />
        </div>
      </div>
    </BkNavigation>
  </div>
</template>

<script setup lang="ts">
import AgIcon from '@/components/ag-icon/Index.vue';

interface IMenu {
  name: string
  title: string
  icon?: string
  enabled?: boolean
  children?: IMenu[]
  // 是否在可编程网关中隐藏，默认 false
  hideInProgrammable?: boolean
}

const route = useRoute();
const router = useRouter();
const { t } = useI18n();

const collapse = ref(true);
const activeMenuKey = ref('');
const platformToolsMenu: IMenu[] = [
  {
    name: 'PlatformToolsToolbox',
    title: t('工具箱'),
    icon: 'gongjuxiang',
  },
  {
    name: 'PlatformToolsAutomatedGateway',
    title: t('自动化接入网关'),
    icon: 'zidongjieru',
  },
  {
    name: 'PlatformToolsProgrammableGateway',
    title: t('可编程网关'),
    icon: 'square-program',
  },
];
const openedKeys = platformToolsMenu.map(e => e.name);
// 页面header名
const headerTitle = ref('');

// 监听当前路由
watch(
  () => route.meta,
  (meta) => {
    activeMenuKey.value = meta.matchRoute as string;
    headerTitle.value = meta.title as string;
  },
  {
    immediate: true,
    deep: true,
  },
);

const handleCollapse = (value: boolean) => {
  collapse.value = !value;
};

const handleGoPage = (routeName: string) => {
  router.push({ name: routeName });
};

const handleBack = () => {
  router.back();
};
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
        display: none !important;
      }

      .nav-slider-list {
        border-top: 1px solid #f0f1f5;
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

    .bk-menu-submenu.is-opened {
      background: #fff !important;
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
        height: 51px;
        padding: 0 24px;
        margin-right: auto;
        font-size: 16px;
        color: #313238;
        background: #fff;
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
      }

      .custom-header-view {
        height: 100%;
        margin-top: 52px;
        overflow: auto;
      }
    }
  }

  :deep(.header-select) {
    width: 240px;

    .bk-input--text {
      background: rgb(245 247 250);
    }
  }
}
</style>
