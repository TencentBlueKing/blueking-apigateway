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
  <div class="mcp-server-table-wrapper">
    <AgTable
      ref="tableRef"
      v-model:table-data="tableData"
      show-settings
      show-selection
      resizable
      :max-limit-config="{ allocatedHeight: 260, mode: 'tdesign' }"
      :immediate="false"
      :show-first-full-row="mcpSelections.size > 0"
      :disabled-check-selection="disabledSelection"
      :filter-value="filterData"
      :api-method="getTableData"
      :columns="tableColumns"
      :hidden-column="hiddenColumn"
      :unchecked-column="uncheckedColumn"
      :row-class-name="handleSetRowClass"
      @clear-filter="handleClearFilter"
      @filter-change="handleFilterChange"
      @sort-change="handleSortChange"
      @selection-change="handleSelectionChange"
    />
  </div>
</template>

<script lang="tsx" setup>
import { locale, t } from '@/locales';
import { Button, Tag } from 'bkui-vue';
import type { ISearchItem, ISearchValue } from 'bkui-vue/lib/search-select/utils';
import type { FilterValue, PrimaryTableProps, TableRowData } from '@blueking/tdesign-ui';
import type { ITableMethod } from '@/types/common';
import type { ICountAndResults } from '@/services/types/utils.ts';
import {
  type IMCPFilterParams,
  type IMCPServerCategory,
  type IMCPServerWithUIState,
  getServers,
} from '@/services/source/mcp-server';
import type { IGatewaysMcpServersListQuery } from '@/services/types/query/gateways.ts';
import type { IMCPServerFilterOptionsOutput, IMCPServerListOutput } from '@/services/types/responses/gateways.ts';
import { useTableFilterChange } from '@/hooks/use-table-filter-change';
import { useFeatureFlag, useGateway } from '@/stores';
import RenderTagOverflow from '@/components/render-tag-overflow/Index.vue';
import AgTable from '@/components/ag-table/Index.vue';

type IMCPServer = IMCPServerWithUIState | TableRowData;

interface IProps { filterCondition?: IMCPServerFilterOptionsOutput }

interface IEmits {
  'view': [id: number]
  'edit': [id: number]
  'suspend': [id: number]
  'enable': [id: number]
  'delete': [id: number]
  'copy-config': [row: IMCPServerWithUIState]
  'selection-change': [selection: IMCPServerWithUIState[]]
  'clear-filter': [void]
};

const searchData = defineModel<ISearchItem[]>('searchData', {
  required: true,
  type: Array,
});

const searchValue = defineModel<ISearchValue[]>('searchValue', {
  required: true,
  type: Array,
});

const mcpSelections = defineModel<Map<number, IMCPServerWithUIState>>('mcpSelections', {
  required: true,
});

const filterData = defineModel<Record<string, string | string[]>>('filterData', {
  required: false,
  type: Object,
  default: () => ({}),
});

const {
  filterCondition = {
    stages: [],
    labels: [],
    categories: [],
  },
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const { handleTableFilterChange } = useTableFilterChange();
const featureFlagStore = useFeatureFlag();
const gatewayStore = useGateway();
const router = useRouter();

const tableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('tableRef');
const tableData = ref<IMCPServer[]>([]);

// 设置面板中默认不勾选的列
const uncheckedColumn = ['label'];

// 风险标签占位宽度（含内边距），存在风险标签时 title 需要为其让出空间
const RISK_TAG_SPACE = 24;

const apigwId = computed(() => gatewayStore.apigwId);
const isEnabledOAuth = computed(() =>
  featureFlagStore?.flags?.ENABLE_MCP_SERVER_OAUTH2_PUBLIC_CLIENT,
);
// 需要隐藏的列
const hiddenColumn = computed(() => {
  const hidePromptsCount = !featureFlagStore?.flags?.ENABLE_MCP_SERVER_PROMPT;
  const hidePersonalClient = !featureFlagStore?.flags?.ENABLE_MCP_SERVER_OAUTH2_PERSONAL_CLIENT;
  const hideOAuthClient = !isEnabledOAuth.value;

  const hiddenColumns: string[] = [];
  if (hidePromptsCount) hiddenColumns.push('prompts_count');
  if (hideOAuthClient) hiddenColumns.push('oauth2_public_client_enabled');
  if (hidePersonalClient) hiddenColumns.push('oauth2_personal_client_enabled');

  return hiddenColumns;
});

const isExistLabel = computed(() => tableData.value.find(item => item?.labels?.length > 0));

// name / title 任一溢出时统一展示 tooltip，内容为完整的名称与描述
// 存在风险标签时 title 让出标签占位宽度，否则铺满剩余空间
const getTitleMaxWidth = (row: IMCPServer) => {
  const hasRiskTag = isEnabledOAuth.value && Boolean(row?.app_permission_risk?.has_risk);
  return hasRiskTag ? `calc(100% - ${RISK_TAG_SPACE}px)` : '100%';
};

const getCellTooltip = (row: IMCPServer) => ({
  placement: 'top',
  content: () => (
    <div class="break-all">
      <div class="font-700">{row.name}</div>
      {row.title ? <div class="mt-4px">{row.title}</div> : null}
    </div>
  ),
  extCls: 'max-w-288px',
  allowHtml: true,
  disabled: !row.isOverflow,
});

const checkIsOverflow = (el: HTMLElement | null) => Boolean(el && el.scrollWidth > el.clientWidth);

const handleCellMouseEnter = (e: MouseEvent, row: IMCPServer) => {
  const wrapper = (e.currentTarget as HTMLElement)?.closest('.mcp-server-cell-content');
  const nameEl = wrapper?.querySelector('.mcp-server-name') as HTMLElement | null;
  const titleEl = wrapper?.querySelector('.mcp-server-title') as HTMLElement | null;
  const isOverflow = checkIsOverflow(nameEl) || checkIsOverflow(titleEl);
  if (row.isOverflow !== isOverflow) {
    row.isOverflow = isOverflow;
  }
};

const handleCellMouseLeave = (row: IMCPServer) => {
  if (row.isOverflow) {
    delete row.isOverflow;
  }
};

const tableColumns = computed(() => {
  const columns: PrimaryTableProps['columns'] = [
    {
      title: t('名称'),
      colKey: 'name',
      width: 264,
      ellipsis: false,
      cell: (_: unknown, { row }: { row: IMCPServer }) => {
        const hasRiskTag = isEnabledOAuth.value && Boolean(row?.app_permission_risk?.has_risk);
        return (
          <div class="flex items-center">
            <div
              class={[
                'ag-dot mr-8px shrink-0',
                { 'border-#2caf5e bg-#daf6e5': Boolean(row.status) },
                { 'border-#c4c6cc bg-#f5f7fa': !row.status },
              ]}
            />
            <div class="mcp-server-cell-content min-w-0 flex-1">
              <div class="flex items-baseline">
                <div
                  v-bk-tooltips={getCellTooltip(row)}
                  class={[
                    'mcp-server-name font-700 hover-cursor-pointer min-w-0 truncate',
                    { 'color-#3a84ff': Boolean(row.status) },
                    { 'color-#c4c6cc hover:color-#3a84ff': !row.status },
                  ]}
                  onClick={(e: MouseEvent) => {
                    e?.stopPropagation();
                    handleView(row.id);
                  }}
                  onMouseenter={(e: MouseEvent) => handleCellMouseEnter(e, row)}
                  onMouseleave={() => handleCellMouseLeave(row)}
                >
                  {row.name}
                </div>
              </div>
              <div class="flex items-center">
                <div
                  v-bk-tooltips={getCellTooltip(row)}
                  class={[
                    'mcp-server-title min-w-0 truncate',
                    { 'color-#979ba5': Boolean(row.status) },
                    { 'color-#c4c6cc': !row.status },
                  ]}
                  style={{ maxWidth: getTitleMaxWidth(row) }}
                  onMouseenter={(e: MouseEvent) => handleCellMouseEnter(e, row)}
                  onMouseleave={() => handleCellMouseLeave(row)}
                >
                  {row.title}
                </div>
                { hasRiskTag
                  && (
                    <Tag
                      theme="danger"
                      class="bg-transparent! p-0! ml-8px border-0 shrink-0 hover-cursor-pointer"
                      v-slots={{
                        icon: () => (
                          <ag-icon name="zhiming" size="16" />
                        ),
                      }}
                      v-bk-tooltips={{
                        content: () => (
                          <div class="break-all">
                            { t('此 MCP Server 已开启 OAuth2公开客户端模式，且包含{count}个应用态鉴权工具({content})',
                              {
                                count: row?.app_permission_risk?.risk_tools?.length,
                                content: row?.app_permission_risk?.risk_tools?.join('、'),
                              })}
                            <div>
                              { t('该工具通过 public 应用身份调用，所有 OAuth2 授权用户均可访问。') }
                            </div>
                          </div>
                        ),
                        extCls: 'max-w-288px',
                        allowHtml: true,
                      }}
                    />
                  )}
              </div>
            </div>
          </div>
        );
      },
    },
    {
      title: t('环境'),
      colKey: 'stage_id',
      width: 84,
      ellipsis: true,
      filter: {
        type: 'single',
        showConfirmAndReset: true,
        popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
        list: (filterCondition.stages ?? []).map((item) => {
          return {
            label: item.name,
            value: item.id,
          };
        }),
      },
      cell: (_: unknown, { row }: { row: IMCPServer }) => {
        return row?.stage?.name
          ? (
            <div class="w-full">
              <RenderTagOverflow
                data={[row?.stage?.name]}
                class={[{ stage_name: Boolean(row.status) }]}
              />
            </div>
          )
          : <span>--</span>;
      },
    },
    {
      title: t('分类'),
      colKey: 'categories',
      width: 106,
      filter: {
        type: 'multiple',
        showConfirmAndReset: true,
        resetValue: [],
        list: (filterCondition.categories ?? []).map((item: IMCPServerCategory) => {
          return {
            label: item.display_name,
            value: item.name,
          };
        }),
      },
      cell: (_: unknown, { row }: { row: IMCPServer }) => {
        const categoriesFilters = (row.categories as IMCPServerCategory[])?.filter((cg: IMCPServerCategory) => !['Official', 'Featured'].includes(cg.name));
        return categoriesFilters.length
          ? (
            <div class="w-full">
              <RenderTagOverflow
                data={categoriesFilters.map((cg: IMCPServerCategory) => cg.display_name)}
              />
            </div>
          )
          : <span>--</span>;
      },
    },
    {
      title: t('标签'),
      colKey: 'label',
      width: isExistLabel.value ? 140 : 80,
      filter: {
        type: 'single',
        showConfirmAndReset: true,
        popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
        list: (filterCondition?.labels ?? []).map((label: string) => {
          return {
            label,
            value: label,
          };
        }),
      },
      cell: (_: unknown, { row }: { row: IMCPServer }) => (
        row?.labels?.length
          ? (
            <div class="w-full">
              <RenderTagOverflow
                data={row.labels as string[]}
              />
            </div>
          )
          : <span>--</span>
      ),
    },
    {
      title: t('工具数量'),
      colKey: 'tools_count',
      width: 80,
      ellipsis: true,
    },
    {
      title: t('Prompt 数量'),
      colKey: 'prompts_count',
      width: 102,
      ellipsis: true,
    },
    {
      title: t('是否公开'),
      colKey: 'is_public',
      width: 82,
      ellipsis: true,
      cell: (_: unknown, { row }: { row: IMCPServer }) => {
        return (
          <Tag
            class="border-transparent"
            theme={row?.is_public ? 'success' : 'warning'}
          >
            {t(row?.is_public ? '公开' : '不公开')}
          </Tag>
        );
      },
    },
    {
      title: t('OAuth2 公开客户端'),
      colKey: 'oauth2_public_client_enabled',
      ellipsis: true,
      width: 140,
      cell: (_: unknown, { row }: { row: IMCPServer }) => {
        return (
          <Tag
            class={
              [
                'border-transparent',
                { 'bg-#e1ecff color-#1768ef hover:bg-#e1ecff': row.oauth2_public_client_enabled },
              ]
            }
          >
            {t(row?.oauth2_public_client_enabled ? '已开启' : '未开启')}
          </Tag>
        );
      },
    },
    {
      title: t('个人令牌'),
      colKey: 'oauth2_personal_client_enabled',
      width: 86,
      ellipsis: true,
      cell: (_: unknown, { row }: { row: IMCPServer }) => {
        return (
          <Tag
            class={
              [
                'border-transparent',
                { 'bg-#e1ecff color-#1768ef hover:bg-#e1ecff': row.oauth2_personal_client_enabled },
              ]
            }
          >
            {t(row?.oauth2_personal_client_enabled ? '已开启' : '未开启')}
          </Tag>
        );
      },
    },
    {
      title: t('发布时间'),
      colKey: 'updated_time',
      width: 196,
      ellipsis: true,
      sorter: true,
    },
    {
      title: t('操作'),
      colKey: 'operate',
      fixed: 'right',
      width: locale.value?.toLowerCase()?.indexOf('en') > -1 ? 92 : 64,
      cell: (_: unknown, { row }: { row: IMCPServer }) => (
        <div class="flex">
          <Button
            text
            theme="primary"
            onClick={() => row.status ? handleEditClick(row) : handleEnableClick(row)}
          >
            {t(row.status ? '编辑' : '启用')}
          </Button>
          <div
            class="ml-12px"
            onClick={(e: MouseEvent) => e?.preventDefault()}
          >
            <bk-dropdown
              trigger="click"
              popoverOptions={{
                clickContentAutoHide: true,
                hideIgnoreReference: true,
              }}
            >
              {{
                default: () => (
                  <ag-icon
                    class="flex items-center justify-center w-16px h-16px color-#4d4f56 cursor-pointer"
                    name="more-fill"
                    size="16"
                  />
                ),
                content: () => (
                  <bk-dropdown-menu>
                    {Boolean(row?.status) && (
                      <div>
                        <bk-dropdown-item onClick={() => handleSuspendClick(row)}>
                          <Button
                            size="small"
                            text
                          >
                            { t('停用') }
                          </Button>
                        </bk-dropdown-item>
                        <bk-dropdown-item onClick={() => handleCopyConfig(row as IMCPServerWithUIState)}>
                          <Button
                            size="small"
                            text
                          >
                            { t('复制配置') }
                          </Button>
                        </bk-dropdown-item>
                      </div>
                    )}
                    <bk-dropdown-item
                      class={{ 'cursor-not-allowed!': Boolean(row?.status) }}
                      v-bk-tooltips={{
                        content: t('请先停用再删除'),
                        disabled: !row?.status,
                      }}
                      onClick={(e: MouseEvent) => {
                        e?.stopPropagation();
                        handleDeleteClick(row);
                      }}
                    >
                      <Button
                        disabled={Boolean(row?.status)}
                        text
                      >
                        { t('删除') }
                      </Button>
                    </bk-dropdown-item>
                    {featureFlagStore.flags.ENABLE_MCP_SERVER_OBSERVABILITY && (
                      <bk-dropdown-item
                        onClick={(e: MouseEvent) => {
                          e?.stopPropagation();
                          handleNavObservability(row);
                        }}
                      >
                        <Button
                          size="small"
                          text
                        >
                          { t('可观测') }
                        </Button>
                      </bk-dropdown-item>
                    )}
                  </bk-dropdown-menu>
                ),
              }}
            </bk-dropdown>
          </div>
        </div>
      ),
    },
  ];

  return columns;
});

const getList = () => tableRef.value?.fetchData(filterData.value, { resetPage: true });

/**
 * 获取表格数据
 * @param params - 请求参数，默认值为空对象
 * @returns 接口返回的表格数据，兜底返回空数组
 */
const getTableData = async (params: IMCPFilterParams): Promise<ICountAndResults<IMCPServerListOutput>> => {
  const requestParams = { ...params };
  const fieldsToJoin = ['categories'];
  fieldsToJoin.forEach((field) => {
    if (requestParams[field] && Array.isArray(requestParams[field])) {
      requestParams[field] = requestParams[field].join(',');
    }
  });

  const res = await getServers(apigwId.value, requestParams as IGatewaysMcpServersListQuery);
  return res;
};

const disabledSelection = (row: IMCPServer): boolean => {
  if (!row.status) {
    row.selectionTip = t('已停用的MCP无法批量操作');
  }

  return !row.status;
};

const handleNavObservability = (row: IMCPServer) => {
  router.push({
    name: 'MCPServerObservability',
    query: {
      mcp_server_name: row.name,
    },
  });
};

const handleView = (id: number) => {
  emit('view', id);
};

const handleEditClick = (row: IMCPServer) => {
  emit('edit', row.id);
};

const handleSuspendClick = (row: IMCPServer) => {
  emit('suspend', row.id);
};

const handleEnableClick = (row: IMCPServer) => {
  emit('enable', row.id);
};

const handleDeleteClick = (row: IMCPServer) => {
  if (!row.status) {
    emit('delete', row.id);
  }
};

const handleSetRowClass = ({ row }: { row: IMCPServer }) => {
  if (!row.status) {
    return 'color-#c4c6cc no-perm-row';
  }
  return '';
};

const handleSortChange = (sort: {
  sortBy: string
  descending: boolean
} | null) => {
  if (sort) {
    const { sortBy: colKey, descending } = sort;
    filterData.value!.order_by = descending ? `-${colKey}` : colKey;
  }
  else {
    delete filterData.value!.order_by;
  }
  getList();
};

// 处理表头筛选联动搜索框
const handleFilterChange: PrimaryTableProps['onFilterChange'] = (filterItem: FilterValue) => {
  handleTableFilterChange({
    filterItem,
    filterData,
    searchOptions: searchData,
    searchParams: searchValue,
  });
  getList();
};

// 复制配置
const handleCopyConfig = (row: IMCPServerWithUIState) => {
  emit('copy-config', row);
};

// 处理复选框
const handleSelectionChange = ({
  selections,
}: {
  selections: TableRowData[]
  selectionsRowKeys: (string | number)[]
}) => {
  emit('selection-change', selections as IMCPServerWithUIState[]);
};

const handleClearFilter = () => {
  emit('clear-filter');
};

defineExpose({ getList });
</script>

<style lang="scss" scoped>
:deep(.no-perm-row) {

  .bk-tag {
    color: #c4c6cc;
    background-color: #f5f7fa;

    &:hover {
      color: #c4c6cc;
      background-color: #f5f7fa;
      border-color: transparent;
    }
  }
}

:deep(.stage_name) {

  .bk-tag {
    color: #1768ef;
    background-color: #e1ecff;

    &:hover {
      background-color: #e1ecff;
    }
  }
}
</style>
