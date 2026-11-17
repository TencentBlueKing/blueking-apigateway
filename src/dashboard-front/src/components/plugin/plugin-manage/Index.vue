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
  <div class="plugin-container">
    <BkLoading :loading="isBindingListLoading">
      <!-- 默认展示 -->
      <template v-if="curBindingPlugins.length === 0">
        <BkException
          v-if="gatewayStore.currentGateway?.kind !== 1"
          :class="{ 'exception-gray': false }"
          class="exception-wrap-item"
          type="empty"
        >
          {{ t('尚未添加插件，') }}
          <BkButton
            v-bk-tooltips="{
              content: t('当前有版本正在发布，请稍后再操作'),
              disabled: !isStageReleasing
            }"
            :disabled="isStageReleasing"
            text
            theme="primary"
            @click="handlePluginAdd"
          >
            {{ t('立即添加') }}
          </BkButton>
        </BkException>
        <BkException
          v-else
          type="empty"
        >
          {{ t('尚未添加插件') }}
        </BkException>
      </template>
      <div
        v-else
        class="bindding-info p-10px"
      >
        <div class="pb-12px pl-12px">
          <BkAlert closable>
            {{ t('插件按优先级从高到低排序，多个插件优先级高的先执行。') }}
          </BkAlert>
        </div>
        <BkButton
          v-if="gatewayStore.currentGateway?.kind !== 1"
          v-bk-tooltips="{
            content: t('当前有版本正在发布，请稍后再操作'),
            disabled: !isStageReleasing
          }"
          :disabled="isStageReleasing"
          class="add-plugin-btn"
          theme="primary"
          @click="handlePluginAdd"
        >
          <AgIcon
            class="icon pr-10px text-12px"
            name="plus"
          />
          {{ t('添加插件') }}
        </BkButton>
        <BkCollapse
          v-model="activeIndex"
          header-icon="right-shape"
          :list="curBindingPlugins"
          class="binding-plugins mt-20px"
        >
          <template #title="slotProps">
            <span class="text-15px">
              {{ slotProps.name }}
              <template v-if="gatewayStore.currentGateway?.kind !== 1">
                <AgIcon
                  v-bk-tooltips="{
                    content: t('当前有版本正在发布，请稍后再操作'),
                    disabled: !isStageReleasing
                  }"
                  class="mx-5px"
                  name="edit-line"
                  size="15"
                  @click.stop="() => handleEditPlugin(slotProps)"
                />
                <AgIcon
                  v-bk-tooltips="{
                    content: t('当前有版本正在发布，请稍后再操作'),
                    disabled: !isStageReleasing
                  }"
                  class="mx-5px"
                  name="delet"
                  size="15"
                  @click.stop="() => handleDeletePlugin(slotProps)"
                />
              </template>
            </span>
          </template>
          <template #content="slotProps">
            <div>
              <ConfigDisplayTable :plugin="slotProps" />
            </div>
          </template>
        </BkCollapse>
      </div>
    </BkLoading>

    <!-- 添加插件 -->
    <BkSideslider
      v-model:is-show="isVisible"
      :title="t('添加插件')"
      ext-cls="plugin-management-slider"
      quick-close
      :width="pluginSliderWidth"
      @closed="handleClosePluginSlider"
    >
      <template #default>
        <div class="plugin-wizard">
          <div class="plugin-steps-header">
            <BkSteps
              :cur-step="state.curStep"
              :steps="pluginSteps"
              controllable
              class="plugin-steps"
              @click="stepChanged"
            />
          </div>
          <!-- 选择插件 -->
          <div
            v-if="state.curStep === 1"
            class="plugins"
          >
            <BkAlert
              class="plugin-priority-alert"
              closable
            >
              {{ t('插件按优先级从高到低排序，多个插件优先级高的先执行。') }}
            </BkAlert>
            <div class="plugin-filter">
              <div class="plugin-filter-heading">
                <div class="plugin-filter-tags">
                  <span class="plugin-filter-label">
                    {{ t('全部分类') }}
                  </span>
                  <BkButton
                    v-for="tag in pluginTags"
                    :key="tag"
                    class="plugin-filter-tag"
                    :class="{ 'is-active': selectedTag === tag }"
                    :aria-pressed="selectedTag === tag"
                    text
                    @click="() => handleTagClick(tag)"
                  >
                    {{ tag }}
                  </BkButton>
                </div>
                <BkButton
                  text
                  theme="primary"
                  @click="handleClearFilterKey"
                >
                  {{ t('清空选项') }}
                </BkButton>
              </div>
              <BkInput
                v-model="searchValue"
                class="plugin-search-input"
                clearable
                type="search"
                :placeholder="t('请输入插件关键字，按Enter搜索')"
                @enter="handleSearch"
                @search="handleSearch"
                @clear="handleSearch"
              />
            </div>
            <BkLoading :loading="isPluginListLoading">
              <div class="plugin-list">
                <div
                  v-for="item in pluginList"
                  :key="item.id"
                  class="plugin-card"
                  :class="{
                    'is-bound': isBound(item),
                    'is-selected': curChooseCode === item.code
                  }"
                  @click="() => handleChoosePlugin(item)"
                >
                  <PluginIcon :code="item.code || item.type" />
                  <div class="plugin-card-content">
                    <div class="plugin-card-heading">
                      <span
                        v-if="isBound(item)"
                        v-bk-tooltips="t('插件已添加，不能再选择')"
                        class="plugin-name"
                      >
                        {{ item.name }}
                      </span>
                      <BkButton
                        v-else
                        class="plugin-name"
                        text
                        :aria-pressed="curChooseCode === item.code"
                        @click.stop="() => handleChoosePlugin(item)"
                      >
                        {{ item.name }}
                      </BkButton>
                      <ul class="binding-list">
                        <li>
                          {{ t('版本：') }} V1.0.0
                        </li>
                        <li>
                          {{ t('已绑环境：') }}
                          <BkPopover
                            placement="top"
                            theme="light"
                            width="220"
                            :disabled="item.related_scope_count.stage === 0"
                            @after-show="() => loadPluginBindings(item.code)"
                          >
                            <span :class="[item.related_scope_count.stage === 0 ? 'binding-empty' : 'binding-number',]">
                              {{ item.related_scope_count.stage }}
                            </span>
                            <template #content>
                              <BkLoading
                                class="bingding-scope"
                                :loading="pluginBindings.get(item.code)?.loading"
                              >
                                <p class="scope-header font-bold">
                                  {{ t('已绑环境') }}
                                </p>
                                <ul class="scope-list mt-10px">
                                  <li
                                    v-for="stageItem in pluginBindings.get(item.code)?.data?.stages"
                                    :key="stageItem.id"
                                    class="scope-li mb-5px"
                                    @mouseenter="handleScopeHover((stageItem.name))"
                                    @mouseleave="handleScopeLeave"
                                    @click="() => handleJumpStage(stageItem)"
                                  >
                                    {{ stageItem.name }}
                                    <AgIcon
                                      v-if="stageItem.name === curHover"
                                      class="icon ml-5px"
                                      name="jump"
                                    />
                                  </li>
                                </ul>
                              </BkLoading>
                            </template>
                          </BkPopover>
                        </li>
                        <li>
                          {{ t('已绑资源：') }}
                          <BkPopover
                            placement="top"
                            theme="light"
                            width="420"
                            :disabled="item.related_scope_count.resource === 0"
                            @after-show="() => loadPluginBindings(item.code)"
                          >
                            <span
                              :class="[item.related_scope_count.resource === 0 ? 'binding-empty' : 'binding-number',]"
                            >
                              {{ item.related_scope_count.resource }}
                            </span>
                            <template #content>
                              <BkLoading
                                class="bingding-scope"
                                :loading="pluginBindings.get(item.code)?.loading"
                              >
                                <p class="scope-header font-bold">
                                  {{ t('已绑资源') }}
                                </p>
                                <ul class="scope-list mt-10px ">
                                  <li
                                    v-for="resourceItem in pluginBindings.get(item.code)?.data?.resources"
                                    :key="resourceItem.id"
                                    class="scope-li mb-5px"
                                    @mouseenter="handleScopeHover((resourceItem.name))"
                                    @mouseleave="handleScopeLeave"
                                    @click="() => handleJumpResource(resourceItem)"
                                  >
                                    {{ resourceItem.name }}
                                    <AgIcon
                                      v-if="resourceItem.name === curHover"
                                      class="icon ml-5px"
                                      name="jump"
                                    />
                                  </li>
                                </ul>
                              </BkLoading>
                            </template>
                          </BkPopover>
                        </li>
                      </ul>
                      <span
                        v-if="isBound(item)"
                        class="plugin-bound-label"
                      >
                        {{ t('已添加') }}
                      </span>
                    </div>
                    <p
                      v-if="item.notes"
                      v-bk-tooltips="{
                        content: item.notes,
                        disabled: truncatedNotesId !== item.id,
                        extCls: 'plugin-notes-tooltip',
                      }"
                      class="plugin-notes"
                      @mouseenter="(event) => handleNotesHover(event, item.id)"
                      @mouseleave="truncatedNotesId = undefined"
                    >
                      {{ item.notes }}
                    </p>
                    <div
                      v-if="item.tags?.length"
                      class="plugin-card-tags"
                    >
                      <BkTag
                        v-for="tag in item.tags"
                        :key="tag"
                      >
                        {{ tag }}
                      </BkTag>
                    </div>
                  </div>
                  <div
                    v-show="curChooseCode === item.code"
                    class="plugin-selected-mark"
                    aria-hidden="true"
                  >
                    <AgIcon
                      class="choose-icon"
                      name="check-1"
                      size="26"
                    />
                  </div>
                </div>
              </div>
              <div
                v-if="!pluginList.length"
                class="mt-82px"
              >
                <AgTableEmpty
                  background="#f5f7fa"
                  :empty-type="tableEmptyConf.emptyType"
                  :abnormal="tableEmptyConf.isAbnormal"
                  @refresh="refreshPluginList"
                  @clear-filter="handleClearFilterKey"
                />
              </div>
            </BkLoading>
          </div>
          <!-- 配置插件 -->
          <PluginConfigEditor
            v-else
            ref="pluginEditorRef"
            v-model:show-example="isExampleVisible"
            class="plugin-wizard-editor"
            :cur-plugin="curChoosePlugin"
            :scope-info="curScopeInfo"
            :edit-plugin="curEditPlugin"
            :type="curType"
            :plugin-list="allPlugins"
            :binding-plugins="curBindingPlugins"
            @choose-plugin="handleChoosePlugin"
            @on-change="handleOperate"
          />
          <div
            v-if="state.curStep === 1"
            class="plugin-wizard-footer"
          >
            <BkButton
              theme="primary"
              :disabled="!curChoosePlugin"
              @click="handleNext"
            >
              {{ t('下一步') }}
            </BkButton>
            <BkButton @click="handleCancel">
              {{ t('取消') }}
            </BkButton>
          </div>
        </div>
      </template>
    </BkSideslider>

    <!-- 修改插件 -->
    <BkSideslider
      v-model:is-show="isEditVisible"
      :title="t('修改插件')"
      ext-cls="plugin-management-slider"
      quick-close
      :width="pluginSliderWidth"
      render-directive="if"
      @closed="handleClosePluginSlider"
    >
      <template #default>
        <div class="plugin-wizard">
          <PluginConfigEditor
            ref="pluginEditorRef"
            v-model:show-example="isExampleVisible"
            class="plugin-wizard-editor"
            :cur-plugin="curChoosePlugin"
            :scope-info="curScopeInfo"
            :edit-plugin="curEditPlugin"
            :type="curType"
            :plugin-list="allPlugins"
            @on-change="handleOperate"
          />
        </div>
      </template>
    </BkSideslider>
  </div>
</template>

<script setup lang="ts">
import PluginConfigEditor, { type IPluginInfoItem } from './config-editor/Index.vue';
import AgTableEmpty from '@/components/base/ag-table-empty/Index.vue';
import {
  InfoBox,
  Message,
} from 'bkui-vue';
import {
  useGateway,
  useStage,
} from '@/stores';
import {
  deletePluginConfig,
  getPluginBindingsList,
  getPluginConfig,
  getPluginListData,
  getPluginTags,
  getScopeBindingPluginList,
} from '@/services/source/gateway/plugin';
import ConfigDisplayTable from './config-display/Index.vue';
import PluginIcon from './components/PluginIcon.vue';
import type {
  IGatewaysPluginsListQuery,
  IPluginBindingListOutput,
  IPluginConfigRetrieveOutput,
  IPluginTypeListOutput,
  IScopePluginConfigListOutput,
} from '@/services/types/gateway/plugin.ts';
import type { ITableEmptyType } from '@/types/common';
import { getStageStatus } from '@/utils';
import { useRouteParams } from '@vueuse/router';
import { useWindowSize } from '@vueuse/core';

interface IProps {
  resourceId?: number
  stageId?: number
}

interface IPluginBindingsEntry {
  loading: boolean
  data?: IPluginBindingListOutput
}

type PluginListItem = IPluginTypeListOutput & { type?: string };

const {
  resourceId = 0,
  stageId = 0,
} = defineProps<IProps>();

const emit = defineEmits<{
  'on-jump': [id: number]
  'on-update-plugin': [void]
}>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const gatewayStore = useGateway();
const stageStore = useStage();
const { width: viewportWidth } = useWindowSize();
// 网关id
const gatewayId = useRouteParams('id', 0, { transform: Number });

const pluginEditorRef = ref<InstanceType<typeof PluginConfigEditor>>();
const scopeType = ref<IGatewaysPluginsListQuery['scope_type'] | ''>('');
const scopeId = ref(-1);
const isBindingListLoading = ref(false);
const isPluginListLoading = ref(false);
const isVisible = ref(false);
const curType = ref<'add' | 'edit'>('add');
const isEditVisible = ref(false);
const isAddSuccess = ref(false);
const searchValue = ref('');
const searchKeyword = ref('');
const pluginList = ref<PluginListItem[]>([]);
const allPlugins = ref<PluginListItem[]>([]);
const pluginTags = ref<string[]>([]);
const selectedTag = ref('');
const pluginBindings = shallowReactive(new Map<string, IPluginBindingsEntry>());
const truncatedNotesId = ref<number>();
const curHover = ref('');
const curBindingPlugins = ref<IScopePluginConfigListOutput[]>([]);
const curChoosePlugin = ref<IPluginInfoItem | null>(null);
const curChooseCode = ref('');
const curEditPlugin = ref<IPluginConfigRetrieveOutput | null>(null);
const curScopeInfo = reactive({
  scopeType: '',
  scopeId: -1,
  apigwId: -1,
});
const state = reactive({ curStep: 1 });
const tableEmptyConf = ref<{
  emptyType: ITableEmptyType
  isAbnormal: boolean
}>({
  emptyType: 'empty',
  isAbnormal: false,
});
// PluginConfigEditor 中的插件示例是否可见
const isExampleVisible = ref(false);

const activeIndex = ref<number[]>([]);

const pluginDeleting = ref(false);
let pluginListRequest = 0;

// 控制插件 slider 宽度，会在展示插件使用示例时变宽
const pluginSliderWidth = computed(() => Math.min(viewportWidth.value, isExampleVisible.value ? 1360 : 960));
const pluginSteps = computed(() => [
  { title: t('选择插件') },
  { title: t('配置插件') },
]);

// 仅"环境配置插件"需要校验是否存在正在发布中的版本；资源配置插件不做该校验
// 注意：stageData 来源于全局 store，可能残留其他网关/页面的环境数据，因此必须限定 scope 类型
const isStageReleasing = computed(() => {
  const stage = stageStore.curStageData;
  return scopeType.value === 'stage' && stage?.id != null && getStageStatus(stage) === 'doing';
});

const isBound = computed(() => {
  return function (obj: any) {
    return curBindingPlugins.value.some((item: { code: string }) => item.code === obj.code);
  };
});

watch(curBindingPlugins, () => {
  activeIndex.value = Object.keys(curBindingPlugins.value)?.map((item: string) => Number(item)) || [];
});

watch(
  [
    () => stageId,
    () => resourceId,
  ],
  () => {
    init();
  },
);

watch([selectedTag, searchKeyword], () => {
  refreshPluginList();
});

watch([isVisible, gatewayId], () => {
  pluginBindings.clear();
}, { flush: 'sync' });

// 监听是否成功添加
watch(
  () => isAddSuccess.value,
  (newVal: any) => {
    if (newVal) {
      init();
    }
  },
  { immediate: true },
);

const stepChanged = (index: number) => {
  if (index === 1) {
    state.curStep = index;
    isExampleVisible.value = false;
  }
  if (index === 2) {
    if (curChoosePlugin.value) {
      state.curStep = index;
    }
    else {
      Message({
        theme: 'warning',
        message: '请先勾选插件',
      });
    }
  }
};

const handleOperate = (operate: string) => {
  switch (operate) {
    case 'pre':
      stepChanged(1);
      break;
    case 'addCancel':
      resetData();
      break;
    case 'editCancel':
      isEditVisible.value = false;
      break;
    case 'addSuccess':
      resetData();
      isAddSuccess.value = true;
      emit('on-update-plugin');
      break;
    case 'editSuccess':
      getBindingDetails(true);
      isEditVisible.value = false;
      emit('on-update-plugin');
      break;
    default:
      break;
  }
};

const loadPluginBindings = async (code: string) => {
  if (!isVisible.value || !gatewayId.value || !code || pluginBindings.has(code)) {
    return;
  }
  const pending = { loading: true };
  pluginBindings.set(code, pending);
  try {
    const data = await getPluginBindingsList(gatewayId.value, code);
    // 关闭抽屉、切换网关或停用插件后，忽略失效请求的结果。
    if (pluginBindings.get(code) === pending) {
      pluginBindings.set(code, {
        loading: false,
        data,
      });
    }
  }
  catch {
    if (pluginBindings.get(code) === pending) {
      pluginBindings.delete(code);
    }
  }
};

const handleNotesHover = (event: MouseEvent, id: number) => {
  const notes = event.currentTarget as HTMLElement;
  truncatedNotesId.value = notes.scrollHeight > notes.clientHeight ? id : undefined;
};

// hover已绑stage或resource数量
const handleScopeHover = (name: string) => {
  curHover.value = name;
};

const handleScopeLeave = () => {
  curHover.value = '';
};

const handleClearFilterKey = () => {
  searchValue.value = '';
  searchKeyword.value = '';
  selectedTag.value = '';
};

// 编辑插件
const handleEditPlugin = async (item: any) => {
  if (isStageReleasing.value) {
    return;
  }
  curType.value = 'edit';
  await getBindingDetails(false);
  const { code, config_id } = item;
  const curEditItem = curBindingPlugins.value.find((pluginItem: { code: string }) => pluginItem.code === code);
  curEditPlugin.value = await getPluginConfig(
    gatewayId.value,
    scopeType.value,
    scopeId.value,
    code,
    config_id,
  );
  curChoosePlugin.value = curEditItem ?? null;
  isEditVisible.value = true;
};

// 删除插件
const handleDeletePlugin = (item: any) => {
  if (isStageReleasing.value) {
    return;
  }
  const { code, config_id } = item;
  InfoBox({
    title: t('确定停用插件？'),
    infoType: 'warning',
    subTitle: t('将删除相关配置，不可恢复，请确认是否删除'),
    confirmText: t('停用'),
    cancelText: t('取消'),
    onConfirm: async () => {
      if (pluginDeleting.value) {
        return;
      }
      pluginDeleting.value = true;
      const targetGatewayId = gatewayId.value;
      try {
        await deletePluginConfig(targetGatewayId, scopeType.value, scopeId.value, code, config_id);
        if (targetGatewayId === gatewayId.value) {
          pluginBindings.delete(code);
        }
        Message({
          message: t('停用成功'),
          theme: 'success',
          width: 'auto',
        });
        emit('on-update-plugin');
        init();
      }
      finally {
        setTimeout(() => {
          pluginDeleting.value = false;
        }, 300);
      }
    },
  });
};

// 跳转stage
const handleJumpStage = (item: any) => {
  const { name } = item;
  const isRouteStage = route.path.includes('stage');
  const query = { stage: name };
  if (isRouteStage) {
    router.push({ query });
  }
  else {
    router.push({
      name: 'apigwStagePluginManage',
      params: { id: gatewayId.value },
      query,
    });
  }
};

// 跳转resource
const handleJumpResource = (item: any) => {
  const { id } = item;
  const isRouteStage = route.path.includes('stage');
  if (isRouteStage) {
    router.push({
      name: 'ResourceSetting',
      params: { id: gatewayId.value },
    });
  }
  emit('on-jump', id);
};

function init() {
  const isStage = route.path.includes('stage');
  scopeType.value = isStage ? 'stage' : 'resource';
  scopeId.value = isStage ? stageId : resourceId;
  curScopeInfo.scopeType = scopeType.value;
  curScopeInfo.scopeId = scopeId.value;
  curScopeInfo.apigwId = gatewayId.value;
  allPlugins.value = [];
  pluginListRequest++;
  if (!scopeId.value) return;
  getBindingDetails(true);
  refreshPluginList();
}

const resetData = () => {
  curChoosePlugin.value = null;
  isVisible.value = false;
  state.curStep = 1;
  isExampleVisible.value = false;
  handleClearFilterKey();
  curChooseCode.value = '';
};

// 获取已绑定插件列表
async function getBindingDetails(isLoading = false) {
  try {
    isBindingListLoading.value = isLoading;
    // 当前环境或资源绑定的插件
    curBindingPlugins.value = await getScopeBindingPluginList(gatewayId.value, scopeType.value, scopeId.value);
  }
  finally {
    isBindingListLoading.value = false;
  }
}

// 获取可配置的插件列表
const refreshPluginList = async () => {
  const currentScopeType = scopeType.value;
  if (scopeId.value <= 0 || !currentScopeType) {
    return;
  }
  const request = ++pluginListRequest;
  const params: IGatewaysPluginsListQuery = {
    scope_type: currentScopeType,
    scope_id: scopeId.value,
    keyword: searchKeyword.value || undefined,
    tag: selectedTag.value || undefined,
  };
  const isFiltered = !!(params.keyword || params.tag);
  try {
    isPluginListLoading.value = true;
    const [pluginRes, tagRes, allPluginRes] = await Promise.all([
      getPluginListData(gatewayId.value, params),
      getPluginTags(gatewayId.value),
      isFiltered && !allPlugins.value.length
        ? getPluginListData(gatewayId.value, {
          scope_type: params.scope_type,
          scope_id: params.scope_id,
        })
        : undefined,
    ]);
    if (request !== pluginListRequest) {
      return;
    }
    pluginList.value = pluginRes.results || [];
    if (!isFiltered || allPluginRes) {
      allPlugins.value = (allPluginRes ?? pluginRes).results || [];
    }
    pluginTags.value = tagRes.tags || [];
    tableEmptyConf.value = {
      emptyType: isFiltered ? 'search-empty' : 'empty',
      isAbnormal: false,
    };
  }
  catch {
    if (request === pluginListRequest) {
      pluginList.value = [];
      tableEmptyConf.value.isAbnormal = true;
    }
  }
  finally {
    if (request === pluginListRequest) {
      isPluginListLoading.value = false;
    }
  }
};

// 立即添加
const handlePluginAdd = () => {
  resetData();
  curType.value = 'add';
  isVisible.value = true;
  isAddSuccess.value = false;
};

// 选择插件
const handleChoosePlugin = (obj: IPluginInfoItem) => {
  const flag = curBindingPlugins.value.some((item: { code: string }) => item.code === obj.code);
  if (flag) {
    return;
  }
  curChooseCode.value = obj.code;
  curChoosePlugin.value = obj;
};

// enter搜索
const handleSearch = () => {
  const keyword = searchValue.value.trim();
  if (searchKeyword.value === keyword) {
    refreshPluginList();
    return;
  }
  searchKeyword.value = keyword;
};

// 下一页
const handleNext = () => {
  state.curStep = 2;
};

// 取消添加
const handleCancel = () => {
  resetData();
};

const handleClosePluginSlider = () => {
  isExampleVisible.value = false;
  pluginEditorRef.value?.clearValidate();
};

const handleTagClick = (tag: string) => {
  if (selectedTag.value === tag) {
    selectedTag.value = '';
    return;
  }
  selectedTag.value = tag;
};

init();

</script>

<style lang="scss" scoped>
.plugin-container {
  overflow-y: auto;

  :deep(.bk-exception-page) {
    height: 420px;
    justify-content: center;

    .bk-exception-img {
      width: 220px;
      height: 130px;
    }

    .bk-exception-footer {
      margin-top: 0;
    }
  }
}

.plugin-management-slider {

  :deep(> .bk-modal-wrapper > .bk-modal-body) {
    display: flex;
    flex-direction: column;
  }

  :deep(> .bk-modal-wrapper > .bk-modal-body > .bk-modal-content) {
    // 让 BKUI 的内联包装层参与 Flex 布局，消除行盒底部的基线间距。
    display: flex;
    min-height: 0;

    // 列表、表单和示例各自滚动，覆盖 BKUI 在外层设置的内联样式。
    overflow: visible !important;
    flex: 1;
    scrollbar-gutter: auto !important;

    .bk-sideslider-content {
      height: 100%;
    }
  }
}

.plugin-wizard {
  display: flex;
  height: 100%;
  min-height: 0;
  flex-direction: column;
}

.plugin-steps-header {
  z-index: 1;
  display: grid;
  min-height: 52px;
  padding: 13px 24px;
  background-color: #fff;
  border-bottom: 1px solid #eaebf0;
  box-shadow: 0 2px 4px #1919290a;
  flex: none;
  place-items: center;
}

.plugin-steps {
  width: min(400px, 100%);

  :deep(.bk-step:not(:last-child) .bk-step-title::after) {
    background-color: #3a84ff;
    background-image: none;
  }

  :deep(.bk-step:not(.current, .done) .bk-step-indicator) {
    color: #63656e;
    background-color: #eaebf0;
    border-color: #eaebf0;
  }

  :deep(.bk-step.done .bk-step-indicator) {
    color: #3a84ff;
    background-color: #e1ecff;
    border-color: #e1ecff;
  }
}

.plugins {
  min-height: 0;
  padding: 16px 24px 24px;
  overflow-y: auto;
  background-color: #f5f7fa;
  flex: 1;
}

.plugin-wizard-editor {
  min-height: 0;
  flex: 1;
}

.plugin-wizard-footer {
  display: flex;
  min-height: 48px;
  padding: 8px 24px;
  background-color: #fafbfd;
  border-top: 1px solid #eaebf0;
  align-items: center;
  flex: none;
  gap: 8px;

  .bk-button {
    min-width: 88px;
  }
}

.plugin-priority-alert {
  font-size: 14px;
  background-color: #f0f5ff;
  box-shadow: 0 2px 4px #1919290d;

  :deep(.bk-alert-wraper) {
    padding: 12px;
  }
}

.plugin-filter {
  padding: 16px;
  margin: 16px 0;
  background-color: #fff;
  border-radius: 2px;
}

.plugin-filter-heading,
.plugin-filter-tags,
.plugin-card-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.plugin-filter-heading {
  margin-bottom: 8px;
  justify-content: space-between;

  > .bk-button {
    font-size: 12px;
  }
}

.plugin-search-input {
  border-radius: 3px;

  :deep(.bk-input--suffix-icon) {
    font-size: 16px;
    color: #979ba5;
  }
}

.plugin-filter-label {
  margin-right: 4px;
  font-size: 12px;
  color: #313238;
}

.plugin-filter-tag.bk-button {
  height: 18px;
  padding: 0 8px;
  font-size: 12px;
  line-height: 18px;
  color: #63656e;
  background-color: #eaebf0;
  border-radius: 2px;

  &:hover,
  &.is-active {
    color: #1768ef;
    background-color: #e1ecff;
  }
}

.plugin-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.plugin-card {
  position: relative;
  display: flex;
  padding: 16px;
  cursor: pointer;
  background-color: #fff;
  border: 1px solid transparent;
  border-radius: 2px;
  box-shadow: 0 2px 4px #1919290d;
  align-items: flex-start;
  gap: 16px;

  &:hover:not(.is-bound),
  &:focus-within:not(.is-bound) {
    background-color: #fafbfd;
    border-color: #a3c5fd;
  }

  &.is-selected:not(.is-bound) {
    background-color: #f0f5ff;
    border-color: #a3c5fd;
  }

  &.is-bound {
    cursor: not-allowed;
    background-color: #fafbfd;

    .plugin-card-content {
      opacity: 60%;
    }
  }
}

.plugin-card-content {
  min-width: 0;
  flex: 1;
}

.plugin-card-heading,
.binding-list {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.plugin-card-heading {
  min-height: 24px;
  gap: 4px 24px;

  .is-selected & {
    padding-right: 32px;
  }
}

.plugin-name,
.plugin-name.bk-button {
  height: auto;
  max-width: 100%;
  padding: 0;
  font-size: 14px;
  font-weight: 700;
  line-height: 24px;
  color: #313238;
  text-align: left;
  white-space: normal;
  overflow-wrap: anywhere;
}

.binding-list {
  margin: 0;
  font-size: 12px;
  line-height: 20px;
  color: #979ba5;
  gap: 0 16px;

  .binding-empty {
    color: #63656e;
  }

  .binding-number {
    color: #3a84ff;
  }
}

.plugin-bound-label {
  margin-left: auto;
  font-size: 12px;
  color: #979ba5;
}

.plugin-notes {
  display: -webkit-box;
  margin: 8px 0 0;
  overflow: hidden;
  font-size: 12px;
  line-height: 20px;
  color: #4d4f56;
  overflow-wrap: anywhere;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

:global(.bk-popper.plugin-notes-tooltip) {
  max-width: min(640px, calc(100vw - 32px));
  line-height: 20px;
  overflow-wrap: anywhere;
}

.plugin-card-tags {
  margin-top: 8px;

  :deep(.bk-tag) {
    height: 18px;
    margin: 0;
    line-height: 18px;
    background-color: #eaebf0;
  }
}

.plugin-selected-mark {
  position: absolute;
  top: -1px;
  right: -1px;
  width: 50px;
  height: 50px;
  color: #fff;
  pointer-events: none;
  background-color: #3a84ff;
  border-top-right-radius: 2px;
  clip-path: polygon(0 0, 100% 0, 100% 100%);

  .choose-icon {
    position: absolute;
    top: 3px;
    right: 3px;
  }
}

.bingding-scope {
  padding: 5px;

  .scope-list {
    margin-left: 17px;

    :deep(.scope-li) {
      list-style: disc !important;
      cursor: pointer;
    }

    .scope-li:hover {
      color: #4B85E5;
    }
  }
}

.bindding-info {
  min-height: 480px;

  .add-plugin-btn {
    margin-left: 12px;

    .icon-ag-plus {
      font-weight: 700;
    }
  }

}

.binding-plugins {

  .apigateway-icon:hover {
    color: #1768ef;
  }
}

:deep(.bk-collapse-icon-left) {

  .bk-collapse-icon {
    top: 15px;
    left: 16px;
  }

  .bk-collapse-item {
    margin-bottom: 5px;
  }
}

:deep(.bk-collapse-icon) {

  svg {
    font-size: 16px;
  }
}

:deep(.bk-collapse-header) {

  .bk-collapse-title {
    font-weight: 700;
  }
}

:deep(.bk-collapse-header):hover {
  background-color: #fff !important;
}

.form-key-cls {
  width: 170px;
  padding: 5px 0;
  font-size: 12px;
  color: #63656E;
  text-align: right;
}

.form-val-cls {
  font-size: 12px;
  color: #313238;
}
</style>
