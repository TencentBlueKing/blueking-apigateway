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
  <div class="page-wrapper-padding backend-service-container">
    <div class="flex justify-between items-center header">
      <div class="header-btn">
        <BkButton
          v-if="!gatewayStore.isProgrammableGateway"
          v-bk-tooltips="{
            content: t('当前有版本正在发布，请稍后再进行后端服务修改'),
            disabled: !hasPublishingStage,
          }"
          class="new-btn"
          :disabled="hasPublishingStage"
          theme="primary"
          @click="handleAdd"
        >
          {{ t('新建') }}
        </BkButton>
      </div>
      <div class="header-search">
        <BkInput
          v-model="filterData.name"
          class="search-input"
          :placeholder="t('请输入服务名称')"
          clearable
        />
      </div>
    </div>
    <!-- 表格区域 -->
    <div class="backend-service-content">
      <BkLoading :loading="isLoading">
        <BkTable
          :key="tableKey"
          :row-class="isNewCreate"
          :data="tableData"
          :pagination="pagination"
          border="outer"
          class="table-layout"
          remote-pagination
          row-hover="auto"
          show-overflow-tooltip
          :columns="columns"
          @page-limit-change="handlePageSizeChange"
          @page-value-change="handlePageChange"
        >
          <template #empty>
            <TableEmpty
              :loading="isLoading"
              :empty-type="tableEmptyConf.emptyType"
              :abnormal="tableEmptyConf.isAbnormal"
              @refresh="getList"
              @clear-filter="handleClearFilterKey"
            />
          </template>
        </BkTable>
      </BkLoading>
    </div>

    <AddBackendService
      ref="addBackendServiceRef"
      :disabled="gatewayStore.isProgrammableGateway || hasPublishingStage"
      :base="baseInfo"
      :edit-id="backendServiceId"
      @done="getList()"
    />
  </div>
</template>

<script setup lang="tsx">
import { uniqueId } from 'lodash-es';
import { Message } from 'bkui-vue';
import { useGateway } from '@/stores';
import { timeFormatter } from '@/utils/timeFormatter';
import { useMaxTableLimit, usePopInfoBox, useQueryList } from '@/hooks';
import {
  deleteBackendService,
  getBackendServiceList,
} from '@/services/source/backendServices';
import { getStageList } from '@/services/source/stage';
import AddBackendService from '@/views/backend-services/components/AddBackendService.vue';
import TableEmpty from '@/components/table-empty/index.vue';

const { t } = useI18n();
const gatewayStore = useGateway();
const router = useRouter();
// 当前视口高度能展示最多多少条表格数据
const { maxTableLimit } = useMaxTableLimit({ allocatedHeight: 190 });

const addBackendServiceEl = useTemplateRef<InstanceType<typeof AddBackendService> & { show: () => void }>('addBackendServiceRef');
const tableKey = ref(uniqueId());
const backendServiceId = ref();
// 基础信息
const baseInfo = ref({
  name: '',
  description: '',
});
const filterData = ref({
  name: '',
  type: '',
});
const tableEmptyConf = ref({
  keyword: '',
  isAbnormal: false,
});
const stageList = ref<{ release: { status: string } }[]>([]);
const columns = shallowRef([
  {
    label: t('后端服务名称'),
    field: 'name',
    render: ({ row }) => {
      return (
        <BkButton
          text
          theme="primary"
          onClick={() => handleEdit(row)}
        >
          { row?.name }
        </BkButton>
      );
    },
  },
  {
    label: t('描述'),
    field: 'description',
    render: ({ row }) => {
      return (
        <span>
          { row?.description || '--' }
        </span>
      );
    },
  },
  {
    label: t('关联的资源'),
    field: 'resource_count',
    render: ({ row }) => {
      return !row?.resource_count || gatewayStore.isProgrammableGateway
        ? (
          <span>
            { row?.resource_count || '--' }
          </span>
        )
        : (
          <BkButton
            text
            theme="primary"
            onClick={() => handleResource(row)}
          >
            { row?.resource_count }
          </BkButton>
        );
    },
  },
  {
    label: t('更新时间'),
    field: 'updated_time',
    render: ({ row }) => {
      return (
        <span>
          { row?.updated_time }
        </span>
      );
    },
  },
  {
    label: t('操作'),
    field: 'operate',
    fixed: 'right',
    width: 150,
    render: ({ row }) => {
      return (
        <div>
          <BkButton
            v-bk-tooltips={{
              content: t('当前有版本正在发布，请稍后再进行后端服务修改'),
              disabled: !hasPublishingStage.value,
            }}
            disabled={hasPublishingStage.value}
            text
            theme="primary"
            style="margin-right: 25px"
            onClick={() => handleEdit(row)}
          >
            { t('编辑') }
          </BkButton>
          {
            row?.resource_count
              ? (
                <span
                  v-bk-tooltips={{
                    content: ['default'].includes(row?.name)
                      ? t('默认后端服务，且被{resourceCount}个资源引用了，不能删除', { resourceCount: row?.resource_count })
                      : t('服务被{resourceCount}个资源引用了，不能删除', { resourceCount: row?.resource_count }),
                  }}
                >
                  <BkButton
                    text
                    theme="primary"
                    disabled={Boolean(row?.resource_count) || ['default'].includes(row?.name)}
                    onClick={() => handleDelete(row)}
                  >
                    { t('删除') }
                  </BkButton>
                </span>
              )
              : (
                <span
                  v-bk-tooltips={{
                    content: t('默认后端服务，不能删除'),
                    disabled: !['default'].includes(row?.name),
                  }}
                >
                  <BkButton
                    theme="primary"
                    text
                    disabled={['default'].includes(row?.name)}
                    onClick={() => handleDelete(row)}
                  >
                    { t('删除') }
                  </BkButton>
                </span>
              )
          }
        </div>
      );
    },
  },
]);

const apigwId = computed(() => gatewayStore.apigwId);
const hasPublishingStage = computed(() => {
  return stageList.value.some(item => ['doing'].includes(item?.release?.status));
});

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList({
  apiMethod: getBackendServiceList,
  filterData,
  initialPagination: {
    limitList: [
      maxTableLimit,
      10,
      20,
      50,
      100,
    ],
    limit: maxTableLimit,
  },
});

watch(
  () => tableData.value, () => {
    updateTableEmptyConfig();
  },
  { deep: true },
);

const isNewCreate = ({ updated_time }: { updated_time: string }) => {
  return isWithinTime(updated_time) ? 'new-created' : '';
};

// 判断后端服务新建时间是否在24h之内
const isWithinTime = (date: string) => {
  const str = timeFormatter(date);
  const targetTime = new Date(str);
  const currentTime = new Date();
  // 计算两个时间之间的毫秒差
  const diff = currentTime.getTime() - targetTime.getTime();
  // 24 小时的毫秒数
  const twentyFourHours = 24 * 60 * 60 * 1000;
  return diff < twentyFourHours;
};

const handleAdd = () => {
  if (hasPublishingStage.value) {
    return;
  }
  baseInfo.value = Object.assign({}, {
    name: '',
    description: '',
  });
  backendServiceId.value = undefined;
  addBackendServiceEl.value?.show();
};

// 点击名称/编辑
const handleEdit = ({ id, name, description }: {
  id: number
  name: string
  description: string
}) => {
  baseInfo.value = Object.assign({}, {
    name,
    description,
  });
  backendServiceId.value = id;
  addBackendServiceEl.value?.show();
};

// 点击关联的资源数
const handleResource = ({ id }: { id: number }) => {
  const params = {
    name: 'apigwResource',
    params: { id: apigwId.value },
    query: { backend_id: id },
  };
  router.push(params);
};

const handleDelete = ({ id, name }: {
  name: string
  id: number
}) => {
  usePopInfoBox({
    isShow: true,
    type: 'warning',
    title: t(`确定删除【${name}】该服务？`),
    subTitle: t('删除操作无法撤回，请谨慎操作'),
    confirmText: t('删除'),
    confirmButtonTheme: 'danger',
    contentAlign: 'left',
    showContentBgColor: true,
    onConfirm: async () => {
      try {
        await deleteBackendService(apigwId.value, id);
        Message({
          message: t('删除成功'),
          theme: 'success',
        });
        getList();
      }
      catch (error) {
        console.log('error', error);
      }
    },
  });
};

const handleClearFilterKey = () => {
  filterData.value = Object.assign({},
    {
      name: '',
      type: '',
    },
  );
  getList();
  updateTableEmptyConfig();
};

const updateTableEmptyConfig = () => {
  tableEmptyConf.value.isAbnormal = pagination.value.abnormal;
  if (filterData.value.name && !tableData.value.length) {
    tableEmptyConf.value.emptyType = 'searchEmpty';
    return;
  }
  tableEmptyConf.value.emptyType = 'empty';
};

const getStageListData = async () => {
  stageList.value = await getStageList(apigwId.value);
};

onBeforeMount(() => {
  getStageListData();
});
</script>

<style lang="scss" scoped>
.backend-service-container {
  overflow: hidden;

  .new-btn {
    min-width: 80px;
    marin-right: 5px;
  }

  .header {
    margin-bottom: 15px;

    .header-search {
      min-width: 500px;
      max-width: calc(100vw - 400px);
    }
  }

  :deep(.new-created){
    background-color: #f1fcf5 !important;
  }

  .table-layout {
    :deep(.bk-table-body) {
    }

    :deep(.bk-table-head) {
      scrollbar-color: transparent transparent;
    }

    :deep(.bk-table-body) {
      scrollbar-color: transparent transparent;
        tbody > tr {
          td {
            background-color: rgba(0,0,0,0);
          }
      }
    }
  }
}
</style>
