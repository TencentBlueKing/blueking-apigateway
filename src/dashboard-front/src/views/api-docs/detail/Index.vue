<template>
  <!--  文档详情页  -->
  <div class="page-wrap">
    <!-- 顶部带返回按钮和系统切换器的通栏 -->
    <header class="page-header">
      <main class="flex items-center header-main">
        <!--  返回按钮  -->
        <i
          class="icon apigateway-icon icon-ag-return-small"
          @click="handleGoBack"
        />
        {{ curTab === 'gateway' ? curTargetName : curTargetBasics?.description ?? '' }}
        <!--  组件系统下拉菜单  -->
        <aside
          v-if="curTab === 'component'"
          class="system-dropdown-wrap"
        >
          <BkDropdown :popover-options="{ boundary: 'body', placement: 'bottom-start' }">
            <div class="dropdown-trigger-btn">
              <span>{{ curTargetName }}</span>
              <i class="ag-doc-icon doc-down-shape apigateway-icon icon-ag-down-shape" />
            </div>
            <template #content>
              <BkDropdownMenu class="dropdown-trigger-content bk-dropdown-list">
                <BkDropdownItem
                  v-for="system in allSystemList"
                  :key="system.name"
                  :title="system.description"
                  @click="() => handleSystemChange(system)"
                >
                  <span class="text-14px">
                    <span class="mr-5px">{{ system.description }}</span>
                    ({{ system.name }})
                  </span>
                </BkDropdownItem>
              </BkDropdownMenu>
            </template>
          </BkDropdown>
        </aside>
      </main>
    </header>
    <!--  正文  -->
    <main class="page-content">
      <BkResizeLayout
        ref="outerResizeLayoutRef"
        placement="right"
        :border="false"
        collapsible
        initial-divide="392px"
        :max="480"
        :min="393"
        style="flex-grow: 1;"
      >
        <template #main>
          <BkResizeLayout
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
                      {{ curTab === 'gateway' ? t('资源列表') : t('API列表') }}
                      <aside
                        v-if="apiList.length"
                        class="sub-title"
                      >
                        {{ filteredApiList.length }}
                      </aside>
                    </header>
                    <main class="nav-filters">
                      <article v-if="curTab === 'gateway'">
                        <BkSelect
                          v-model="curStageName"
                          :clearable="false"
                          filterable
                          :input-search="false"
                          :prefix="t('环境')"
                          @change="handleStageChange"
                        >
                          <BkOption
                            v-for="option in stageList"
                            :key="option.id"
                            :value="option.name"
                            :label="option.name"
                          />
                        </BkSelect>
                      </article>
                      <article>
                        <BkInput
                          v-model="keyword"
                          type="search"
                          :placeholder="searchPlaceholder"
                          clearable
                        />
                      </article>
                    </main>
                  </header>
                  <!--  API 列表  -->
                  <main class="resource-list custom-scroll-bar">
                    <template v-if="filteredApiList.length">
                      <BkCollapse
                        v-model="activeGroupPanelNames"
                        class="api-group-collapse"
                      >
                        <BkCollapsePanel
                          v-for="group of apiGroupList"
                          :key="group.id"
                          :name="group.name"
                        >
                          <template #header>
                            <div class="api-group-collapse-header">
                              <AngleUpFill
                                class="menu-header-icon"
                                :class="{ fold: !activeGroupPanelNames.includes(group.name) }"
                              />
                              <div class="api-group-collapse-title">
                                {{ group.name }}
                              </div>
                            </div>
                          </template>
                          <template #content>
                            <article
                              v-for="api in group.apiList"
                              :key="api.id"
                              class="resource-item"
                              :class="{ active: api.id === curApi?.id }"
                              @click="() => handleApiClick(api.id, api.name)"
                            >
                              <header
                                v-dompurify-html="getHighlightedHtml(api.name)"
                                class="res-item-name"
                              />
                              <main
                                v-dompurify-html="getHighlightedHtml(api.description)"
                                class="res-item-desc"
                              />
                            </article>
                          </template>
                        </BkCollapsePanel>
                      </BkCollapse>
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
                  v-bkloading="{ loading: isLoading }"
                  :api="curApi"
                  :nav-list="navList"
                  :markdown-html="curApiMarkdownHtml"
                  :updated-time="updatedTime"
                  @show-sdk-instruction="isSdkInstructionSliderShow = true"
                />
              </div>
            </template>
          </BkResizeLayout>
        </template>
        <!--  右栏，网关/组件主要信息和SDK  -->
        <template #aside>
          <aside class="aside-right">
            <main class="apigw-desc-wrap custom-scroll-bar">
              <DocDetailSideContent
                v-if="curTargetBasics"
                :basics="curTargetBasics"
                :sdks="sdks"
              />
            </main>
          </aside>
        </template>
      </BkResizeLayout>
    </main>
    <!--  SDK使用说明 Slider  -->
    <SDKInstructionSlider v-model="isSdkInstructionSliderShow" />
  </div>
</template>

<script lang="ts" setup>
import {
  getApigwResourceDocDocs,
  getApigwResourcesDocs,
  getApigwStagesDocs,
  getGatewaysDetailsDocs,
} from '@/services/source/docs';
import {
  getComponenSystemDetail,
  getComponentSystemList,
  getESBSDKDetail,
  getSystemAPIList,
  getSystemComponentDoc,
} from '@/services/source/docs-esb.ts';
import {
  type IApiGatewayBasics,
  type IApiGatewaySdkDoc,
  type IBoard,
  type IComponent,
  type IComponentSdk,
  type INavItem,
  type IResource,
  type IStage,
  type ISystem,
  type ISystemBasics,
  type TabType,
} from '../types';
import MarkdownIt from 'markdown-it';
import { ResizeLayout } from 'bkui-vue';
import DocDetailMainContent from '../components/DocDetailMainContent.vue';
import DocDetailSideContent from '../components/DocDetailSideContent.vue';
import SDKInstructionSlider from '../components/SDKInstructionSlider.vue';
import TableEmpty from '@/components/table-empty/index.vue';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import hljs from 'highlight.js';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();

const curTab = ref<TabType>('gateway');
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
const keyword = ref(''); // 筛选器输入框的搜索关键字
const activeGroupPanelNames = ref<string[]>([]); // API分类 collapse 展开的 panel

const searchPlaceholder = computed(() => {
  return t(
    '在{resourceLength}个{type}中搜索...',
    {
      resourceLength: apiList.value.length,
      type: curTab.value === 'gateway' ? t('资源') : 'API',
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
    }
    else {
      groupList.push({
        id,
        name,
        apiList: [api],
      });
    }
    return groupList;
  }, [] as {
    id: number
    name: string
    apiList: typeof apiList.value
  }[]);
});

const allSystemList = computed(() => {
  const curBoard = boardList.value[0];
  const systems: ISystem[] = [];
  curBoard.categories.forEach(cat => cat.systems.forEach(system => systems.push(system)));
  return systems;
});

// 分类列表变化时更新 collapse 展开状态
watch(apiGroupList, () => {
  activeGroupPanelNames.value = apiGroupList.value.map(item => item.name);
});

watch(() => route.query, async () => {
  if (route.query?.apiName) {
    curComponentApiName.value = route.query.apiName as string;
    curApi.value = apiList.value.find(api => api.name === curComponentApiName.value) ?? null;
    navList.value = [];

    if (curApi.value) {
      await getApigwResourceDoc();
    }
  }

  if (route.query?.stage) {
    curStageName.value = route.query.stage as string;
    await fetchApiList();
  }
}, { deep: true });

const fetchTargetBasics = async () => {
  try {
    if (curTab.value === 'gateway') {
      const { sdks: sdksResponse, ...restResponse } = await getGatewaysDetailsDocs(curTargetName.value);
      curTargetBasics.value = restResponse;
      sdks.value = sdksResponse;
    }
    else if (curTab.value === 'component') {
      curTargetBasics.value = await getComponenSystemDetail(board.value, curTargetName.value);
    }
  }
  catch {
    curTargetBasics.value = null;
  }
};

const fetchEsbSdks = async () => {
  if (curTab.value !== 'component') {
    return;
  }
  try {
    const response = await getESBSDKDetail(board.value, { language: 'python' });
    sdks.value = [{
      language: 'python',
      ...response,
    }];
  }
  catch {
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

    const requestedStage = stageList.value.find(stage => stage.name === route.query?.stage);
    if (requestedStage) {
      curStageName.value = requestedStage.name;
    }
    else {
      const prodStage = stageList.value.find(stage => stage.name === 'prod');
      curStageName.value = prodStage?.name || stageList.value[0]?.name || '';
    }
  }
  catch {
    stageList.value = [];
  }
};

const fetchApiList = async () => {
  try {
    console.log(curTargetName.value);
    let res: (IResource & IComponent)[] = [];
    navList.value = [];
    if (curTab.value === 'gateway') {
      const query = {
        limit: 10000,
        offset: 0,
        stage_name: curStageName.value,
      };
      res = await getApigwResourcesDocs(curTargetName.value, query) as (IResource & IComponent)[];
    }
    else if (curTab.value === 'component') {
      res = await getSystemAPIList(board.value, curTargetName.value) as (IResource & IComponent)[];
    }
    apiList.value = res ?? [];
    // 为 api 添加默认分类
    apiList.value.forEach((api) => {
      if (!api.labels?.length) {
        api.labels = [{
          id: -1,
          name: t('默认分类'),
        }];
      }
    });

    if (route.query?.apiName) {
      curComponentApiName.value = route.query.apiName as string;
    }

    if (curComponentApiName.value) {
      curApi.value = apiList.value.find(api => api.name === curComponentApiName.value) ?? null;
    }
    else {
      curApi.value = apiList.value[0] ?? null;
    }
    if (curApi.value) {
      await getApigwResourceDoc();
    }
  }
  catch {
    apiList.value = [];
  }
};

const handleApiClick = (resId: number, apiName: string) => {
  if (curApi.value.id === resId) return;

  router.replace({
    name: 'apiDocDetail',
    params: { ...route.params },
    query: {
      ...route.query,
      apiName,
    },
  });
};

const md = new MarkdownIt({
  linkify: false,
  html: true,
  breaks: true,
  highlight(str: string, lang: string) {
    try {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(str, {
          language: lang,
          ignoreIllegals: true,
        }).value;
      }
    }
    catch {
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
    navList.value.push({
      id: `${idPrefix}${headingText}`,
      name: headingText,
    });
  }
  return self.renderToken(tokens, idx, options);
};

const getApigwResourceDoc = async () => {
  try {
    isLoading.value = true;
    let res: any;
    if (curTab.value === 'gateway') {
      const query = { stage_name: curStageName.value };
      res = await getApigwResourceDocDocs(curTargetName.value, curApi.value.name, query);
    }
    else if (curTab.value === 'component') {
      res = await getSystemComponentDoc(board.value, curTargetName.value, curApi.value.name);
    }
    const { content, updated_time } = res;
    curApiMarkdownHtml.value = md.render(content);
    updatedTime.value = updated_time;
  }
  finally {
    isLoading.value = false;
  }
};

const handleStageChange = () => {
  router.replace({
    name: 'apiDocDetail',
    params: { ...route.params },
    query: {
      ...route.query,
      stage: curStageName.value,
    },
  });
  // await fetchApiList();
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
  }
  catch {
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
  if (curTab.value === 'gateway') {
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
    params: { curTab: curTab.value },
  });
};

onBeforeMount(() => {
  const { params } = route;
  curTab.value = params.curTab as TabType || 'gateway';
  curTargetName.value = params.targetName as string;
  curComponentApiName.value = params.componentName as string || '';
  board.value = params.board as string || 'default';
  init();
});

</script>

<style lang="scss" scoped>
.page-header {
  position: sticky;
  top: 0;
  z-index: 1;
  display: flex;
  height: 52px;
  background: #fff;
  border-bottom: 1px solid #dcdee5;
  box-shadow: 0 3px 4px 0 #0000000a;
  padding-inline: 24px;
  justify-content: space-between;
  align-items: center;

  .header-main {
    display: flex;
    margin-right: auto;
    font-size: 16px;
    color: #313238;
    box-sizing: border-box;
    flex-grow: 1;
    flex-basis: 52px;

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
        font-size: 12px;
        line-height: 28px;
        color: #63656E;
        padding-inline: 6px;
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
    display: flex;
    width: 28px;
    height: 28px;
    color: #63656e;
    cursor: pointer;
    background: #fff;
    border-radius: 2px;
    justify-content: center;
    align-items: center;

    &:hover {
      background: #f0f1f5;
    }

    &.active {
      color: #3a84ff;
      background: #e1ecff;
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
    width: auto;
    min-width: 280px;
    background-color: #fff;
    border-radius: 2px;
    box-shadow: 0 2px 4px 0 #1919290d;

    .left-aside-header {
      padding: 16px 24px 12px;

      .title {
        display: flex;
        margin-bottom: 12px;
        font-size: 14px;
        line-height: 22px;
        letter-spacing: 0;
        color: #313238;
        align-items: center;

        .sub-title {
          display: flex;
          width: 30px;
          height: 16px;
          margin-left: 8px;
          font-size: 12px;
          color: #979ba5;
          background: #f0f1f5;
          border-radius: 2px;
          justify-content: center;
          align-items: center;
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
          background-color: #c4c6cc;
          border-radius: 2px;
        }

        .custom-icon {
          display: inline-block;
          margin: -3px 6px 0 0;
          font-size: 13px;
          vertical-align: middle;
        }

        .api-group-collapse-header {
          display: flex;
          padding: 4px 6px;
          cursor: pointer;
          align-items: center;

          .api-group-collapse-title {
            margin-left: 4px;
            font-weight: bold;
            color: #63656e;
          }

          .menu-header-icon {
            font-size: 14px;
            color: #979ba5;
            transition: all .2s;

            &.fold {
              transform: rotate(-90deg);
            }
          }
        }

        :deep(.bk-collapse-content) {
          padding: 2px 0;
        }

        .component-list {
          padding: 0;
          margin: 0;
          list-style: none;

          >li {
            position: relative;
            padding: 6px 36px 6px 56px;
            overflow: hidden;
            font-size: 12px;
            text-overflow: ellipsis;
            white-space: nowrap;
            cursor: pointer;

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
            font-weight: 700;
            color: #63656e;
          }

          .label {
            color: #979ba5;
          }

          .name,
          .label {
            overflow: hidden;
            line-height: 20px;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
        }
      }

      .resource-item {
        display: flex;
        height: 52px;
        padding-left: 24px;
        cursor: pointer;
        background: #fff;
        flex-direction: column;
        justify-content: center;

        .res-item-name,
        .res-item-desc {
          display: -webkit-box;
          overflow: hidden;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 1;
        }

        .res-item-name {
          font-size: 14px;
          line-height: 22px;
          color: #313238;
        }

        .res-item-desc {
          font-size: 12px;
          line-height: 20px;
          color: #979ba5;
        }

        &:hover,
        &.active {
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
    background-color: #c4c6cc;
    border-radius: 2px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }
}
</style>
