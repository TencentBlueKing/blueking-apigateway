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
  <div class="page-wrapper-padding alarm-strategy-container">
    <div class="header flex justify-between m-b-16px">
      <div class="header-btn flex ">
        <span class="m-r-10px">
          <BkButton
            theme="primary"
            class="m-r-5px w-80px"
            @click="handleAdd"
          >
            {{ t('新建') }}
          </BkButton>
        </span>
      </div>
      <div class="header-search">
        <BkInput
          v-model="filterData.keyword"
          class="w-300px search-input"
          :placeholder="t('请输入告警策略名称，按Enter搜索')"
        />
      </div>
    </div>

    <div class="alarm-strategy-content">
      <AgTable
        ref="tableRef"
        v-model:table-data="tableData"
        v-model:settings="settings"
        row-key="id"
        disable-data-page
        show-settings
        :filter-value="filterData"
        :sort="sortData"
        :api-method="getTableData"
        :columns="tableColumns"
        @clear-filter="handleClearFilter"
      />
    </div>

    <!-- 新建/编辑 -->
    <AddAlarmStrategy
      v-model:slider-params="sliderConfig"
      v-model:detail-data="formData"
      v-model:effective-stage="effectiveStage"
      :init-data="initData"
      :label-list="labelList"
      :stage-list="stageList"
      @done="getList"
    />
  </div>
</template>

<script lang="tsx" setup>
import { cloneDeep } from 'lodash-es';
import { Message, Switcher } from 'bkui-vue';
import type {
  FilterValue,
  PrimaryTableProps,
  SortInfo,
} from '@blueking/tdesign-ui';
import { ITableMethod } from '@/types/common';
import { useGateway } from '@/stores';
import { usePopInfoBox } from '@/hooks';
import { getGatewayLabels } from '@/services/source/gateway';
import {
  type IAlarmStrategy,
  deleteStrategy,
  getStrategyDetail,
  getStrategyList,
  updateStrategyStatus,
} from '@/services/source/monitor';
import { getStageList } from '@/services/source/stage';
import AgTable from '@/components/ag-table/Index.vue';
import AddAlarmStrategy from '@/views/monitor-alarm/alarm-strategy/components/AddAlarmStrategy.vue';

const { t } = useI18n();
const gatewayStore = useGateway();
// const { maxTableLimit, clientHeight } = useMaxTableLimit();

const tableRef = useTemplateRef<InstanceType<typeof AgTable> & ITableMethod>('tableRef');

const tableColumns = shallowRef<PrimaryTableProps['columns']>([
  {
    title: t('告警策略名称'),
    colKey: 'name',
    ellipsis: true,
    fixed: 'left',
  },
  {
    title: t('标签'),
    colKey: 'gateway_labels',
    cell: (h, { row }: { row?: Partial<IAlarmStrategy> }) => {
      if (row?.gateway_labels?.length) {
        return (
          <div class="lh-1 single-hide">
            <span
              v-bk-tooltips={{
                content: labelTooltip(row?.gateway_labels),
                placement: 'top',
              }}
              class="label-box"
            >
              {
                row.gateway_labels.map((label, index) => {
                  if (index < 4) {
                    return (
                      <span class="ag-label">
                        { label.name }
                      </span>
                    );
                  }
                  if (index === row.gateway_labels.length - 1 && index > 3) {
                    return (
                      <span class="ag-label">
                        ...
                      </span>
                    );
                  }
                })
              }
            </span>
          </div>
        );
      }
      return '--';
    },
  },
  {
    title: t('生效环境'),
    colKey: 'effective_stages',
    ellipsis: true,
    cell: (h, { row }: { row?: Partial<IAlarmStrategy> }) => {
      if (Array.isArray(row?.effective_stages)) {
        return (
          <span>{ row.effective_stages.length > 0 ? row.effective_stages.join() : t('所有环境')}</span>
        );
      }
      return '--';
    },
  },
  {
    title: t('更新时间'),
    colKey: 'updated_time',
  },
  {
    title: t('是否启用'),
    colKey: 'enabled',
    cell: (h, { row }: { row?: Partial<IAlarmStrategy> }) => {
      if (row?.statusUpdating) {
        return (
          <BkLoading
            style="width: 48px;"
            loading
            theme="default"
            size="small"
            opacity={1}
          >
            <div style="height: 20px;" />
          </BkLoading>
        );
      }
      return (
        <Switcher
          v-model={row.enabled}
          theme="primary"
          true-value
          false-value={false}
          disabled={statusSwitcherDisabled.value}
          onChange={() => handleIsEnable(row)}
        />
      );
    },
  },
  {
    title: t('操作'),
    colKey: 'operate',
    fixed: 'right',
    cell: (h, { row }: { row?: Partial<IAlarmStrategy> }) => {
      return (
        <div>
          <BkButton
            class="m-r-25px"
            theme="primary"
            text
            onClick={() => handleEdit(row)}
          >
            { t('编辑') }
          </BkButton>
          <BkButton
            theme="primary"
            text
            onClick={() => handleDelete(row)}
          >
            { t('删除') }
          </BkButton>
        </div>
      );
    },
  },
]);
const settings = shallowRef({
  size: 'small',
  checked: [],
  disabled: [],
});

const filterData = ref<FilterValue>({});
const sortData = ref<SortInfo>({});
const statusSwitcherDisabled = ref(false);
const tableData = ref([]);
const labelList = ref([]);
const effectiveStage = ref('');
// 新建初始数据
const formData = ref({
  name: '',
  alarm_type: 'resource_backend',
  alarm_subtype: '',
  gateway_label_ids: [],
  config: {
    detect_config: {
      duration: 300,
      method: 'gte',
      count: 3,
    },
    converge_config: { duration: 86400 },
    notice_config: {
      notice_way: ['im'],
      notice_role: ['maintainer'],
      notice_extra_receiver: [],
    },
  },
  effective_stages: [],
});
const stageList = ref<{
  id: number
  name: string
}[]>([]);
const sliderConfig = ref({
  isShow: false,
  title: '',
});
let initData = reactive({});

const apigwId = computed(() => gatewayStore.apigwId);

const getTableData = async (params: Record<string, any> = {}) => {
  const results = await getStrategyList(apigwId.value, params);
  return results ?? [];
};

const getList = () => {
  tableRef.value!.fetchData(filterData.value, { resetPage: true });
};

const handleSearch = () => {
  getList();
};

watch(filterData, () => {
  handleSearch();
}, { deep: true });

const labelTooltip = (labels: {
  id: number
  name: string
}[]) => {
  const labelNameList = labels.map((item: {
    id: number
    name: string
  }) => {
    return item.name;
  });
  return labelNameList.join('; ');
};

const handleAdd = () => {
  sliderConfig.value = Object.assign({}, {
    isShow: true,
    title: t('新建告警策略'),
  });
  formData.value = Object.assign({}, {
    name: '',
    alarm_type: 'resource_backend',
    alarm_subtype: '',
    gateway_label_ids: [],
    config: {
      detect_config: {
        duration: 300,
        method: 'gte',
        count: 3,
      },
      converge_config: { duration: 86400 },
      notice_config: {
        notice_way: ['im'],
        notice_role: ['maintainer'],
        notice_extra_receiver: [],
      },
    },
    effective_stages: [],
  });
  initData = cloneDeep({
    form: formData.value,
    effectiveStage: 'all',
  });
  effectiveStage.value = 'all';
};

// 是否启用
const handleIsEnable = async (item: IAlarmStrategy) => {
  const { enabled, id } = item;
  try {
    if (item.statusUpdating) {
      return;
    }
    item.statusUpdating = true;
    await updateStrategyStatus(apigwId.value, id, { enabled });
    Message({
      message: enabled ? t('启用成功') : t('禁用成功'),
      theme: 'success',
      width: 'auto',
    });
    await getList();
  }
  finally {
    item.statusUpdating = false;
  }
};

const handleEdit = async ({ id }: { id: number }) => {
  try {
    const res = await getStrategyDetail(apigwId.value, id);
    formData.value = { ...res };
    // 当生效环境为空时，应该把生效环境初始化为 ‘全部环境’
    effectiveStage.value = res?.effective_stages?.length > 0 ? 'custom' : 'all';
    initData = cloneDeep({
      form: formData.value,
      effectiveStage: effectiveStage.value,
    });
  }
  finally {
    sliderConfig.value = Object.assign({}, {
      isShow: true,
      title: t('编辑告警策略'),
    });
  }
};

const handleDelete = (
  {
    id,
    name,
  }: {
    id: number
    name: string
  }) => {
  usePopInfoBox({
    isShow: true,
    title: t(`确定要删除告警策略【${name}】?`),
    type: 'warning',
    subTitle: t('策略删除后，将不再接收相关通知'),
    confirmText: t('删除'),
    confirmButtonTheme: 'danger',
    onConfirm: async () => {
      await deleteStrategy(apigwId.value, id);
      Message({
        message: t('删除成功'),
        theme: 'success',
      });
      getList();
    },
  });
};

const handleClearFilter = () => {
  filterData.value.keyword = '';
  getList();
};

const getStages = async () => {
  const res = await getStageList(apigwId.value);
  stageList.value = res || [];
};

const init = async () => {
  labelList.value = await getGatewayLabels(apigwId.value);
  nextTick(() => {
    tableData.value.forEach((item) => {
      item.statusUpdating = false;
    });
  });
};
init();

onBeforeMount(() => {
  getStages();
});
</script>

<style lang="scss" scoped>
:deep(.label-box) {
  .ag-label {
    height: 24px;
    line-height: 22px;
    border: 1px solid #dcdee5;
    text-align: center;
    padding: 0 10px;
    max-width: 90px;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: normal;
    display: inline-block;
    margin-right: 4px;
    border-radius: 2px;
    white-space: nowrap;
  }
}
</style>
