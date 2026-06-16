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
  <div class="flow-log-detail-wrapper">
    <AgTable
      ref="tableRef"
      v-model:table-data="tableData"
      class="flow-log-detail-table"
      row-key="tempUniqueId"
      show-settings
      show-cell-empty-content
      height="auto"
      max-height="none"
      :immediate="false"
      :expand-icon="false"
      :is-exist-unique-key="false"
      :row-class-name="getRowClass"
      :api-method="getTableData"
      :columns="tableColumns"
      :expandable="expandableConfig"
      :expanded-row-keys="expandableConfig.expandedRowKeys"
      :table-empty-type="detailEmptyConf.emptyType"
      :filter-value="searchParams"
      @row-click="handleRowClick"
      @clear-filter="handleClearFilter"
    >
      <!-- 展开行内容 -->
      <template #expandedRow="{ row }">
        <div
          v-if="row.isExpand"
          class="expand-details"
        >
          <template
            v-for="({ label, field }, index) of expandedFields"
            :key="`${field}-${index}`"
          >
            <div
              v-if="isShowField({ row, field })"
              class="flex items-center expand-details-row"
            >
              <div class="label">
                {{ label }}
                <span class="color-#979ba5">
                  (
                  <span
                    v-bk-tooltips="t('复制')"
                    class="hover:bg-#f0f1f5 cursor-pointer"
                    @click.stop="() => copy(field)"
                  >
                    {{ field }}
                  </span>
                  ) :
                </span>
              </div>
              <div class="value">
                <!-- 200状态码时响应正文提示 -->
                <span
                  v-if="field === 'response_body' && row.status === 200"
                  class="flex items-center color-#ff9c01"
                >
                  <InfoLine class="text-14px mr-8px" />
                  <span>{{ t('状态码为 200 时不记录响应正文') }}</span>
                </span>
                <span
                  v-else
                  class="hover:cursor-pointer"
                  :class="[isFieldExpanded(row, field) ? 'py-4px' : 'truncate']"
                  @click.stop="() => handleToggleFieldExpand(row, field)"
                >
                  {{ formatCellValue(row[field], field) }}
                </span>
                <!-- 操作按钮组 -->
                <div
                  v-if="!(formatCellValue(row[field], field) === '--')"
                  class="opt-btns"
                >
                  <CopyShape
                    v-bk-tooltips="t('复制')"
                    class="opt-copy opt-icon"
                    @click="() => handleRowCopy(field, row)"
                  />
                  <template v-if="isShowRetrieveBtn(field)">
                    <EnlargeLine
                      v-bk-tooltips="t('添加到本次检索')"
                      class="opt-icon"
                      @click="() => handleInclude(field, row)"
                    />
                    <NarrowLine
                      v-bk-tooltips="t('从本次检索中排除')"
                      class="opt-icon"
                      @click="() => handleExclude(field, row)"
                    />
                  </template>
                </div>
              </div>
            </div>
          </template>
        </div>
      </template>
    </AgTable>

    <!-- 调用链路详情侧边栏 -->
    <AgTraceChainSlider
      ref="traceChainSliderRef"
      :api-gateway-id="apiGatewayId"
      :request-id="callChainDetail?.request_id || callChainDetail?.x_request_id"
    />
  </div>
</template>

<script lang="tsx" setup>
import dayjs from 'dayjs';
import { Button, Popover } from 'bkui-vue';
import type { PrimaryTableProps, TableRowData } from '@blueking/tdesign-ui';
// 图标组件
import { CopyShape, EnlargeLine, InfoLine, NarrowLine } from 'bkui-vue/lib/icon';
// 服务请求
import {
  type IFlowLogTable,
  type IObservabilitySearchParams,
  fetchObservabilityLogList,
} from '@/services/source/observability';
// 工具函数
import { copy } from '@/utils';
import { t } from '@/locales';
// 组件
import AgStatusDot from '@/components/ag-status-dot/Index.vue';
import AgTable from '@/components/ag-table/Index.vue';
import AgTraceChainSlider from '@/views/mcp-server/components/TraceChainSlider.vue';

interface IProps { apiGatewayId: string | number }

type IFlowLogTableUIState = IFlowLogTable & {
  isExpand: boolean
  [key: string]: any
};

interface IEmits {
  'clear-filter': [void]
  'request': [void]
}

const pageCount = defineModel('pageCount', {
  type: Number,
  default: 0,
});
const searchParams = defineModel('searchParams', {
  type: Object,
  default: () => ({}),
});
const includeQuery = defineModel<string[]>('includeQuery', {
  type: Array,
  default: () => [],
});
const excludeQuery = defineModel<string[]>('excludeQuery', {
  type: Array,
  default: () => [],
});
const detailEmptyConf = defineModel('detailEmptyConf', {
  type: Object,
  default: () => ({
    emptyType: '',
    isAbnormal: false,
  }),
});

const { apiGatewayId } = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const tableRef = ref<InstanceType<typeof AgTable>>();
const traceChainSliderRef = ref<InstanceType<typeof AgTraceChainSlider>>();
const tableData = ref<IFlowLogTableUIState[]>([]);
const expandableConfig = ref({
  expandColumn: false,
  expandedRowKeys: [] as IFlowLogTableUIState[],
});
// 缓存上一个展开行
const lastExpandRow = ref<IFlowLogTableUIState | null>(null);
const callChainDetail = ref<Partial<IFlowLogTableUIState>>({});
// 缓存每行文本内容的点击状态
const fieldExpandMap = ref<Map<string, boolean>>(new Map());

// 展开行显示的字段配置
interface IFieldItem {
  label: string
  field: string
}
const expandedFields = shallowRef<IFieldItem[]>([
  {
    label: '请求ID',
    field: 'request_id',
  },
  {
    label: '全链路请求ID',
    field: 'x_request_id',
  },
  {
    label: '请求时间',
    field: 'timestamp',

  },
  {
    label: '网关ID',
    field: 'gateway_id',

  },
  {
    label: '网关名称',
    field: 'gateway_name',

  },
  {
    label: 'MCP Server ID',
    field: 'mcp_server_id',

  },
  {
    label: 'MCP Server',
    field: 'mcp_server_name',

  },
  {
    label: 'MCP 方法',
    field: 'mcp_method',

  },
  {
    label: '工具名称',
    field: 'tool_name',

  },
  {
    label: 'Prompt 名称',
    field: 'prompt_name',

  },
  {
    label: '蓝鲸应用',
    field: 'app_code',
  },
  {
    label: '蓝鲸用户',
    field: 'bk_username',

  },
  {
    label: '客户端IP',
    field: 'client_ip',

  },
  {
    label: '客户端ID',
    field: 'client_id',
  },
  {
    label: '会话ID',
    field: 'session_id',
  },
  {
    label: '请求参数',
    field: 'params',
  },
  {
    label: '响应内容',
    field: 'response',
  },
  {
    label: '请求体大小',
    field: 'request_body_size',
  },
  {
    label: '响应体大小',
    field: 'response_body_size',
  },
  {
    label: '耗时',
    field: 'latency',
  },
  {
    label: 'Trace ID',
    field: 'trace_id',
  },
  {
    label: '状态',
    field: 'status',
  },
  {
    label: '错误',
    field: 'error',
  },
].map(item => ({
  ...item,
  label: ['trace_id', 'mcp_server_name', 'mcp_server_id'].includes(item.field) ? item.label : t(item.label),
})));

// 表格列配置
const tableColumns = shallowRef<PrimaryTableProps['columns']>([
  {
    title: t('请求时间'),
    colKey: 'timestamp',
    ellipsis: true,
    width: 240,
    cell: (_: unknown, { row }: { row: TableRowData }) => {
      return (
        <div class="flex items-center">
          <ag-icon
            name={row.isExpand ? 'down-shape' : 'right-shape'}
            class={`mr-8px color-${row.isExpand ? '#4d4f56' : '#979ba5'}`}
            size="14"
          />
          <span>{formatCellValue(row.timestamp as number, 'timestamp')}</span>
        </div>
      );
    },
  },
  {
    title: 'MCP Server',
    colKey: 'mcp_server_name',
    width: 300,
    ellipsis: true,
  },
  {
    title: 'Tool/Prompt',
    colKey: 'tool_name',
    ellipsis: true,
    cell: (_: unknown, { row }: { row: TableRowData }) => {
      return row.tool_name || row.prompt_name || '--';
    },
  },
  {
    title: t('MCP 方法'),
    colKey: 'mcp_method',
    ellipsis: true,
  },
  {
    title: t('耗时'),
    colKey: 'latency',
    width: 150,
    ellipsis: true,
    cell: (_: unknown, { row }: { row: TableRowData }) => {
      const duration = row.latency;
      if (!duration) {
        return '--';
      }
      return String(duration).replace(/(\d+\.\d{2})\d*/, '$1');
    },
  },
  {
    title: 'app_code',
    colKey: 'app_code',
    ellipsis: true,
  },
  {
    title: t('状态'),
    colKey: 'status',
    width: 130,
    cell: (_: unknown, { row }: { row: TableRowData }) => {
      const curRow = row as IFlowLogTableUIState;

      return (
        <AgStatusDot
          class="lh-20px"
          type={isSuccessStatus(curRow) ? 'success' : 'error'}
          text={t(isSuccessStatus(curRow) ? '成功' : '失败')}
        />
      );
    },
  },
  {
    title: t('错误'),
    colKey: 'error',
    ellipsis: true,
    cell: (_: unknown, { row }: { row: TableRowData }) => {
      if (!row.error) return '--';
      return <span class="color-#ea3636">{row.error}</span>;
    },
  },
  {
    title: t('操作'),
    colKey: 'operate',
    fixed: 'right',
    width: 102,
    cell: (_: unknown, { row }: { row: TableRowData }) => {
      const isDisabled = !row.request_id && !row.x_request_id;
      return (
        <div class="flex">
          <Popover
            content={t('request_id 和 x_request_id 不存在')}
            disabled={!isDisabled}
            popoverDelay={0}
          >
            <Button
              text
              theme="primary"
              disabled={isDisabled}
              onClick={(e: MouseEvent) => {
                e.stopPropagation();
                handleShowCallChain(row as IFlowLogTableUIState);
              }}
            >
              {t('调用链')}
            </Button>
          </Popover>
        </div>
      );
    },
  },
]);

/**
 * 获取日志列表
 * @param params 筛选参数
 */
const getList = (params: IObservabilitySearchParams) => {
  tableRef.value?.fetchData(params, { resetPage: true });
};

/**
 * 获取分页信息
 */
const getPagination = () => {
  return tableRef.value?.getPagination();
};

/**
 * 表格数据请求方法（供AgTable调用）
 * @param params 筛选参数
 * @param extraStr 额外参数
 */
const getTableData = async (params: IObservabilitySearchParams = {}, extraStr?: string) => {
  try {
    const res = await fetchObservabilityLogList(apiGatewayId as number, params as any, extraStr);
    const { fields = [], count = 0 } = res ?? {};
    // 更新展开字段配置
    expandedFields.value = fields;
    // 更新总条数
    pageCount.value = count;
    // 清空单元格文本内容展开状态
    fieldExpandMap.value.clear();
    // 更新表格数据
    return res;
  }
  catch {
    tableData.value = [];
    pageCount.value = 0;
    return {
      results: [],
      count: 0,
    };
  }
};

/**
 * 格式化单元格值
 * @param value 原始值
 * @param field 字段名
 */
const formatCellValue = (value: string | number | null, field: string) => {
  const emptyValueList = [null, '', '{}', '[]'];

  if (value === null || emptyValueList.includes(String(value))) {
    return '--';
  }

  if (['timestamp'].includes(field)) {
    return dayjs.unix(Number(value)).format('YYYY-MM-DD HH:mm:ss ZZ');
  }

  if (['request_body_size', 'request_body_size'].includes(field)) {
    return `${value} bytes`;
  }

  return value;
};

// 统一控制字段是否展示
const isShowField = ({ row, field }: {
  row: IFlowLogTableUIState
  field: string
}) => {
  const EXCLUDE_LOG_PATH = '/app/logs/mcp_proxy_api.log';
  // path 字段且不是指定日志路径才显示
  if (field === 'path') {
    return row?.[field] !== EXCLUDE_LOG_PATH;
  }

  return true;
};

/**
 * 判断当前字段是否展开
 * @param field 字段名
 * @param row 行数据
 */
const isFieldExpanded = (row: IFlowLogTableUIState, field: string) => {
  const key = `${row.tempUniqueId}-${field}`;
  return fieldExpandMap.value.get(key) ?? false;
};

/**
 * 是否打开trace侧边栏
 */
const handleShowTraceSlider = () => {
  nextTick(() => {
    traceChainSliderRef.value?.show();
  });
};

/**
 * 显示调用链详情
 * @param row 行数据
 */
const handleShowCallChain = (row: IFlowLogTableUIState) => {
  callChainDetail.value = { ...row } as IFlowLogTableUIState;
  handleShowTraceSlider();
};

/**
 * 点击文本切换单行/完整展示
 * @param field 字段名
 * @param row 行数据
 */
const handleToggleFieldExpand = (row: IFlowLogTableUIState, field: string) => {
  const key = `${row.tempUniqueId}-${field}`;
  const map = fieldExpandMap.value;
  map.set(key, !(map.get(key) ?? false));
};

/**
 * 复制行字段值
 * @param field 字段名
 * @param row 行数据
 */
const handleRowCopy = (field: string, row: IFlowLogTableUIState) => {
  const rowField = row[field];
  const copyContent = formatCellValue(rowField, field);
  copy(copyContent as string);
};

/**
 * 添加到检索条件
 * @param field 字段名
 * @param row 行数据
 */
const handleInclude = (field: string, row: IFlowLogTableUIState) => {
  const rowField = row[field] as string | number;
  if (!rowField) return;
  const fieldStr = `${field}:${rowField}`;
  // 去重后添加
  if (!includeQuery.value.includes(fieldStr)) {
    includeQuery.value.push(fieldStr);
  }
  // 从排除列表移除
  const excludeIndex = excludeQuery.value.indexOf(fieldStr);
  if (excludeIndex > -1) {
    excludeQuery.value.splice(excludeIndex, 1);
  }
  emit('request');
};

/**
 * 排除出检索条件
 * @param field 字段名
 * @param row 行数据
 */
const handleExclude = (field: string, row: IFlowLogTableUIState) => {
  if (!row[field]) return;
  const fieldStr = `${field}:${row[field]}`;
  // 去重后添加
  if (!excludeQuery.value.includes(fieldStr)) {
    excludeQuery.value.push(fieldStr);
  }
  // 从包含列表移除
  const includeIndex = includeQuery.value.indexOf(fieldStr);
  if (includeIndex > -1) {
    includeQuery.value.splice(includeIndex, 1);
  }
  emit('request');
};

/**
 * 行点击事件（展开/收起）
 */
const handleRowClick = async ({ e, row }: {
  e: MouseEvent
  row: IFlowLogTableUIState
}) => {
  e.stopPropagation();
  const newIsExpand = !row.isExpand;

  // 重置上一个展开行
  if (lastExpandRow.value && lastExpandRow.value !== row) {
    (lastExpandRow.value as IFlowLogTableUIState).isExpand = false;
    (lastExpandRow.value as IFlowLogTableUIState).selection = [];
  }

  // 更新当前行状态
  row.isExpand = newIsExpand;
  expandableConfig.value.expandedRowKeys = newIsExpand
    ? [(row as IFlowLogTableUIState).tempUniqueId]
    : [];
  lastExpandRow.value = newIsExpand ? row : null;

  if (newIsExpand) {
    row.selection = [];
  }
};

/**
 * 清空筛选条件
 */
const handleClearFilter = () => {
  emit('clear-filter');
};

/**
 * 判断是否显示检索按钮
 * @param field 字段名
 */
const isShowRetrieveBtn = (field: string) => {
  const allowFields: string[] = ['request_id'];
  return allowFields.includes(field);
};

const isSuccessStatus = (row: IFlowLogTableUIState) => {
  return row.status && ((Number(row.status) >= 200 && Number(row.status) < 300) || ['success'].includes(row.status));
};

const getRowClass = ({ row }: { row: IFlowLogTableUIState }) => {
  return !isSuccessStatus(row) || row.error ? 'error-exception hover:cursor-pointer' : 'hover:cursor-pointer';
};

defineExpose({
  getList,
  getPagination,
});
</script>

<style lang="scss" scoped>
.flow-log-detail-wrapper {
  margin-right: 24px;
  margin-left: 46px;
  box-sizing: border-box;

  :deep(.flow-log-detail-table) {
    border: 1px solid #dcdee5;
    border-collapse: collapse;

    .t-table__expanded-row {
      background-color: #f5f7fb;

      .t-table__row-full-element {
        padding: 0;

        .expand-details {
          margin: 24px;
          border-radius: 4px;
          box-sizing: border-box;

          &-row {
            min-height: 32px;
            padding-left: 24px;
            font-size: 12px;
            line-height: 20px;

            .label {
              width: 300px;
              color: #4d4f56;
            }

            .value {
              display: flex;
              max-width: calc(100% - 332px);
              color: #313238;
              word-break: break-all;
              white-space: pre-wrap;
              align-items: center;

              .opt-btns {
                display: inline-flex;
                margin-left: 8px;
                font-size: 16px;
                color: #979ba5;

                .opt-icon {
                  margin-right: 4px;
                  color: #3a84ff;
                  cursor: pointer;
                }
              }
            }

            &:nth-child(odd) {
              background-color: #ffffff;
            }

            &:nth-child(even) {
              background-color: #fafbfd;
            }
          }
        }
      }
    }
  }
}

:deep(.error-exception) {
  background-color: #f9edec;

  td {
    background-color: #f9edec;
  }
}
</style>
