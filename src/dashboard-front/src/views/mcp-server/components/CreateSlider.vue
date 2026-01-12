/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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
    class="create-slider"
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
            <BkFormItem
              :label="t('环境')"
              property="stage_id"
              :rules="[
                {
                  required: true,
                  message: t('环境不能为空'),
                  trigger: 'blur',
                },
              ]"
              required
            >
              <BkSelect
                v-model="formData.stage_id"
                :clearable="false"
                :disabled="isEditMode || noValidStage"
                @change="handleStageSelectChange"
              >
                <BkOption
                  v-for="_stage in stageList"
                  :id="_stage.id"
                  :key="_stage.id"
                  :disabled="!_stage.resource_version?.version"
                  :name="_stage.name"
                />
              </BkSelect>
            </BkFormItem>
            <BkFormItem
              :label="t('服务名称')"
              property="name"
              :rules="[
                {
                  required: true,
                  message: t('服务名称不能为空'),
                  trigger: 'blur',
                },
              ]"
              required
            >
              <BkInput
                ref="nameRef"
                v-model="formData.name"
                :placeholder="t('请输入小写字母、数字、连字符(-)')"
                :disabled="isEditMode || noValidStage"
                :prefix="(isEditMode || noValidStage) ? undefined : serverNamePrefix"
              />
              <div class="name-help-text">
                <div class="lh-22px text-body">
                  {{ t('唯一标识，以网关名称和环境名称为前缀，创建后不可更改') }}
                </div>
              </div>
            </BkFormItem>
            <BkFormItem
              :label="t('服务展示名')"
              property="title"
              :rules="[
                {
                  validator: (value: string) => value?.trim()?.length >= 3,
                  message: t('服务展示名不能小于3个字符'),
                  trigger: 'blur',
                },
              ]"
              class="custom-form-item-required"
            >
              <BkInput
                ref="titleRef"
                v-model="formData.title"
                :placeholder="t('请输入3-32个字符的服务展示名称')"
                :maxlength="32"
                clearable
              />
            </BkFormItem>
            <BkFormItem
              :label="t('描述')"
              property="description"
              :rules="[
                {
                  validator: (value: string) => value?.trim()?.length >= 10,
                  message: t('描述不能小于10个字符'),
                  trigger: 'blur',
                },
              ]"
              class="custom-form-item-required"
            >
              <BkInput
                ref="descriptionRef"
                v-model="formData.description"
                type="textarea"
                :minlength="10"
                :maxlength="2048"
                :rows="4"
                :disabled="noValidStage"
                :placeholder="t('请输入10-2048个字符的描述')"
                clearable
                show-word-limit
                resize
              />
            </BkFormItem>
            <BkFormItem
              :label="t('标签')"
              property="labels"
            >
              <BkTagInput
                v-model="formData.labels"
                :disabled="noValidStage"
                allow-create
                collapse-tags
                has-delete-icon
              />
            </BkFormItem>
            <BkFormItem
              class="form-protocol-type"
              property="protocol_type"
              required
            >
              <template #label>
                <span class="connect-method">
                  {{ t('连接方式') }}
                </span>
                <span class="color-#979ba5 text-12px ml-16px">
                  <InfoLine class="v-mid" />
                  {{ t('切换连接方式后，客户端需要基于新协议重新建立连接') }}
                </span>
              </template>
              <BkRadioGroup v-model="formData.protocol_type">
                <BkRadio
                  v-for="item of MCP_PROTOCOL_TYPE"
                  :key="item.value"
                  :label="item.value"
                >
                  {{ item.label }}
                </BkRadio>
                <div class="text-14px color-#979ba5 lh-32px ml-8px">
                  ({{ t('不推荐，建议使用Streamable HTTP') }})
                </div>
              </BkRadioGroup>
              <div class="flex items-center bg-#f5f7fa h-32px text-12px pl-8px url">
                <div class="min-w-55px color-#4d4f56">
                  {{ t('访问地址') }}:
                </div>
                <div
                  v-bk-tooltips="{
                    placement:'top',
                    content: previewUrl,
                    disabled: !isOverflow,
                    extCls: 'max-w-1180px',
                  }"
                  class="truncate color-#313238"
                  @mouseenter="(e: MouseEvent) => handleMouseenter(e)"
                  @mouseleave="handleMouseleave"
                >
                  {{ previewUrl }}
                </div>
                <div class="ml-8px pr-8px cursor-pointer hover:text-#3a84ff">
                  <AgIcon
                    name="copy-info"
                    @click.stop="handleCopyClick"
                  />
                </div>
              </div>
            </BkFormItem>
            <BkFormItem
              :label="t('是否公开')"
              property="is_public"
              required
            >
              <BkSwitcher
                v-model="formData.is_public"
                :disabled="noValidStage"
                theme="primary"
                class="mr-4px"
              />
              <span class="text-12px color-#979ba5">{{
                t('不公开则不会展示到 MCP 市场，且蓝鲸应用无法申请主动申请权限，只能由网关管理员给应用主动授权')
              }}</span>
            </BkFormItem>
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
                class="flex items-center justify-between pl-24px pr-16px mt-16px mb-16px"
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
                        class="p-16px min-w-280px"
                      >
                        <div class="selector-title">
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
                          />
                        </BkLoading>
                      </div>
                      <template v-if="['prompt'].includes(activeTab)">
                        <BkResizeLayout
                          initial-divide="366px"
                          class="h-full!"
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
                                />
                              </BkLoading>
                            </div>
                          </template>
                          <template #main>
                            <BkLoading :loading="promptDetailLoading">
                              <div class="mt-16px pl-24px pr-24px">
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
                                          extCls: 'max-w-880px',
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
                        :style="{ width: `${resizePreviewWidth}px`}"
                        class="result-preview"
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
                          >
                            <div
                              v-for="(checks, index) in renderPreviewByTab"
                              :key="index"
                              class="list-main"
                            >
                              <div class="list-item">
                                <div class="w-90% flex items-center">
                                  <div
                                    v-bk-tooltips="{
                                      placement:'top',
                                      content: checks.name,
                                      disabled: !isOverflow,
                                      extCls: 'max-w-290px',
                                    }"
                                    class="color-#3a84ff text-12px truncate name"
                                    @mouseenter="(e: MouseEvent) => handleMouseenter(e)"
                                    @mouseleave="handleMouseleave"
                                  >
                                    {{ checks.name }}
                                  </div>
                                  <BkTag
                                    v-if="!['tool'].includes(checks.mode_type)"
                                    :theme="checks?.is_public ? 'success' : 'warning'"
                                    class="ml-4px"
                                  >
                                    {{ checks?.is_public ? t('公开') : t('私有') }}
                                  </BkTag>
                                </div>
                                <AgIcon
                                  class="delete-icon"
                                  name="icon-close"
                                  size="24"
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
          </BkForm>
        </div>
      </div>
    </template>
    <template #footer>
      <div class="ml-16px">
        <BkButton
          :disabled="noValidStage"
          class="w-100px!"
          theme="primary"
          :loading="submitLoading"
          @click="handleSubmit"
        >
          {{ t('确定') }}
        </BkButton>
        <BkButton
          class="w-100px! ml-4px"
          @click="handleCancel"
        >
          {{ t('取消') }}
        </BkButton>
      </div>
    </template>
  </BkSideslider>
</template>

<script lang="tsx" setup>
import { cloneDeep, escape, uniq, uniqBy } from 'lodash-es';
import type { PrimaryTableProps } from '@blueking/tdesign-ui';
import { type ISearchItem } from 'bkui-lib/search-select/utils';
import { InfoLine } from 'bkui-lib/icon';
import { getStageList } from '@/services/source/stage';
import { getVersionDetail } from '@/services/source/resource';
import type { IFormMethod, ITableMethod } from '@/types/common';
import { refDebounced } from '@vueuse/core';
import {
  Divider,
  Form,
  Input,
  Message,
  PopConfirm,
  ResizeLayout,
} from 'bkui-vue';
import {
  type IMCPServerPrompt,
  type IMCPServerTool,
  createServer,
  getServer,
  getServerPrompts,
  getServerPromptsDetail,
  patchServer,
} from '@/services/source/mcp-server';
import { usePopInfoBox, useSidebar } from '@/hooks';
import { HTTP_METHODS, MCP_PROTOCOL_TYPE } from '@/constants';
import { copy } from '@/utils';
import {
  useEnv,
  useFeatureFlag,
  useGateway,
} from '@/stores';
import i18n from '@/locales';
import TableEmpty from '@/components/table-empty/Index.vue';
import AgTable from '@/components/ag-table/Index.vue';

interface IProps { serverId?: number }

interface FormData {
  name: string
  title: string
  description: string
  stage_id: number | undefined
  is_public: boolean
  labels: string[]

}

const { serverId = 0 } = defineProps<IProps>();

const emit = defineEmits<{ updated: [] }>();

const router = useRouter();
const gatewayStore = useGateway();
const envStore = useEnv();
const featureFlagStore = useFeatureFlag();
const { initSidebarFormData, isSidebarClosed } = useSidebar();

const { t } = i18n.global;

let loadingTimer: NodeJS.Timeout | null = null;

const nameRef = ref<InstanceType<typeof Input>>(null);
const titleRef = ref<InstanceType<typeof Input>>(null);
const descriptionRef = ref<InstanceType<typeof Input>>(null);
const resourceRef = ref<InstanceType<typeof HTMLDivElement>>(null);
const resizeLayoutRef = ref<InstanceType<typeof ResizeLayout>>(null);
const toolTableRef = ref<InstanceType<typeof AgTable> & ITableMethod>();
const promptTableRef = ref<InstanceType<typeof AgTable> & ITableMethod>();
const formRef = ref<InstanceType<typeof Form> & IFormMethod>();
const toolNameRef = ref<InstanceType<typeof Form> & IFormMethod>();
const popoverConfirmRef = ref<InstanceType<typeof PopConfirm>>();
const defaultFormData = ref<FormData>({
  name: '',
  description: '',
  protocol_type: 'streamable_http',
  stage_id: 0,
  is_public: true,
  labels: [],
});
const formData = ref<FormData>(cloneDeep(defaultFormData.value));
const toolNameRowData = ref({});
const isShow = ref(false);
const submitLoading = ref(false);
const searchLoading = ref(false);
const promptDetailLoading = ref(false);
const isOverflow = ref(false);
const url = ref('');
const filterKeyword = ref('');
const activeTab = ref<'tool' | 'prompt'>('tool');
const promptTableEmptyType = ref<'empty' | 'search-empty'>('empty');
const resizePreviewWidth = ref(297);
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
                        <BkFormItem
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
                        </BkFormItem>
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
  min: 888,
  max: 1040,
};

const isEnablePrompt = computed(() => featureFlagStore?.flags?.ENABLE_MCP_SERVER_PROMPT);
const isEditMode = computed(() => !!serverId);
const gatewayId = computed(() => gatewayStore?.currentGateway?.id);
const stage = computed(() => stageList.value.find(stage => stage.id === formData.value.stage_id));
const stageName = computed(() => stage.value?.name || '');
const serverNamePrefix = computed(() => `${gatewayStore.currentGateway!.name}-${stageName.value}-`);
const sliderTitle = computed(() => {
  return isEditMode.value
    ? t('编辑 {n}', { n: `${serverNamePrefix.value}${formData.value.name}` })
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
  handleSetLoading(true);

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
const previewUrl = computed(() => {
  const prefix = envStore.env.BK_API_RESOURCE_URL_TMPL
    .replace('{api_name}', 'bk-apigateway')
    .replace('{stage_name}', 'prod')
    .replace('{resource_path}', 'api/v2/mcp-servers');
  return `${prefix || ''}/${serverNamePrefix.value}${formData.value.name}/${!['sse'].includes(formData.value.protocol_type)
    ? 'mcp'
    : formData.value.protocol_type}/`;
});
const escapedCodeContent = computed(() => {
  return escape(curPromptData.value?.content ?? '');
});

watch(isShow, async () => {
  if (isShow.value) {
    clearValidate();
    if (isEnablePrompt.value) {
      await Promise.allSettled([
        fetchStageList(),
        fetchPromptResources(),
      ]);
    }
    else {
      resourceTabList.value = resourceTabList.value.filter(item => !['prompt'].includes(item.value));
      await fetchStageList();
    }
    initSidebarFormData(getDiffFormData());
    if (isEditMode.value) {
      await fetchServer();
    }
  }
});

const getDiffFormData = () => {
  return {
    formData: formData.value,
    toolSelections: toolSelections.value,
    promptSelections: promptSelections.value,
  };
};

const resetResizeLayout = () => {
  nextTick(() => {
    const modalContentEl = document.querySelector('.create-slider .bk-modal-content');
    if (modalContentEl) {
      modalContentEl.scrollTop = 0;
    }
    if (!resizeLayoutRef.value) {
      return;
    }
    const asideLayout = resizeLayoutRef.value.asideRef;
    if (asideLayout) {
      Object.assign(asideLayout.style, {
        width: '888px',
        maxWidth: '1040px',
        minWidth: '888px',
      });
    }
  });
};

const toolDisabledSelection = (row) => {
  row.selectionTip = t(toolSelections.value.map(item => item.name).includes(row.name) && !row.has_openapi_schema
    ? '该资源数据有变更，请确认一下请求参数是否正确配置。'
    : '该资源未配置请求参数声明，不能添加到 MCP');
  return !row.has_openapi_schema;
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
  resizePreviewWidth.value = 1182 - resizeWidth;
};

/**
 * 检查是否存在私有Prompt并弹出风险提示框
 * @returns Promise<boolean> - 确认继续返回true，取消返回false
 */
const isExistPrivatePrompt = (): Promise<boolean> => {
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
  try {
    await formRef.value?.validate();
  }
  catch {
    const {
      name,
      title,
      description,
    } = formData.value;
    // 自动focus到必填项
    if (!name) {
      nameRef.value?.focus();
      handleScrollView(nameRef.value?.$el);
      return;
    }
    if (!title?.trim().length < 3) {
      titleRef.value?.focus();
      handleScrollView(titleRef.value?.$el);
      return;
    }
    if (!description.length < 10) {
      titleRef.value?.focus();
      handleScrollView(titleRef.value?.$el);
      return;
    }
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

  const currentGatewayId = gatewayStore.currentGateway?.id;

  try {
    submitLoading.value = true;
    let params = {
      resource_names: toolSelections.value.map(item => item.name),
      tool_names: toolSelections.value.map(item => item.tool_name),
      prompts: isEnablePrompt.value ? promptSelections.value : undefined,
    };
    if (isEditMode.value) {
      const { description, is_public, protocol_type, labels, title } = formData.value as FormData;
      params = Object.assign(params, {
        description,
        is_public,
        protocol_type,
        labels,
        title,
      });
      await patchServer(currentGatewayId, serverId, params);
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
      await createServer(currentGatewayId, params);
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

const noValidStage = computed(() => stageList.value.every(stage => stage.status === 0));

const isCurrentStageValid = computed(() =>
  stageList.value.find(stage => stage.id === formData.value.stage_id)?.status === 1);

const fetchStageList = async () => {
  const response = await getStageList(gatewayId.value);
  stageList.value = response || [];
  const validStage = stageList.value.find(stage => stage.status === 1);
  formData.value.stage_id = validStage?.id ?? undefined;
  if (formData.value.stage_id) {
    await fetchStageResources();
  }
};

const fetchServer = async () => {
  try {
    const response = await getServer(gatewayId.value, serverId!);
    const {
      name = '',
      title = '',
      description = '',
      protocol_type = 'streamable_http',
      labels = [],
      is_public = true,
      stage = { id: 0 },
      resource_names = [],
      tool_names = [],
      prompts = [],
    } = response ?? {};
    formData.value = {
      ...formData.value,
      name,
      title,
      description,
      labels,
      is_public,
      stage_id: stage.id || 0,
      protocol_type,
    };
    url.value = response?.url ?? '';
    // 仅当资源名称数组有有效数据时执行逻辑
    if (resource_names?.length) {
      const resourceNameToIndexMap = new Map();
      resource_names.forEach((name, index) => {
        resourceNameToIndexMap.set(name, index);
      });
      const hasToolNames = tool_names?.length > 0;

      resourceList.value.forEach((item) => {
        const nameIndex = resourceNameToIndexMap.get(item.name);
        if (hasToolNames && nameIndex !== undefined && nameIndex > -1) {
          item.tool_name = tool_names[nameIndex] || item.name;
        }
      });

      const resourceToolData = resourceList.value.filter(item =>
        resourceNameToIndexMap.has(item.name),
      );

      toolSelections.value = resourceToolData.map(({ name, id }) => {
        const correctIndex = resourceNameToIndexMap.get(name);
        const toolName = hasToolNames && correctIndex !== undefined
          ? tool_names[correctIndex] || ''
          : '';

        return {
          name,
          id,
          mode_type: 'tool',
          tool_name: toolName,
        };
      });

      toolTableRef.value?.setSelectionData(toolSelections.value);
      resourceNameToIndexMap.clear();
    }
    // 渲染prompt勾选数据
    if (prompts.length) {
      // 处理已经是绑定的但是列表里面没有这个prompt的无权限数据
      const authorizedPromptIds = new Set(promptTableData.value.map(item => item.id));
      noPermPrompt.value = prompts.filter(item => !authorizedPromptIds.has(item.id)).map((item) => {
        return {
          ...item,
          is_no_perm: !authorizedPromptIds.has(item.id),
        };
      });
      promptSelections.value = prompts.map(item => ({
        ...item,
        mode_type: 'prompt',
        is_no_perm: !authorizedPromptIds.has(item.id),
      }));
      if (noPermPrompt.value.length) {
        promptTableData.value = [...promptTableData.value, ...noPermPrompt.value];
        if (Object.keys(curPromptData.value).length === 0 && promptTableData.value.length) {
          curPromptData.value = { ...promptTableData.value[0] };
        }
      }
      promptTableRef.value?.setSelectionData(promptSelections.value);
    }
    allSelections.value = [...toolSelections.value, ...promptSelections.value];
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
    if (stage.value && stage.value.resource_version?.id) {
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
  if (!gatewayStore.currentGateway?.id) return;
  const res = await getServerPrompts(gatewayStore.currentGateway.id);
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
    const res = await getServerPromptsDetail(gatewayStore.currentGateway?.id, { ids: [curPromptData.value.id] });
    curPromptData.value = Object.assign(curPromptData.value, res?.prompts?.[0] ?? {});
  }
  catch {
    curPromptData.value = {};
  }
  finally {
    promptDetailLoading.value = false;
  }
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

const handleSelectionChange = (selections: any[], type: 'tool' | 'prompt') => {
  const filteredItems = allSelections.value.filter(item => item.mode_type !== type);
  const mergedItems = [...filteredItems, ...selections];
  const uniqueItems = uniqBy(mergedItems, 'id');
  allSelections.value = [...uniqueItems];
};

const handleToolSelectionChange: PrimaryTableProps['onSelectChange'] = ({ selections }) => {
  toolSelections.value = selections;
  if (!selections.length) {
    allSelections.value = allSelections.value.filter(item => item.mode_type !== 'tool');
  }
  else {
    const toolItems = selections.map(item => ({
      ...item,
      mode_type: 'tool',
    }));
    handleSelectionChange(toolItems, 'tool');
  }
};

const handlePromptSelectionChange: PrimaryTableProps['onSelectChange'] = ({ selections }) => {
  promptSelections.value = selections;
  if (!selections.length) {
    allSelections.value = allSelections.value.filter(item => item.mode_type !== 'prompt');
  }
  else {
    const promptItems = selections.map(item => ({
      ...item,
      mode_type: 'prompt',
    }));
    handleSelectionChange(promptItems, 'prompt');
  }
};

const handleToolFilterChange: PrimaryTableProps['onFilterChange'] = (filters) => {
  toolFilterData.value = { ...filters };
};

const handleEditToolName = (row: IMCPServerTool) => {
  const bodyEl = document.querySelector('body');
  if (bodyEl) {
    bodyEl.classList.add('overflow-hidden');
  }
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
      selectData.tool_name = row.tool_name;
    }
    handleCancelToolName();
  }
  catch {
    toolNameRowData.value.isShow = true;
  }
};

const handleCancelToolName = () => {
  toolNameRowData.value = {};
  const bodyEl = document.querySelector('body');
  if (bodyEl) {
    bodyEl.classList.remove('overflow-hidden');
  }
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

const handleToolClearSelection = () => {
  toolSelections.value = [];
  allSelections.value = allSelections.value.filter(item => !['tool'].includes(item.mode_type));
};

const handlePromptClearSelection = () => {
  promptSelections.value = [];
  allSelections.value = allSelections.value.filter(item => ['tool'].includes(item.mode_type));
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

const handleCopyClick = () => {
  copy(previewUrl.value);
};

const resetSliderData = () => {
  formData.value = cloneDeep(defaultFormData.value);
  stageList.value = [];
  resourceList.value = [];
  toolSelections.value = [];
  promptSelections.value = [];
  allSelections.value = [];
  noPermPrompt.value = [];
  url.value = '';
  filterKeyword.value = '';
  activeTab.value = 'tool';
  curPromptData.value = {};
  resizeLayoutConfig = {
    min: 880,
    max: 1040,
  };
  toolFilterData.value = {};
};

const handleScrollView = (el: HTMLInputElement | HTMLElement) => {
  el.scrollIntoView({
    behavior: 'smooth',
    block: 'center',
  });
};

const handleBeforeClose = () => {
  const results = isSidebarClosed(JSON.stringify(getDiffFormData()));
  return results;
};

const handleCancel = () => {
  resetResizeLayout();
  handleClearSelections();
  clearValidate();
  resetSliderData();
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
.create-slider {

  :deep(.bk-modal-content) {
    overflow-y: auto;
    overflow-x: hidden !important;
  }

  .slider-content {
    width: 100%;

    .main {
      padding: 28px 40px 0;
      color: #4d4f56;

      .name-help-text {

        .text-body {
          font-size: 12px;
          color: #979ba5;
        }
      }
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
}

// 这里直接在formItem写校验规则会触发空校验，所以自定义样式
:deep(.custom-form-item-required) {
  position: relative;

  .bk-form-label::after {
    position: absolute;
    top: 0;
    width: 14px;
    color: #ea3636;
    text-align: center;
    content: "*";
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
    display: flex;

    .selector-main {
      flex-shrink: 0;

      .selector-title {
        margin-bottom: 8px;
        font-size: 14px;
        font-weight: 700;
        color: #4d4f56;
      }

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
      padding: 16px;
      background-color: #f5f7fa;

      .header-title-wrapper {
        display: flex;
        margin-bottom: 16px;
        font-size: 14px;
        justify-content: space-between;

        .name {
          font-weight: 700;
          color: #4d4f56;
        }
      }

      &-list {
        max-height: 713px;
        overflow-y: auto;

        .list-main {
          overflow-y: auto;
          flex: 1;

          .list-item {
            display: flex;
            height: 32px;
            padding: 6px 10px;
            margin-bottom: 4px;
            background-color: #ffffff;
            border-radius: 2px;
            justify-content: space-between;
            align-items: center;

            .delete-icon {
              color: #c4c6cc;
              cursor: pointer;

              &:hover {
                color: #3a84ff;
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

:deep(.form-protocol-type) {
  .bk-form-label {

    &::after {
      display: none;
    }

    .connect-method {
      position: relative;

      &::after {
        position: absolute;
        top: 0;
        width: 14px;
        color: #ea3636;
        text-align: center;
        content: "*";
      }
    }
  }
}
</style>
