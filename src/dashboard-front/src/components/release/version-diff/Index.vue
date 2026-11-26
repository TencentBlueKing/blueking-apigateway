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
  <div class="ag-version-diff-box">
    <p class="summary-data">
      <span class="font-bold color-#63656e">
        {{ t('对比结果') }}：
      </span>
      <template v-if="isDataLoading">
        <span>
          <Spinner fill="#3a84ff" />
          {{ t('正在努力对比中…') }}
        </span>
      </template>
      <template v-else-if="localSourceId || localTargetId">
        <span>
          {{ t('新增') }}
          <span class="font-bold color-#2dcb56 m-5px">
            {{ diffData.add.length }}
          </span>
          {{ t('个资源') }}，
        </span>
        <span>
          {{ t('更新') }}
          <span class="font-bold color-#ff9c01! m-5px">
            {{ diffData.update.length }}
          </span>
          {{ t('个资源') }}，
        </span>
        <span>
          {{ t('删除') }}
          <span class="font-bold color-#ea3636 m-5px">
            {{ diffData.delete.length }}
          </span>
          {{ t('个资源') }}
        </span>
      </template>
      <template v-else>
        --
      </template>
    </p>

    <div class="flex justify-between items-center mb-15px">
      <div class="flex items-center gap-10px">
        <BkInput
          v-model="searchParams.keyword"
          clearable
          class="w-310px!"
          :placeholder="t('请输入资源名称、资源地址或请求路径，回车结束')"
          type="search"
          @enter="handleSearch"
          @clear="handleClear"
        />
        <BkSelect
          v-model="searchParams.diffType"
          class="w-140px"
          clearable
          :placeholder="t('全部差异类型')"
        >
          <BkOption
            v-for="option in diffTypeList"
            :id="option.id"
            :key="option.id"
            :name="option.name"
          />
        </BkSelect>
        <BkCheckbox
          v-model="searchParams.onlyUpdated"
          true-value
          :false-value="false"
        >
          {{ t('仅显示有差异的资源属性') }}
        </BkCheckbox>
        <BkCheckbox
          v-model="searchParams.hideOnlyDiffInDocUpdatedTime"
          true-value
          :false-value="false"
        >
          {{ t('隐藏仅文档更新的资源') }}
        </BkCheckbox>
      </div>

      <div class="tag-list">
        <div class="legend-group">
          <div class="tag success" />
          <div>{{ t('新增') }}</div>
        </div>
        <div class="legend-group">
          <div class="tag warning" />
          <div>{{ t('更新') }}</div>
        </div>
        <div class="legend-group">
          <div class="tag danger" />
          <div>{{ t('删除') }}</div>
        </div>
      </div>
    </div>

    <div
      class="diff-wrapper"
      :class="[{ 'no-result': !hasResult }]"
    >
      <div class="diff-header">
        <div class="source-header">
          <!-- <div class="marked">{{ t('源版本') }}</div> -->
          <div class="version">
            <template
              v-if="localSourceId && (localSourceId !== 'current' || localTargetId !== 'current')"
            >
              <BkSelect
                v-if="sourceSwitch || pageType === 'createVersion'"
                v-model="localSourceId"
                class="float-left mr-10px choose-version"
                :placeholder="t('请选择源版本')"
                :clearable="false"
                :input-search="false"
                filterable
                @change="handleVersionChange"
              >
                <template #trigger>
                  <span
                    v-bk-tooltips="{ content: localSourceTriggerLabel, delay: 300 }"
                    class="trigger-label"
                  >
                    {{ localSourceTriggerLabel }}
                  </span>
                  <AgIcon
                    name="down-shape"
                    class="trigger-label-icon"
                  />
                </template>
                <BkOption
                  v-for="option in localVersionList"
                  :id="option.id"
                  :key="option.id"
                  :disabled="option.id === localTargetId"
                  :name="option.resource_version_display"
                />
              </BkSelect>
              <span
                v-else
                class="title"
              >
                <template v-if="pageType === 'publishEnvironment'">
                  {{
                    sourceVersion.version ? t('当前版本（{version}）', { version: sourceVersion.version }) : t('暂无版本')
                  }}
                </template>
                <template v-else>
                  {{ sourceVersion.version }} {{ sourceVersion.comment ? `(${sourceVersion.comment})` : '' }}
                </template>
              </span>
            </template>
            <span
              v-else
              class="title"
            >
              {{ t('暂无版本') }}
            </span>
          </div>
        </div>
        <div class="target-header">
          <div class="version">
            <BkSelect
              v-if="targetSwitch && pageType !== 'createVersion'"
              v-model="localTargetId"
              class="float-left mr-10px w-320px choose-version"
              :placeholder="t('请选择目标版本')"
              :clearable="false"
              :input-search="false"
              filterable
              @change="handleVersionChange"
            >
              <template #trigger>
                <span class="trigger-label">
                  {{ localTargetTriggerLabel }}
                  <AgIcon
                    name="down-shape"
                    class="trigger-label-icon"
                  />
                </span>
              </template>
              <BkOption
                v-for="option in localVersionList"
                :id="option.id"
                :key="option.id"
                :disabled="option.id === localSourceId"
                :name="option.resource_version_display"
              />
            </BkSelect>
            <span
              v-else
              class="title"
            >
              <template v-if="pageType !== 'createVersion'">
                <template v-if="pageType === 'publishEnvironment'">
                  {{ t('待发布（{version}）', { version: targetVersion.version }) }}
                </template>
                <template v-else>
                  {{ targetVersion.version }} {{ targetVersion.comment ? `(${targetVersion.comment})` : '' }}
                </template>
              </template>
              <template v-else>
                {{ t('当前最新资源列表') }}
              </template>
            </span>
          </div>
          <!-- <div class="marked">{{ t('目标版本') }}</div> -->
        </div>
        <button
          v-if="targetSwitch && sourceSwitch && localSourceId"
          class="switch-btn"
          @click="handleSwitch"
        >
          <AgIcon name="exchange-line" />
        </button>
      </div>

      <div class="diff-main">
        <BkLoading
          :loading="isDataLoading"
          color="#ffffff"
          :opacity="1"
          :z-index="1000"
          class="diff-loading"
        >
          <!-- 新增 -->
          <div
            v-for="addItem in filteredDiffData.add"
            :key="addItem.id"
            class="diff-item"
          >
            <div class="source-box">
              <div
                class="metadata pl-10px"
                @click="() => handleToggle(addItem)"
              >
                <AgIcon
                  v-if="!addItem.isExpanded"
                  name="right-shape"
                  class="expand-icon"
                />
                <AgIcon
                  v-else
                  name="down-shape"
                  class="expand-icon"
                />
                <span class="resource-title">--</span>
              </div>
              <div class="resource-box">
                <BkException
                  v-show="addItem.isExpanded"
                  class="exception-part"
                  type="empty"
                  scene="part"
                >
                  {{ t('此版本无该资源') }}
                </BkException>
              </div>
            </div>
            <div class="target-box">
              <div
                class="metadata success"
                @click="() => handleToggle(addItem)"
              >
                <AgIcon
                  v-if="!addItem.isExpanded"
                  name="right-shape"
                  class="expand-icon"
                />
                <AgIcon
                  v-else
                  name="down-shape"
                  class="expand-icon"
                />
                <span
                  v-bk-xss-html="renderTitle(addItem)"
                  class="resource-title"
                  :title="`【${addItem?.method}】${addItem?.path}`"
                />
              </div>
              <div class="resource-box">
                <ResourceDiffDetail
                  v-show="addItem.isExpanded"
                  :cur-resource="addItem"
                  :backends-list="backendsList"
                />
              </div>
            </div>
          </div>

          <!-- 删除 -->
          <div
            v-for="deleteItem in filteredDiffData.delete"
            :key="deleteItem.id"
            class="diff-item"
          >
            <div class="source-box">
              <div
                class="metadata"
                @click="() => handleToggle(deleteItem)"
              >
                <AgIcon
                  v-if="!deleteItem.isExpanded"
                  name="right-shape"
                  class="expand-icon"
                />
                <AgIcon
                  v-else
                  name="down-shape"
                  class="expand-icon"
                />
                <span
                  v-bk-xss-html="renderTitle(deleteItem)"
                  class="resource-title"
                  :title="`【${deleteItem?.method}】${deleteItem?.path}`"
                />
              </div>
              <div class="resource-box">
                <ResourceDiffDetail
                  v-show="deleteItem.isExpanded"
                  :cur-resource="deleteItem"
                  :backends-list="backendsList"
                />
              </div>
            </div>
            <div class="target-box">
              <div
                class="metadata danger"
                @click="() => handleToggle(deleteItem)"
              >
                <AgIcon
                  v-if="!deleteItem.isExpanded"
                  name="right-shape"
                  class="expand-icon"
                />
                <AgIcon
                  v-else
                  name="down-shape"
                  class="expand-icon"
                />
                <span
                  v-bk-xss-html="renderTitle(deleteItem)"
                  class="resource-title"
                  :title="`【${deleteItem?.method}】${deleteItem?.path}`"
                />
              </div>
              <div class="resource-box">
                <ResourceDiffDetail
                  v-show="deleteItem.isExpanded"
                  class="opacity-35"
                  :cur-resource="deleteItem"
                  :backends-list="backendsList"
                />
              </div>
            </div>
          </div>

          <!-- 更新 -->
          <div
            v-for="updateItem in filteredDiffData.update"
            :key="`${updateItem.source.id}:${updateItem.target.id}`"
            class="diff-item"
          >
            <div class="source-box">
              <div
                class="metadata"
                @click="() => handleToggle(updateItem)"
              >
                <AgIcon
                  v-if="!updateItem.isExpanded"
                  name="right-shape"
                  class="expand-icon"
                />
                <AgIcon
                  v-else
                  name="down-shape"
                  class="expand-icon"
                />
                <span
                  v-bk-xss-html="renderTitle(updateItem.source)"
                  class="resource-title"
                  :title="`【${updateItem?.source?.method}】${updateItem?.source?.path}`"
                />
              </div>
              <div class="resource-box">
                <ResourceDiffDetail
                  v-show="updateItem.isExpanded"
                  class="source-version"
                  :cur-resource="updateItem.source"
                  :backends-list="backendsList"
                  :diff-data="updateItem.target.diff"
                  :only-show-diff="searchParams.onlyUpdated"
                  is-source
                />
              </div>
            </div>
            <div class="target-box">
              <div
                class="metadata warning"
                @click="() => handleToggle(updateItem)"
              >
                <AgIcon
                  v-if="!updateItem.isExpanded"
                  name="right-shape"
                  class="expand-icon"
                />
                <AgIcon
                  v-else
                  name="down-shape"
                  class="expand-icon"
                />
                <span
                  v-bk-xss-html="renderTitle(updateItem.target)"
                  class="resource-title"
                  :title="`【${updateItem?.target?.method}】${updateItem?.target?.path}`"
                />
              </div>

              <div class="resource-box">
                <ResourceDiffDetail
                  v-show="updateItem.isExpanded"
                  :cur-resource="updateItem.target"
                  :backends-list="backendsList"
                  :diff-data="updateItem.source.diff"
                  :only-show-diff="searchParams.onlyUpdated"
                />
              </div>
            </div>
          </div>

          <template v-if="!hasResult && !isDataLoading">
            <!-- 无数据 -->
            <AgTableEmpty
              v-if="hasFilter"
              :empty-type="emptyType"
              :abnormal="false"
              @refresh="getDiffData"
              @clear-filter="handleClearFilterKey"
            />
            <BkException
              v-else
              class="mt-50px diff-tips"
              type="search-empty"
              scene="part"
            >
              {{
                !localTargetId
                  ? t('请选择目标版本')
                  : t('版本资源配置无差异')
              }}
            </BkException>
          </template>
        </BkLoading>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Spinner } from 'bkui-vue/lib/icon';
import AgTableEmpty from '@/components/base/ag-table-empty/Index.vue';
import { getBackendServiceList } from '@/services/source/gateway/backend';
import { getLabelList } from '@/services/source/gateway/label';
import { getVersionDiff, getVersionList } from '@/services/source/gateway/resource-version';
import type { IBackendListOutput } from '@/services/types/gateway/backend.ts';
import type { IResourceVersionDiffResource } from '@/services/types/gateway/resource-version';
import { useGateway } from '@/stores';
import type { ITableEmptyType } from '@/types/common';
import type { IDiffData, IVersionItem } from '@/types/resource-version';
import ResourceDiffDetail from './components/ResourceDiffDetail.vue';
import { type ResourceDiffType, filterDiffData } from './resource-diff';

interface IProps {
  versionList?: IVersionItem[]
  sourceId?: number | string
  targetId?: number | string
  sourceSwitch?: boolean
  targetSwitch?: boolean
  curDiffEnabled?: boolean
  /** 业务场景：createVersion（生成资源版本）/ publishEnvironment（发布到环境） */
  pageType?: string
}

interface ILocalVersionItem extends IVersionItem {
  name?: string
  resource_version_display?: string
  stage_text?: string[]
}

/** 列表条目（新增 / 更新 / 删除）的联合类型，均带有展开状态 */
type DiffListItem = IDiffData['add'][number] | IDiffData['update'][number] | IDiffData['delete'][number];

const {
  versionList = [],
  sourceId = '',
  targetId = '',
  sourceSwitch = true,
  targetSwitch = true,
  curDiffEnabled = true,
  pageType = '',
} = defineProps<IProps>();

const gatewayStore = useGateway();
const { t } = useI18n();
const route = useRoute();

/** HTTP 请求方法对应的标签样式类 */
const HTTP_METHOD_TAG_CLASS: Record<string, string> = {
  POST: 'bk-tag-info',
  GET: 'bk-tag-success',
  DELETE: 'bk-tag-danger',
  PUT: 'bk-tag-warning',
  PATCH: 'bk-tag-info',
  ANY: 'bk-tag-success',
};

const EMPTY_VERSION = {
  id: '',
  comment: '',
  version: '',
};

const isDataLoading = ref(false);
const localSourceId = ref(sourceId);
const localTargetId = ref(targetId || 'current');
const localVersionList = ref<Partial<ILocalVersionItem>[]>(versionList);
const backendsList = ref<IBackendListOutput[]>([]);
const diffData = reactive<IDiffData>({
  add: [],
  delete: [],
  update: [],
});
// 回车确认后生效的搜索词，与输入框草稿值 searchParams.keyword 区分
const appliedKeyword = ref('');
const searchParams = reactive<{
  keyword: string
  diffType: ResourceDiffType | ''
  onlyUpdated: boolean
  hideOnlyDiffInDocUpdatedTime: boolean
}>({
  keyword: '',
  diffType: '',
  onlyUpdated: false,
  // 是否隐藏仅存在文档更新的资源，默认展示
  hideOnlyDiffInDocUpdatedTime: false,
});
const diffTypeList = reactive<{
  id: ResourceDiffType
  name: string
}[]>([
  {
    id: 'add',
    name: t('新增'),
  },
  {
    id: 'delete',
    name: t('删除'),
  },
  {
    id: 'update',
    name: t('更新'),
  },
]);

// 递增请求序号：标识最新一次版本对比请求，用于丢弃过期响应并避免旧请求误关 loading
let latestDiffRequestId = 0;

// 当前网关 ID
const apigwId = computed(() => +route.params.id);

// 筛选结果同时用于列表渲染和空状态判断，避免两处重复过滤或结果不一致
const filteredDiffData = computed(() => filterDiffData(diffData, {
  keyword: appliedKeyword.value,
  diffType: searchParams.diffType,
  hideOnlyDiffInDocUpdatedTime: searchParams.hideOnlyDiffInDocUpdatedTime,
}));

const hasResult = computed(() =>
  Object.values(filteredDiffData.value).some(items => items.length > 0) || isDataLoading.value,
);

const hasFilter = computed(() =>
  Boolean(appliedKeyword.value || searchParams.diffType || searchParams.hideOnlyDiffInDocUpdatedTime),
);

// 空状态类型直接由筛选状态派生，避免回车搜索或切换筛选后未同步更新
const emptyType = computed<ITableEmptyType>(() =>
  (hasFilter.value && !hasResult.value ? 'searchEmpty' : 'empty'),
);

const sourceVersion = computed(() =>
  localVersionList.value.find(item => item.id === localSourceId.value) ?? EMPTY_VERSION,
);

const targetVersion = computed(() =>
  localVersionList.value.find(item => item.id === localTargetId.value) ?? EMPTY_VERSION,
);

// 下拉触发器文案按数值 ID 匹配：'current' 转为 NaN 不命中，自动回落为「当前最新资源列表」
const localSourceTriggerLabel = computed(() => {
  const match = localVersionList.value.find(item => Number(item.id) === Number(localSourceId.value));
  return match ? match.resource_version_display : t('当前最新资源列表');
});

const localTargetTriggerLabel = computed(() => {
  const match = localVersionList.value.find(item => Number(item.id) === Number(localTargetId.value));
  return match ? match.resource_version_display : t('当前最新资源列表');
});

watch(
  () => [sourceId, targetId],
  async ([nextSourceId, nextTargetId]) => {
    localSourceId.value = nextSourceId;
    localTargetId.value = nextTargetId || 'current';
    await getDiffData();
  },
);

/** 转义正则元字符，避免搜索路径含 `[`、`(`、`+` 等符号时触发 RegExp 语法异常 */
const escapeRegExp = (text: string) => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const handleToggle = (item: DiffListItem) => {
  item.isExpanded = !item.isExpanded;
};

const handleSearch = (keyword?: string) => {
  appliedKeyword.value = keyword || '';
};

const handleClear = () => {
  appliedKeyword.value = '';
};

const handleSwitch = async () => {
  [localSourceId.value, localTargetId.value] = [
    localTargetId.value,
    localSourceId.value,
  ];
  await getDiffData();
};

/** 渲染单条资源头部（方法标签 + 路径），命中搜索词时高亮关键词 */
const renderTitle = (item: Pick<IResourceVersionDiffResource, 'method' | 'path'>) => {
  // 先根据原始请求方法确定标签颜色，再做关键词高亮，避免 HTML 标签破坏方法匹配
  const tagClass = HTTP_METHOD_TAG_CLASS[item.method] ?? 'bk-tag-info';
  let { method, path } = item;

  if (appliedKeyword.value) {
    const keywordReg = new RegExp(`(${escapeRegExp(appliedKeyword.value)})`, 'ig');
    method = method.replace(keywordReg, '<i class="keyword font-bold color-#3a84ff">$1</i>');
    path = path.replace(keywordReg, '<i class="keyword font-bold color-#3a84ff">$1</i>');
  }

  return `<div class="bk-tag ${tagClass} bk-tag--default" style="border-radius: 2px;margin-right: 4px;">`
    + `<span class="bk-tag-text">${method}</span>`
    + `</div><span class="title-content">${path}</span>`;
};

const resetFilters = (includeOnlyUpdated = false) => {
  searchParams.keyword = '';
  searchParams.diffType = '';
  searchParams.hideOnlyDiffInDocUpdatedTime = false;
  if (includeOnlyUpdated) {
    searchParams.onlyUpdated = false;
  }
  appliedKeyword.value = '';
};

const handleClearFilterKey = async () => {
  resetFilters();
  await getDiffData();
};

const handleVersionChange = async () => {
  resetFilters(true);
  await getDiffData();
};

const getDiffData = async () => {
  // 每次触发均递增序号，确保切换版本时立即发起新查询且正在飞行的旧请求自然失效
  const requestId = ++latestDiffRequestId;

  diffData.add = [];
  diffData.delete = [];
  diffData.update = [];

  if (!localSourceId.value) {
    isDataLoading.value = false;
    return false;
  }

  isDataLoading.value = true;

  try {
    const res = await getVersionDiff(apigwId.value, {
      source_resource_version_id: String(localSourceId.value).replace('current', ''),
      target_resource_version_id: String(localTargetId.value).replace('current', ''),
    });

    // 若期间已发起新的对比请求，丢弃过期响应，避免旧结果覆盖最新选择
    if (requestId !== latestDiffRequestId) {
      return false;
    }

    Object.assign(diffData, {
      add: res.add.map(item => ({
        ...item,
        isExpanded: false,
      })),
      delete: res.delete.map(item => ({
        ...item,
        isExpanded: false,
      })),
      update: res.update.map(item => ({
        ...item,
        isExpanded: false,
      })),
    } satisfies IDiffData);
  }
  finally {
    // 仅由最新一次请求解除加载态，避免旧请求提前关闭新请求的 loading
    if (requestId === latestDiffRequestId) {
      isDataLoading.value = false;
    }
  }
};

const getApigwVersions = async () => {
  const response = await getVersionList(apigwId.value, {
    limit: 1000,
    offset: 0,
  });

  if (curDiffEnabled) {
    localVersionList.value = [
      {
        id: 'current',
        name: t('当前最新资源列表'),
        resource_version_display: t('当前最新资源列表'),
      },
      ...response.results.map(item => ({
        ...item,
        resource_version_display: item.comment ? `${item.version}(${item.comment})` : item.version,
        stage_text: item.released_stages.map(stage => stage.name),
      })),
    ];
  }
  else {
    localVersionList.value = response.results;
  }
};

const getLabels = async () => {
  const res = await getLabelList(apigwId.value);
  gatewayStore.setGatewayLabels(res);
};

// 后端服务列表
const getBackendsList = async () => {
  const res = await getBackendServiceList(apigwId.value);
  backendsList.value = res.results || [];
};

const init = async () => {
  await Promise.all([
    getDiffData(),
    getApigwVersions(),
    getLabels(),
    getBackendsList(),
  ]);
};

onMounted(() => {
  init();
});

onUnmounted(() => {
  // 组件卸载时使飞行中的请求失效，避免异步回调继续修改状态
  latestDiffRequestId += 1;
});
</script>

<style lang="scss" scoped>
.summary-data {
  height: 40px;
  padding: 0 16px;
  margin-bottom: 15px;
  font-size: 14px;
  line-height: 40px;
  color: #63656e;
  background-color: #f5f7fa;
}

.tag-list {
  display: flex;
  float: right;
  height: 32px;
  line-height: 32px;
  align-items: center;

  .legend-group {
    display: flex;
    align-items: center;
    margin-left: 10px;
    font-size: 13px;
    color: #63656e;

    .tag {
      width: 10px;
      height: 10px;
      margin-right: 5px;

      &.success {
        background: #dcffe2;
        border: 1px solid #94f5a4;
      }

      &.danger {
        background: #ffe9e8;
        border: 1px solid #ffbdbd;
      }

      &.warning {
        background: #ffefd6;
        border: 1px solid #ffe3b5;
      }
    }
  }
}

.diff-wrapper {
  position: relative;
  min-height: 300px;
  border: 1px solid #dcdee5;
  border-radius: 2px;

  &.no-result {

    &::after {
      display: none;
    }
  }

  &::after {
    position: absolute;
    top: 0;
    left: 50%;
    z-index: 100;
    display: inline-block;
    width: 1px;
    height: 100%;
    margin-left: -1px;
    background: #dbdee4;
    content: "";
  }
}

.diff-main {
  max-height: calc(100vh - 362px);
  min-height: 300px;
  overflow: hidden auto;

  .diff-loading {
    min-height: 300px;
    padding: 6px 0;
  }
}

.diff-item {
  display: flex;

  .source-box,
  .target-box {
    width: 50%;
    padding: 6px 12px;

    .metadata {
      position: relative;
      height: 36px;
      padding-left: 10px;

      // border: 1px solid #f0f1f5;
      font-size: 12px;
      font-weight: bold;
      line-height: 36px;
      color: #63656e;
      cursor: pointer;
      background: #f0f1f5;
      border-radius: 2px;

      .expand-icon {
        position: absolute;
        top: 12px;
        z-index: 1;
        color: #979ba5;
      }

      .resource-title {
        position: relative;
        display: inline-block;
        width: 96%;
        max-width: 550px;
        margin-left: 18px;
        overflow: hidden;
        font-weight: 700;
        text-overflow: ellipsis;
        white-space: nowrap;

        :deep(.bk-tag-text) {
          font-weight: 400;
        }
      }

      // .bk-icon {
      //   display: inline-block;
      //   transform-origin: center;
      //   transition: all ease 0.3s;

      //   &.active {
      //     transform: rotate(90deg);
      //   }
      // }

      &.danger {
        background: #fef2f2;

        // border-color: #fe9c9c;

        .resource-title {
          color: #ea3636;

          :deep(.title-content) {
            text-decoration: line-through;
          }
        }
      }

      &.success {
        background: #f0fcf4;

        // border-color: #94f5a4;

        .resource-title {
          color: #2dcb56;
        }
      }

      &.warning {
        background: #fff9ef;

        // border-color: #ffd694;

        .resource-title {
          color: #ff9c01;
        }
      }
    }
  }

  .resource-box {
    position: relative;
    height: calc(100% - 36px);
    padding-inline: 15px;

    .exception-part {
      position: absolute;
      top: calc(50% - 40px);
      left: 0;
      transform: translateY(-50%);
    }
  }

  .delete-icon {
    position: absolute;
    top: 20px;
    right: 20px;
    z-index: 10;
    width: 68px;
    height: 68px;
  }
}

.diff-header {
  position: relative;
  display: flex;

  .switch-btn {
    position: absolute;
    top: 50%;
    left: 50%;
    z-index: 110;
    width: 27px;
    height: 27px;
    color: #63656e;
    background: #fff;
    border: none;
    border-radius: 50%;
    transform: translateY(-50%) translateX(-50%);
    box-shadow: 0 2px 4px 0 rgb(0 0 0 / 10%);

    &:hover {
      color: #3a84ff;
    }

    i {
      display: inline-block;
      margin-top: -4px;
      vertical-align: middle;
    }
  }

  .source-header,
  .target-header {
    display: flex;
    width: 50%;
    height: 42px;
    line-height: 42px;
    background-color: #f0f1f5;

    .choose-version {
      width: 320px;
      cursor: pointer;

      :deep(.bk-select-trigger) {
        display: flex;
        align-items: center;
        justify-content: center;
      }

      .trigger-label {
        position: relative;
        display: inline-block;
        max-width: 180px;
        margin-right: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      // .trigger-label-icon {
      //   position: absolute;
      //   top: 15px;
      //   right: 0;
      // }
    }

    .marked {
      width: 130px;
      font-size: 13px;
      color: #63656e;
      text-align: center;
    }

    .version {
      position: relative;
      text-align: center;
      flex: 1;
    }

    .title {
      font-size: 13px;
      font-weight: 700;
      color: #63656e;
      text-align: center;
      flex: 1;
    }
  }

  .source-header {
    background-color: #f5f7fa;
    border-right: 1px solid #dcdee5;
    border-bottom: 1px solid #dcdee5;

    .marked {
      border-right: 1px solid #dcdee5;
    }
  }

  .target-header {
    background-color: #f0f1f5;

    // border-left: 1px solid #dcdee5;
    border-bottom: 1px solid #dcdee5;

    .marked {
      border-left: 1px solid #dcdee5;
    }
  }
}
</style>

<!-- eslint-disable-next-line vue/enforce-style-attribute -- 跨子组件共享版本差异选择器与提示样式 -->
<style lang="scss">
.version {

  .bk-select {
    position: absolute;
    left: 50%;
    font-size: 13px;
    font-weight: 700;
    color: #63656e;
    border: none;
    transform: translateX(-50%);

    &.is-default-trigger.is-unselected::before {
      width: 280px;
      font-size: 13px;
      font-weight: 700;
      color: #63656e;
      text-align: center;
    }

    .bk-input {
      border: none;
    }

    .bk-input--text {
      background: transparent;
    }

    .bk-input--text::placeholder {
      font-size: 13px;
      font-weight: 700;
      color: #63656e;
      text-align: center;
    }

    &.is-focus .bk-input--default {
      box-shadow: none;
    }
  }
}

.diff-tips {
  color: #63656E;
}
</style>
