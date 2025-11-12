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
  <template v-if="currentStageVersionId === 0">
    <div class="exception-empty">
      <BkException
        type="empty"
        scene="part"
        :description="t('当前环境尚未发布，暂无资源信息')"
      />
    </div>
  </template>

  <template v-else>
    <div class="resource-info">
      <BkInput
        v-model="filterValue.keyword"
        class="w-520px mb-16px"
        clearable
        type="search"
        :placeholder="t('请输入后端服务、资源名称、前端请求路径搜索')"
      />
      <AgTable
        v-model:table-data="tableData"
        :columns="columns"
        table-row-key="id"
        show-settings
        :filter-row="null"
        :frontend-search="isSearching"
        local-page
        :row-class-name="getRowClassName"
        @filter-change="handleFilterChange"
        @clear-filter="handleClearQueries"
      >
        <template #empty>
          <TableEmpty
            :empty-type="filterValue.keyword ? 'search-empty' : 'empty'"
            @clear-filter="filterValue.keyword = ''"
          />
        </template>
      </AgTable>
    </div>
  </template>

  <!-- 资源详情 -->
  <ResourceDetails
    ref="resourceDetailsRef"
    :info="currentResource"
  />

  <!-- 环境编辑 -->
  <CreateStage
    ref="stageSidesliderRef"
    :stage-id="stageId"
    @hidden="handleCloseStage"
  />
</template>

<script setup lang="tsx">
import { useGateway, useStage } from '@/stores';
import { getGatewayLabels } from '@/services/source/gateway';
import {
  type IStageListItem,
  getStageList,
} from '@/services/source/stage';
import { getVersionDetail } from '@/services/source/resource';
import ResourceDetails from './ResourceDetails.vue';
import CreateStage from '../../components/CreateStage.vue';
import { copy } from '@/utils';
import RenderTagOverflow from '@/components/render-tag-overflow/Index.vue';
import AgTable from '@/components/ag-table/Index.vue';
import type { PrimaryTableProps } from '@blueking/tdesign-ui';
import { METHOD_THEMES } from '@/enums';
import { HTTP_METHODS } from '@/constants';
import { cloneDeep } from 'lodash-es';
import TableEmpty from '@/components/table-empty/Index.vue';

interface IProps {
  stageAddress: string
  stageId: number
  versionId: number
}

const {
  stageAddress,
  stageId,
  // versionId,
} = defineProps<IProps>();

const { t } = useI18n();
// 优先从store里取值，因为这里的值是同步更新的，不会存在vue内置钩子依赖执行顺序问题
const gatewayStore = useGateway();
const stageStore = useStage();

const filterValue = ref<Record<string, any>>({ keyword: '' });
const currentStage = ref<any>(null);
const currentResource = ref<any>({});
const resourceDetailsRef = ref();
const stageSidesliderRef = ref();
// 是否是点击了后端服务
const highlightRowId = ref(0);

// 网关标签
const labels = ref<any[]>([]);

// 资源信息
const tableData = ref<any[]>([]);
const initTableData = ref<any[]>([]);
const stageList = ref<IStageListItem[]>([]);

const gatewayId = computed<number>(() => gatewayStore.apigwId);

const isSearching = computed(() => !!filterValue.value.keyword);

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

const renderStageTag = computed(() => {
  return <span class="inline-block bg-#e4faf0 color-#14a568 rounded-2px text-10px w-18px! h-16px! line-height-16px text-center">{ t('环') }</span>;
});

const renderResourceTag = computed(() => {
  return <span class="inline-block bg-#EDF4FF color-#3A84FF rounded-2px text-10px w-18px! h-16px! line-height-16px text-center">{ t('资') }</span>;
});

const columns = computed<PrimaryTableProps['columns']>(() => [
  {
    colKey: 'backend',
    title: t('后端服务'),
    cell: (h, { row }) => (
      <bk-button
        theme="primary"
        text
        onClick={() => {
          highlightRowId.value = row.id;
          handleCheckStage({
            resourceName: row.name,
            backendName: row.proxy?.backend?.name,
          });
        }}
      >
        { row.proxy?.backend?.name ?? '--' }
      </bk-button>
    ),
  },
  {
    colKey: 'name',
    title: t('资源名称'),
    ellipsis: true,
    cell: (h, { row }) => (
      <div>
        <bk-button
          theme="primary"
          text
          onClick={() => showDetails(row)}
        >
          { row.name }
        </bk-button>
        {
          hasNoVerification(row)
            ? (
              <ag-icon
                v-bk-tooltips={{ content: t('该资源未配置认证方式，存在安全风险。') + t('如当前配置符合预期，可忽略该提示。') }}
                name="exclamation-circle-fill"
                class="ml-6px color-#F59500"
              />
            )
            : ''
        }
      </div>
    ),
  },
  {
    colKey: 'method',
    title: t('前端请求方法'),
    cell: (h, { row }) => (
      <bk-tag theme={METHOD_THEMES[row.method as keyof typeof METHOD_THEMES]}>
        {row.method}
      </bk-tag>
    ),
    filter: {
      type: 'multiple',
      showConfirmAndReset: true,
      resetValue: [],
      list: customMethodsList.value,
    },
  },
  {
    colKey: 'path',
    title: t('前端请求路径'),
    ellipsis: true,
  },
  {
    colKey: 'label_ids',
    title: t('标签'),
    filter: {
      type: 'multiple',
      showConfirmAndReset: true,
      resetValue: [],
      list: labelsList.value,
    },
    cell: (h, { row }) => (
      labels.value?.filter(label => row.gateway_label_ids?.includes(label.id)).map(label => label.name).length
        ? (
          <RenderTagOverflow
            data={labels.value?.filter(label => row.gateway_label_ids?.includes(label.id)).map(label => label.name)}
          />
        )
        : <span>--</span>
    ),
  },
  {
    colKey: 'plugins',
    displayTitle: t('生效的插件'),
    title: () => {
      return (
        <div>
          <bk-popover
            allow-html
            content="#plugins_header_tip"
            theme="light"
            popoverDelay={0}
          >
            <div class="underline decoration-dashed underline-offset-4">
              {t('生效的插件')}
            </div>
          </bk-popover>

          <div id="plugins_header_tip">
            <div class="mb-16px break-all">
              { t('当环境与资源同时启用同一个插件时，资源的优先级将高于环境')}
            </div>
            <div class="mb-8px">
              { renderResourceTag.value }
              <span class="ml-8px">{t('代表“ 资源中配置的插件生效 ”')}</span>
            </div>
            <div>
              { renderStageTag.value }
              <span class="ml-8px">{t('代表“ 环境中配置的插件生效 ”')}</span>
            </div>
          </div>
        </div>
      );
    },
    cell: (h, { row }) => (
      row.plugins?.length
        ? (
          <div class="flex items-center">
            {row.plugins.map(plugin => (
              <div class="flex items-center" key={plugin.id}>
                {plugin.binding_type === 'stage' ? renderStageTag.value : ''}
                {plugin.binding_type === 'resource' ? renderResourceTag.value : ''}
                <span class="v-middle ml-4px mr-4px">{ plugin.name }</span>
              </div>
            ))}
          </div>
        )
        : <span>--</span>
    ),
  },
  {
    colKey: 'is_public',
    title: t('是否公开'),
    cell: (h, { row }) => (
      <span class={{
        'color-#FE9C00': row.is_public,
        'color-#63656e': !row.is_public,
      }}
      >
        { row.is_public ? t('是') : t('否')}
      </span>
    ),
  },
  {
    colKey: 'act',
    title: t('操作'),
    width: 200,
    cell: (h, { row }) => (
      <>
        <bk-button
          text
          theme="primary"
          class="mr-10px"
          onClick={() => showDetails(row)}
        >
          { t('查看资源详情') }
        </bk-button>
        <bk-button
          text
          theme="primary"
          onClick={() => copyPath(row)}
        >
          { t('复制资源地址') }
        </bk-button>
      </>
    ),
  },
]);

const labelsList = computed(() => {
  if (!labels.value?.length) {
    return [];
  }

  return labels.value?.map((item: any) => {
    return {
      label: item.name,
      value: item.id,
    };
  });
});

const currentStageVersionId = computed(() => {
  return currentStage.value?.resource_version?.id;
});

watch(filterValue, () => {
  tableData.value = initTableData.value.filter((row) => {
    let result = true;
    if (filterValue.value.keyword) {
      result = !!(row.proxy?.backend?.name?.toLowerCase()?.includes(filterValue.value.keyword)
        || row.name.toLowerCase()?.includes(filterValue.value.keyword)
        || row.path.toLowerCase()?.includes(filterValue.value.keyword));
    }
    if (result && filterValue.value.method && filterValue.value.method.length) {
      result = filterValue.value.method.includes(row.method);
    }
    if (result && filterValue.value.label_ids && filterValue.value.label_ids.length) {
      result = filterValue.value.label_ids.some(
        (checkedLabelId: number) => row.gateway_label_ids.some(id => id === checkedLabelId),
      );
    }
    return result;
  });
}, { deep: true });

watch(
  () => stageId,
  async () => {
    if (stageId) {
      await init();
    }
  },
  { immediate: true },
);

const getTableData = async () => {
  if (!currentStage.value || !currentStageVersionId.value) {
    return;
  }
  const response = await getVersionDetail(
    gatewayId.value,
    currentStageVersionId.value,
    { stage_id: currentStage.value.id },
  );

  response.resources?.forEach((item: any) => {
    item.gateway_label_names = [];
    item?.gateway_label_ids?.forEach((id: string) => {
      const tagLabel = labels.value?.find((label: any) => label.id === id);
      if (tagLabel) {
        item.gateway_label_names?.push(tagLabel.name);
      }
    });
  });
  tableData.value = response.resources || [];
  initTableData.value = cloneDeep(response.resources) || [];
};

async function init() {
  stageList.value = stageStore.stageList;
  if (!stageStore.stageList.length) {
    stageList.value = await getStageList(gatewayId.value);
  }
  currentStage.value = stageList.value.find((item: { id: number }) => item.id === Number(stageId));
  if (currentStage.value) {
    await getLabels();
    // 依赖 getLabels() 获取的标签列表，需在这之后请求
    await getTableData();
  }
}

async function getLabels() {
  labels.value = await getGatewayLabels(gatewayId.value);
};

const getRowClassName = ({ row }) => {
  return row.id === highlightRowId.value ? 'highlight-row' : '';
};

const handleCloseStage = () => {
  highlightRowId.value = 0;
};

const showDetails = (row: any) => {
  currentResource.value = row;
  resourceDetailsRef.value?.showSideslider();
};

const copyPath = (row: any) => {
  copy(stageAddress.replace(/\/$/, '') + row.path);
};

// 查看环境
const handleCheckStage = ({ backendName }: {
  resourceName: string
  backendName: string
}) => {
  // 可传入 add | edit | check
  stageSidesliderRef.value?.handleShowSideslider('check', { backendName });
};

const handleClearQueries = () => {
  filterValue.value = {};
};

const handleFilterChange: PrimaryTableProps['onFilterChange'] = (filters) => {
  Object.assign(filterValue.value, filters);
};

const hasNoVerification = (row: any) => {
  const config = JSON.parse(row.contexts?.resource_auth?.config || '{}');
  return config.auth_verified_required === false && config.app_verified_required === false;
};

defineExpose({ reload: init });

</script>

<style lang="scss" scoped>

.exception-empty {
  display: flex;
  height: 420px;
  align-items: center;

  :deep(.bk-exception-description) {
    margin-top: 0;
    font-size: 14px;
  }

  :deep(.bk-exception-img) {
    width: 220px;
    height: 130px;
  }
}

:deep(.highlight-row) {
  background-color: #e1ecff;
}
</style>

<style lang="scss">
.content-footer {
  justify-content: flex-end;

  .btn-filter-save.disabled {
    display: none !important;
  }
}
</style>
