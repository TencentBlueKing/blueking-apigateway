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
  <BkSideslider
    v-model:is-show="isShow"
    :title="sliderTitle"
    :width="1280"
    class="create-mcp-slider"
    :class="[
      {
        'enabled-oauth2-public-client': isExistOAuthData,
        'app-auth-mcp-slider': isEnabledOAuth && appAuthStatusList.length > 0
      }
    ]"
    quick-close
    :before-close="handleBeforeClose"
    @hidden="handleCancel"
  >
    <template #default>
      <div class="slider-content">
        <div class="main">
          <BkAlert
            v-if="noValidStage"
            class="mb-24px"
            theme="warning"
          >
            {{ t('没有可用的环境') }}
          </BkAlert>
          <BkForm
            ref="formRef"
            :model="formData"
            form-type="vertical"
          >
            <!-- 基础表单组件 -->
            <div class="bg-white p-16px pb-24px mb-24px server-basic-form">
              <ServerBasicForm
                ref="serverBasicFormRef"
                v-model:form-data="formData"
                :stage-list="stageList"
                :no-valid-stage="noValidStage"
                :is-edit-mode="isEditMode"
                :categories-list="categoriesList"
                @stage-change="handleStageSelectChange"
              />
            </div>
            <div class="bg-white p-16px mb-24px">
              <OAuthSwitcher
                v-model:form-data="formData"
                @oauth-change="handleOAuthChange"
              />
              <!-- 资源选择表格 -->
              <BkFormItem :class="`resource-table-form-item ${activeTab}`">
                <template #label>
                  <div class="resource-form-item-label">
                    <div
                      v-for="item of resourceTabList"
                      :key="item.value"
                      class="label-text"
                      :class="{ 'is-active': activeTab === item.value }"
                      @click="handleMcpTypeChange(item.value)"
                    >
                      <span>{{ item.label }}</span>
                      <span
                        v-if="item.required"
                        class="required-mark"
                      >
                        *
                      </span>
                    </div>
                  </div>
                </template>
                <div
                  v-if="['tool'].includes(activeTab)"
                  class="flex items-center justify-between h-40px px-24px"
                >
                  <div class="resource-tips">
                    {{ t('请从已经发布到该环境的资源列表选取资源作为 MCP Server 的工具') }}
                  </div>
                  <BkButton
                    :disabled="noValidStage || !isCurrentStageValid"
                    text
                    theme="primary"
                    class="text-14px!"
                    @click="handleRefreshClick"
                  >
                    <AgIcon
                      class="mr-4px"
                      name="refresh-line"
                    />
                    {{ t('刷新') }}
                  </BkButton>
                </div>
                <div
                  ref="resourceRef"
                  class="resource-selector-wrapper"
                  :class="[{
                    'set-border': ['tool'].includes(activeTab)
                  }]"
                >
                  <div class="selector-main">
                    <BkResizeLayout
                      ref="resizeLayoutRef"
                      :max="resizeLayoutConfig.max"
                      :min="resizeLayoutConfig.min"
                      :initial-divide="`${resizeLayoutConfig.max}px`"
                      :border="false"
                      @resizing="handleResizeLayout"
                    >
                      <template #aside>
                        <div
                          v-if="['tool'].includes(activeTab)"
                          class="bg-white h-full px-24px pt-16px min-w-280px"
                        >
                          <div class="lh-22px color-#4d4f56 text-14px font-700 pb-16px">
                            {{ t('资源列表') }}
                          </div>
                          <div class="mb-16px">
                            <BkInput
                              v-model="filterKeyword"
                              :disabled="noValidStage"
                              type="search"
                            />
                          </div>
                          <BkLoading :loading="searchLoading">
                            <AgTable
                              ref="toolTableRef"
                              v-model:table-data="filteredToolList"
                              resizable
                              show-selection
                              local-page
                              :show-settings="false"
                              :show-first-full-row="toolSelections.length > 0"
                              :disabled-check-selection="toolDisabledSelection"
                              :columns="toolTableColumns"
                              :table-empty-type="toolTableEmptyType"
                              :filter-value="toolFilterData"
                              :row-class-name="handleSetToolRowClass"
                              @filter-change="handleToolFilterChange"
                              @clear-filter="handleToolClearFilter"
                              @clear-selection="handleToolClearSelection"
                              @selection-change="handleToolSelectionChange"
                              @page-change="renderPreviewViewWidth"
                            />
                          </BkLoading>
                        </div>
                        <template v-if="['prompt'].includes(activeTab)">
                          <BkResizeLayout
                            initial-divide="366px"
                            class="bg-white h-full!"
                            :border="false"
                          >
                            <template #aside>
                              <div class="p-16px">
                                <BkSearchSelect
                                  v-model="filterPromptValues"
                                  :data="filterPromptConditions"
                                  :placeholder="t('搜索中英文名、标签、内容、修改人')"
                                  :value-split-code="'+'"
                                  class="mb-16px"
                                  clearable
                                  unique-select
                                  value-behavior="need-key"
                                />
                                <BkLoading
                                  :loading="searchLoading"
                                  :z-index="99"
                                >
                                  <AgTable
                                    ref="promptTableRef"
                                    v-model:table-data="filteredPromptList"
                                    resizable
                                    local-page
                                    show-selection
                                    :show-settings="false"
                                    :show-first-full-row="promptSelections.length > 0"
                                    :row-class-name="handleSetPromptRowClass"
                                    :columns="promptTableColumns"
                                    :table-empty-type="promptTableEmptyType"
                                    @clear-filter="handlePromptClearFilter"
                                    @clear-selection="handlePromptClearSelection"
                                    @selection-change="handlePromptSelectionChange"
                                    @row-click="handlePromptRowClick"
                                    @page-change="renderPreviewViewWidth"
                                  />
                                </BkLoading>
                              </div>
                            </template>
                            <template #main>
                              <BkLoading :loading="promptDetailLoading">
                                <div class="mt-16px px-24px">
                                  <div
                                    v-if="Object.keys(curPromptData)?.length"
                                    class="p-16px pb-8px prompt-row-detail"
                                  >
                                    <div class="flex items-center gap-4px">
                                      <div class="max-w-85% min-w-0 flex text-14px font-700 color-#4d4f56">
                                        <div
                                          v-bk-tooltips="{
                                            placement:'top',
                                            content: `${curPromptData.name} (${curPromptData?.code})`,
                                            disabled: !isOverflow,
                                            extCls: 'max-w-794px',
                                          }"
                                          class="w-full truncate"
                                          @mouseenter="(e: MouseEvent) => handleMouseenter(e)"
                                          @mouseleave="handleMouseleave"
                                        >
                                          {{ curPromptData?.name ?? '--' }}
                                          <span
                                            class="ml-8px"
                                          >
                                            ({{ curPromptData?.code ?? '--' }})
                                          </span>
                                        </div>
                                      </div>
                                      <div class="flex items-center">
                                        <BkTag
                                          :theme="curPromptData?.is_public ? 'success' : 'warning'"
                                        >
                                          {{ curPromptData?.is_public ? t('公开') : t('私有') }}
                                        </BkTag>
                                        <BkTag
                                          v-if="curPromptData?.is_no_perm"
                                          class="ml-4px"
                                        >
                                          {{ t('无权限') }}
                                        </BkTag>
                                      </div>
                                    </div>
                                    <template v-if="!curPromptData.is_no_perm">
                                      <div class="mt-12px lh-22px text-14px">
                                        <code
                                          v-if="curPromptData?.content?.length"
                                          class="color-#4d4f56 break-all whitespace-pre-line font-unset"
                                        >
                                          {{ escapedCodeContent }}
                                        </code>
                                      </div>
                                      <div
                                        v-if="curPromptData?.labels?.length"
                                        class="mt-12px"
                                      >
                                        <BkTag
                                          v-for="label of curPromptData?.labels"
                                          :key="label"
                                          class="mr-4px mb-8px"
                                        >
                                          {{ label }}
                                        </BkTag>
                                      </div>
                                    </template>
                                  </div>
                                </div>
                              </BkLoading>
                            </template>
                          </BkResizeLayout>
                        </template>
                      </template>
                      <template #main>
                        <div
                          :style="{ width: resizePreviewWidth }"
                          class="px-24px py-16px result-preview"
                        >
                          <div class="flex-1">
                            <div class="header-title-wrapper">
                              <div class="font-bold color-#4d4f56 text-14px lh-22px">
                                {{ t('结果预览') }}
                              </div>
                              <BkButton
                                text
                                theme="primary"
                                :disabled="renderPreviewByTab.length < 1"
                                @click="handleClearSelections(activeTab)"
                              >
                                {{ t('清空') }}
                              </BkButton>
                            </div>
                            <div
                              v-if="renderPreviewByTab.length"
                              class="sticky top-0 result-preview-list"
                              :style="renderPreviewViewWidth()"
                            >
                              <div
                                v-for="(checks, index) in renderPreviewByTab"
                                :key="index"
                                class="list-main"
                              >
                                <div class="flex items-center justify-between list-item">
                                  <div class="w-92% flex items-center">
                                    <div
                                      v-bk-tooltips="{
                                        placement:'top',
                                        content: checks.tool_name || checks.name,
                                        disabled: !isOverflow
                                      }"
                                      class="min-w-20px color-#3a84ff text-12px truncate name"
                                      @mouseenter="(e: MouseEvent) => handleMouseenter(e)"
                                      @mouseleave="handleMouseleave"
                                    >
                                      {{ checks.tool_name || checks.name }}
                                    </div>
                                    <BkTag
                                      v-if="!['tool'].includes(checks.mode_type)"
                                      :theme="checks?.is_public ? 'success' : 'warning'"
                                      class="ml-4px"
                                    >
                                      {{ t(checks?.is_public ? '公开' : '私有') }}
                                    </BkTag>
                                    <template v-if="isEnabledOAuthTag(checks)">
                                      <BkTag
                                        v-if="renderOAuthConfig(checks)?.auth_verified_required"
                                        theme="info"
                                        class="ml-4px"
                                      >
                                        {{ t('用户态') }}
                                      </BkTag>
                                      <template v-if="renderOAuthConfig(checks)?.app_verified_required">
                                        <BkTag
                                          theme="warning"
                                          class="ml-4px"
                                        >
                                          {{ t('应用态') }}
                                        </BkTag>
                                        <BkTag
                                          theme="danger"
                                          class="ml-4px"
                                        >
                                          <template #icon>
                                            <AgIcon name="zhiming" />
                                          </template>
                                          {{ t('风险') }}
                                        </BkTag>
                                      </template>
                                    </template>
                                  </div>
                                  <AgIcon
                                    class="delete-icon"
                                    name="icon-close"
                                    size="20"
                                    @click="() => handleRemoveResource(checks)"
                                  />
                                </div>
                              </div>
                            </div>
                            <TableEmpty
                              v-else
                              class="h-[calc(100%-50px)]"
                            />
                          </div>
                        </div>
                      </template>
                    </BkResizeLayout>
                  </div>
                </div>
              </BkFormItem>
            </div>
          </BkForm>
        </div>
      </div>
    </template>
    <template #footer>
      <div
        ref="footerRef"
        class="w-full bg-white px-24px z-999 create-mcp-footer-wrapper"
      >
        <OAuthAlert
          v-if="isExistOAuthData"
          class="py-8px"
          :app-auth-status-list="appAuthStatusList"
        />
        <BkButton
          :disabled="noValidStage"
          class="min-w-88px"
          theme="primary"
          :loading="submitLoading"
          @click="handleSubmit"
        >
          {{ t(appAuthStatusList.length > 0 ? '已知晓风险并提交' : '确定') }}
        </BkButton>
        <BkButton
          class="min-w-88px ml-8px"
          @click="handleCancel"
        >
          {{ t('取消') }}
        </BkButton>
      </div>
    </template>
  </BkSideslider>
</template>

<script lang="tsx" setup>
import { cloneDeep, escape, uniq } from 'lodash-es';
import {
  Divider,
  Form,
  Input,
  Message,
  PopConfirm,
  ResizeLayout,
} from 'bkui-vue';
import type { PrimaryTableProps } from '@blueking/tdesign-ui';
import type { ISearchItem } from 'bkui-lib/search-select/utils';
import type { IFormMethod, ITableMethod } from '@/types/common';
import { getStageList } from '@/services/source/stage';
import { getVersionDetail } from '@/services/source/resource';
import { refDebounced } from '@vueuse/core';
import {
  type IMCPFormData,
  type IMCPServerCategory,
  type IMCPServerPrompt,
  type IMCPServerTool,
  createServer,
  getMcpCategoryList,
  getServer,
  getServerPrompts,
  getServerPromptsDetail,
  patchServer,
} from '@/services/source/mcp-server';
import { usePopInfoBox, useSidebar } from '@/hooks';
import { HTTP_METHODS } from '@/constants';
import {
  useFeatureFlag,
  useGateway,
} from '@/stores';
import i18n from '@/locales';
import ServerBasicForm from '@/views/mcp-server/components/ServerBasicForm.vue';
import OAuthSwitcher from '@/views/mcp-server/components/OAuthSwitcher.vue';
import OAuthAlert from '@/views/mcp-server/components/OAuthAlert.vue';
import TableEmpty from '@/components/table-empty/Index.vue';
import AgTable from '@/components/ag-table/Index.vue';

interface IProps { serverId?: number }

const { serverId = 0 } = defineProps<IProps>();

const emit = defineEmits<{ updated: [] }>();

const router = useRouter();
const gatewayStore = useGateway();
const featureFlagStore = useFeatureFlag();
const { initSidebarFormData, isSidebarClosed } = useSidebar();

const { t } = i18n.global;

let loadingTimer: NodeJS.Timeout | null = null;
// 持久化实例，仅创建一次
const resourceNameToIndexMap = new Map<string, number>();
const authorizedPromptIds = new Set<number>();

const footerRef = ref<InstanceType<typeof HTMLDivElement>>(null);
const resourceRef = ref<InstanceType<typeof HTMLDivElement>>(null);
const resizeLayoutRef = ref<InstanceType<typeof ResizeLayout>>(null);
const toolTableRef = ref<InstanceType<typeof AgTable> & ITableMethod>();
const promptTableRef = ref<InstanceType<typeof AgTable> & ITableMethod>();
const formRef = ref<InstanceType<typeof Form> & IFormMethod>();
const toolNameRef = ref<InstanceType<typeof Form> & IFormMethod>();
const popoverConfirmRef = ref<InstanceType<typeof PopConfirm>>();
const serverBasicFormRef = ref<InstanceType<typeof ServerBasicForm>>();
const defaultFormData = ref<IMCPFormData>({
  name: '',
  url: '',
  description: '',
  protocol_type: 'streamable_http',
  stage_id: 0,
  is_public: true,
  oauth2_public_client_enabled: false,
  labels: [],
  categories: [],
});
const formData = ref<IMCPFormData>(cloneDeep(defaultFormData.value));
const isShow = ref(false);
const submitLoading = ref(false);
const searchLoading = ref(false);
const promptDetailLoading = ref(false);
const isOverflow = ref(false);
const filterKeyword = ref('');
const activeTab = ref<'tool' | 'prompt'>('tool');
const promptTableEmptyType = ref<'empty' | 'search-empty'>('empty');
const resizePreviewWidth = ref('100%');
const stageList = ref([]);
const resourceList = ref([]);
const promptTableData = ref([]);
const curPromptData = ref({});
const toolSelections = ref([]);
const promptSelections = ref([]);
const allSelections = ref([]);
const noPermPrompt = ref([]);
const toolFilterData = ref({});
const promptLabels = ref([]);
const filterPromptValues = ref([]);
const categoriesList = ref<IMCPServerCategory[]>([]);

const customMethodsList = computed(() => {
  const methods = HTTP_METHODS.map(item => ({
    label: item.name,
    value: item.id,
  }));

  return [
    {
      label: 'All',
      checkAll: true,
    },
    ...methods,
  ];
});

const toolNameRowData = shallowRef({});
const resourceTabList = shallowRef<{
  label: string
  value: string
  required: boolean
}[]>([
  {
    label: t('工具'),
    value: 'tool',
    required: true,
  },
  {
    label: 'Prompt',
    value: 'prompt',
    required: false,
  },
]);
const toolTableColumns = shallowRef<PrimaryTableProps['columns']>([
  {
    title: t('资源名称'),
    colKey: 'name',
    ellipsis: true,
    cell: (_, { row }: { row: IMCPServerTool }) => {
      if (!row?.name) {
        return '--';
      }
      return (
        <div class="flex-row">
          <div
            v-bk-tooltips={{
              placement: 'top',
              content: row.name,
              disabled: !row.isOverflow,
              extCls: 'max-w-480px',
            }}
            class={[
              'truncate mr-4px',
              { 'color-#3a84ff cursor-pointer': gatewayStore.currentGateway?.kind === 0 },
              { 'color-#979ba5 hover:color-#3a84ff': !row.has_openapi_schema },
            ]}
            onMouseenter={e => toolTableRef.value?.handleCellEnter({
              e,
              row,
            })}
            onMouseLeave={e => toolTableRef.value?.handleCellLeave({
              e,
              row,
            })}
            onClick={() => handleToolNameClick(row)}
          >
            { row.name }
          </div>
        </div>
      );
    },
  },
  {
    title: t('工具名称'),
    colKey: 'tool_name',
    ellipsis: true,
    cell: (_, { row }: { row: IMCPServerTool }) => {
      row.tool_name = row.tool_name ?? row.name;
      if (!row.tool_name) {
        return '--';
      }
      return (
        <div class="flex-row items-center relative overflow-hidden tool-name">
          <div
            v-bk-tooltips={{
              placement: 'top',
              content: row.tool_name,
              disabled: !row.isOverflow,
              extCls: 'max-w-480px',
            }}
            class={[
              'truncate mr-4px',
              { 'cursor-pointer': gatewayStore.currentGateway?.kind === 0 },
              { 'color-#979ba5': !row.has_openapi_schema },
            ]}
            onMouseenter={(e: MouseEvent) => {
              toolTableRef.value?.handleCellEnter({
                e,
                row,
              });
            }}
            onMouseLeave={e => toolTableRef.value?.handleCellLeave({
              e,
              row,
            })}
          >
            { row.tool_name }
          </div>
          { row.has_openapi_schema && (
            <PopConfirm
              ref={popoverConfirmRef}
              trigger="manual"
              width="400"
              placement="right"
              extCls="tool-name-popover"
              is-show={toolNameRowData.value.id === row.id && toolNameRowData.value.isShow}
              onConfirm={() => handleConfirmToolName(row)}
              onCancel={() => handleCancelToolName(row)}
            >
              {{
                default: () => (
                  <AgIcon
                    name="edit-line"
                    class="hidden cursor-pointer vertical-mid tool-name-edit-icon"
                    onClick={(e: MouseEvent) => {
                      e?.stopPropagation();
                      handleEditToolName(row);
                    }}
                    v-clickOutSide={(e: MouseEvent) => handleClickOutSide(e)}
                  />
                ),
                content: () => (
                  <div class="w-full break-all tool-name-popover-content">
                    <span class="text-16px color-#313238">
                      <span class="min-w-64px lh-24px">
                        {t('工具名称')}
                      </span>
                      <Divider
                        direction="vertical"
                        type="solid"
                      />
                      <span class="text-14px color-#979ba5 lh-22px">
                        { t('资源名称：{value}', { value: row.tool_name }) }
                      </span>
                    </span>
                    <div class="mt-16px">
                      <Form
                        ref={toolNameRef}
                        form-type="vertical"
                        model={toolNameRowData.value}
                        rules={toolNameRules}
                      >
                        <Form.FormItem
                          label={t('工具名称')}
                          required={true}
                          property="tool_name"
                          class="tool-name-form-item"
                        >
                          <Input
                            v-model={toolNameRowData.value.tool_name}
                            placeholder={t('请输入工具名称')}
                            maxlength={128}
                            tooltipsOptions={{
                              content: () => (
                                <div>
                                  { t('长度限制：最多 128 个字符') }
                                  <br />
                                  { t('首尾字符：必须以字母或数字开头和结尾（a-z、A-Z、0-9）') }
                                  <br />
                                  { t('中间字符：允许字母、数字、连字符（-）、下划线（_）、点号（.）') }
                                </div>
                              ),
                              placement: 'right',
                              disabled: false,
                              allowHtml: true,
                            }}
                            autofocus={true}
                          />
                        </Form.FormItem>
                      </Form>
                    </div>
                  </div>
                ),
              }}
            </PopConfirm>
          )}
        </div>
      );
    },
  },
  {
    title: t('请求方法'),
    colKey: 'method',
    filter: {
      type: 'multiple',
      popupProps: {
        placement: 'bottom',
        attach: 'body',
      },
      showConfirmAndReset: true,
      resetValue: [],
      placements: ['right'],
      list: customMethodsList.value,
    },
    cell: (_, { row }: { row: IMCPServerTool }) => (
      <BkTag
        theme={methodTagThemeMap[row.method as keyof typeof methodTagThemeMap]}
      >
        {row.method}
      </BkTag>
    ),
  },
  {
    title: t('请求路径'),
    colKey: 'path',
    ellipsis: true,
  },
  {
    title: t('描述'),
    colKey: 'description',
    ellipsis: true,
  },
]);
const promptTableColumns = shallowRef<PrimaryTableProps['columns']>([
  {
    title: t('Prompt 名称'),
    colKey: 'name',
    cell: (_h, { row }: { row: IMCPServerPrompt }) => {
      if (!row?.name) {
        return '--';
      }
      return (
        <div class="flex-row">
          <div
            v-bk-tooltips={{
              content: row.name,
              placement: 'top',
              disabled: !row.isOverflow,
              extCls: 'max-w-480px',
            }}
            class="truncate color-#4d4f56 mr-4px prompt-name"
            onMouseenter={e => promptTableRef.value?.handleCellEnter({
              e,
              row,
            })}
            onMouseLeave={e => promptTableRef.value?.handleCellLeave({
              e,
              row,
            })}
          >
            { row.name }
          </div>
          <bk-tag theme={row.is_public ? 'success' : 'warning'}>
            { t(row.is_public ? '公开' : '私有') }
          </bk-tag>
          {row?.is_no_perm && (
            <bk-tag
              class="ml-4px"
            >
              { t('无权限') }
            </bk-tag>
          )}
        </div>
      );
    },
  },
]);
const privatePromptColumns = shallowRef<PrimaryTableProps['columns']>([
  {
    title: 'Prompt',
    colKey: 'name',
    ellipsis: true,
    cell: (_h, { row }: { row: IMCPServerPrompt }) => {
      return row.name || '--';
    },
  },
]);
const filterKeywordDebounced = refDebounced(filterKeyword, 300);

const toolNameRules = {
  tool_name: [
    {
      required: true,
      message: t('请输入工具名称'),
      trigger: 'blur',
    },
    {
      validator: (value: string) => {
        const reg = /^[a-zA-Z0-9][a-zA-Z0-9\-._]*[a-zA-Z0-9]$/;
        return reg.test(value);
      },
      message: () => `${t('首尾字符：必须以字母或数字开头和结尾（a-z、A-Z、0-9）')}, ${t('中间字符：允许字母、数字、连字符（-）、下划线（_）、点号（.）')}`,
      trigger: 'blur',
    },
    {
      validator: (value: string) => {
        const trimValue = value.trim();
        if (!trimValue) return;

        const sameNameItems = resourceList.value?.filter((item: IMCPServerTool) => {
          return item.tool_name?.trim() === trimValue;
        }) || [];

        const currentEditRowId = toolNameRowData.value?.id;
        const filteredSameItems = currentEditRowId
          ? sameNameItems.filter(item => item.id !== currentEditRowId)
          : sameNameItems;

        return filteredSameItems.length === 0;
      },
      message: t('工具名称不可重复'),
      trigger: 'blur',
    },
  ],
};

const methodTagThemeMap = {
  POST: 'info',
  GET: 'success',
  DELETE: 'danger',
  PUT: 'warning',
  PATCH: 'info',
  ANY: 'success',
};

let resizeLayoutConfig = {
  min: 794,
  max: 800,
};

const gatewayId = computed(() => gatewayStore.currentGateway?.id);
const isEditMode = computed(() => !!serverId);
const isEnablePrompt = computed(() => featureFlagStore?.flags?.ENABLE_MCP_SERVER_PROMPT);
const stage = computed(() => stageList.value.find(sg => sg.id === formData.value.stage_id));
const stageName = computed(() => stage.value?.name || '');
const serverNamePrefix = computed(() => `${gatewayStore.currentGateway?.name}-${stageName.value}-`);
const sliderTitle = computed(() => {
  return isEditMode.value
    ? t('编辑 {n}', { n: formData.value.name })
    : t('创建 MCP Server');
});
const toolTableEmptyType = computed(() => filterKeywordDebounced.value?.trim()?.toLowerCase()
  || toolFilterData.value?.method?.length > 0
  ? 'searchEmpty'
  : 'empty');
const filteredToolList = computed(() => {
  const keyword = filterKeywordDebounced.value.trim().toLowerCase();
  const methodsData = toolFilterData.value?.method ?? [];
  const currentResourceList = resourceList.value;

  return currentResourceList.filter((resource) => {
    const matchKeyword = (() => {
      const targetStr = [
        resource.name,
        resource.path,
        resource.tool_name,
        resource.method,
      ].join(' ').toLowerCase();
      return keyword ? targetStr.includes(keyword) : true;
    })();

    const matchMethods = (() => {
      const validMethodsData = Array.isArray(methodsData)
        ? methodsData.map(m => m?.toString().toUpperCase().trim())
        : [];
      if (validMethodsData.length === 0) return true;

      return validMethodsData.includes(resource.method);
    })();

    return matchKeyword && matchMethods;
  });
});
const filteredPromptList = computed(() => {
  const hasSearchCondition = filterPromptValues.value.length > 0;
  if (hasSearchCondition) {
    handleSetLoading(true);
  }

  const searchConditions = {
    name: filterPromptValues.value.find(item => item.id === 'name')?.values[0]?.id ?? '',
    content: filterPromptValues.value.find(item => item.id === 'content')?.values[0]?.id ?? '',
    updated_by: filterPromptValues.value.find(item => item.id === 'updated_by')?.values[0]?.id ?? [],
    labels: filterPromptValues.value.find(item => item.id === 'labels')?.values.map((v: { id: string }) => v.id) ?? [],
  };
  const results = promptTableData.value?.filter((item) => {
    const { name, code, content, updated_by = '', labels = [] } = item;
    let isMatch = true;

    // 匹配中英文名
    if (searchConditions.name) {
      const nameRegex = new RegExp(searchConditions.name, 'gi');
      isMatch = isMatch && (!!name?.match(nameRegex) || !!code?.match(nameRegex));
    }

    // 匹配内容
    if (searchConditions.content) {
      const contentRegex = new RegExp(searchConditions.content, 'gi');
      isMatch = isMatch && !!content?.match(contentRegex);
    }

    // 匹配修改人
    if (searchConditions.updated_by) {
      const userRegex = new RegExp(searchConditions.updated_by, 'gi');
      isMatch = isMatch && !!updated_by?.match(userRegex);
    }

    // 匹配标签
    if (searchConditions.labels.length) {
      // 表格项的labels与搜索标签有交集则匹配
      const hasLabel = searchConditions.labels.some(label => labels.includes(label));
      isMatch = isMatch && hasLabel;
    }

    return isMatch;
  });

  promptTableEmptyType.value = results.length < 1 && filterPromptValues.value.length > 0 ? 'searchEmpty' : 'empty';

  return results;
});
const renderPreviewByTab = computed(() => {
  return allSelections.value.filter(item => item.mode_type === activeTab.value);
});
const filterPromptConditions = computed<ISearchItem[]>(() => [
  {
    name: t('中英文名'),
    id: 'name',
    placeholder: t('请输入中英文名'),
  },
  {
    name: t('标签'),
    id: 'labels',
    placeholder: t('请选择标签'),
    children: promptLabels.value,
    multiple: true,
  },
  {
    name: t('内容'),
    id: 'content',
    placeholder: t('请输入内容'),
  },
  {
    name: t('修改人'),
    id: 'updated_by',
    placeholder: t('请输入修改人'),
  },
]);
const escapedCodeContent = computed(() => {
  return escape(curPromptData.value?.content ?? '');
});
const noValidStage = computed(() => stageList.value.every(stage => stage.status === 0));
const isCurrentStageValid = computed(() =>
  stageList.value.find(stage => stage.id === formData.value.stage_id)?.status === 1);
// 处理工具oauth态
const isEnabledOAuth = computed(() => formData.value.oauth2_public_client_enabled);
// 选中的应用态工具数据
const appAuthStatusList = computed(() => {
  if (!isEnabledOAuth.value) return [];
  return toolSelections.value.filter(item => renderOAuthConfig(item)?.app_verified_required);
});
// 选中工具项是否存在应用态或用户态数据
const isExistOAuthData = computed(() => isEnabledOAuth.value && toolSelections.value.some(auth =>
  renderOAuthConfig(auth)?.auth_verified_required || renderOAuthConfig(auth)?.app_verified_required),
);

// 开启OAuth2 公开客户端模式才展示工具应用态或用户态
const isEnabledOAuthTag = payload => ['tool'].includes(payload.mode_type) && isEnabledOAuth.value;

const renderOAuthConfig = (payload) => {
  const resourceAuthConfig = payload?.contexts?.resource_auth?.config;
  if (resourceAuthConfig) {
    return JSON.parse(resourceAuthConfig);
  }

  return {};
};

// 结果预览高度自适应不同选项表格的高度
const renderPreviewViewWidth = () => {
  const initH = 32;
  const toolClientH = (toolTableRef.value?.TDesignTableRef?.$el?.offsetHeight ?? 0) + initH;
  const promptClientH = (promptTableRef.value?.TDesignTableRef?.$el?.offsetHeight ?? 0) + initH;
  return { maxHeight: `${activeTab.value.includes('tool') ? toolClientH : promptClientH}px` };
};

/**
 * 获取公共异步数据（提取重复逻辑，降低耦合）
 * @param {boolean} isEnablePrompt  是否启用 Prompt 功能
 */
const fetchCommonData = async (isEnablePrompt: boolean) => {
  // 定义基础请求列表
  const requestList = isEditMode.value ? [fetchCategoryList()] : [fetchStageList(), fetchCategoryList()];
  // 启用 Prompt 时，追加 Prompt 资源请求
  if (isEnablePrompt) {
    requestList.push(fetchPromptResources());
  }
  else {
    // 禁用 Prompt 时，过滤掉 prompt 相关的标签
    resourceTabList.value = resourceTabList.value.filter(
      item => !['prompt'].includes(item.value),
    );
  }
  const results = await Promise.allSettled(requestList);
  // 处理单个请求的失败情况
  results.forEach((result) => {
    if (result.status === 'rejected') {
      Message({
        theme: 'error',
        message: JSON.stringify(result?.reason?.stack),
      });
    }
  });
};

// 获取常用环境列表 分类列表数据，设置默认初始化表单
const getCommonListData = async () => {
  await fetchCommonData(isEnablePrompt.value);
  initSidebarFormData(getDiffFormData());
};

/**
 * 处理 isShow 状态变化的核心逻辑
 * @param {boolean} isShowVal 当前 isShow 的值
 */
const handleIsShowChange = async (isShowVal: boolean) => {
  const bodyEl = document.querySelector('body');
  if (bodyEl) {
    bodyEl.classList.toggle('overflow-hidden', isShowVal);
  }

  // 仅在 isShow 为 true 时执行后续逻辑
  if (!isShowVal) return;

  clearValidate();
  if (isEditMode.value) {
    await fetchServer();
  }
  getCommonListData();
  renderPreviewViewWidth();
};

watch(isShow, handleIsShowChange, { immediate: false });

const getDiffFormData = () => {
  return {
    formData: formData.value,
    toolSelections: toolSelections.value,
    promptSelections: promptSelections.value,
  };
};

const resetResizeLayout = () => {
  nextTick(() => {
    const modalContentEl = document.querySelector('.create-mcp-slider .bk-modal-content');
    if (modalContentEl) {
      modalContentEl.scrollTop = 0;
    }
    if (!resizeLayoutRef.value) {
      return;
    }
    const asideLayout = resizeLayoutRef.value.asideRef;
    if (asideLayout) {
      Object.assign(asideLayout.style, {
        width: '794px',
        maxWidth: '800px',
        minWidth: '794px',
      });
    }
  });
};

const toolDisabledSelection = (row) => {
  // 先判断当前行是否已被勾选（存在于 toolSelections 中）
  const isSelected = toolSelections.value.some(item => item.id === row.id);

  // 设置禁用提示语
  row.selectionTip = isSelected
    ? t('该资源数据有变更，请确认一下请求参数是否正确配置。')
    : t('该资源未配置请求参数声明，不能添加到 MCP');

  // 已勾选（isSelected=true）→ 允许取消勾选（返回 false，不禁用）
  // 未勾选（isSelected=false）+ 无openapi_schema → 禁止勾选（返回 true，禁用）
  // 有openapi_schema → 正常勾选（返回 false，不禁用）
  return !row.has_openapi_schema && !isSelected;
};

const handleMouseenter = (e: MouseEvent) => {
  const cell = (e.target as HTMLElement).closest('.truncate');
  if (cell) {
    isOverflow.value = cell.scrollWidth > cell.clientWidth;
  }
};

const handleMouseleave = () => {
  isOverflow.value = false;
};

const clearValidate = () => {
  formRef.value?.clearValidate();
};

const handleSetToolRowClass = ({ row }: { row: IMCPServerTool }) => {
  if (!row.has_openapi_schema) {
    return 'is-disabled-tool';
  }
  return '';
};

const handleSetPromptRowClass = ({ row }: { row: IMCPServerPrompt }) => {
  if (row.id === curPromptData.value.id) {
    return 'cursor-pointer is-selected-prompt';
  }
  return 'cursor-pointer';
};

const handleResizeLayout = (resizeWidth: number) => {
  resizePreviewWidth.value = `${1168 - resizeWidth}px`;
};

/**
 * 检查是否存在私有Prompt并弹出风险提示框
 * @returns Promise<boolean> - 确认继续返回true，取消返回false
 */
const isExistPrivatePrompt = (): Promise<boolean> => {
  // 此处逻辑是为了强制触发 categories 的 blur 事件以关闭 TagInput 下拉
  serverBasicFormRef.value?.handleCategoriesBlur();
  const privateData = promptSelections.value.filter(item => !item.is_public);
  if (!privateData.length) {
    return true;
  }
  return new Promise((resolve) => {
    usePopInfoBox({
      isShow: true,
      type: 'warning',
      title: t('此操作存在风险'),
      class: 'prompt-info-box',
      subTitle: () => {
        return (
          <div>
            <div class="bg-[#f5f6fa] p-16px pt-12px pb-12px mb-16px">
              { t('以下 Prompt 仅在授权空间内可用，添加到 MCP 后，所有经MCP 授权的应用均可访问该 Prompt 信息') }
            </div>
            <AgTable
              v-model:tableData={privateData}
              columns={privatePromptColumns.value}
              resizable
              localPage
              maxHeight={300}
              showPagination={false}
              showSettings={false}
            />
          </div>
        );
      },
      confirmText: t('继续执行'),
      cancelText: t('取消'),
      confirmButtonTheme: 'primary',
      contentAlign: 'left',
      showContentBgColor: true,
      onConfirm: () => resolve(true),
      onCancel: () => resolve(false),
    });
  });
};

const handleSubmit = async () => {
  // 基础表单验证
  const basicFormValidate = serverBasicFormRef.value?.validateForm();
  const isBasicValidate = typeof basicFormValidate === 'boolean' && basicFormValidate;
  try {
    await formRef.value?.validate();
  }
  catch {
    if (!isBasicValidate) {
      basicFormValidate?.focus?.();
      handleScrollView(basicFormValidate?.$el);
      return;
    }
  }

  if (!isBasicValidate) {
    handleScrollView(basicFormValidate?.$el);
    return;
  }

  let isValidate = toolSelections.value.length > 0;

  if (!isValidate) {
    handleScrollView(resourceRef.value);
    Message({
      theme: 'warning',
      message: t('请选择工具'),
    });
    return;
  }

  isValidate = await isExistPrivatePrompt();
  if (!isValidate) return;

  try {
    submitLoading.value = true;
    let params = {
      resource_names: toolSelections.value.map(item => item.name),
      tool_names: toolSelections.value.map(item => item.tool_name ?? item.name),
      prompts: isEnablePrompt.value ? promptSelections.value : undefined,
      category_ids: categoriesList.value.filter(cg =>
        formData.value.categories.includes(cg.name))
        .map(cname => cname.id),
    };
    if (isEditMode.value) {
      const {
        title,
        description,
        is_public,
        oauth2_public_client_enabled,
        protocol_type,
        labels,
      } = formData.value;
      params = Object.assign(params, {
        description,
        is_public,
        oauth2_public_client_enabled,
        protocol_type,
        labels,
        title,
      });
      await patchServer(gatewayId.value, serverId, params);
      Message({
        theme: 'success',
        message: t('编辑成功'),
      });
    }
    else {
      params = {
        ...params,
        ...formData.value,
        name: `${serverNamePrefix.value}${formData.value.name}`,
      };
      await createServer(gatewayId.value, params);
      Message({
        theme: 'success',
        message: t('创建成功'),
      });
    }

    emit('updated');
    isShow.value = false;
  }
  finally {
    submitLoading.value = false;
  }
};

const fetchStageList = async () => {
  const response = await getStageList(gatewayId.value);
  stageList.value = response || [];
  if (!formData.value.stage_id) {
    formData.value.stage_id = stageList.value.find(stage => stage.status === 1)?.id ?? 0;
  }
  if (formData.value.stage_id) {
    await fetchStageResources();
  }
};

/**
 * 统一更新全选数据（确保工具/Prompt 都处理完成）
 */
const updateAllSelections = () => {
  setTimeout(() => {
    allSelections.value = [...toolSelections.value, ...promptSelections.value];
  }, 200);
};

/**
 * 工具资源渲染（分片处理，不阻塞主线程）
 * @param resource_names 资源名称列表
 * @param tool_names 工具名称列表
 */
const renderToolResource = (resource_names: string[], tool_names: string[]) => {
  try {
    if (!resource_names?.length) {
      return;
    }

    // 清空复用的Map（避免旧数据干扰）
    resourceNameToIndexMap.clear();
    const chunkSize = 50;
    let currentIndex = 0;

    const processChunk = () => {
      const endIndex = Math.min(currentIndex + chunkSize, resource_names.length);
      for (let i = currentIndex; i < endIndex; i++) {
        resourceNameToIndexMap.set(resource_names[i], i);
      }
      currentIndex = endIndex;

      // 未处理完则继续分片（利用浏览器空闲时间）
      if (currentIndex < resource_names.length) {
        requestIdleCallback(processChunk);
      }
      else {
        const hasToolNames = tool_names?.length > 0;
        // 轻量遍历，避免修改原数组
        const updatedResourceList = resourceList.value.map((item) => {
          const nameIndex = resourceNameToIndexMap.get(item.name);
          if (hasToolNames && nameIndex !== undefined && nameIndex > -1) {
            return {
              ...item,
              tool_name: tool_names[nameIndex] || item.name,
            };
          }
          return item;
        });

        const resourceToolData = updatedResourceList.filter(item =>
          resourceNameToIndexMap.has(item.name),
        );

        // 分片更新：先更20条，快速渲染
        toolSelections.value = resourceToolData.slice(0, 20).map(({ name, id, contexts }) => ({
          name,
          id,
          mode_type: 'tool',
          tool_name: hasToolNames && resourceNameToIndexMap.get(name) !== undefined
            ? tool_names[resourceNameToIndexMap.get(name)] || ''
            : '',
          contexts,
        }));

        // 剩余数据异步更新，确保DOM挂载
        setTimeout(() => {
          toolSelections.value = resourceToolData.map(({ name, id, contexts }) => ({
            name,
            id,
            mode_type: 'tool',
            tool_name: hasToolNames && resourceNameToIndexMap.get(name) !== undefined
              ? tool_names[resourceNameToIndexMap.get(name)] || ''
              : '',
            contexts,
          }));
          toolTableRef.value?.setSelectionData(toolSelections.value);
          // 延迟清空Map，确保数据使用完成
          setTimeout(() => resourceNameToIndexMap.clear(), 500);
        }, 0);
      }
    };

    // 启动分片处理
    processChunk();
  }
  catch {
    resourceNameToIndexMap.clear();
  }
};

/**
 * Prompt 资源渲染（分片处理，不阻塞主线程）
 * @param prompts Prompt 数据列表
 */
const renderPromptResource = (prompts: IMCPServerPrompt[]) => {
  try {
    if (!prompts?.length) {
      return;
    }

    // 清空复用的Set
    authorizedPromptIds.clear();
    const chunkSize = 50;
    let currentIndex = 0;

    const processPromptChunk = () => {
      const endIndex = Math.min(currentIndex + chunkSize, promptTableData.value.length);
      for (let i = currentIndex; i < endIndex; i++) {
        authorizedPromptIds.add(promptTableData.value[i].id);
      }
      currentIndex = endIndex;

      if (currentIndex < promptTableData.value.length) {
        requestIdleCallback(processPromptChunk);
      }
      else {
        // 处理无权限数据
        noPermPrompt.value = prompts.filter(item => !authorizedPromptIds.has(item.id)).map(item => ({
          ...item,
          mode_type: 'prompt',
          is_no_perm: true,
        }));

        // 分片更新
        promptSelections.value = prompts.slice(0, 20).map(item => ({
          ...item,
          mode_type: 'prompt',
          is_no_perm: !authorizedPromptIds.has(item.id),
        }));

        setTimeout(() => {
          promptSelections.value = prompts.map(item => ({
            ...item,
            mode_type: 'prompt',
            is_no_perm: !authorizedPromptIds.has(item.id),
          }));

          // 合并无权限数据（避免重复创建数组）
          if (noPermPrompt.value.length) {
            promptTableData.value.push(...noPermPrompt.value);
            if (Object.keys(curPromptData.value).length === 0 && promptTableData.value.length) {
              curPromptData.value = { ...promptTableData.value[0] };
            }
          }
          promptTableRef.value?.setSelectionData(promptSelections.value);
          // 延迟清空Set
          setTimeout(() => authorizedPromptIds.clear(), 500);
        }, 0);
      }
    };

    processPromptChunk();
  }
  catch {
    authorizedPromptIds?.clear();
  }
};

const fetchServer = async () => {
  try {
    const response = await getServer(gatewayId.value, serverId!);

    const {
      name = '',
      title = '',
      description = '',
      url = '',
      protocol_type = 'streamable_http',
      labels = [],
      oauth2_public_client_enabled = false,
      is_public = true,
      stage = { id: 0 },
      resource_names = [],
      tool_names = [],
      prompts = [],
      categories = [],
    } = response ?? {};

    formData.value = {
      ...formData.value,
      name,
      title,
      url,
      description,
      labels,
      is_public,
      oauth2_public_client_enabled,
      stage_id: stage.id || 0,
      protocol_type,
      categories: categories.map(item => item.name || ''),
    };

    try {
      await fetchStageList();
    }
    finally {
      // 启动资源渲染（微任务执行，不阻塞主线程）
      queueMicrotask(() => renderToolResource(resource_names, tool_names));
      queueMicrotask(() => renderPromptResource(prompts));
      // 统一更新全选数据
      updateAllSelections();
    }
  }
  catch {
    formData.value = cloneDeep(defaultFormData.value);
  }
  finally {
    initSidebarFormData(getDiffFormData());
  }
};

const fetchStageResources = async () => {
  try {
    searchLoading.value = true;
    if (stage.value?.resource_version?.id) {
      const response = await getVersionDetail(
        gatewayId.value,
        stage.value.resource_version.id,
        {
          stage_id: stage.value.id,
          source: 'mcp_server',
        },
      );
      resourceList.value = response.resources || [];
    }
    else {
      resourceList.value = [];
    }
  }
  finally {
    searchLoading.value = false;
  }
};

const fetchPromptResources = async () => {
  const res = await getServerPrompts(gatewayId.value);
  promptTableData.value = res?.prompts ?? [];

  if (promptTableData.value.length) {
    curPromptData.value = promptTableData.value.at(0);
    const allLabels = promptTableData.value.map(item => item?.labels ?? []).flat(1);
    promptLabels.value = uniq(allLabels).map((item) => {
      return {
        name: item,
        id: item,
      };
    });
    await fetchPromptResourcesDetail();
  }
};

const fetchPromptResourcesDetail = async () => {
  promptDetailLoading.value = true;
  try {
    const res = await getServerPromptsDetail(gatewayId.value, { ids: [curPromptData.value.id] });
    curPromptData.value = Object.assign(curPromptData.value, res?.prompts?.[0] ?? {});
  }
  catch {
    curPromptData.value = {};
  }
  finally {
    promptDetailLoading.value = false;
  }
};

// 获取MCP分类
const fetchCategoryList = async () => {
  const res = await getMcpCategoryList(gatewayId.value);
  categoriesList.value = (res ?? []).map((cg) => {
    return {
      ...cg,
      tips: cg.description,
      id: String(cg.id),
    };
  });
};

const handlePromptRowClick = ({
  e,
  row,
}: {
  e: MouseEvent
  row: IMCPServerPrompt
}) => {
  e?.stopPropagation();
  const isCheckbox = (e.target as HTMLElement).closest('.custom-ag-table-checkbox');
  const isRepeat = `${curPromptData.value.id}&${curPromptData.value.code}` === `${row.id}&${row.code}`;
  if (isCheckbox || isRepeat) {
    return;
  }
  curPromptData.value = row;
  fetchPromptResourcesDetail();
};

const getSliderContentHeight = () => {
  // 动态获取footer高度，计算内容区域最大高度
  setTimeout(() => {
    const modalContentEl = document.querySelector('.create-mcp-slider .bk-modal-content');
    const footerH = footerRef.value?.offsetHeight;
    if (modalContentEl) {
      modalContentEl.style.maxHeight = !isEnabledOAuth.value ? modalContentEl.style.height : `calc(100% - ${footerH + 54}px)`;
    }
  });
};

const handleRemoveResource = ({
  name,
  mode_type,
  id,
}: {
  name?: string
  mode_type?: string
  id?: number
}) => {
  const removeData = `${mode_type}&${name}&${id}`;
  if (['tool'].includes(mode_type)) {
    toolSelections.value = toolSelections.value.filter(item => `${mode_type}&${item.name}&${item.id}` !== removeData);
    toolTableRef.value?.setSelectionData(toolSelections.value);
  }
  else {
    promptSelections.value = promptSelections.value.filter(item => `${mode_type}&${item.name}&${item.id}` !== removeData);
    promptTableRef.value?.setSelectionData(promptSelections.value);
  }
  allSelections.value = allSelections.value.filter(item => `${mode_type}&${item.name}&${item.id}` !== removeData);
};

const handleToolSelectionChange: PrimaryTableProps['onSelectChange'] = ({ selections }) => {
  // 这里把响应式数据数据逻辑放到setTimeout异步执行，避免阻塞主线程
  setTimeout(() => {
    toolSelections.value = selections;
    // 保留 Prompt 项，替换工具项
    const promptItems = allSelections.value.filter(item => item.mode_type === 'prompt');
    const toolItems = selections.map(item => ({
      ...item,
      mode_type: 'tool',
    }));
    allSelections.value = [...promptItems, ...toolItems];
    getSliderContentHeight();
  }, 0);
};

const handlePromptSelectionChange: PrimaryTableProps['onSelectChange'] = ({ selections }) => {
  // 这里把响应式数据数据逻辑放到setTimeout异步执行，避免阻塞主线程
  setTimeout(() => {
    promptSelections.value = selections;
    // 保留工具项，替换 Prompt 项
    const toolItems = allSelections.value.filter(item => item.mode_type === 'tool');
    const promptItems = selections.map(item => ({
      ...item,
      mode_type: 'prompt',
    }));
    allSelections.value = [...toolItems, ...promptItems];
  }, 0);
};

const handleToolFilterChange: PrimaryTableProps['onFilterChange'] = (filters) => {
  toolFilterData.value = { ...filters };
};

const handleEditToolName = (row: IMCPServerTool) => {
  toolNameRowData.value = {
    ...row,
    tool_name: row.tool_name ?? row.name,
    isShow: true,
  };
};

const handleConfirmToolName = async (row) => {
  try {
    await toolNameRef.value?.validate();
    const toolData = resourceList.value.find(item => item.id === row.id);
    if (toolData) {
      toolData.tool_name = toolNameRowData.value.tool_name;
    }
    const selectData = toolSelections.value.find(item => item.id === toolData.id);
    if (selectData) {
      selectData.tool_name = toolNameRowData.value.tool_name;
    }
    handleCancelToolName();
  }
  catch {
    toolNameRowData.value.isShow = true;
  }
};

const handleCancelToolName = () => {
  toolNameRowData.value = {};
};

const handleClickOutSide = (e: MouseEvent) => {
  const cell = (e.target as HTMLElement).closest('.tool-name-edit-icon');
  if (!cell) {
    handleCancelToolName();
  }
};

/**
 * 设置搜索loading状态
 * @param isLoading - 是否显示loading
 * @param delay - 自动关闭延迟（默认500ms）
 */
const handleSetLoading = (isLoading: boolean, delay = 500) => {
  if (loadingTimer) {
    clearTimeout(loadingTimer);
    loadingTimer = null;
  }

  searchLoading.value = isLoading;

  if (isLoading) {
    loadingTimer = setTimeout(() => {
      searchLoading.value = false;
      loadingTimer = null;
    }, delay);
  }
};

const handleClearSelections = (type?: string) => {
  const typeMap = {
    tool: () => {
      toolSelections.value = [];
      toolTableRef.value?.handleResetSelection();
    },
    prompt: () => {
      promptSelections.value = [];
      promptTableRef.value?.handleResetSelection();
    },
    all: () => {
      allSelections.value = [];
      toolSelections.value = [];
      promptSelections.value = [];
      toolTableRef.value?.handleResetSelection();
      promptTableRef.value?.handleResetSelection();
    },
  };
  return typeMap[type ?? 'all']?.();
};

const handleToolClearSelection = () => {
  toolSelections.value = [];
  allSelections.value = allSelections.value.filter(item => item.mode_type !== 'tool');
};

const handlePromptClearSelection = () => {
  promptSelections.value = [];
  allSelections.value = allSelections.value.filter(item => item.mode_type !== 'prompt');
};

const handleToolClearFilter = () => {
  filterKeyword.value = '';
  toolFilterData.value = {};
  handleSetLoading(true);
};

const handlePromptClearFilter = () => {
  handleSetLoading(true);
  filterPromptValues.value = [];
};

const handleRefreshClick = async () => {
  if (!isCurrentStageValid.value) {
    return;
  }
  filterKeyword.value = '';
  toolNameRowData.value = {};
  searchLoading.value = true;
  await fetchStageList();
  toolSelections.value = toolSelections.value.filter(item =>
    resourceList.value.some(resource => resource.id === item.id),
  );
  searchLoading.value = false;
};

const handleStageSelectChange = () => {
  toolTableRef.value?.handleResetSelection();
  handleToolClearSelection();
  fetchStageResources();
};

const handleToolNameClick = (row: { id: number }) => {
  if (gatewayStore.currentGateway?.kind === 1) return;
  const routeData = router.resolve({
    name: 'ResourceEdit',
    params: {
      id: gatewayId.value,
      resourceId: row.id,
    },
  });
  window.open(routeData.href, '_blank');
};

const handleMcpTypeChange = (tab: string) => {
  activeTab.value = tab;
  const tabMap = {
    tool: () => {
      if (toolSelections.value.length) {
        nextTick(() => {
          toolTableRef.value?.setSelectionData(toolSelections.value);
        });
      }
    },
    prompt: () => {
      if (promptSelections.value.length) {
        nextTick(() => {
          promptTableRef.value?.setSelectionData(promptSelections.value);
        });
      }
    },
  };
  return tabMap[tab]?.();
};

// 切换oauth是否开启同步更新节点宽度
const handleOAuthChange = () => {
  getSliderContentHeight();
};

const resetSliderData = () => {
  formData.value = cloneDeep(defaultFormData.value);
  stageList.value = [];
  resourceList.value = [];
  toolSelections.value = [];
  promptSelections.value = [];
  allSelections.value = [];
  noPermPrompt.value = [];
  filterKeyword.value = '';
  activeTab.value = 'tool';
  curPromptData.value = {};
  resizeLayoutConfig = {
    min: 794,
    max: 800,
  };
  toolFilterData.value = {};
  toolTableRef.value?.setPagination({
    current: 1,
    pageSize: 10,
  });
  promptTableRef.value?.setPagination({
    current: 1,
    pageSize: 10,
  });
};

const handleScrollView = (el: HTMLInputElement | HTMLElement) => {
  el.scrollIntoView({
    behavior: 'smooth',
    block: 'center',
  });
};

const handleBeforeClose = () => {
  serverBasicFormRef.value?.handleCategoriesBlur();
  const results = isSidebarClosed(JSON.stringify(getDiffFormData()));
  return results;
};

const handleCancel = () => {
  resetResizeLayout();
  handleClearSelections();
  clearValidate();
  resetSliderData();
  serverBasicFormRef.value?.handleCategoriesBlur();
  isShow.value = false;
};

defineExpose({
  show: () => {
    isShow.value = true;
  },
  clearValidate,
});

</script>

<style lang="scss">
.prompt-info-box {

  .set-bg-color {
    background-color: transparent;
  }
}

.tool-name-popover {

  .is-error {
    margin-bottom: 36px;
  }
}
</style>

<style lang="scss" scoped>
.create-mcp-slider {

  :deep(.bk-modal-content) {
    background-color: #f5f7fa;
    overflow-y: auto;
    overflow-x: hidden !important;
  }

  .slider-content {
    width: 100%;

    .main {
      padding: 28px 40px 0;
      color: #4d4f56;
    }

    :deep(.tool-name) {

      &:hover {
        .icon-ag-edit-line {
          display: block;
        }
      }
    }

    :deep(.is-disabled-tool) {
      td {
        color: #979ba5;

        .bk-tag {
          color: #979ba5;
          background-color: #f0f1f5;
        }
      }
    }

    :deep(.is-selected-prompt) {
      background-color: #f0f5ff;

      .prompt-name {
        color: #3a84ff;
      }
    }
  }

  &.enabled-oauth2-public-client,
  &.app-auth-mcp-slider {

    .slider-content {
      margin-bottom: 24px;
    }

    :deep(.bk-sideslider-footer) {
      padding: 0;
      height: auto !important;
    }
  }
}

.resource-table-form-item {
  border: 1px solid #dcdee5;
  border-radius: 2px 2px 0 0;

  .resource-form-item-label {
    display: flex;
    align-items: center;
    height: 42px;
    line-height: 42px;
    background-color: #fafbfd;
    border-bottom: 1px solid #dcdee5;

    .label-text {
      position: relative;
      min-width: 92px;
      border-right: 1px solid #dcdee5;
      text-align: center;
      cursor: pointer;
      transition: all 0.2s;

      .required-mark {
        position: absolute;
        top: 0;
        width: 14px;
        font-size: 14px;
        color: #ea3636;
      }

      &:hover,
      &.is-active {
        background-color: #ffffff;
        color: #3a84ff;
      }
    }

  }

  .resource-tips {
    font-size: 12px;
    color: #979ba5;
    line-height: 16px;
  }

  .resource-selector-wrapper {
    background-color: #f5f7fa;

    .selector-main {
      flex-shrink: 0;

      .prompt-row-detail {
        color: #4d4f56;
        border: 1px solid #dcdee5;
        border-radius: 2px;
      }
    }

    .result-preview {
      display: flex;
      flex-direction: column;
      height: 100%;

      .header-title-wrapper {
        display: flex;
        justify-content: space-between;
        margin-bottom: 16px;
        font-size: 14px;

        .name {
          font-weight: 700;
          color: #4d4f56;
        }
      }

      &-list {
        overflow-y: auto;

        .list-main {
          overflow-y: auto;
          flex: 1;

          .list-item {
            height: 32px;
            padding: 6px 10px;
            padding-right: 0;
            margin-bottom: 4px;
            background-color: #ffffff;
            border-radius: 2px;

            .delete-icon {
              flex-shrink: 0;
              color: #c4c6cc;

              &:hover {
                color: #3a84ff;
                cursor: pointer;
              }
            }
          }
        }
      }
    }

    &.set-border {
      border-top: 1px solid #dcdee5;
    }
  }

  &.prompt {
    :deep(.bk-form-label) {
      margin-bottom: 0;
    }
  }
}
</style>
