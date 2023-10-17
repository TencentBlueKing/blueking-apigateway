<template>
  <div class="navigation-main">
    <bk-navigation
      class="navigation-main-content"
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
            v-for="menu in menuData"
            :key="menu.name"
            :title="menu.title"
          >
            <bk-menu-item v-for="child in menu.children" :key="child.name" @click="handleGoPage(child.name)">
              {{ child.title }}
            </bk-menu-item>
          </bk-submenu>
        </bk-menu>
      </template>
      <template #side-header>
        <bk-select class="header-select" v-model="apigwId" @change="handleGoPage(activeMenuKey)">
          <bk-option
            v-for="item in gatewaysList" :key="item.id" :id="item.id" :name="item.name"
          />
        </bk-select>
      </template>
      <div class="content-view">
        <router-view></router-view>
      </div>
      <template #header>
        <!-- 环境概览 -->
        <stage-top-bar v-if="route.meta.isCustomTopbar === 'stageOverview'" />
        <div
          v-else
          class="header"
        >
          {{ headerTitle }}
        </div>
      </template>
    </bk-navigation>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { menuData } from '@/common/menu';
import { useGetApiList } from '@/hooks';
import { useCommon } from '@/store';
import stageTopBar from '@/components/stage-top-bar.vue';

const route = useRoute();
const router = useRouter();
// 全局公共字段存储
const common = useCommon();
// 获取网关数据方法
const {
  getGatewaysListData,
} = useGetApiList();
const collapse = ref(true);
// 选中的菜单
const activeMenuKey = ref('');
const gatewaysList = ref<any>([]);
const openedKeys = menuData.map(e => e.name);

// 当前网关Id
const apigwId = ref(0);

// 页面header名
const headerTitle = ref('');
const handleCollapse = (v: boolean) => {
  collapse.value = !v;
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
  },
  { immediate: true, deep: true },
);

onMounted(async () => {
  gatewaysList.value = await getGatewaysListData();
});

const handleGoPage = (routeName: string) => {
  router.push({
    name: routeName,
    params: {
      id: apigwId.value,
    },
  });
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
          .item-icon{
            .default-icon{
              background-color: rgb(197, 199, 205);
            }
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
      .submenu-header-content{
        color: rgb(99, 101, 110);
      }
      .bk-menu-submenu.is-opened {
        background: #fff !important;
      }
    }

    :deep(.navigation-container) {
      .container-header{
      }
    }

  &-content {
    border: 1px solid #ddd;

    .content-view {
      font-size: 24px;
    }

    .header {
      margin-right: auto;
      color: #313238;
      font-size: 16px;
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
