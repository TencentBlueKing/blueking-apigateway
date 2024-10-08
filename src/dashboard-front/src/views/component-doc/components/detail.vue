<template>
  <div class="ag-container">
    <div class="left">
      <div class="simple-side-nav">
        <div class="metedata" style="height: 65px;">
          <strong class="name">{{ curSystem.description || '--' }}</strong>
          <p class="desc">{{ curSystem.name }}</p>
          <i
            class="more ag-doc-icon doc-menu apigateway-icon icon-ag-menu" v-bk-tooltips.top="t('所有系统')"
            @click="handleTogglePanel"></i>
          <div
            :class="`version-logo ${curVersion}`"
            :style="{ backgroundImage: `url(${versionLogoMap[curVersionIndex % 4].logo})` }">
            <em :style="{ backgroundColor: `${versionLogoMap[curVersionIndex % 4].color}` }">
              <span style="transform: scale(0.8); display: inline-block;">{{ curBoardLabel }}</span>
            </em>
          </div>
        </div>
        <div class="component-list-box">
          <p :class="['span', { 'active': routeName === 'ComponentAPIDetailIntro' }]" @click="handleShowIntro">
            {{ t('简介') }} </p>
          <div class="list-data">
            {{ t('API 列表') }}
            <span class="ag-badge">{{ curComponentList.length }}</span>
          </div>
          <div class="search">
            <bk-input
              :placeholder="$t('请输入API名称')" right-icon="bk-icon icon-search" clearable
              v-model="keyword"></bk-input>
          </div>
          <ul class="component-list" v-if="curComponentList.length">
            <li
              :class="{ 'active': curComponentName === component.name }" v-for="component of curComponentList"
              :key="component.id" @click="handleShowDoc(component)">
              <!-- eslint-disable-next-line vue/no-v-html -->
              <p class="name" v-dompurify-html="hightlight(component.name, 'api')"></p>
              <!-- eslint-disable-next-line vue/no-v-html -->
              <p class="label" v-dompurify-html="hightlight(component.description, 'api')"></p>
            </li>
          </ul>
          <template v-else-if="keyword">
            <TableEmpty :keyword="keyword" @clear-filter="keyword = ''" />
          </template>
        </div>
      </div>

      <!-- eslint-disable-next-line vue/valid-v-on -->
      <div
        class="nav-panel" ref="panel" v-if="isNavPanelShow"
        v-clickOutSide="handleTogglePanel">
        <div class="version-panel">
          <bk-dropdown ref="dropdown" :popover-options="popoverOptions" class="m16">
            <div class="version-name">
              <svg aria-hidden="true" class="category-icon vm">
                <use :xlink:href="`#doc-icon${curVersionData.logoIndex % 4}`"></use>
              </svg>
              <strong class="vm">{{ curVersionData.board_label }}</strong>
              <i class="ag-doc-icon doc-down-shape f12 apigateway-icon icon-ag-down-shape"></i>
            </div>
            <template #content>
              <bk-dropdown-menu class="bk-dropdown-list w250">
                <bk-dropdown-item v-for="component in componentList" :key="component.board">
                  <a href="javascript:;" @click="handleSwitchVersion(component)">{{ component.board_label }}</a>
                </bk-dropdown-item>
              </bk-dropdown-menu>
            </template>
          </bk-dropdown>

          <bk-input
            class="searcher" :placeholder="t('请输入系统名称')" clearable v-model="panelKeyword"
            @clear="handleClear"></bk-input>
          <div class="panel-container">
            <template v-if="filterData.categories.length">
              <div class="ag-card" v-for="(category, index) of filterData.categories" :key="index">
                <p class="card-title" :id="`${curVersionData.board_label}_${category.name}`">
                  {{ category.name }}
                  <span class="total">({{ category.systems.length }})</span>
                </p>
                <div class="card-content">
                  <ul class="systems">
                    <li v-for="item of category.systems" :key="item.name">
                      <router-link
                        :to="{
                          name: 'ComponentAPIDetailIntro',
                          params: { version: curVersionData.board, id: item.name }
                        }">
                        <!-- eslint-disable-next-line vue/no-v-html -->
                        <span
                          v-dompurify-html="hightlight(item.description, 'panel')"
                          @click="isNavPanelShow = false"
                        ></span>
                      </router-link>
                      <p class="desc">
                        <!-- eslint-disable-next-line vue/no-v-html -->
                        <span v-dompurify-html="hightlight(item.name, 'panel')"></span>
                      </p>
                    </li>
                  </ul>
                </div>
              </div>
            </template>
            <template v-else-if="panelKeyword">
              <TableEmpty :keyword="panelKeyword" @clear-filter="handleClear" />
            </template>
          </div>
        </div>
      </div>
    </div>

    <div class="right">
      <bk-loading :loading="mainContentLoading">
        <router-view :key="route.path"></router-view>
      </bk-loading>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';
import {
  getComponentSystemList,
  getComponenSystemDetail,
  getSystemAPIList,
} from '@/http';
import logo1 from '@/images/1.svg';
import logo2 from '@/images/2.svg';
import logo3 from '@/images/3.svg';
import logo4 from '@/images/4.svg';
import TableEmpty from '@/components/table-empty.vue';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();

const curVersion = ref<string>('default');
const curSystemName = ref<string>('');
const curBoardLabel = ref<string>('');
const keyword = ref<string>('');
const curComponentName = ref<string>('');
const panelKeyword = ref<string>('');
const componentList = ref([]);
const originComponentList = ref([]);
const isNavPanelShow = ref<boolean>(false);
const mainContentLoading = ref<boolean>(false);
const toggleTimer = ref(null);
const clearTimer = ref(null);
const dropdown = ref(null);
const panel = ref(null);
const curComponent = ref({
  id: '',
  content: '',
  innerHtml: '',
  markdownHtml: '',
  name: '',
});
const curSystem = ref({
  name: '',
  label: '',
  description: '',
});
const curVersionData = ref<any>({
  board: '',
  board_label: '',
  categories: [],
});

const popoverOptions = {
  boundary: 'body',
};

const routeName = computed(() => {
  return route.name;
});
const versionLogoMap = computed(() => {
  return [
    {
      logo: logo1,
      color: '#3b83ff',
    },
    {
      logo: logo3,
      color: '#ff9700',
    },
    {
      logo: logo2,
      color: '#3babfe',
    },
    {
      logo: logo4,
      color: '#2dca56',
    },
  ];
});
const curVersionIndex = computed(() => {
  const match = componentList.value.find(item => item.board === curVersion.value);
  return match ? match.logoIndex : 0;
});
// 搜索后的API List
const curComponentList = computed(() => {
  return originComponentList.value.filter((item) => {
    return item.name.indexOf(keyword.value) > -1 || item.description.indexOf(keyword.value) > -1;
  });
});
const filterData = computed(() => {
  const data = {
    board: '',
    board_label: '',
    categories: [] as any,
  };
  curVersionData.value.categories.forEach((category: any) => {
    const list: any = [];
    const obj = { ...category };
    const keyword = panelKeyword.value.toLowerCase();
    category.systems.forEach((system: any) => {
      if (system.description.toLowerCase().indexOf(keyword) > -1 || system.name.toLowerCase().indexOf(keyword) > -1) {
        list.push(system);
      }
    });

    if (list.length) {
      obj.systems = list;
      data.categories.push(obj);
    }
  });
  return data;
});


// 获取组件系统列表
const getComponentList = async () => {
  try {
    const res = await getComponentSystemList(curVersion.value);
    componentList.value = res;
    componentList.value.forEach((item: any, index: number) => {
      item.logoIndex = index;
    });
    if (componentList.value.length) {
      const match = componentList.value.find(item => item.board === curVersion.value);
      curVersionData.value = match || componentList.value[0];
      curBoardLabel.value = curVersionData.value.board_label;
    }
  } catch (error) {
    console.log('error', error);
  }
};
// 获取APIlist
const getAPIList = async () => {
  try {
    const res = await getSystemAPIList(curVersion.value, curSystemName.value);
    originComponentList.value = res;
  } catch (error) {
    console.log('error', error);
  }
};
// 获取当前system 的信息
const getSystemDetail = async () => {
  try {
    const res = await getComponenSystemDetail(curVersion.value, curSystemName.value);
    curSystem.value = res;
  } catch (error) {
    console.log('error', error);
  }
};

const handleClear = () => {
  clearTimeout(clearTimer.value);
  clearTimer.value = setTimeout(() => {
    panelKeyword.value = '';
    isNavPanelShow.value = true;
  }, 1);
};
const handleTogglePanel = () => {
  clearTimeout(toggleTimer.value);
  toggleTimer.value = setTimeout(() => {
    isNavPanelShow.value = !isNavPanelShow.value;
  }, 0);
};
const handleShowIntro = () => {
  curComponentName.value = '';
  router.push({
    name: 'ComponentAPIDetailIntro',
  });
};
const handleShowDoc = (component: any) => {
  curComponent.value = component;
  curComponentName.value = curComponent.value.name;
  router.push({
    name: 'componentAPIDetailDoc',
    params: {
      componentId: component.name,
    },
  });
};
const handleSwitchVersion = (component: any) => {
  curVersionData.value = component;
  dropdown.value.hide();
};

// 高亮
const hightlight = (value: any, type: string) => {
  const curKeyword = type === 'panel' ? panelKeyword.value : keyword.value;
  if (curKeyword) {
    return value.replace(new RegExp(`(${curKeyword})`), '<em class="ag-keyword">$1</em>');
  }
  return value;
};


const init = () => {
  const routeParams: any = route.params;
  curVersion.value = routeParams.version;
  curSystemName.value = routeParams.id;
  curComponentName.value = routeParams.componentId;
  mainContentLoading.value = true;
  getSystemDetail();
  getComponentList();
  getAPIList();
  mainContentLoading.value = false;
  // 回到页头
  const container = document.documentElement || document.body;
  container.scrollTo({
    top: 0,
    behavior: 'smooth',
  });
};
// 监听route变化
watch(
  () => route,
  (v: any) => {
    if (!v.params.id) {
      return;
    }
    isNavPanelShow.value = false;
    init();
  },
  { deep: true },
);
init();
</script>

<style lang="scss" scoped>
.m16 {
  margin: 16px;
}

.w250 {
  width: 250px;
}

:deep(.container-content) {
  :deep(.content) {
    height: auto !important;
  }
}

.bk-dropdown-popover {
  .bk-dropdown-content {
    .bk-dropdown-list {
      width: 250px;

      .bk-dropdown-item {
        a {
          display: block;
          height: 32px;
          line-height: 33px;
          padding: 0 16px;
          color: #63656e;

          &:hover {
            color: #3a84ff;
          }
        }
      }
    }
  }
}

.ag-container {
  width: 1200px;
  display: flex;
  margin: 16px auto 20px auto;
  align-items: stretch;

  >.left {
    width: 260px;
    margin-right: 16px;
    position: relative;
  }

  >.right {
    flex: 1;
    height: auto;

    >div {
      height: 100%;
    }

    .intro-doc,
    .component-doc {
      height: 100%;
    }

    .version-name {
      font-size: 16px;
      font-weight: 700;
      text-align: left;
      color: #313238;
      line-height: 21px;
      padding: 10px 0 15px 0;

      svg {
        width: 20px;
        height: 20px;
        vertical-align: middle;
        margin-right: 3px;
      }

      span {
        vertical-align: middle;
      }
    }
  }

  .ag-kv-box {
    .kv-row {
      font-size: 14px;
      line-height: 30px;
      display: flex;

      .k {
        width: 175px;
        text-align: left;
        color: #979BA5;
      }

      .v {
        color: #313238;
      }
    }
  }
}

.simple-side-nav {
  width: 260px;
  height: 100%;
  background: #FFF;
  box-shadow: 0px 2px 6px 0px rgba(0, 0, 0, 0.1);
  border-radius: 2px;
  /* padding-bottom: 30px; */

  .metedata {
    padding: 11px 16px;
    position: relative;
    border-bottom: 1px solid #DCDEE5;

    .name {
      font-size: 16px;
      text-align: left;
      color: #313238;
    }

    .desc {
      font-size: 12px;
      color: #c4c6cc;
    }

    .more {
      position: absolute;
      font-size: 26px;
      right: 10px;
      top: 18px;
      cursor: pointer;
    }

    .version-logo {
      position: absolute;
      left: -8px;
      top: -8px;
      height: 26px;
      background-repeat: no-repeat;
      background-position: left top;

      img {
        height: 26px;
      }

      em {
        position: relative;
        line-height: 18px;
        font-size: 10px;
        font-style: normal;
        color: #FFF;
        /* background: #3b83ff; */
        display: block;
        padding: 0px 8px;
        border-radius: 0 3px 3px 0;
        min-width: 44px;
      }
    }
  }

  .component-list-box {
    .span {
      height: 42px;
      line-height: 42px;
      margin: 7px 0;
      padding: 0 21px;
      display: block;
      font-size: 14px;
      text-align: left;
      color: #63656e;
      overflow: hidden;
      cursor: pointer;

      &.active {
        background: #E1ECFF;
        color: #3A84FF;
      }
    }

    .list-data {
      height: 40px;
      line-height: 40px;
      font-size: 14px;
      color: #63656E;
      padding: 0 16px;
      position: relative;
      border-top: 1px solid #F0F1F5;
    }

    .search {
      margin: 0 16px 15px 16px;
    }

    .component-list {
      max-height: calc(100vh - 400px);
      overflow: auto;

      &::-webkit-scrollbar {
        width: 4px;
        background-color: lighten(#C4C6CC, 80%);
      }

      &::-webkit-scrollbar-thumb {
        height: 5px;
        border-radius: 2px;
        background-color: #C4C6CC;
      }

      >li {
        height: 42px;
        padding: 0 16px;
        cursor: pointer;
        margin-bottom: 15px;
        overflow: hidden;

        &:hover,
        &.active {
          background-color: #e1ecff;

          .name {
            color: #3A84FF;
          }
        }
      }

      .name {
        font-size: 14px;
        text-align: left;
        color: #63656e;
        line-height: 18px;
        margin: 2px 0;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
      }

      .label {
        font-size: 12px;
        text-align: left;
        color: #979BA5;
        line-height: 18px;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
      }
    }
  }
}


.support-btn {
  position: absolute;
  font-size: 12px;
  color: #3A84FF;
  top: 60px;
  right: 26px;
}

.ag-badge {
  min-width: 30px;
  height: 18px;
  background: #f0f1f5;
  border-radius: 2px;
  font-size: 12px;
  text-align: left;
  color: #979ba5;
  display: inline-block;
  line-height: 18px;
  text-align: center;
  padding: 0 5px;
  position: absolute;
  right: 16px;
  top: 11px;
}


.nav-panel {
  height: 500px;
  position: absolute;
  left: 262px;
  top: 0;
  overflow: auto;
  z-index: 100;
  background: #FFF;
  width: 870px;
  max-height: 640px;
  background: #ffffff;
  border: 1px solid #dcdee5;
  box-shadow: 0px 2px 6px 0px rgba(0, 0, 0, 0.1);

  .panel-container {
    max-height: 420px;
    overflow: auto;
  }

  .category-icon {
    width: 20px;
    height: 20px;
  }

  .version-name {
    line-height: 32px;
    height: 32px;
    padding: 0 10px;

    &:hover {
      min-width: 140px;
      background: #f0f1f5;
      border-radius: 2px;
    }

    >strong {
      font-size: 16px;
      color: #313238;
      font-weight: normal;
    }
  }

  .searcher {
    width: 400px;
    position: absolute;
    right: 16px;
    top: 16px;
  }

  .ag-card {
    box-shadow: none;
    margin-top: 0 !important;
    padding: 18px 30px 10px 30px;

    .card-title {
      font-size: 14px;
      font-weight: 700;
      text-align: left;
      color: #63656e;
      line-height: 19px;

      .total {
        font-size: 14px;
        color: #979ba5;
        font-weight: normal;
      }
    }

    .card-content {
      margin-top: 20px;
    }

    .systems {
      display: flex;
      flex-wrap: wrap;

      >li {
        width: 25%;
        margin-bottom: 20px;
      }

      a {
        font-size: 14px;
        display: block;
        margin-bottom: 4px;
        color: #63656e;

        &:hover {
          color: #3a84ff;
        }
      }

      .desc {
        font-size: 12px;
        color: #C4C6CC;
      }
    }
  }
}

.wrapper {
  margin-top: 10px;
  padding: 10px 5px;
  background: #fafbfd;
}


.column-key {
  font-size: 14px;
  color: #63656E;
  line-height: 22px;
}

.column-value {
  font-size: 14px;
  color: #313238;
  line-height: 22px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  max-width: 90%;
  display: inline-block;
}

.ag-doc-icon {
  font-size: 16px;
  color: #979BA5;
  cursor: pointer;
  margin-right: 5px;

  &:hover {
    color: #3A84FF;
  }
}

.select-custom {
  margin-bottom: 10px !important;
  border: none !important;
  border-bottom: 1px solid #F0F1F5 !important;

  &.bk-select.is-focus {
    box-shadow: none;
  }

  :deep(.bk-select-name) {
    font-weight: bold;
    color: #63656E;
    font-size: 14px;
    padding-left: 0;
  }
}

.version-panel {
  margin-bottom: 20px;

  &:last-child {
    margin-bottom: 0;
  }
}
</style>
