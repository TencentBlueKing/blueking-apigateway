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
                :is-show-slider="isShow"
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
                field="oauth2_public_client_enabled"
                :is-show="isShowPublicClient"
                :title="t('OAuth2 公开客户端模式')"
                :description="t('开启后，用户通过浏览器 OAuth2 授权即可使用，无需手动配置 API 凭证。票据将以 public 公开应用身份签发。')"
                icon="oauth2"
                @oauth-change="updateSliderContentHeight"
              />
              <OAuthSwitcher
                v-model:form-data="formData"
                field="oauth2_personal_client_enabled"
                :is-show="isShowPersonalClient"
                :title="t('个人令牌')"
                :description="t('开启后，用户可以使用个人令牌调用该 MCP Server。')"
                icon="user-token"
                @oauth-change="updateSliderContentHeight"
              >
                <template
                  v-if="personalTokenLink"
                  #externalDescription
                >
                  <BkButton
                    size="small"
                    theme="primary"
                    text
                    class="text-12px!"
                    @click="handleViewDoc"
                  >
                    {{ t('查看文档') }}
                  </BkButton>
                </template>
              </OAuthSwitcher>
              <!-- 资源选择表格 -->
              <BkFormItem
                class="resource-table-form-item"
                :class="activeTab"
              >
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
                          <BkLoading
                            ref="toolTableRegion"
                            :loading="searchLoading"
                            :z-index="99"
                          >
                            <AgTable
                              ref="toolTableRef"
                              v-model:table-data="filteredToolList"
                              cache-identifier="mcp-create-tool-table"
                              class="mb-16px!"
                              show-selection
                              local-page
                              :auto-height="false"
                              :show-settings="false"
                              :show-first-full-row="toolSelections.length > 0"
                              :disabled-check-selection="isToolSelectionDisabled"
                              :columns="toolTableColumns"
                              :table-empty-type="toolTableEmptyType"
                              :filter-value="toolFilterData"
                              :row-class-name="handleSetToolRowClass"
                              @filter-change="handleToolFilterChange"
                              @clear-filter="handleToolClearFilter"
                              @clear-selection="handleToolClearSelection"
                              @selection-change="handleToolSelectionChange"
                            >
                              <template #selectionPopoverContent="row">
                                <div class="flex items-center">
                                  <div>{{ getToolSelectionTip(row) }}</div>
                                  <div
                                    v-if="!row.has_openapi_schema && !isProgrammableGateway"
                                    class="ml-16px color-#699df4 cursor-pointer"
                                    @click="handleToolNameClick(row)"
                                  >
                                    <AgIcon
                                      name="jump"
                                      color="#699df4"
                                      class="mr-6px"
                                    />
                                    {{ t('去配置') }}
                                  </div>
                                  <div
                                    v-if="requiresShorterToolName(row) && row.has_openapi_schema"
                                    class="font-700"
                                  >
                                    {{ t('请缩短工具名称。') }}
                                  </div>
                                </div>
                              </template>
                            </AgTable>
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
                                  value-split-code="+"
                                  class="mb-16px"
                                  clearable
                                  unique-select
                                  value-behavior="need-key"
                                />
                                <BkLoading
                                  ref="promptTableRegion"
                                  :loading="searchLoading"
                                  :z-index="99"
                                >
                                  <AgTable
                                    ref="promptTableRef"
                                    v-model:table-data="filteredPromptList"
                                    cache-identifier="mcp-create-prompt-table"
                                    resizable
                                    local-page
                                    show-selection
                                    :auto-height="false"
                                    :show-settings="false"
                                    :show-first-full-row="promptSelections.length > 0"
                                    :row-class-name="handleSetPromptRowClass"
                                    :columns="promptTableColumns"
                                    :table-empty-type="promptTableEmptyType"
                                    @clear-filter="handlePromptClearFilter"
                                    @clear-selection="handlePromptClearSelection"
                                    @selection-change="handlePromptSelectionChange"
                                    @row-click="handlePromptRowClick"
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
                                          v-bk-xss-html="curPromptData?.content"
                                          class="color-#4d4f56 break-all whitespace-pre-line font-unset"
                                        />
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
                                :disabled="!activeSelections.length"
                                @click="handleClearSelections(activeTab)"
                              >
                                {{ t('清空') }}
                              </BkButton>
                            </div>
                            <div
                              v-if="activeSelections.length"
                              class="sticky top-0 result-preview-list"
                              :style="selectionPreviewStyle"
                            >
                              <div
                                v-for="selection in activeSelections"
                                :key="selection.id ?? selection.name"
                                class="list-main"
                              >
                                <div class="flex items-center justify-between list-item">
                                  <div class="w-92% flex items-center">
                                    <div
                                      v-bk-tooltips="{
                                        placement:'top',
                                        content: selection.tool_name || selection.name,
                                        disabled: !isOverflow
                                      }"
                                      class="min-w-20px color-#4d4f56 text-12px truncate name"
                                      @mouseenter="(e: MouseEvent) => handleMouseenter(e)"
                                      @mouseleave="handleMouseleave"
                                    >
                                      {{ selection.tool_name || selection.name }}
                                    </div>
                                    <BkTag
                                      v-if="activeTab === 'prompt'"
                                      :theme="selection.is_public ? 'success' : 'warning'"
                                      class="ml-4px"
                                    >
                                      {{ t(selection.is_public ? '公开' : '私有') }}
                                    </BkTag>
                                    <template v-if="activeTab === 'tool' && isEnabledOAuth">
                                      <BkTag
                                        v-if="renderOAuthConfig(selection).auth_verified_required"
                                        theme="info"
                                        class="ml-4px"
                                      >
                                        {{ t('用户态') }}
                                      </BkTag>
                                      <template v-if="renderOAuthConfig(selection).app_verified_required">
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
                                    @click="removePreviewSelection(selection)"
                                  />
                                </div>
                              </div>
                            </div>
                            <AgTableEmpty
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
          class="my-8px"
          :is-edit-mode="isEditMode"
          :is-enabled-personal-client="isEnabledPersonalClient"
          :is-enabled-public-client="isEnabledPublicClient"
          :app-auth-status-list="appAuthStatusList"
          @on-expand="updateSliderContentHeight"
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
import { cloneDeep, uniq } from 'lodash-es';
import {
  Tag as BkTag,
  Divider,
  Form,
  Input,
  Message,
  PopConfirm,
  Popover,
  ResizeLayout,
} from 'bkui-vue';
import type { ISearchItem } from 'bkui-vue/lib/search-select/utils.d';
import type { IOptions } from 'bkui-vue/lib/directives';
import type {
  IFormMethod,
  IMethodFilterItem,
  ISearchSelectFilter,
} from '@/types/common';
import type { IAuthConfig } from '@/types/resource';
import { getStageList } from '@/services/source/gateway/stage';
import { getVersionDetail } from '@/services/source/gateway/resource-version';
import {
  createServer,
  getMcpCategoryList,
  getServer,
  getServerPrompts,
  getServerPromptsDetail,
  patchServer,
} from '@/services/source/gateway/mcp-server/server';
import type {
  IMCPFormData,
  IMCPServerCategory,
  IMCPServerPrompt,
  IMCPServerTool,
  IMCPTabType,
  IMCPToolSelections,
  IResourceAuthConfig,
  ToolNameRowType,
} from '@/types/mcp-server';
import { refDebounced, useElementSize } from '@vueuse/core';
import type { ComponentPublicInstance } from 'vue';
import type {
  IMCPServerRemotePromptsOutput,
  IMCPServerRetrieveOutput,
} from '@/services/types/gateway/mcp-server/server.ts';
import type { IStageListOutput } from '@/services/types/gateway/stage.ts';
import { usePopInfoBox, useSidebar } from '@/hooks';
import { HTTP_METHODS } from '@/constants';
import {
  useEnv,
  useFeatureFlag,
  useGateway,
} from '@/stores';
import { t } from '@/locales';
import ServerBasicForm from '@/views/mcp-server/components/ServerBasicForm.vue';
import OAuthSwitcher from '@/views/mcp-server/components/OAuthSwitcher.vue';
import OAuthAlert from '@/views/mcp-server/components/OAuthAlert.vue';
import AgTableEmpty from '@/components/base/ag-table-empty/Index.vue';
import AgTable, {
  type FilterValue,
  type IAgTableInstance,
  type ITableColumn,
  type ITableEmptyType,
  type ITableSelection,
  type RowEventContext,
  type TableRow,
} from '@/components/base/ag-table';

type IResourceTabItem = {
  label: string
  value: IMCPTabType
  required: boolean
};

type IResizeLayoutConfig = {
  min: number
  max: number
};

type IMCPSelections = (Partial<IMCPServerTool> | Partial<IMCPServerPrompt>) & IMCPToolSelections;

interface IProps { serverId?: number }

const { serverId = 0 } = defineProps<IProps>();

const emit = defineEmits<{ updated: [] }>();

const router = useRouter();
const gatewayStore = useGateway();
const envStore = useEnv();
const featureFlagStore = useFeatureFlag();
const { initSidebarFormData, isSidebarClosed } = useSidebar();

let loadingTimer: ReturnType<typeof setTimeout> | null = null;
let clearMapTimer: ReturnType<typeof setTimeout> | null = null;

// 持久化实例，仅创建一次
const resourceNameToIndexMap = new Map<string, number>();
const authorizedPromptIds = new Set<number>();

const footerRef = useTemplateRef<HTMLDivElement>('footerRef');
const resourceRef = useTemplateRef<HTMLDivElement>('resourceRef');
const resizeLayoutRef = useTemplateRef<InstanceType<typeof ResizeLayout>>('resizeLayoutRef');
const toolTableRef = useTemplateRef<IAgTableInstance<IMCPServerTool>>('toolTableRef');
const promptTableRef = useTemplateRef<IAgTableInstance<IMCPServerPrompt>>('promptTableRef');
const toolTableRegion = useTemplateRef<ComponentPublicInstance>('toolTableRegion');
const promptTableRegion = useTemplateRef<ComponentPublicInstance>('promptTableRegion');
const { height: toolTableHeight } = useElementSize(toolTableRegion, undefined, { box: 'border-box' });
const { height: promptTableHeight } = useElementSize(promptTableRegion, undefined, { box: 'border-box' });
const formRef = useTemplateRef<InstanceType<typeof Form> & IFormMethod>('formRef');
const toolNameRef = ref<InstanceType<typeof Form> & IFormMethod>();
const popoverConfirmRef = ref<InstanceType<typeof PopConfirm>>();
const serverBasicFormRef = useTemplateRef<InstanceType<typeof ServerBasicForm>>('serverBasicFormRef');
const toolNameInputRef = ref<InstanceType<typeof Input> & { focus: () => void }>();
const defaultFormData = ref<IMCPFormData>({
  name: '',
  title: '',
  url: '',
  description: '',
  protocol_type: 'streamable_http',
  stage_id: 0,
  is_public: true,
  oauth2_public_client_enabled: false,
  oauth2_personal_client_enabled: false,
  raw_response_enabled: false,
  labels: [] as string[],
  categories: [] as string[],
});
const isShow = ref(false);
const submitLoading = ref(false);
const searchLoading = ref(false);
const promptDetailLoading = ref(false);
const isOverflow = ref(false);
const filterKeyword = ref('');
const activeTab = ref<IMCPTabType>('tool');
const promptTableEmptyType = ref<ITableEmptyType>('empty');
const resizePreviewWidth = ref('100%');
const formData = ref<IMCPFormData>(cloneDeep(defaultFormData.value));
const toolFilterData = ref<Record<string, any>>({});
const curPromptData = ref<Partial<IMCPServerPrompt>>({});
const stageList = ref<IStageListOutput[]>([]);
const resourceList = ref<IMCPServerTool[]>([]);
const promptTableData = ref<IMCPServerPrompt[]>([]);
const toolSelections = ref<IMCPSelections[]>([]);
const promptSelections = ref<IMCPServerPrompt[]>([]);
const noPermPrompt = ref<IMCPServerPrompt[]>([]);
const promptLabels = ref<ISearchItem[]>([]);
const filterPromptValues = ref<ISearchSelectFilter[]>([]);
const categoriesList = ref<IMCPServerCategory[]>([]);
const hiddenCategoriesList = ref<IMCPServerCategory[]>([]);
const resourceNameList = ref<string[]>([]);

const customMethodsList = computed<IMethodFilterItem[]>(() => {
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

const toolNameRowData = ref<ToolNameRowType>({} as ToolNameRowType);
const resourceTabList = shallowRef<IResourceTabItem[]>([
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
const toolTableColumns = shallowRef<ITableColumn<IMCPServerTool>[]>([
  {
    title: t('资源名称'),
    colKey: 'name',
    cell: (_h, { row }) => {
      if (!row.name) {
        return '--';
      };

      return (
        <div class="flex-row items-center relative overflow-hidden">
          <div
            v-bk-tooltips={{
              placement: 'top',
              content: row.name ?? '',
              disabled: !row.isOverflow,
            }}
            class={[
              'truncate mr-4px',
              gatewayStore.currentGateway?.kind === 0
                ? 'color-#3a84ff cursor-pointer'
                : '',
              !row.has_openapi_schema && 'color-#979ba5!',
            ]}
            onMouseenter={(e: MouseEvent) => {
              toolTableRef.value?.handleCellEnter({
                e,
                row,
              });
            }}
            onMouseleave={() => {
              toolTableRef.value?.handleCellLeave({ row });
            }}
            onClick={() => {
              if (isToolSelectionDisabled(row) && !row.has_openapi_schema) return;

              handleToolNameClick(row);
            }}
          >
            {row.name}
          </div>

          {(isToolSelectionDisabled(row) && !row.has_openapi_schema) && (
            <Popover
              trigger="hover"
              placement="top"
              popoverDelay={300}
            >
              {{
                default: () => (
                  <ag-icon
                    name="exclamation-circle-fill"
                    class="min-w-14px flex-shrink-0 color-#f59500 cursor-pointer"
                  />
                ),
                content: () => (
                  <div class="flex items-center">
                    <div>
                      { getToolSelectionTip(row) }
                    </div>
                    {!isProgrammableGateway.value && (
                      <div
                        class="ml-16px color-#699df4 cursor-pointer"
                        onClick={() => handleToolNameClick(row)}
                      >
                        <ag-icon
                          name="jump"
                          color="#699df4"
                          class="mr-6px"
                        />
                        {t('去配置')}
                      </div>
                    )}
                  </div>
                ),
              }}
            </Popover>
          )}
        </div>
      );
    },
  },
  {
    title: t('工具名称'),
    colKey: 'tool_name',
    cell: (_h, { row }) => {
      const toolName = row.tool_name ?? row.name;

      if (!toolName) {
        return '--';
      }

      return (
        <div class="flex-row items-center relative overflow-hidden tool-name">
          <div
            v-bk-tooltips={{
              placement: 'top',
              content: toolName,
              disabled: !row.isOverflow,
            }}
            class={[
              'truncate mr-4px',
              { 'cursor-pointer': gatewayStore.currentGateway?.kind === 0 },
              { 'color-#979ba5': !row.has_openapi_schema },
            ]}
            onMouseenter={(e: MouseEvent) =>
              toolTableRef.value?.handleCellEnter({
                e,
                row,
              })}
            onMouseleave={() =>
              toolTableRef.value?.handleCellLeave({ row })}
          >
            { toolName }
          </div>
          { row.has_openapi_schema && (
            <div class="flex items-center">
              <PopConfirm
                ref={popoverConfirmRef}
                trigger={'manual' as any}
                width="400"
                placement="right"
                // @ts-expect-error fix later
                extCls="tool-name-popover"
                arrow={false}
                is-show={toolNameRowData.value.id === row.id && toolNameRowData.value.isShow}
                onConfirm={() => handleConfirmToolName(row)}
                onCancel={() => handleCancelToolName()}
              >
                {{
                  default: () => (
                    <ag-icon
                      name="edit-line"
                      class="invisible cursor-pointer vertical-mid tool-name-edit-icon"
                      onClick={(e: MouseEvent) => {
                        e?.stopPropagation();
                        handleEditToolName(row);
                      }}
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
                          { t('资源名称：{value}', { value: toolName }) }
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
                              ref={toolNameInputRef}
                              placeholder={t('请输入工具名称')}
                              maxlength={toolNameLengthLimit.value}
                              tooltipsOptions={{
                                content: (
                                  <div>
                                    { t('MCP Server 名称 + 工具名称不得超过 64 字符') }
                                    ，
                                    { t('剩余可输入 {count} 字符', { count: remainingToolNameCharacters.value }) }
                                    <br />
                                    { t('首尾字符：必须以字母或数字开头和结尾（a-z、A-Z、0-9）') }
                                    <br />
                                    { t('中间字符：允许字母、数字、连字符（-）、下划线（_）、点号（.）') }
                                  </div>
                                ),
                                placement: 'right',
                                disabled: false,
                                allowHtml: true,
                              } as Partial<IOptions>}
                            />
                          </Form.FormItem>
                        </Form>
                      </div>
                    </div>
                  ),
                }}
              </PopConfirm>
              { requiresShorterToolName(row) && (
                <Popover
                  trigger="hover"
                  placement="top"
                  popoverDelay={0}
                >
                  {{
                    default: () => (
                      <ag-icon
                        name="exclamation-circle-fill"
                        class="ml-4px min-w-14px color-#f59500 cursor-pointer"
                      />
                    ),
                    content: () => (
                      <div>
                        <span class="font-400">
                          {t('MCP Server 名称 + 工具名称不得超过 64 字符，超限可能导致部分客户端调用失败。')}
                        </span>
                        <span class="font-700">
                          {t('请缩短工具名称。')}
                        </span>
                      </div>
                    ),
                  }}
                </Popover>
              )}
            </div>
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
      list: customMethodsList.value,
    },
    cell: (_h, { row }) => (
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
const promptTableColumns = shallowRef<ITableColumn<IMCPServerPrompt>[]>([
  {
    title: t('Prompt 名称'),
    colKey: 'name',
    cell: (_h, { row }) => {
      if (!row.name) {
        return '--';
      }

      return (
        <div class="flex-row">
          <div
            v-bk-tooltips={{
              content: row.name ?? '',
              placement: 'top',
              disabled: !row.isOverflow,
              extCls: 'max-w-480px',
            }}
            class="truncate color-#4d4f56 mr-4px prompt-name"
            onMouseenter={(e: MouseEvent) =>
              promptTableRef.value?.handleCellEnter({
                e,
                row,
              })}
            onMouseleave={() =>
              promptTableRef.value?.handleCellLeave({ row })}
          >
            { row.name }
          </div>
          <bk-tag theme={row.is_public ? 'success' : 'warning'}>
            { t(row.is_public ? '公开' : '私有') }
          </bk-tag>
          {row.is_no_perm && (
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
const privatePromptColumns = shallowRef<ITableColumn<IMCPServerPrompt>[]>([
  {
    title: 'Prompt',
    colKey: 'name',
    ellipsis: true,
    cell: (_h, { row }) => {
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
      validator: (value: string) => value?.length > 0 && value.length <= toolNameLengthLimit.value,
      message: () => `${t('MCP Server 名称 + 工具名称不得超过 64 字符')}, ${t('剩余可输入 {count} 字符', { count: remainingToolNameCharacters.value })}`,
      trigger: 'change',
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
          ? sameNameItems.filter((item: IMCPServerTool) => item.id !== currentEditRowId)
          : sameNameItems;

        return filteredSameItems.length === 0;
      },
      message: t('工具名称不可重复'),
      trigger: 'blur',
    },
  ],
};

const methodTagThemeMap: Record<string, '' | 'success' | 'warning' | 'info' | 'danger'> = {
  POST: 'info',
  GET: 'success',
  DELETE: 'danger',
  PUT: 'warning',
  PATCH: 'info',
  ANY: 'success',
};

let resizeLayoutConfig: IResizeLayoutConfig = {
  min: 794,
  max: 800,
};

const gatewayId = computed<number | undefined>(() => gatewayStore.currentGateway?.id);
const isProgrammableGateway = computed<boolean>(() => gatewayStore.isProgrammableGateway);
const isEditMode = computed<boolean>(() => !!serverId);
const isEnablePrompt = computed<boolean>(() => featureFlagStore?.flags?.ENABLE_MCP_SERVER_PROMPT);
const stage = computed<IStageListOutput | undefined>(() =>
  stageList.value.find(sg => sg.id === formData.value.stage_id),
);
const stageName = computed<string>(() => stage.value?.name || '');
const serverNamePrefix = computed<string>(() => `${gatewayStore.currentGateway?.name}-${stageName.value}-`);
const sliderTitle = computed<string>(() => {
  return isEditMode.value
    ? t('编辑 {n}', { n: formData.value.name })
    : t('创建 MCP Server');
});
const toolTableEmptyType = computed<ITableEmptyType>(() => filterKeywordDebounced.value?.trim()?.toLowerCase()
  || toolFilterData.value?.method?.length > 0
  ? 'searchEmpty'
  : 'empty');
const filteredToolList = computed<IMCPServerTool[]>(() => {
  const keyword = filterKeywordDebounced.value.trim().toLowerCase();
  const methodsData = toolFilterData.value?.method ?? [];
  const currentResourceList = resourceList.value;

  return currentResourceList.filter((resource: IMCPServerTool) => {
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
const filteredPromptList = computed<IMCPServerPrompt[]>(() => {
  const hasSearchCondition = filterPromptValues.value.length > 0;
  if (hasSearchCondition) {
    handleSetLoading(true);
  }

  const searchConditions = {
    name: filterPromptValues.value.find(item => item.id === 'name')?.values[0]?.id ?? '',
    content: filterPromptValues.value.find(item => item.id === 'content')?.values[0]?.id ?? '',
    updated_by: filterPromptValues.value.find(item => item.id === 'updated_by')?.values[0]?.id ?? [],
    labels: filterPromptValues.value.find(item => item.id === 'labels')?.values.map(v => String(v.id)) ?? [],
  };
  const results = promptTableData.value?.filter((item: IMCPServerPrompt) => {
    const { name, code, content, updated_by = '', labels = [] } = item;
    let isMatch = true;

    // 匹配中英文名
    if (searchConditions.name) {
      const nameRegex = new RegExp(String(searchConditions.name), 'gi');
      isMatch = isMatch && (!!name?.match(nameRegex) || !!code?.match(nameRegex));
    }

    // 匹配内容
    if (searchConditions.content) {
      const contentRegex = new RegExp(String(searchConditions.content), 'gi');
      isMatch = isMatch && !!content?.match(contentRegex);
    }

    // 匹配修改人
    if (searchConditions.updated_by) {
      const userRegex = new RegExp(String(searchConditions.updated_by), 'gi');
      isMatch = isMatch && !!updated_by?.match(userRegex);
    }

    // 匹配标签
    if (searchConditions?.labels?.length) {
      // 表格项的labels与搜索标签有交集则匹配
      const hasLabel = searchConditions.labels.some((label: string) => (labels as string[]).includes(label));
      isMatch = isMatch && hasLabel;
    }

    return isMatch;
  });

  promptTableEmptyType.value = results.length < 1 && hasSearchCondition ? 'searchEmpty' : 'empty';

  return results;
});
// 预览和提交读取同一批选中项，行内编辑工具别名后两处会一起更新。
const activeSelections = computed<IMCPSelections[]>(() =>
  activeTab.value === 'tool' ? toolSelections.value : promptSelections.value);
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
const noValidStage = computed<boolean>(() =>
  stageList.value.length > 0 && stageList.value.every(sg => sg.status === 0));
const isCurrentStageValid = computed<boolean>(() =>
  stageList.value.find(sg => sg.id === formData.value.stage_id)?.status === 1);
const isShowPublicClient = computed(() => featureFlagStore?.flags?.ENABLE_MCP_SERVER_OAUTH2_PUBLIC_CLIENT);
const isShowPersonalClient = computed(() => featureFlagStore?.flags?.ENABLE_MCP_SERVER_OAUTH2_PERSONAL_CLIENT);
// 公开客户端
const isEnabledPublicClient = computed<boolean>(() =>
  isShowPublicClient.value && formData.value.oauth2_public_client_enabled,
);
// 个人令牌
const isEnabledPersonalClient = computed<boolean>(() =>
  isShowPersonalClient.value && formData.value.oauth2_personal_client_enabled,
);
// 处理工具oauth态
const isEnabledOAuth = computed<boolean>(() => isEnabledPublicClient.value || isEnabledPersonalClient.value);
// 选中的应用态工具数据
const appAuthStatusList = computed<IMCPSelections[]>(() => {
  if (!isEnabledOAuth.value) return [];
  return toolSelections.value.filter(item => renderOAuthConfig(item)?.app_verified_required);
});
// 选中工具项是否存在应用态或用户态数据
const isExistOAuthData = computed<boolean>(() =>
  isEnabledOAuth.value && toolSelections.value.some(auth =>
    renderOAuthConfig(auth).auth_verified_required || renderOAuthConfig(auth).app_verified_required,
  ),
);
const mcpServerName = computed(() => isEditMode.value ? formData.value.name : `${serverNamePrefix.value}${formData.value.name}`);
// 服务名称和工具名称共用 64 个字符的限额。
const toolNameLengthLimit = computed(() => 64 - mcpServerName.value.length);
const remainingToolNameCharacters = computed(() =>
  Math.max(0, toolNameLengthLimit.value - (toolNameRowData.value.tool_name?.length ?? 0)));
const personalTokenLink = computed(() => envStore?.env?.DOC_LINKS?.AUTH_PERSONAL_TOKEN);
// 翻页、加载内容或切换页签后，右侧预览按当前表格容器的高度调整。
const selectionPreviewStyle = computed(() => ({
  maxHeight: `${(activeTab.value === 'tool' ? toolTableHeight.value : promptTableHeight.value) + 32}px`,
}));

// 选择的工具配置解析
const renderOAuthConfig = (payload: IMCPSelections): IAuthConfig => {
  const config = payload?.contexts?.resource_auth?.config as string | IResourceAuthConfig;

  const defaultConfig: IAuthConfig = {
    auth_verified_required: false,
    app_verified_required: false,
    resource_perm_required: false,
  };

  if (typeof config === 'string') {
    try {
      return JSON.parse(config) as IAuthConfig;
    }
    catch {
      return defaultConfig;
    }
  }
  else if (config && typeof config === 'object') {
    return {
      auth_verified_required: config.auth_verified_required ?? false,
      app_verified_required: config.app_verified_required ?? false,
      resource_perm_required: config.resource_perm_required ?? false,
    };
  }
  else {
    return defaultConfig;
  }
};

/**
 * 获取公共异步数据（提取重复逻辑，降低耦合）
 * @param {boolean} isEnablePrompt  是否启用 Prompt 功能
 */
const fetchCommonData = async (isEnablePrompt: boolean) => {
  // 定义基础请求列表
  const requestList = isEditMode.value ? [] : [fetchStageList(), fetchCategoryList()];
  // 启用 Prompt 时，追加 Prompt 资源请求
  if (isEnablePrompt) {
    requestList.push(fetchPromptResources());
  }
  else {
    // 禁用 Prompt 时，过滤掉 prompt 相关的标签
    resourceTabList.value = resourceTabList.value.filter(item => !['prompt'].includes(item.value));
  }
  if (requestList.length) {
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
  }
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
  // 仅在 isShow 为 true 时执行后续逻辑
  if (!isShowVal) return;

  clearValidate();
  if (isEditMode.value) {
    // 需要优先获取分类列表，再从列表筛选不需要展示的分类
    await fetchCategoryList();
    await fetchServer();
  }
  getCommonListData();
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

const isToolSelected = (row: IMCPServerTool) => toolSelections.value.some(tool => tool.id === row.id);

const requiresShorterToolName = (row: IMCPServerTool) => {
  // 编辑旧配置时允许保留原先选中的工具。
  if (isEditMode.value && isToolSelected(row) && resourceNameList.value.includes(row.name)) return false;
  const toolName = row.tool_name ?? row.name ?? '';
  return toolName.length > toolNameLengthLimit.value;
};

// 已选工具后来缺失 OpenAPI 声明时，仍要允许用户取消勾选。
const isToolSelectionDisabled = (row: IMCPServerTool) =>
  row.has_openapi_schema ? requiresShorterToolName(row) : !isToolSelected(row);

const getToolSelectionTip = (row: IMCPServerTool) => {
  if (row.has_openapi_schema) {
    return requiresShorterToolName(row)
      ? t('MCP Server 名称 + 工具名称不得超过 64 字符，超限可能导致部分客户端调用失败。')
      : '';
  }
  if (isProgrammableGateway.value) return t('可编程网关请参考框架文档，配置资源请求参数声明');
  return isToolSelected(row)
    ? t('该资源数据有变更，请确认一下请求参数是否正确配置。')
    : t('该资源未配置请求参数声明，不能添加到 MCP');
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
    // @ts-expect-error 返回 true 代表无私有 Prompt，可继续
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
              tableData={privateData}
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

const handleSubmit = async (): Promise<void> => {
  // 基础表单验证
  const basicFormValidate = serverBasicFormRef.value?.validateForm();
  const isBasicValidate = typeof basicFormValidate === 'boolean' && basicFormValidate;
  try {
    await formRef.value?.validate();
  }
  catch {
    if (!isBasicValidate) {
      (basicFormValidate as { focus?: () => void }).focus?.();
      handleScrollView((basicFormValidate as { $el?: HTMLElement }).$el!);
      return;
    }
  }

  if (!isBasicValidate) {
    handleScrollView(basicFormValidate?.$el);
    return;
  }

  let isValidate = toolSelections.value.length > 0;

  if (!isValidate) {
    handleScrollView(resourceRef.value!);
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
    let categoryIds = categoriesList.value
      .filter(cg => formData.value.categories.includes(cg.name))
      .map(cname => cname.id);
    if (hiddenCategoriesList.value.length) {
      categoryIds = [...categoryIds, ...hiddenCategoriesList.value.map(item => item.id)];
    }
    const config = {
      resource_names: toolSelections.value.map(item => item.name),
      tool_names: toolSelections.value.map(item => item.tool_name ?? item.name),
      prompts: isEnablePrompt.value ? promptSelections.value : undefined,
      category_ids: categoryIds,
    };
    if (isEditMode.value) {
      const {
        title,
        description,
        is_public,
        oauth2_public_client_enabled,
        oauth2_personal_client_enabled,
        raw_response_enabled,
        protocol_type,
        labels,
      } = formData.value;
      const params = {
        ...config,
        description,
        is_public,
        oauth2_public_client_enabled,
        oauth2_personal_client_enabled,
        raw_response_enabled,
        protocol_type,
        labels,
        title,
      };
      await patchServer(gatewayId.value!, serverId!, params);
      Message({
        theme: 'success',
        message: t('编辑成功'),
      });
    }
    else {
      const params = {
        ...config,
        ...formData.value,
        name: mcpServerName.value,
      };
      await createServer(gatewayId.value!, params);
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

const fetchStageList = async ({ preserveAliases = false } = {}) => {
  const response = await getStageList(gatewayId.value!);
  stageList.value = response || [];
  if (!formData.value.stage_id) {
    formData.value.stage_id = stageList.value.find(sg => sg.status === 1)?.id ?? 0;
  }
  if (formData.value.stage_id) {
    await fetchStageResources({ preserveAliases });
  }
};

// 兼容旧版浏览器无法识别requestIdleCallback
const scheduleIdle = (callback: () => void, timeout = 3000): void => {
  if (typeof requestIdleCallback === 'function') {
    requestIdleCallback(callback, { timeout });
  }
  else {
    setTimeout(callback, 0);
  }
};

/**
 * 工具资源渲染（分片处理，不阻塞主线程）
 * @param resource_names 资源名称列表
 * @param tool_names 工具名称列表
 */
const renderToolResource = (resource_names: string[], tool_names: string[]) => {
  if (clearMapTimer) {
    clearTimeout(clearMapTimer);
    clearMapTimer = null;
  }

  try {
    if (!resource_names?.length) {
      return;
    }

    // 清空复用的Map（避免旧数据干扰）
    resourceNameToIndexMap.clear();
    const chunkSize = 50;
    let currentIndex = 0;
    const hasToolNames = tool_names?.length > 0;

    const processChunk = () => {
      const endIndex = Math.min(currentIndex + chunkSize, resource_names.length);
      for (let i = currentIndex; i < endIndex; i++) {
        resourceNameToIndexMap.set(resource_names[i], i);
      }
      currentIndex = endIndex;

      // 未处理完则继续分片
      if (currentIndex < resource_names.length) {
        // 兼容旧版浏览器无法识别requestIdleCallback
        scheduleIdle(processChunk);
        return;
      }

      // 给 resourceList 追加 tool_name
      const updatedResourceList = resourceList.value.map((item: IMCPServerTool) => {
        const nameIndex = resourceNameToIndexMap.get(item.name);
        return {
          ...item,
          tool_name: hasToolNames && nameIndex !== undefined ? (tool_names[nameIndex] || item.name) : item.name,
        };
      });
      resourceList.value = updatedResourceList;

      // 过滤出匹配的资源项
      const resourceToolData = updatedResourceList.filter(item =>
        resourceNameToIndexMap.has(item.name),
      );
        // 分片更新：先更20条，快速渲染
      toolSelections.value = resourceToolData.slice(0, 20).map(({
        id,
        name,
        tool_name,
        contexts,
      }: IMCPToolSelections) => {
        return {
          name,
          id,
          tool_name: tool_name || name,
          contexts,
        };
      });

      // 剩余数据异步更新，确保DOM挂载
      setTimeout(() => {
        toolSelections.value = resourceToolData.map(({ name, tool_name, id, contexts }: IMCPSelections) => {
          return {
            name,
            id,
            tool_name: tool_name || name,
            contexts,
          };
        });
        toolTableRef.value?.setSelectionData(toolSelections.value as IMCPServerTool[]);
        // 延迟清空Map，确保数据使用完成
        clearMapTimer = setTimeout(() => {
          resourceNameToIndexMap.clear();
          clearMapTimer = null;
        }, 500);
      }, 0);
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
        // 兼容旧版浏览器无法识别requestIdleCallback
        scheduleIdle(processPromptChunk);
      }
      else {
        // 处理无权限数据
        noPermPrompt.value = prompts
          .filter((item: IMCPServerPrompt) => !authorizedPromptIds.has(item.id))
          .map((item: IMCPServerPrompt) => ({
            ...item,
            is_no_perm: true,
          }));

        // 分片更新
        promptSelections.value = prompts.slice(0, 20).map((item: IMCPServerPrompt) => ({
          ...item,
          is_no_perm: !authorizedPromptIds.has(item.id),
        }));

        setTimeout(() => {
          promptSelections.value = prompts.map((item: IMCPServerPrompt) => ({
            ...item,
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
    const response = await getServer(gatewayId.value!, serverId!);

    const {
      name = '',
      title = '',
      description = '',
      url = '',
      protocol_type = 'streamable_http',
      labels = [] as string[],
      oauth2_public_client_enabled = false,
      oauth2_personal_client_enabled = false,
      is_public = true,
      raw_response_enabled = false,
      stage = { id: 0 },
      resource_names = [],
      tool_names = [],
      prompts = [],
      categories = [],
    } = (response ?? {}) as IMCPServerRetrieveOutput;

    formData.value = {
      ...formData.value,
      name,
      title,
      url,
      description,
      labels,
      is_public,
      oauth2_public_client_enabled,
      oauth2_personal_client_enabled,
      raw_response_enabled,
      stage_id: stage.id || 0,
      protocol_type,
      categories: (categories as IMCPServerCategory[]).map((item: IMCPServerCategory) => item.name || ''),
    };
    // 缓存已存量的工具
    resourceNameList.value = resource_names;
    // 获取已存在但不需要显示在页面上的分类
    hiddenCategoriesList.value = (categories as IMCPServerCategory[]).filter((item: IMCPServerCategory) =>
      !categoriesList.value.map((v: IMCPServerCategory) => v.name).includes(item.name));

    try {
      await fetchStageList();
    }
    finally {
      // 启动资源渲染（微任务执行，不阻塞主线程）
      queueMicrotask(() => renderToolResource(resource_names, tool_names));
      queueMicrotask(() => renderPromptResource(prompts as IMCPServerPrompt[]));
    }
  }
  catch {
    formData.value = cloneDeep(defaultFormData.value);
  }
  finally {
    initSidebarFormData(getDiffFormData());
  }
};

// 收集当前未提交的自定义工具别名（排除与资源原名一致的默认值），刷新候选列表时按资源 ID 保留
const collectCustomToolAliases = () => {
  const aliasById = new Map<number, string>();
  for (const item of resourceList.value) {
    if (item.id != null && item.tool_name && item.tool_name !== item.name) {
      aliasById.set(item.id, item.tool_name);
    }
  }
  for (const item of toolSelections.value) {
    if (item.id != null && item.tool_name && item.tool_name !== item.name && !aliasById.has(item.id)) {
      aliasById.set(item.id, item.tool_name);
    }
  }
  return aliasById;
};

const fetchStageResources = async ({ preserveAliases = false } = {}) => {
  const aliasById = preserveAliases ? collectCustomToolAliases() : undefined;
  try {
    searchLoading.value = true;
    if (stage.value?.resource_version?.id) {
      const response = await getVersionDetail(
        gatewayId.value!,
        stage.value.resource_version.id,
        {
          stage_id: stage.value.id,
          // @ts-expect-error source 参数用于 MCP Server 筛选
          source: 'mcp_server',
        },
      );
      const nextResources = response.resources || [];
      resourceList.value = aliasById?.size
        ? nextResources.map((item) => {
          const alias = aliasById.get(item.id);
          return alias
            ? {
              ...item,
              tool_name: alias,
            }
            : item;
        })
        : nextResources;
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
  const res: IMCPServerRemotePromptsOutput = await getServerPrompts(gatewayId.value!);
  promptTableData.value = res?.prompts ?? [];

  if (promptTableData.value.length) {
    curPromptData.value = promptTableData.value[0];
    const allLabels = promptTableData.value.map((item: IMCPServerPrompt) => item?.labels ?? []).flat(1);
    promptLabels.value = uniq(allLabels).map((item: string) => {
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
    const res: IMCPServerRemotePromptsOutput = await getServerPromptsDetail(
      gatewayId.value!,
      {
        ids: [curPromptData.value.id as number],
      },
    );
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
  const res = await getMcpCategoryList(gatewayId.value!);
  categoriesList.value = (res ?? []).map((cg: IMCPServerCategory) => {
    return {
      ...cg,
      tips: cg.description,
      id: cg.id,
    };
  });
};

const handlePromptRowClick = ({ e, row }: RowEventContext<TableRow<IMCPServerPrompt>>) => {
  e?.stopPropagation();
  const isCheckbox = (e.target as HTMLElement).closest('.custom-ag-table-checkbox');
  const isRepeat = `${curPromptData.value.id}&${curPromptData.value.code}` === `${row.id}&${row.code}`;
  if (isCheckbox || isRepeat) {
    return;
  }
  curPromptData.value = row;
  fetchPromptResourcesDetail();
};

const updateSliderContentHeight = () => {
  // 动态获取footer高度，计算内容区域最大高度
  setTimeout(() => {
    const modalContentEl = document.querySelector('.create-mcp-slider .bk-modal-content');
    const footerH = footerRef.value?.offsetHeight;
    if (modalContentEl) {
      (modalContentEl as HTMLElement).style.maxHeight = !isEnabledOAuth.value
        ? (modalContentEl as HTMLElement).style.height
        : `calc(100% - ${(footerH ?? 0) + 62}px)`;
    }
  });
};

const removePreviewSelection = ({ id, name }: IMCPToolSelections) => {
  const keepOtherItems = (item: IMCPToolSelections) => item.id !== id || item.name !== name;
  if (activeTab.value === 'tool') {
    toolSelections.value = toolSelections.value.filter(keepOtherItems);
    toolTableRef.value?.setSelectionData(toolSelections.value as IMCPServerTool[]);
  }
  else {
    promptSelections.value = promptSelections.value.filter(keepOtherItems);
    promptTableRef.value?.setSelectionData(promptSelections.value);
  }
};

const handleToolSelectionChange = ({ selections }: ITableSelection<TableRow<IMCPServerTool>>) => {
  toolSelections.value = selections;
  updateSliderContentHeight();
};

const handlePromptSelectionChange = ({ selections }: ITableSelection<TableRow<IMCPServerPrompt>>) => {
  promptSelections.value = selections;
};

const handleToolFilterChange = (filters: FilterValue): void => {
  toolFilterData.value = { ...filters };
};

const handleEditToolName = (row: IMCPServerTool) => {
  toolNameRowData.value = {
    ...row,
    tool_name: row.tool_name ?? row.name,
    isShow: true,
  };
  setTimeout(() => {
    toolNameInputRef.value?.focus?.();
  }, 200);
};

const handleConfirmToolName = async (row: IMCPServerTool) => {
  try {
    await toolNameRef.value?.validate();
    const alias = toolNameRowData.value.tool_name;
    const sourceTool = resourceList.value.find(tool => tool.id === row.id);
    const selectedTool = toolSelections.value.find(tool => tool.id === row.id);
    if (sourceTool) sourceTool.tool_name = alias;
    if (selectedTool) selectedTool.tool_name = alias;
    handleCancelToolName();
  }
  catch {
    toolNameRowData.value.isShow = true;
  }
};

const handleCancelToolName = () => {
  toolNameRowData.value.isShow = false;
  setTimeout(() => {
    toolNameRowData.value = {};
  }, 200);
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
  const typeMap: Record<string, () => void> = {
    tool: () => {
      toolSelections.value = [];
      toolTableRef.value?.handleResetSelection();
    },
    prompt: () => {
      promptSelections.value = [];
      promptTableRef.value?.handleResetSelection();
    },
    all: () => {
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
};

const handlePromptClearSelection = () => {
  promptSelections.value = [];
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
  await fetchStageList({ preserveAliases: true });
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

const handleToolNameClick = (row: IMCPServerTool) => {
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
  activeTab.value = tab as 'tool' | 'prompt';
  const tabMap: Record<string, () => void> = {
    tool: () => {
      if (toolSelections.value.length) {
        nextTick(() => {
          toolTableRef.value?.setSelectionData(toolSelections.value as IMCPServerTool[]);
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

const handleViewDoc = () => {
  window.open(personalTokenLink.value, '_blank');
};

const resetSliderData = () => {
  formData.value = cloneDeep(defaultFormData.value);
  stageList.value = [];
  resourceList.value = [];
  toolSelections.value = [];
  promptSelections.value = [];
  noPermPrompt.value = [];
  categoriesList.value = [];
  hiddenCategoriesList.value = [];
  resourceNameList.value = [];
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

<!-- eslint-disable-next-line vue/enforce-style-attribute -- 覆盖挂载在 body 下的提示框与气泡弹层样式 -->
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
    overflow-x: hidden !important;
    background-color: #f5f7fa;
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
          visibility: visible;
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
      height: auto !important;
      padding: 0;
    }
  }
}

.resource-table-form-item {
  border: 1px solid #dcdee5;
  border-radius: 2px 2px 0 0;
  box-sizing: border-box;

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
      text-align: center;
      cursor: pointer;
      border-top: 1px solid #dcdee5;
      border-right: 1px solid #dcdee5;
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
        color: #3a84ff;
        background-color: #fff;
      }
    }
  }

  .resource-tips {
    font-size: 12px;
    line-height: 16px;
    color: #979ba5;
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
            background-color: #fff;
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
