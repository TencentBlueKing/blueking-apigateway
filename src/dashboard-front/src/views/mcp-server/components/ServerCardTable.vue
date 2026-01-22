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
      resizable
      :max-limit-config="{ allocatedHeight: 260, mode: 'tdesign' }"
      :immediate="false"
      :filter-value="filterData"
      :api-method="getTableData"
      :columns="tableColumns"
      :hidden-column="hiddenColumn"
      :row-class-name="handleSetRowClass"
      @clear-filter="handleClearFilter"
      @filter-change="handleFilterChange"
      @sort-change="handleSortChange"
    />
  </div>
</template>

<script lang="tsx" setup>
import { Button, Tag } from 'bkui-vue';
import type { ITableMethod } from '@/types/common';
import type { FilterValue, PrimaryTableProps } from '@blueking/tdesign-ui';
import { type IMCPServerFilterOptions, getServers } from '@/services/source/mcp-server';
import { useTableFilterChange } from '@/hooks/use-table-filter-change';
import { useFeatureFlag, useGateway } from '@/stores';
import AgTable from '@/components/ag-table/Index.vue';
import RenderTagOverflow from '@/components/render-tag-overflow/Index.vue';

type IMCPServer = Awaited<ReturnType<typeof getServers>>['results'][number];

interface IProps { filterCondition?: IMCPServerFilterOptions }

type IEmits = {
  'edit': [id: number]
  'suspend': [id: number]
  'enable': [id: number]
  'delete': [id: number]
  'clear-filter': [void]
};

const searchData = defineModel('searchData', {
  required: true,
  type: Array,
});

const searchValue = defineModel('searchValue', {
  required: true,
  type: Array,
});

const filterData = defineModel<Partial<IMCPServer>>('filterData', {
  required: false,
  type: Object,
});

const {
  filterCondition = {
    stages: [],
    labels: [],
    categories: [],
  },
} = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const { t } = useI18n();
const { handleTableFilterChange } = useTableFilterChange();
const featureFlagStore = useFeatureFlag();
const gatewayStore = useGateway();

const tableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('tableRef');
const tableData = ref<IMCPServer[]>([]);

const apigwId = computed(() => gatewayStore.apigwId);
const hiddenColumn = computed(() => (!featureFlagStore?.flags?.ENABLE_MCP_SERVER_PROMPT ? ['prompts_count'] : []));

const tableColumns = shallowRef<PrimaryTableProps['columns']>([
  {
    title: t('名称'),
    colKey: 'name',
    width: 300,
    ellipsis: true,
    cell: (_, { row }: { row: IMCPServer }) => {
      return (
        <div class="flex items-baseline">
          <div
            class={[
              'mr-12px ag-dot',
              { 'border-#2caf5e bg-#daf6e5': row.status === 1 },
              { 'border-#c4c6cc bg-#f5f7fa': row.status === 0 },
            ]}
          />
          <div
            v-bk-tooltips={{
              content: row.name,
              placement: 'top',
              disabled: !row.isOverflow,
              extCls: 'max-w-480px',
            }}
            class="truncate"
            onMouseenter={e =>
              tableRef.value?.handleCellEnter({
                e,
                row,
              })}
            onMouseLeave={e =>
              tableRef.value?.handleCellLeave({
                e,
                row,
              })}
          >
            {row.name}
          </div>
        </div>
      );
    },
  },
  {
    title: t('展示名'),
    colKey: 'title',
    width: 200,
    ellipsis: true,
  },
  {
    title: t('环境'),
    colKey: 'stage_id',
    ellipsis: true,
    width: 130,
    cell: (_, { row }: { row: IMCPServer }) => {
      return (
        <Tag class={[
          'max-w-100px truncate border-transparent',
          { 'bg-#e1ecff color-#1768ef hover:bg-#e1ecff': row.status },
          { 'bg-#f5f7fa color-#c4c6cc! hover:bg-#f5f7fa!': !row.status },
        ]}
        >
          {row?.stage?.name || '--'}
        </Tag>
      );
    },
    filter: {
      type: 'single',
      showConfirmAndReset: true,
      popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
      list: filterCondition.stages.map((item) => {
        return {
          label: item.name,
          value: item.id,
        };
      }),
    },
  },
  {
    title: t('分类'),
    colKey: 'categories',
    width: 200,
    filter: {
      type: 'multiple',
      showConfirmAndReset: true,
      resetValue: [],
      list: filterCondition.categories.map((item) => {
        return {
          label: item.display_name,
          value: item.name,
        };
      }),
    },
    cell: (_, { row }) => (
      row.categories?.length
        ? (
          <div class="w-160px">
            <RenderTagOverflow
              data={row.categories.map(cg => cg.display_name)}
            />
          </div>
        )
        : <span>--</span>

    ),
  },
  {
    title: t('工具数量'),
    colKey: 'tools_count',
    align: 'right',
    ellipsis: true,
  },
  {
    title: t('Prompt数量'),
    colKey: 'prompts_count',
    align: 'right',
    width: 150,
    ellipsis: true,
  },
  {
    title: t('发布时间'),
    colKey: 'updated_time',
    ellipsis: true,
    sorter: true,
    width: 260,
  },
  {
    title: t('描述'),
    colKey: 'description',
    ellipsis: true,
    width: 200,
    cell: (_, { row }: { row: IMCPServer }) => {
      return row?.description || '--';
    },
  },
  {
    title: t('操作'),
    colKey: 'operate',
    fixed: 'right',
    width: 80,
    cell: (_, { row }) => (
      <div class="flex">
        <Button
          text
          theme="primary"
          onClick={() => row.status === 1 ? handleEditClick(row) : handleEnableClick(row)}
        >
          {t(row.status === 1 ? '编辑' : '启用')}
        </Button>
        <div
          class="ml-12px"
          onClick={(e: MouseEvent) => e?.preventDefault()}
        >
          <bk-dropdown trigger="click">
            {{
              default: () => (
                <AgIcon
                  class="flex items-center justify-center w-16px h-16px color-#4d4f56 cursor-pointer"
                  name="more-fill"
                  size="16"
                />
              ),
              content: () => (
                <bk-dropdown-menu>
                  {row?.status === 1 && (
                    <bk-dropdown-item

                      onClick={() => handleSuspendClick(row)}
                    >
                      <Button
                        size="small"
                        text
                      >
                        { t('停用') }
                      </Button>
                    </bk-dropdown-item>
                  )}
                  <bk-dropdown-item onClick={() => handleDeleteClick(row)}>
                    <Button
                      v-bk-tooltips={{
                        content: t('请先停用再删除'),
                        disabled: row?.status === 0,
                      }}
                      disabled={row?.status === 1}
                      text
                    >
                      { t('删除') }
                    </Button>
                  </bk-dropdown-item>
                </bk-dropdown-menu>
              ),
            }}
          </bk-dropdown>
        </div>
      </div>
    ),
  },
]);

const getList = () => tableRef.value?.fetchData(filterData.value, { resetPage: true });

/**
 * 获取表格数据
 * @param params - 请求参数，默认值为空对象
 * @returns 接口返回的表格数据，兜底返回空数组
 */
const getTableData = async (params: Record<string, any> = {}): Promise<any[]> => {
  const requestParams = { ...params };
  const fieldsToJoin = ['categories'];
  fieldsToJoin.forEach((field) => {
    if (requestParams[field] && Array.isArray(requestParams[field])) {
      requestParams[field] = requestParams[field].join(',');
    }
  });

  const res = await getServers(apigwId.value, requestParams);
  return res;
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
    return 'color-#c4c6cc';
  }
  return '';
};

const handleSortChange: PrimaryTableProps['onSortChange'] = (sort) => {
  if (sort) {
    const { sortBy: colKey, descending } = sort;
    filterData.value.order_by = descending ? `-${colKey}` : colKey;
  }
  else {
    delete filterData.value.order_by;
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

const handleClearFilter = () => {
  emit('clear-filter');
};
defineExpose({ getList });
</script>

<style lang="scss" scoped>
.mcp-server-table-wrapper {

}
</style>
