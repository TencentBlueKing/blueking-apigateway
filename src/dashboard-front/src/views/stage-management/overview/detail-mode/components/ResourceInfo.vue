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
        ref="resourceTableRef"
        v-model:table-data="tableData"
        cache-identifier="StageOverview"
        :columns="columns"
        table-row-key="id"
        show-settings
        :filter-value="filterValue"
        local-page
        resizable
        :row-class-name="getRowClassName"
        :table-empty-type="tableEmptyType"
        @filter-change="handleFilterChange"
        @clear-filter="handleClearQueries"
      />
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
import { cloneDeep } from 'lodash-es';
import { copy } from '@/utils';
import { useGateway, useStage } from '@/stores';
import { METHOD_THEMES } from '@/enums';
import { HTTP_METHODS, RESOURCE_TYPE_LIST } from '@/constants';
import { getStageList } from '@/services/source/gateway/stage';
import type { IStageListItem } from '@/types/stage';
import { getLabelList } from '@/services/source/gateway/label';
import { getVersionDetail } from '@/services/source/gateway/resource-version';
import type { IExtractApiReturn } from '@/services/types/utils.ts';
import ResourceDetails from './ResourceDetails.vue';
import CreateStage from '../../components/CreateStage.vue';
import AgOverflowTags from '@/components/base/ag-overflow-tags/Index.vue';
import AgTable, {
  type FilterValue,
  type IAgTableInstance,
  type ITableColumn,
  type ITableEmptyType,
} from '@/components/base/ag-table';

type IGatewayLabelItem = IExtractApiReturn<typeof getLabelList>[number];
type IVersionResource = IExtractApiReturn<typeof getVersionDetail>['resources'][number] & {
  gateway_label_names?: string[]
};

interface IProps {
  stageAddress: string
  stageId: number
  // 动态 Tab 面板组件公共入参占位，避免透传到根 DOM
  // eslint-disable-next-line vue/no-unused-properties
  versionId: number | undefined
  // eslint-disable-next-line vue/no-unused-properties
  stage: Record<string, any> | undefined
}
const {
  stageAddress,
  stageId,
} = defineProps<IProps>();

const { t } = useI18n();
// 优先从store里取值，因为这里的值是同步更新的，不会存在vue内置钩子依赖执行顺序问题
const gatewayStore = useGateway();
const stageStore = useStage();

const filterValue = ref<Record<string, any>>({ keyword: '' });
const resourceTableRef = useTemplateRef<IAgTableInstance<IVersionResource>>('resourceTableRef');
const currentStage = ref<any>(null);
const currentResource = ref<any>({});
const resourceDetailsRef = useTemplateRef('resourceDetailsRef');
const stageSidesliderRef = useTemplateRef('stageSidesliderRef');
// 是否是点击了后端服务
const highlightRowId = ref(0);

// 网关标签
const labels = ref<IGatewayLabelItem[]>([]);

// 资源信息
const tableData = ref<IVersionResource[]>([]);
const initTableData = ref<IVersionResource[]>([]);
const stageList = ref<IStageListItem[]>([]);

const gatewayId = computed<number>(() => gatewayStore.apigwId);

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

const isAIGateway = computed(() => gatewayStore.isAIGateway);

const columns = computed<ITableColumn<IVersionResource>[]>(() => {
  const backendCol: ITableColumn<IVersionResource>[] = [
    {
      colKey: 'backend',
      title: isAIGateway.value ? t('后端/模型服务') : t('后端服务'),
      ellipsis: true,
      cell: (_h, { row }) => (
        <span
          class="color-#3a84ff cursor-pointer"
          onClick={() => {
            highlightRowId.value = row.id;
            handleCheckStage({
              resourceName: row.name,
              backendName: row.proxy?.backend?.name,
            });
          }}
        >
          { row.proxy?.backend?.name ?? '--' }
        </span>
      ),
    },
  ];
  // ai网关需要展示的列
  const aiCols: ITableColumn<IVersionResource>[] = isAIGateway.value
    ? [
      ...backendCol,
      {
        colKey: 'kind',
        title: t('资源类型'),
        ellipsis: true,
        minWidth: 100,
        filter: {
          type: 'single',
          showConfirmAndReset: true,
          popupProps: { overlayInnerClassName: 'custom-radio-filter-wrapper' },
          list: RESOURCE_TYPE_LIST,
        },
        cell: (_h, { row }) => {
          const resourceTypeData = RESOURCE_TYPE_LIST.find(item => item.value === row.kind);
          return (
            <bk-tag theme={resourceTypeData?.theme ?? 'default'}>
              {resourceTypeData?.label ?? t('普通 API')}
            </bk-tag>
          );
        },
      },
    ]
    : backendCol;

  return [
    ...aiCols,
    {
      colKey: 'name',
      title: t('资源名称'),
      ellipsis: (_h, { row }) => row.name,
      minWidth: 150,
      cell: (_h, { row }) => (
        <span
          class="color-#3A84FF cursor-pointer"
          onClick={() => showDetails(row)}
        >
          <span>{ row.name }</span>
          <span>
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
          </span>
        </span>
      ),
    },
    {
      colKey: 'method',
      title: t('前端请求方法'),
      cell: (_h, { row }) => (
        <bk-tag theme={METHOD_THEMES[row.method as keyof typeof METHOD_THEMES]}>
          {row.method}
        </bk-tag>
      ),
      filter: {
        type: 'multiple',
        showConfirmAndReset: true,
        popupProps: {
          overlayInnerClassName: 'resource-info-filter-wrapper',
        },
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
        popupProps: {
          overlayInnerClassName: 'resource-info-filter-wrapper',
        },
        resetValue: [],
        list: labelsList.value,
      },
      cell: (_h, { row }) => (
        labels.value?.filter((label: IGatewayLabelItem) =>
          row.gateway_label_ids?.includes(label.id)).map((label: IGatewayLabelItem) => label.name).length
          ? (
            <AgOverflowTags
              data={labels.value?.filter((label: IGatewayLabelItem) =>
                row.gateway_label_ids?.includes(label.id)).map((label: IGatewayLabelItem) => label.name)}
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
              trigger="hover"
              theme="light"
              popoverDelay={0}
            >
              {{
                default: () => (
                  <div class="underline decoration-dashed underline-offset-4">
                    {t('生效的插件')}
                  </div>
                ),
                content: () => (
                  <div class="plugins_header_tip">
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
                ),
              }}
            </bk-popover>
          </div>
        );
      },
      ellipsis: true,
      cell: (_h, { row }) => (
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
      cell: (_h, { row }) => (
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
      cell: (_h, { row }) => (
        <>
          <bk-button
            text
            theme="primary"
            class="mr-12px"
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
  ];
});

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

const tableEmptyType = computed<ITableEmptyType>(() => filterValue.value.keyword ? 'search-empty' : 'empty');

watch(filterValue, () => {
  tableData.value = initTableData.value.filter((row: any) => {
    let result = true;
    if (filterValue.value.keyword) {
      const keywordInLowerCase = filterValue.value.keyword.toLowerCase();
      result = !!(row.proxy?.backend?.name?.toLowerCase()?.includes(keywordInLowerCase)
        || row.name.toLowerCase()?.includes(keywordInLowerCase)
        || row.path.toLowerCase()?.includes(keywordInLowerCase));
    }
    if (result && filterValue.value.method && filterValue.value.method.length) {
      result = filterValue.value.method.includes(row.method);
    }
    if (result && filterValue.value.kind) {
      result = filterValue.value.kind.includes(row.kind);
    }
    if (result && filterValue.value.label_ids && filterValue.value.label_ids.length) {
      result = filterValue.value.label_ids.some(
        (checkedLabelId: number) => row.gateway_label_ids.some((id: number) => id === checkedLabelId),
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
  resetFilterAndPage();
};

// 数据源改变时，重置筛选并回到第一页（保留当前自适应每页条数）
const resetFilterAndPage = () => {
  filterValue.value = { keyword: '' };
  nextTick(() => {
    const pageSize = resourceTableRef.value?.getPagination()?.pageSize ?? 10;
    resourceTableRef.value?.setPagination({
      current: 1,
      pageSize,
    });
  });
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
  labels.value = await getLabelList(gatewayId.value);
}

const getRowClassName = ({ row }: { row: IVersionResource }) => {
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

const handleFilterChange = (filters: FilterValue) => {
  filterValue.value = {
    ...filterValue.value,
    ...filters,
    method: filters.method?.filter((item: string | undefined) => !!item) || [],
  };
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

<!-- eslint-disable-next-line vue/enforce-style-attribute -- 覆盖挂载在 body 下的 TDesign 表头筛选弹层样式 -->
<style lang="scss">
.content-footer {
  justify-content: flex-end;

  .btn-filter-save.disabled {
    display: none !important;
  }
}

.resource-info-filter-wrapper {

  .t-table__filter-pop-wrapper {
    max-height: 300px !important;
  }
}
</style>
