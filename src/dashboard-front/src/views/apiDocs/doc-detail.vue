<template>
  <!--  文档详情页  -->
  <div class="page-wrap">
    <!-- 顶部带返回按钮和系统切换器的通栏 -->
    <header class="page-header">
      <main class="flex-row align-items-center header-main">
        <!--  返回按钮  -->
        <i
          class="icon apigateway-icon icon-ag-return-small"
          @click="handleGoBack()"
        ></i>
        {{ curTab === 'apigw' ? curTargetName : curTargetBasics?.description ?? '' }}
        <!--  组件系统下拉菜单  -->
        <aside v-if="curTab === 'component'" class="system-dropdown-wrap">
          <bk-dropdown ref="dropdown" :popover-options="{ boundary: 'body', placement: 'bottom-start' }">
            <div class="dropdown-trigger-btn">
              <span>{{ curTargetName }}</span>
              <i class="ag-doc-icon doc-down-shape apigateway-icon icon-ag-down-shape"></i>
            </div>
            <template #content>
              <bk-dropdown-menu class="dropdown-trigger-content bk-dropdown-list">
                <bk-dropdown-item
                  v-for="system in allSystemList"
                  :key="system.name"
                  :title="system.description"
                  @click="handleSystemChange(system)"
                >
                  <span class="f14">
                    <span class="ag-strong fw-normal mr5">{{ system.description }}</span>
                    ({{ system.name }})
                  </span>
                </bk-dropdown-item>
              </bk-dropdown-menu>
            </template>
          </bk-dropdown>
        </aside>
      </main>
    </header>
    <!--  正文  -->
    <main class="page-content">
      <bk-resize-layout
        ref="outerResizeLayoutRef"
        placement="right"
        :border="false"
        collapsible
        initial-divide="392px"
        :max="480"
        :min="293"
        style="flex-grow: 1;"
      >
        <template #main>
          <bk-resize-layout
            placement="left"
            style="margin-left: 40px;"
            initial-divide="288px"
            :max="400"
            :min="288"
            :border="false"
          >
            <!--  左栏，API 列表  -->
            <template #aside>
              <div class="left">
                <div class="left-aside-wrap">
                  <!--  筛选器  -->
                  <header class="left-aside-header">
                    <header class="title">
                      {{ curTab === 'apigw' ? t('资源列表') : t('API列表') }}
                      <aside v-if="apiList.length" class="sub-title">{{ filteredApiList.length }}</aside>
                    </header>
                    <main class="nav-filters">
                      <article v-if="curTab === 'apigw'">
                        <bk-select
                          v-model="curStageName"
                          :clearable="false"
                          filterable
                          :input-search="false"
                          :prefix="t('环境')"
                          @change="handleStageChange"
                        >
                          <bk-option
                            v-for="option in stageList"
                            :key="option.id"
                            :value="option.name"
                            :label="option.name"
                          >
                          </bk-option>
                        </bk-select>
                      </article>
                      <article>
                        <bk-input
                          type="search"
                          v-model="keyword"
                          :placeholder="searchPlaceholder"
                          clearable
                        >
                        </bk-input>
                      </article>
                    </main>
                  </header>
                  <!--  API 列表  -->
                  <main class="resource-list custom-scroll-bar">
                    <template v-if="filteredApiList.length">
                      <bk-collapse class="api-group-collapse" v-model="activeGroupPanelNames">
                        <bk-collapse-panel v-for="group of apiGroupList" :key="group.id" :name="group.name">
                          <template #header>
                            <div class="api-group-collapse-header">
                              <angle-up-fill
                                class="menu-header-icon"
                                :class="{ fold: !activeGroupPanelNames.includes(group.name) }"
                              />
                              <div class="api-group-collapse-title">{{ group.name }}</div>
                            </div>
                          </template>
                          <template #content>
                            <article
                              class="resource-item"
                              v-for="api in group.apiList"
                              :key="api.id"
                              :class="{ active: api.id === curApi?.id }"
                              @click="handleApiClick(api.id)"
                            >
                              <header
                                class="res-item-name" v-dompurify-html="getHighlightedHtml(api.name)" v-bk-overflow-tips
                              ></header>
                              <main class="res-item-desc" v-dompurify-html="getHighlightedHtml(api.description)"></main>
                            </article>
                          </template>
                        </bk-collapse-panel>
                      </bk-collapse>
                    </template>
                    <template v-else-if="keyword">
                      <TableEmpty
                        :keyword="keyword"
                        @clear-filter="keyword = ''"
                      />
                    </template>
                  </main>
                </div>
              </div>
            </template>
            <!--  中间栏，当前 API 文档内容  -->
            <template #main>
              <div class="main-content-wrap">
                <DocDetailMainContent
                  :api="curApi"
                  :nav-list="navList"
                  :markdown-html="curApiMarkdownHtml"
                  :updated-time="updatedTime"
                  @show-sdk-instruction="isSdkInstructionSliderShow = true"
                  v-bkloading="{ loading: isLoading }"
                ></DocDetailMainContent>
              </div>
            </template>
          </bk-resize-layout>
        </template>
        <!--  右栏，网关/组件主要信息和SDK  -->
        <template #aside>
          <aside class="aside-right">
            <main class="apigw-desc-wrap custom-scroll-bar">
              <DocDetailSideContent
                :basics="curTargetBasics"
                :sdks="sdks"
              />
            </main>
          </aside>
        </template>
      </bk-resize-layout>
    </main>
    <!--  SDK使用说明 Slider  -->
    <SdkInstructionSlider v-model="isSdkInstructionSliderShow"></SdkInstructionSlider>
  </div>
</template>

<script lang="ts" setup>
import {
  computed,
  onBeforeMount,
  provide,
  ref,
  watch,
} from 'vue';
import { useI18n } from 'vue-i18n';
import {
  useRoute,
  useRouter,
} from 'vue-router';
import {
  getApigwResourceDocDocs,
  getApigwResourcesDocs,
  getApigwStagesDocs,
  getComponenSystemDetail,
  getComponentSystemList,
  getESBSDKDetail,
  getGatewaysDetailsDocs,
  getSystemAPIList,
  getSystemComponentDoc,
} from '@/http';
import {
  IApiGatewayBasics,
  IApiGatewaySdkDoc,
  IComponent,
  IComponentSdk,
  INavItem,
  IResource,
  IStage,
  IBoard,
  ISystemBasics,
  TabType,
  ISystem,
} from '@/views/apiDocs/types';
import MarkdownIt from 'markdown-it';
import { ResizeLayout } from 'bkui-vue';
import DocDetailMainContent from '@/views/apiDocs/components/doc-detail-main-content.vue';
import DocDetailSideContent from '@/views/apiDocs/components/doc-detail-side-content.vue';
import SdkInstructionSlider from '@/views/apiDocs/components/sdk-instruction-slider.vue';
import TableEmpty from '@/components/table-empty.vue';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import hljs from 'highlight.js';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const curTab = ref<TabType>('apigw');
const board = ref('default');
// 提供当前 tab 的值
// 注入时请使用：const curTab = inject<Ref<TabType>>('curTab');
provide('curTab', curTab);

const stageList = ref<IStage[]>([]);
const curStageName = ref('');

// 当前的网关或组件被命名为 target
const curTargetName = ref(''); // 当前文档所属的网关或组件名称
const curTargetBasics = ref<IApiGatewayBasics & ISystemBasics | null>(null); // 当前文档所属的target主要信息
const apiList = ref<(IResource & IComponent)[]>([]); // 当前target下的所有api
const curComponentApiName = ref(''); // 当前组件api名称，路由用
const curApi = ref<IResource & IComponent | null>(null); // 当前选中的 api
const curApiMarkdownHtml = ref('');
const updatedTime = ref<string | null>(null);
const sdks = ref<IApiGatewaySdkDoc[] & IComponentSdk[]>([]);
const isSdkInstructionSliderShow = ref(false);
const navList = ref<INavItem[]>([]);
const outerResizeLayoutRef = ref<InstanceType<typeof ResizeLayout> | null>(null);
const isLoading = ref(false);
const keyword = ref('');  // 筛选器输入框的搜索关键字
const activeGroupPanelNames = ref<string[]>([]);  // API分类 collapse 展开的 panel

const searchPlaceholder = computed(() => {
  return t(
    '在{resourceLength}个{type}中搜索...',
    {
      resourceLength: apiList.value.length,
      type: curTab.value === 'apigw' ? t('资源') : 'API',
    },
  );
});

const filteredApiList = computed(() => {
  const regex = new RegExp(keyword.value, 'i');
  return apiList.value.filter(api => regex.test(api.name) || regex.test(api.description));
});

// API 分类列表
const apiGroupList = computed(() => {
  return filteredApiList.value.reduce((groupList, api) => {
    const { id, name } = api.labels[0];
    const group = groupList.find(item => item.id === id);

    if (group) {
      group.apiList.push(api);
    } else {
      groupList.push({
        id,
        name,
        apiList: [api],
      });
    }
    return groupList;
  }, [] as { id: number, name: string, apiList: typeof apiList.value }[]);
});

// 分类列表变化时更新 collapse 展开状态
watch(apiGroupList, () => {
  activeGroupPanelNames.value = apiGroupList.value.map(item => item.name);
});

const allSystemList = computed(() => {
  const curBoard = boardList.value[0];
  const systems: ISystem[] = [];
  curBoard.categories.forEach(cat => cat.systems.forEach(system => systems.push(system)));
  return systems;
});

const fetchTargetBasics = async () => {
  try {
    if (curTab.value === 'apigw') {
      const { sdks: sdksResponse, ...restResponse } = await getGatewaysDetailsDocs(curTargetName.value);
      curTargetBasics.value = restResponse;
      sdks.value = sdksResponse;
    } else if (curTab.value === 'component') {
      curTargetBasics.value = await getComponenSystemDetail(board.value, curTargetName.value);
    }
  } catch {
    curTargetBasics.value = null;
  }
};

const fetchEsbSdks = async () => {
  if (curTab.value !== 'component') {
    return;
  }
  try {
    const response = await getESBSDKDetail(board.value, { language: 'python' });
    sdks.value = [{ language: 'python', ...response }];
  } catch {
    sdks.value = [];
  }
};

const fetchApigwStages = async () => {
  try {
    const query = {
      limit: 10000,
      offset: 0,
    };
    stageList.value = await getApigwStagesDocs(curTargetName.value, query);
    const prodStage = stageList.value.find(stage => stage.name === 'prod');
    curStageName.value = prodStage?.name || stageList.value[0]?.name || '';
  } catch {
    stageList.value = [];
  }
};

const fetchApiList = async () => {
  try {
    let res: (IResource & IComponent)[] = [];
    navList.value = [];
    if (curTab.value === 'apigw') {
      const query = {
        limit: 10000,
        offset: 0,
        stage_name: curStageName.value,
      };
      res = await getApigwResourcesDocs(curTargetName.value, query) as (IResource & IComponent)[];
    } else if (curTab.value === 'component') {
      res = await getSystemAPIList(board.value, curTargetName.value) as (IResource & IComponent)[];
    }
    apiList.value = res ?? [];
    // 为 api 添加默认分类
    apiList.value.forEach((api) => {
      if (!api.labels?.length) {
        api.labels = [{ id: -1, name: t('默认分类') }];
      }
    });

    if (curComponentApiName.value) {
      curApi.value = apiList.value.find(api => api.name === curComponentApiName.value) ?? null;
    } else {
      curApi.value = apiList.value[0] ?? null;
    }
    if (curApi.value) {
      await getApigwResourceDoc();
    }
  } catch {
    apiList.value = [];
  }
};

const handleApiClick = async (resId: number) => {
  if (curApi.value.id === resId) return;
  navList.value = [];
  curApi.value = apiList.value.find(res => res.id === resId) ?? null;
  if (curApi.value) {
    await getApigwResourceDoc();
  }
};

const md = new MarkdownIt({
  linkify: false,
  html: true,
  breaks: true,
  highlight(str: string, lang: string) {
    try {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(str, { language: lang, ignoreIllegals: true }).value;
      }
    } catch {
      return str;
    }
    return str;
  },
});

// markdown 解析器自定义规则，用于给 ### 标题添加 id，导航要用
md.renderer.rules.heading_open = function (tokens, idx, options, env, self) {
  const curToken = tokens[idx];
  const nextToken = tokens[idx + 1];
  let count = 2;
  // 找到 ### 标题，并且只包含一行文本的 token
  if (curToken.markup === '###' && nextToken?.type === 'inline') {
    let headingText = nextToken.content;
    if (navList.value.find(item => item.name === headingText)) {
      headingText = `${headingText}${count}`;
      count = count + 1;
    }
    // 给标题元素ID一个前缀，便于导航目录识别
    const idPrefix = 'doc-heading-';
    curToken.attrPush([
      'id',
      `${idPrefix}${headingText}`,
    ]);
    navList.value.push({ id: `${idPrefix}${headingText}`, name: headingText });
  }
  return self.renderToken(tokens, idx, options);
};

const getApigwResourceDoc = async () => {
  try {
    isLoading.value = true;
    let res: any;
    if (curTab.value === 'apigw') {
      const query = {
        stage_name: curStageName.value,
      };
      res = await getApigwResourceDocDocs(curTargetName.value, curApi.value.name, query);
    } else if (curTab.value === 'component') {
      res = await getSystemComponentDoc(board.value, curTargetName.value, curApi.value.name);
    }
    const { content, updated_time } = res;
    curApiMarkdownHtml.value = md.render(content);
    updatedTime.value = updated_time;
  } finally {
    isLoading.value = false;
  }
};

const handleStageChange = async () => {
  await fetchApiList();
};

const getHighlightedHtml = (value: string) => {
  if (keyword.value) {
    return value.replace(new RegExp(`(${keyword.value})`, 'i'), '<em class="ag-keyword">$1</em>');
  }
  return value;
};

const boardList = ref<IBoard[]>([]);

const fetchBoardList = async () => {
  try {
    boardList.value = await getComponentSystemList(board.value) as IBoard[];
  } catch {
    boardList.value = [];
  }
};

const handleSystemChange = async (system: ISystem) => {
  if (system.name === curTargetName.value) return;
  curTargetName.value = system.name;
  curComponentApiName.value = '';
  await init();
};

const init = async () => {
  if (curTab.value === 'apigw') {
    await fetchApigwStages();
  }
  await Promise.all([
    fetchTargetBasics(),
    fetchEsbSdks(),
    fetchApiList(),
  ]);
  if (curTab.value === 'component') {
    await fetchBoardList();
  }
};

const handleGoBack = () => {
  router.push({
    name: 'apiDocs',
    params: {
      curTab: curTab.value,
    },
  });
};

onBeforeMount(() => {
  const { params } = route;
  curTab.value = params.curTab as TabType || 'apigw';
  curTargetName.value = params.targetName as string;
  curComponentApiName.value = params.componentName as string || '';
  init();
});

</script>

<style lang="scss" scoped>

.page-header {
  position: sticky;
  top: 0;
  padding-inline: 24px;
  background: #fff;
  border-bottom: 1px solid #dcdee5;
  box-shadow: 0 3px 4px 0 #0000000a;
  height: 52px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 1;

  .header-main {
    flex-grow: 1;
    display: flex;
    flex-basis: 52px;
    box-sizing: border-box;
    margin-right: auto;
    color: #313238;
    font-size: 16px;

    .icon-ag-return-small {
      font-size: 32px;
      color: #3a84ff;
      cursor: pointer;
    }

    .system-dropdown-wrap {
      display: flex;
      align-items: center;
      margin-left: 8px;

      .dropdown-trigger-btn {
        height: 30px;
        line-height: 28px;
        padding-inline: 6px;
        color: #63656E;
        font-size: 12px;
      }

      .dropdown-trigger-content {
        :deep(.bk-dropdown-item) {
          max-width: 300px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
    }
  }

  .detail-toggle {
    width: 28px;
    height: 28px;
    display: flex;
    justify-content: center;
    align-items: center;
    background: #fff;
    border-radius: 2px;
    color: #63656e;
    cursor: pointer;

    &:hover {
      background: #f0f1f5;
    }

    &.active {
      background: #e1ecff;
      color: #3a84ff;
    }
  }
}

.page-content {
  display: flex;
  margin: 0 auto;

  .left {
    padding: 16px 8px 0 0;
  }

  .left-aside-wrap {
    min-width: 280px;
    width: auto;
    box-shadow: 0 2px 4px 0 #1919290d;
    border-radius: 2px;
    background-color: #ffffff;

    .left-aside-header {
      padding: 16px 24px 12px;

      .title {
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        font-size: 14px;
        color: #313238;
        letter-spacing: 0;
        line-height: 22px;

        .sub-title {
          margin-left: 8px;
          display: flex;
          justify-content: center;
          align-items: center;
          width: 30px;
          height: 16px;
          background: #f0f1f5;
          border-radius: 2px;
          font-size: 12px;
          color: #979ba5;
        }
      }

      .nav-filters {
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
    }

    .resource-list {
      height: calc(100vh - 282px);
      overflow-y: scroll;

      .api-group-collapse {
        max-height: 100%;
        overflow: auto;

        :deep(.bk-collapse-item) {
          margin-bottom: 12px;
        }

        :deep(.icon-angle-right) {
          display: none;
        }

        &::-webkit-scrollbar {
          width: 4px;
          background-color: lighten(#c4c6cc, 80%);
        }

        &::-webkit-scrollbar-thumb {
          height: 5px;
          border-radius: 2px;
          background-color: #c4c6cc;
        }

        .custom-icon {
          margin: -3px 6px 0 0;
          font-size: 13px;
          vertical-align: middle;
          display: inline-block;
        }

        .api-group-collapse-header {
          padding: 4px 6px;
          display: flex;
          align-items: center;
          cursor: pointer;

          .api-group-collapse-title {
            color: #63656e;
            margin-left: 4px;
            font-weight: bold;
          }

          .menu-header-icon {
            transition: all .2s;
            color: #979ba5;
            font-size: 14px;

            &.fold {
              transform: rotate(-90deg);
            }
          }
        }

        :deep(.bk-collapse-content) {
          padding: 2px 0;
        }

        .component-list {
          list-style: none;
          margin: 0;
          padding: 0;

          > li {
            font-size: 12px;
            position: relative;
            padding: 6px 36px 6px 56px;
            cursor: pointer;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;

            &:hover,
            &.active {
              background: #f0f5ff;

              .name,
              .label {
                color: #3a84ff;
              }
            }
          }

          .name {
            color: #63656e;
            font-weight: 700;
          }

          .label {
            color: #979ba5;
          }

          .name,
          .label {
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
            line-height: 20px;
          }
        }
      }

      .resource-item {
        padding-left: 24px;
        height: 52px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        background: #fff;
        cursor: pointer;

        .res-item-name,
        .res-item-desc {
          display: -webkit-box;
          -webkit-line-clamp: 1;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .res-item-name {
          font-size: 14px;
          color: #313238;
          line-height: 22px;
        }

        .res-item-desc {
          font-size: 12px;
          color: #979ba5;
          line-height: 20px;
        }

        &:hover, &.active {
          background: #e1ecff;

          .res-item-name {
            color: #3a84ff;
          }
        }
      }
    }
  }

  .main-content-wrap {
    padding-top: 16px;
  }

  .aside-right {
    .apigw-desc-wrap {
      height: calc(100vh - 144px);
      overflow-y: scroll;
      background-color: #fff;
    }
  }

  // 去掉左侧伸缩栏的拉伸线
  :deep(.bk-resize-layout-left > .bk-resize-layout-aside) {
    padding-right: 8px;
    border-right: none;
  }

  // 去掉右侧伸缩栏的拉伸线
  :deep(.bk-resize-layout-right > .bk-resize-layout-aside) {
    border-left: none;
    transition: none !important;
  }

  // 隐藏的折叠按钮
  :deep(.bk-resize-layout > .bk-resize-layout-aside .bk-resize-collapse) {
    // 避免折叠按钮溢出制造横向滚动条
    svg {
      width: 16px !important;
      height: 16px !important;
    }
  }
}

.custom-scroll-bar {
  &::-webkit-scrollbar {
    width: 4px;
    background-color: lighten(#c4c6cc, 80%);
  }

  &::-webkit-scrollbar-thumb {
    height: 5px;
    border-radius: 2px;
    background-color: #c4c6cc;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }
}
</style>
