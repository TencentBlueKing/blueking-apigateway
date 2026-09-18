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
        <template v-if="curTab === 'component'">
          <BkDivider direction="vertical" />
          <aside class="system-dropdown-wrap">
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
                    :title="system.description ?? undefined"
                    @click="() => handleSystemChange(system)"
                  >
                    <span class="text-12px">
                      <span class="mr-5px">{{ system.description }}</span>
                      ({{ system.name }})
                    </span>
                  </BkDropdownItem>
                </BkDropdownMenu>
              </template>
            </BkDropdown>
          </aside>
        </template>
      </main>
    </header>
    <!--  正文  -->
    <main class="page-content">
      <BkResizeLayout
        class="detail-resize-layout"
        placement="left"
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
                          <div class="flex items-center">
                            <header
                              :ref="(el) => setNameRef(el, api.id)"
                              v-bk-xss-html="getHighlightedHtml(api.name)"
                              v-bk-tooltips="{ content: api.name, disabled: !overflowMap[api.id]?.name }"
                              class="res-item-name mr-8px"
                            />
                            <BkTag
                              v-if="curTargetBasics?.kind === 2"
                              theme="info"
                            >
                              {{ t('模型代理 API') }}
                            </BkTag>
                            <BkTag
                              v-if="curTargetBasics?.is_deprecated"
                              theme="danger"
                            >
                              deprecated
                            </BkTag>
                          </div>
                          <main
                            :ref="(el) => setDescRef(el, api.id)"
                            v-bk-xss-html="getHighlightedHtml(api.description ?? '')"
                            v-bk-tooltips="{ content: api.description, disabled: !overflowMap[api.id]?.desc }"
                            class="res-item-desc"
                          />
                        </article>
                      </template>
                    </BkCollapsePanel>
                  </BkCollapse>
                </template>
                <template v-else-if="keyword">
                  <TableEmpty
                    :empty-type="!!keyword ? 'searchEmpty' : 'empty'"
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
              v-if="apiList.length && curApi"
              v-bkloading="{ loading: isLoading }"
              :api="curApi"
              :basics="curTargetBasics"
              :nav-list="navList"
              :markdown-html="curApiMarkdownHtml"
              :extra-markdown-html="extraMarkdownHtml"
              :updated-time="updatedTime"
              :doc="curDoc"
              :resource-url="resourceUrl"
              @show-gateway-detail="handleShowGatewayDetail"
              @show-apply-permission="handleShowApplyPermission"
            />
            <TableEmpty
              v-else
              empty-type="empty"
              class="empty-wrapper"
            />
          </div>
        </template>
      </BkResizeLayout>
    </main>
    <BkSideslider
      v-model:is-show="isGatewayDetailSliderShow"
      :width="720"
      :title="curTab === 'gateway' ? t('网关详情') : t('组件详情')"
      ext-cls="gateway-detail-sideslider"
      quick-close
    >
      <div class="gateway-detail-slider">
        <DocDetailSideContent
          v-if="curTargetBasics"
          :basics="curTargetBasics"
          :sdks="sdks"
          :board="board"
        />
      </div>
    </BkSideslider>
    <ApplyPermissionDialog
      v-if="curApi"
      v-model:is-show="isApplyDialogShow"
      :gateway-name="curTargetName"
      :resource-name="curApi.name"
    />
  </div>
</template>

<script lang="ts" setup>
import { refDebounced } from '@vueuse/core';
import {
  getApigwResourceDocDocs,
  getApigwResourcesDocs,
  getApigwStagesDocs,
  getGatewaysDetailsDocs,
} from '@/services/source/docs';
import {
  getComponentSystemDetail,
  getComponentSystemList,
  getESBSDKDetail,
  getSystemAPIList,
  getSystemComponentDoc,
} from '@/services/source/docs-esb.ts';
import type { ComponentPublicInstance } from 'vue';
import type {
  IDocsEsbBoardsSystemsListResponse as IBoard,
  IDocsGatewaysStagesListResponse as IStage,
  ISystemSLZ as ISystem,
} from '@/services/types/responses/docs';
import type { INavItem } from '../components/DocDetailSideNav.vue';
import type { ISdkItem } from '../components/DocSdkSection.vue';
import { type DocTab, docTabKey } from '../utils/doc-context';
import MarkdownIt from 'markdown-it';
import DocDetailMainContent, { type IDocApi, type IDocContent } from '../components/DocDetailMainContent.vue';
import DocDetailSideContent, { type IDocBasics } from '../components/DocDetailSideContent.vue';
import ApplyPermissionDialog from '../components/ApplyPermissionDialog.vue';
import TableEmpty from '@/components/table-empty/Index.vue';
import { AngleUpFill } from 'bkui-vue/lib/icon';
import hljs from 'highlight.js';
import { useEnv, useFeatureFlag } from '@/stores';
import {
  buildResourceUrl,
  getContentSchema,
  isStructuredDoc,
  mergeGatewayConfigIntoSchema,
  needsAuthSection,
  shouldRenderSchemaParams,
  stripOverlappingMarkdown,
} from '../utils/compose-doc';

interface IApiGroup {
  id: number
  name: string
  apiList: IDocApi[]
}

interface IMarkdownRenderEnv {
  headings: INavItem[]
}

interface IRenderedMarkdown {
  html: string
  headings: INavItem[]
}

type TemplateElement = Element | ComponentPublicInstance | null;

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const envStore = useEnv();
const featureFlagStore = useFeatureFlag();

const curTab = ref<DocTab>('gateway');
const board = ref('default');
// 提供当前 tab 的值
provide(docTabKey, curTab);

const stageList = ref<IStage[]>([]);
const curStageName = ref('');

// 当前的网关或组件被命名为 target
const curTargetName = ref(''); // 当前文档所属的网关或组件名称
const curTargetBasics = ref<IDocBasics | null>(null); // 当前文档所属的target主要信息
const apiList = ref<IDocApi[]>([]); // 当前target下的所有api
const boardList = ref<IBoard[]>([]);
const curComponentApiName = ref(''); // 当前组件api名称，路由用
const curApi = ref<IDocApi | null>(null); // 当前选中的 api
const curDoc = ref<IDocContent | null>(null);
const curApiMarkdownHtml = ref('');
const extraMarkdownHtml = ref('');
const updatedTime = ref<string | null>(null);
const sdks = ref<ISdkItem[]>([]);
const isGatewayDetailSliderShow = ref(false);
const isApplyDialogShow = ref(false);
const navList = ref<INavItem[]>([]);

const handleShowGatewayDetail = () => {
  isApplyDialogShow.value = false;
  isGatewayDetailSliderShow.value = true;
};

const handleShowApplyPermission = () => {
  isGatewayDetailSliderShow.value = false;
  isApplyDialogShow.value = true;
};

watch(curApi, () => {
  isApplyDialogShow.value = false;
});
const isLoading = ref(false);
const keyword = ref(''); // 筛选器输入框的搜索关键字
const debouncedKeyword = refDebounced(keyword, 500);
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
  const keyword = debouncedKeyword.value.toLowerCase();
  if (!keyword) {
    return apiList.value;
  }
  return apiList.value.filter(api =>
    api.name?.toLowerCase().includes(keyword) || api.description?.toLowerCase().includes(keyword),
  );
});
const defaultApiCategory = computed(() => ({
  id: -1,
  name: t('默认分类'),
}));

// API 分类列表
const apiGroupList = computed(() => {
  return filteredApiList.value.reduce<IApiGroup[]>((groupList, api) => {
    const { id, name } = api.labels?.[0] || defaultApiCategory.value;
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
  }, []);
});

const allSystemList = computed(() => {
  const curBoard = boardList.value.find((item: IBoard) => item.board === board.value);
  const systems: ISystem[] = [];
  if (curBoard) {
    curBoard.categories.forEach(cat => cat.systems.forEach((system: ISystem) => systems.push(system)));
  }
  return systems;
});

const resourceUrl = computed(() => {
  if (!curApi.value || curTab.value !== 'gateway') {
    return '';
  }
  const urlTemplate = envStore.env.BK_API_RESOURCE_URL_TMPL;
  if (!urlTemplate) {
    return '';
  }
  return buildResourceUrl(
    urlTemplate,
    curTargetName.value,
    curStageName.value,
    curApi.value.path || '',
  );
});

// 分类列表变化时更新 collapse 展开状态
watch(apiGroupList, () => {
  activeGroupPanelNames.value = apiGroupList.value.map(item => item.name);
});

watch([filteredApiList, debouncedKeyword], async () => {
  await nextTick();
  checkOverflow();
});

watch(() => route.query, async () => {
  if (route.query?.stage) {
    curStageName.value = String(route.query.stage);
    await fetchApiList();
  }

  const apiName = String(route.query.apiName ?? '');
  if (apiName) {
    curComponentApiName.value = apiName;
    curApi.value = apiList.value.find(api => api.name === curComponentApiName.value) ?? null;
    navList.value = [];

    if (curApi.value) {
      await getApigwResourceDoc();
    }
  }
}, { deep: true });

const fetchTargetBasics = async () => {
  try {
    if (curTab.value === 'gateway') {
      const { sdks: sdksResponse, ...restResponse } = await getGatewaysDetailsDocs(curTargetName.value);
      curTargetBasics.value = restResponse;
      sdks.value = Array.isArray(sdksResponse) ? sdksResponse : [];
    }
    else if (curTab.value === 'component') {
      curTargetBasics.value = await getComponentSystemDetail(board.value, curTargetName.value);
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

    const requestedStage = stageList.value.find((stage: IStage) => stage.name === route.query?.stage);
    if (requestedStage) {
      curStageName.value = requestedStage.name;
    }
    else {
      const prodStage = stageList.value.find((stage: IStage) => stage.name === 'prod');
      curStageName.value = prodStage?.name || stageList.value[0]?.name || '';
    }
  }
  catch {
    stageList.value = [];
  }
};

const fetchApiList = async () => {
  try {
    let res: IDocApi[] = [];
    navList.value = [];
    if (curTab.value === 'gateway') {
      const query = {
        limit: 10000,
        offset: 0,
        stage_name: curStageName.value,
      };
      res = await getApigwResourcesDocs(curTargetName.value, query);
    }
    else if (curTab.value === 'component') {
      res = await getSystemAPIList(board.value, curTargetName.value);
    }
    apiList.value = res ?? [];
    // 为 api 添加默认分类
    apiList.value.forEach((api) => {
      if (!api.labels?.length) {
        api.labels = [{ ...defaultApiCategory.value }];
      }
    });

    if (route.query?.apiName) {
      curComponentApiName.value = String(route.query.apiName);
    }

    if (curComponentApiName.value) {
      curApi.value = apiList.value.find(api => api.name === curComponentApiName.value)
        ?? null;
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
  if (curApi.value?.id === resId) return;

  router.replace({
    name: 'ApiDocDetail',
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
  const renderEnv = env as IMarkdownRenderEnv;
  // 找到 ### 标题，并且只包含一行文本的 token
  if (curToken.markup === '###' && nextToken?.type === 'inline') {
    const headingText = nextToken.content;
    const duplicateCount = renderEnv.headings.filter(item => item.name === headingText).length;
    const headingIdText = duplicateCount ? `${headingText}${duplicateCount + 1}` : headingText;
    // 给标题元素ID一个前缀，便于导航目录识别
    const idPrefix = 'doc-heading-';
    curToken.attrPush([
      'id',
      `${idPrefix}${headingIdText}`,
    ]);
    renderEnv.headings.push({
      id: `${idPrefix}${headingIdText}`,
      name: headingText,
    });
  }
  return self.renderToken(tokens, idx, options);
};

const renderMarkdown = (content = ''): IRenderedMarkdown => {
  const renderEnv: IMarkdownRenderEnv = { headings: [] };
  return {
    html: md.render(content, renderEnv),
    headings: renderEnv.headings,
  };
};

const getApigwResourceDoc = async () => {
  try {
    isLoading.value = true;
    const api = curApi.value;
    if (!api) {
      return;
    }
    let res: IDocContent | undefined;
    if (curTab.value === 'gateway') {
      const query = { stage_name: curStageName.value };
      res = await getApigwResourceDocDocs(curTargetName.value, api.name, query);
    }
    else if (curTab.value === 'component') {
      res = await getSystemComponentDoc(board.value, curTargetName.value, api.name);
    }
    const { content, updated_time } = res || {};
    curDoc.value = res ?? null;
    updatedTime.value = updated_time ?? null;
    navList.value = [];

    if (curTab.value === 'gateway' && res && isStructuredDoc(res) && curApi.value) {
      const extra = stripOverlappingMarkdown(content || '', shouldRenderSchemaParams(res));
      const renderedExtra = renderMarkdown(extra);
      const structuredNav = buildStructuredNav(res, curApi.value, extra);
      extraMarkdownHtml.value = renderedExtra.html;
      curApiMarkdownHtml.value = '';
      navList.value = [
        ...structuredNav,
        ...renderedExtra.headings.filter(item => !structuredNav.some(nav => nav.id === item.id)),
      ];
    }
    else {
      const renderedMarkdown = renderMarkdown(content || '');
      extraMarkdownHtml.value = '';
      curApiMarkdownHtml.value = renderedMarkdown.html;
      navList.value = renderedMarkdown.headings;
    }
  }
  finally {
    isLoading.value = false;
  }
};

const buildStructuredNav = (
  doc: IDocContent,
  api: IDocApi,
  extraMarkdown = '',
): INavItem[] => {
  const nav: INavItem[] = [
    {
      id: 'doc-heading-调用地址',
      name: t('调用地址'),
    },
  ];
  if (needsAuthSection({
    plugins: doc.plugins,
    verifiedAppRequired: api.verified_app_required,
    verifiedUserRequired: api.verified_user_required,
    isTenantMode: featureFlagStore.isTenantMode,
  })) {
    nav.push({
      id: 'doc-heading-认证方式',
      name: t('认证方式'),
    });
  }
  if (shouldRenderSchemaParams(doc)) {
    const schema = mergeGatewayConfigIntoSchema(doc.openapi_schema, {
      path: api.path,
      plugins: doc.plugins,
    });
    if (schema.parameters?.length || getContentSchema(schema.requestBody?.content)) {
      nav.push({
        id: 'doc-heading-请求参数',
        name: t('请求参数'),
      });
    }
    const hasResponseContent = Object.values(schema.responses || {}).some((response) => {
      return Boolean(response.description || getContentSchema(response.content));
    });
    if (hasResponseContent) {
      nav.push({
        id: 'doc-heading-响应参数',
        name: t('响应参数'),
      });
    }
  }
  if (extraMarkdown && !/^#{1,6}\s+/m.test(extraMarkdown)) {
    nav.push({
      id: 'doc-heading-补充说明',
      name: t('补充说明'),
    });
  }
  return nav;
};

const handleStageChange = () => {
  router.replace({
    name: 'ApiDocDetail',
    params: { ...route.params },
    query: {
      ...route.query,
      stage: curStageName.value,
    },
  });
  // await fetchApiList();
};

const getHighlightedHtml = (value: string = '') => {
  const keyword = debouncedKeyword.value;
  // 提前返回，同时避免空关键字导致 indexOf 死循环
  if (!keyword) {
    return value;
  }

  const lowerValue = value.toLowerCase();
  const lowerKeyword = keyword.toLowerCase();
  let result = '';
  let startIndex = 0;
  let matchIndex = lowerValue.indexOf(lowerKeyword, startIndex);

  while (matchIndex !== -1) {
    // 匹配位置之前的普通文本
    result += value.slice(startIndex, matchIndex);
    // 高亮片段，截取原文以保留大小写
    result += `<b class="ag-keyword">${value.slice(matchIndex, matchIndex + keyword.length)}</b>`;
    // 从本次匹配结束处继续往后找
    startIndex = matchIndex + keyword.length;
    matchIndex = lowerValue.indexOf(lowerKeyword, startIndex);
  }

  // 拼接最后一段剩余文本
  result += value.slice(startIndex);
  return result;
};

const nameRefs = new Map<number, HTMLElement>();
const descRefs = new Map<number, HTMLElement>();
type IOverflow = {
  name: boolean
  desc: boolean
};

const overflowMapRef = ref<Record<number, IOverflow>>({});
const overflowMap = computed(() => overflowMapRef.value);

const toHTMLElement = (el: TemplateElement): HTMLElement | null => {
  if (!el) return null;
  if (el instanceof HTMLElement) return el;
  if ('$el' in el && el.$el instanceof HTMLElement) return el.$el;
  return null;
};

const setNameRef = (el: TemplateElement, id: number) => {
  const node = toHTMLElement(el);
  if (!node) {
    nameRefs.delete(id);
    return;
  }
  nameRefs.set(id, node);
};

const setDescRef = (el: TemplateElement, id: number) => {
  const node = toHTMLElement(el);
  if (!node) {
    descRefs.delete(id);
    return;
  }
  descRefs.set(id, node);
};

const checkOverflow = () => {
  nameRefs.forEach((el, id) => {
    const nameOverflow = el.scrollWidth > el.clientWidth || el.scrollHeight > el.clientHeight;
    if (!overflowMapRef.value[id]) {
      overflowMapRef.value[id] = {
        name: false,
        desc: false,
      };
    }
    overflowMapRef.value[id].name = nameOverflow;
  });
  descRefs.forEach((el, id) => {
    const descOverflow = el.scrollWidth > el.clientWidth || el.scrollHeight > el.clientHeight;
    if (!overflowMapRef.value[id]) {
      overflowMapRef.value[id] = {
        name: false,
        desc: false,
      };
    }
    overflowMapRef.value[id].desc = descOverflow;
  });
};

const fetchBoardList = async () => {
  try {
    boardList.value = await getComponentSystemList(board.value);
  }
  catch {
    boardList.value = [];
  }
};

const handleSystemChange = async (system: ISystem) => {
  if (system.name === curTargetName.value) return;
  curTargetName.value = system.name;
  curComponentApiName.value = '';
  router.replace({
    name: 'ApiDocDetail',
    params: {
      ...route.params,
      targetName: curTargetName.value,
    },
  });
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
    name: 'ApiDocs',
    params: { curTab: curTab.value },
  });
};

onBeforeMount(() => {
  const { params } = route;
  curTab.value = params.curTab === 'component' ? 'component' : 'gateway';
  curTargetName.value = String(params.targetName ?? '');
  curComponentApiName.value = String(params.componentName ?? '');
  board.value = String(params.board || 'default');
  init();
});
</script>

<style lang="scss" scoped>
@use "sass:color";

.page-wrap {
  display: flex;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  flex-direction: column;
}

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
  flex-shrink: 0;

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

      .dropdown-trigger-btn {
        display: flex;
        height: 30px;
        font-size: 12px;
        line-height: 28px;
        color: #3a84ff;
        padding-inline: 6px;
        gap: 4px;
        align-items: center;
        cursor: pointer;
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
  width: 100%;
  min-height: 0;
  padding: 16px 0;
  margin: 0 auto;
  box-sizing: border-box;
  flex: 1;

  .detail-resize-layout {
    height: 100%;
    min-height: 0;
    margin-left: 40px;
    flex-grow: 1;
  }

  .left {
    height: 100%;
    padding-right: 8px;
    box-sizing: border-box;
  }

  .left-aside-wrap {
    display: flex;
    width: auto;
    height: 100%;
    min-width: 280px;
    min-height: 0;
    background-color: #fff;
    border-radius: 2px;
    box-shadow: 0 2px 4px 0 #1919290d;
    flex-direction: column;

    .left-aside-header {
      flex-shrink: 0;
      padding: 16px 16px 12px;

      .title {
        display: flex;
        margin-bottom: 12px;
        font-size: 14px;
        font-weight: 700;
        line-height: 22px;
        letter-spacing: 0;
        color: #313238;
        align-items: center;

        .sub-title {
          display: inline-flex;
          height: 16px;
          min-width: 16px;
          padding: 0 5px;
          margin-left: 8px;
          font-size: 12px;
          font-weight: 400;
          line-height: 16px;
          color: #979ba5;
          background: #f0f1f5;
          border-radius: 8px;
          justify-content: center;
          align-items: center;
        }
      }

      .nav-filters {
        display: flex;
        flex-direction: column;
        gap: 8px;

        :deep(.bk-select),
        :deep(.bk-input) {
          width: 100%;
        }
      }
    }

    .resource-list {
      flex: 1;
      min-height: 0;
      overflow-y: auto;

      .api-group-collapse {
        max-height: 100%;
        overflow: auto;

        :deep(.bk-collapse-item) {
          margin-bottom: 4px;
          background: transparent;
          border: none;
          box-shadow: none;
        }

        :deep(.bk-collapse-header) {
          height: auto;
          padding: 0;
          line-height: 22px;
          background: transparent !important;
        }

        :deep(.icon-angle-right) {
          display: none;
        }

        &::-webkit-scrollbar {
          width: 4px;
          background-color: color.scale(#c4c6cc, $lightness: 80%);
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
          padding: 6px 16px;
          cursor: pointer;
          align-items: center;

          .api-group-collapse-title {
            margin-left: 4px;
            font-size: 12px;
            font-weight: 700;
            line-height: 20px;
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
          padding: 0;
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
        min-height: 48px;
        padding: 8px 16px 8px 32px;
        cursor: pointer;
        background: #fff;
        flex-direction: column;
        justify-content: center;

        .res-item-desc {
          display: -webkit-box;
          overflow: hidden;
          font-size: 12px;
          line-height: 20px;
          color: #979ba5;
          -webkit-box-orient: vertical;
          -webkit-line-clamp: 1;
        }

        .res-item-name {
          display: block;
          overflow: hidden;
          font-size: 14px;
          line-height: 22px;
          color: #313238;
          text-overflow: ellipsis;
          white-space: nowrap;
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
    height: 100%;
    min-height: 0;
    padding-right: 8px;
    box-sizing: border-box;
  }

  .empty-wrapper {
    height: 100%;
  }

  .aside-right {
    padding-top: 16px;

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

.gateway-detail-slider {
  padding: 0;
  background: #f5f7fa;
}

.custom-scroll-bar {

  &::-webkit-scrollbar {
    width: 4px;
    background-color: color.scale(#c4c6cc, $lightness: 80%);
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

<style lang="scss">
.gateway-detail-sideslider {

  .bk-sideslider-title {
    display: flex;
    width: 100%;
    padding-right: 0;
  }
}
</style>
