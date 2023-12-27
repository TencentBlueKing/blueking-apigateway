<template>
  <div class="navigation-main">
    <bk-navigation
      :class="['navigation-main-content', route.name === 'apigwResourceVersion' ? 'custom-height-navigation' : '']"
      :default-open="collapse"
      navigation-type="left-right"
      @toggle="handleCollapse"
    >
      <template #menu>
        <bk-menu
          :collapse="collapse"
          :opened-keys="openedKeys"
          :active-key="activeMenuKey"
        >
          <bk-submenu
            v-for="menu in subMenuList"
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
            <bk-menu-item
              v-for="child in menu.children" :key="child.name" @click="handleGoPage(child.name, apigwId)">
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
          </bk-submenu>
          <bk-menu-item
            v-for="menuItem in menuList" :key="menuItem.name"
            @click="handleGoPage(menuItem.name, apigwId)">
            <template #icon>
              <i :class="['icon apigateway-icon', `icon-ag-${menuItem.icon}`]"></i>
            </template>
            {{ menuItem.title }}
          </bk-menu-item>
        </bk-menu>
      </template>
      <template #side-header>
        <bk-select
          class="header-select" filterable
          v-model="apigwId"
          @change="handleGoPage(activeMenuKey, apigwId)"
          :clearable="false">
          <bk-option
            v-for="item in gatewaysList" :key="item.id" :id="item.id" :name="item.name"
          />
        </bk-select>
      </template>
      <div class="content-view">
        <!-- 默认头部 -->
        <div class="flex-row align-items-center content-header" v-if="!route.meta.customHeader">
          <i
            class="icon apigateway-icon icon-ag-return-small"
            v-if="route.meta.showBackIcon"
            @click="handleBack"></i>
          {{ headerTitle }}
        </div>
        <div :class="route.meta.customHeader ? 'custom-header-view' : 'default-header-view'">
          <router-view
            :key="apigwId" :apigw-id="apigwId">
          </router-view>
        </div>
      </div>
    </bk-navigation>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { menuData } from '@/common/menu';
import { useGetApiList } from '@/hooks';
import { useCommon, usePermission } from '@/store';
import { getPermissionApplyList, getGatewaysDetail } from '@/http';

const route = useRoute();
const router = useRouter();
// 全局公共字段存储
const common = useCommon();
const permission = usePermission();
const filterData = ref({ name: '' });
// 获取网关数据方法
const {
  getGatewaysListData,
} = useGetApiList(filterData);
const collapse = ref(true);
// 选中的菜单
const activeMenuKey = ref('');
const gatewaysList = ref<any>([]);
const openedKeys = menuData.map(e => e.name);

// 区分是否有子菜单
const subMenuList = computed(() => menuData.filter(e => e.children?.length));
const menuList = computed(() => menuData.filter(e => !e.children?.length));

// 当前网关Id
const apigwId = ref(0);

// 页面header名
const headerTitle = ref('');
const handleCollapse = (v: boolean) => {
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

// 监听当前路由
watch(
  () => route,
  (val: any) => {
    activeMenuKey.value = val.meta.matchRoute;
    apigwId.value = Number(val.params.id);
    headerTitle.value = val.meta.title;
    // 设置全局网关id
    common.setApigwId(apigwId.value);
    // 设置全局网关名称
    handleSetApigwName();
    // 设置当前网关详情
    handleSetApigwDeatail();
  },
  { immediate: true, deep: true },
);

// 获取权限审批的数量
const getPermiList = async () => {
  try {
    const res = await getPermissionApplyList(apigwId.value, { offset: 0, limit: 10 });
    permission.setCount(res.count);
  } catch (error) {
    console.log('error', error);
  }
};

onMounted(async () => {
  gatewaysList.value = await getGatewaysListData();
  // 初始化设置一次
  handleSetApigwName();
  getPermiList();
});

const handleGoPage = (routeName: string, apigwId?: number) => {
  common.setApigwId(apigwId);
  router.push({
    name: routeName,
    params: {
      id: apigwId,
    },
  });
  getPermiList();
};

const handleBack = () => {
  router.back();
};
</script>
<style lang="scss" scoped>
.navigation-main {
  height: calc(100vh - 52px);
  &-radio {
    margin: 10px 0 20px 0;
  }

  :deep(.navigation-nav) {
      .nav-slider{
        background: #fff !important;
        .bk-navigation-title{
          flex-basis: 51px !important;
        }
        .nav-slider-list{
          border-top: 1px solid #f0f1f5;
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
      .bk-menu-submenu.is-opened {
        background: #fff !important;
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
        flex-basis: 51px;
        padding: 0 24px;
        background: #fff;
        border-bottom: 1px solid #dcdee5;
        box-shadow: 0 3px 4px rgba(64,112,203,0.05882);
        height: 51px;
        margin-right: auto;
        color: #313238;
        font-size: 16px;
        .icon-ag-return-small{
          font-size: 32px;
          color: #3a84ff;
          cursor: pointer;
        }
      }
      .default-header-view{
        height: calc(100vh - 105px);
        overflow: auto;
      }
      .custom-header-view{
        margin-top: 52px;
        height: 100%;
        overflow: auto;
      }
    }
  }
  :deep(.header-select){
      width: 240px;
      .bk-input--text{
        background: rgb(245, 247, 250);
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
</style>
