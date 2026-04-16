/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
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
      resizable
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
          <div
            v-for="({ label, field }, index) of expandedFields"
            :key="index"
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
                class="truncate"
              >
                {{ formatCellValue(row[field], field) }}
              </span>
              <!-- 操作按钮组 -->
              <div
                v-if="row[field]"
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
        </div>
      </template>
      <!-- 空单元格占位 -->
      <template #cellEmptyContent="{ col }">
        <template v-if="!col.fixed">
          <span class="empty-placeholder">--</span>
        </template>
        <template v-else />
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
// 图标组件
import { CopyShape, EnlargeLine, InfoLine, NarrowLine } from 'bkui-vue/lib/icon';
// 类型定义
import type { PrimaryTableProps } from '@blueking/tdesign-ui';
// 服务请求
import {
  type IFlowLogTable,
  type IObservabilityBasicForm,
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

const route = useRoute();
const router = useRouter();

const tableRef = ref<InstanceType<typeof AgTable>>();
const traceChainSliderRef = ref<InstanceType<typeof AgTraceChainSlider>>();
const tableData = ref<IFlowLogTable[]>([]);
const expandableConfig = ref({
  expandColumn: false,
  expandedRowKeys: [],
});
// 缓存上一个展开行
const lastExpandRow = ref<IFlowLogTable | null>(null);
const callChainDetail = ref<IFlowLogTable>({});

// 展开行显示的字段配置
interface IFieldItem {
  label: string
  field: keyof IFlowLogTable
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
    cell: (_, { row }: { row?: IFlowLogTable }) => {
      return (
        <div class="flex items-center">
          <AgIcon
            name={row?.isExpand ? 'down-shape' : 'right-shape'}
            class={`color-${row?.isExpand ? '#4d4f56' : '#979ba5'}`}
            size="14"
            class="mr-8px"
          />
          <span>{formatCellValue(row?.timestamp, 'timestamp')}</span>
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
    cell: (_, { row }: { row?: IFlowLogTable }) => {
      return row?.tool_name || row?.prompt_name || '--';
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
    cell: (_, { row }: { row?: IFlowLogTable }) => {
      const duration = row?.latency;
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
    cell: (_, { row }: { row?: IFlowLogTable }) => {
      return (
        <AgStatusDot
          class="lh-20px"
          type={isSuccessStatus(row) ? 'success' : 'error'}
          text={t(isSuccessStatus(row) ? '成功' : '失败')}
        />
      );
    },
  },
  {
    title: t('错误'),
    colKey: 'error',
    ellipsis: true,
    cell: (_, { row }: { row?: IFlowLogTable }) => {
      if (!row?.error) return '--';
      return <span class="color-#ea3636">{row.error}</span>;
    },
  },
  {
    title: t('操作'),
    colKey: 'operate',
    fixed: 'right',
    width: 102,
    cell: (_, { row }: { row?: IFlowLogTable }) => {
      const isDisabled = !row?.request_id && !row?.x_request_id;
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
                handleShowCallChain(row);
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
const getList = (params: IObservabilityBasicForm) => {
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
const getTableData = async (params: IObservabilityBasicForm = {}, extraStr?: string) => {
  try {
    const res = await fetchObservabilityLogList(apiGatewayId, params, extraStr);
    const { fields = [], count = 0 } = res ?? {};
    // 更新展开字段配置
    expandedFields.value = fields;
    // 更新总条数
    pageCount.value = count;
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
const formatCellValue = (value: string | undefined, field: string) => {
  if (!value) return '--';

  if (['timestamp'].includes(field)) {
    return dayjs.unix(Number(value)).format('YYYY-MM-DD HH:mm:ss ZZ');
  }

  if (['request_body_size', 'request_body_size'].includes(field)) {
    return `${value} bytes`;
  }

  return value;
};

/**
 * 是否打开trace侧边栏
 */
const handleShowTraceSlider = () => {
  nextTick(() => {
    traceChainSliderRef.value?.show();
    router.replace({
      query: {
        ...route.query,
        request_id: undefined,
        showTraceChain: undefined,
      },
    });
  });
};

/**
 * 显示调用链详情
 * @param row 行数据
 */
const handleShowCallChain = (row: IFlowLogTable) => {
  callChainDetail.value = { ...row };
  handleShowTraceSlider();
};

/**
 * 复制行字段值
 * @param field 字段名
 * @param row 行数据
 */
const handleRowCopy = (field: keyof IFlowLogTable, row: IFlowLogTable) => {
  const copyContent = `${field}: ${row[field] || '--'}`;
  copy(copyContent);
};

/**
 * 添加到检索条件
 * @param field 字段名
 * @param row 行数据
 */
const handleInclude = (field: keyof IFlowLogTable, row: IFlowLogTable) => {
  if (!row[field]) return;
  const fieldStr = `${field}:${row[field]}`;
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
const handleExclude = (field: keyof IFlowLogTable, row: IFlowLogTable) => {
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
 * @param param0 事件和行数据
 */
const handleRowClick = async ({ e, row }: {
  e: MouseEvent
  row: IFlowLogTable
}) => {
  e.stopPropagation();
  const newIsExpand = !row.isExpand;

  // 重置上一个展开行
  if (lastExpandRow.value && lastExpandRow.value !== row) {
    lastExpandRow.value.isExpand = false;
    lastExpandRow.value.selection = [];
  }

  // 更新当前行状态
  row.isExpand = newIsExpand;
  expandableConfig.value.expandedRowKeys = newIsExpand
    ? [row.tempUniqueId as string]
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
const isShowRetrieveBtn = (field: keyof IFlowLogTable) => {
  const allowFields: Array<keyof IFlowLogTable> = ['request_id'];
  return allowFields.includes(field);
};

const isSuccessStatus = (row: IFlowLogTable) => {
  return row?.status && ((Number(row.status) >= 200 && Number(row.status) < 300) || ['success'].includes(row.status));
};

const getRowClass = ({ row }: { row: IFlowLogTable }) => {
  return !isSuccessStatus(row) || row.error ? 'error-exception hover:cursor-pointer' : 'hover:cursor-pointer';
};

watch(
  () => route.query,
  (newQuery) => {
    const { request_id, showTraceChain } = newQuery ?? {};
    // 路由中带request_id时自动填充调用链
    if (request_id) {
      callChainDetail.value.request_id = request_id;
      // 路由中带showTraceChain时自动打开调用链侧边栏
      if (showTraceChain) {
        handleShowTraceSlider();
      }
    }
  },
  { immediate: true },
);

defineExpose({
  getList,
  getPagination,
});
</script>

<style lang="scss" scoped>
.flow-log-detail-wrapper {
  margin-left: 46px;
  margin-right: 24px;
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
            padding-left: 24px;
            font-size: 12px;
            height: 32px;
            line-height: 20px;

            .label {
              width: 300px;
              color: #4d4f56;
            }

            .value {
              display: flex;
              align-items: center;
              color: #313238;
              word-break: break-all;
              white-space: pre-wrap;
              max-width: calc(100% - 332px);

              .opt-btns {
                display: inline-flex;
                margin-left: 8px;
                font-size: 16px;
                color: #979ba5;

                .opt-icon {
                  color: #3a84ff;
                  margin-right: 4px;
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
