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
      <AgTable
        ref="tableRef"
        show-settings
        resizable
        :api-method="getTableData"
        :columns="columns"
        @clear-filter="handleClearFilterKey"
      />
    </div>

    <AddBackendService
      ref="addBackendServiceRef"
      :disabled="gatewayStore.isProgrammableGateway || hasPublishingStage"
      :base="baseInfo"
      :edit-id="backendServiceId"
      @done="handleBackendServiceAdded"
    />
  </div>
</template>

<script setup lang="tsx">
import { Message } from 'bkui-vue';
import { useGateway } from '@/stores';
import { usePopInfoBox } from '@/hooks';
import {
  deleteBackendService,
  getBackendServiceList,
} from '@/services/source/backend-services.ts';
import { getStageList } from '@/services/source/stage';
import AddBackendService from '@/views/backend-services/components/AddBackendService.vue';
import AgTable from '@/components/ag-table/Index.vue';
import type { PrimaryTableProps } from '@blueking/tdesign-ui';

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const gatewayStore = useGateway();

const addBackendServiceEl = useTemplateRef<InstanceType<typeof AddBackendService> & { show: () => void }>('addBackendServiceRef');
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
const stageList = ref<{ release: { status: string } }[]>([]);

const tableRef = useTemplateRef('tableRef');

const columns = computed<PrimaryTableProps['columns']>(() => [
  {
    title: t('后端服务名称'),
    colKey: 'name',
    cell: (h, { row }) => {
      return (
        <div
          v-bk-tooltips={{
            content: row.name,
            placement: 'top',
            disabled: !row.isOverflow,
            extCls: 'max-w-480px',
          }}
          class="truncate color-#3a84ff cursor-pointer"
          onMouseenter={e => tableRef.value?.handleCellEnter({
            e,
            row,
          })}
          onMouseLeave={e => tableRef.value?.handleCellLeave({
            e,
            row,
          })}
          onClick={() => handleEdit(row)}
        >
          { row.name }
        </div>
      );
    },
  },
  {
    title: t('描述'),
    colKey: 'description',
    ellipsis: true,
    cell: (h, { row }) => {
      return (
        <span>
          { row?.description || '--' }
        </span>
      );
    },
  },
  {
    title: t('关联的资源'),
    colKey: 'resource_count',
    cell: (h, { row }) => {
      return !row?.resource_count || gatewayStore.isProgrammableGateway
        ? (
          <span>
            { row?.resource_count || '--' }
          </span>
        )
        : (
          <bk-button
            text
            theme="primary"
            onClick={() => handleResource(row)}
          >
            { row?.resource_count }
          </bk-button>
        );
    },
  },
  {
    title: t('更新时间'),
    colKey: 'updated_time',
    width: 260,
    ellipsis: true,
    cell: (h, { row }) => {
      return (
        <span>
          { row?.updated_time }
        </span>
      );
    },
  },
  {
    title: t('操作'),
    colKey: 'operate',
    fixed: 'right',
    width: 150,
    cell: (h, { row }) => {
      return (
        <div>
          <bk-button
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
          </bk-button>
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
                  <bk-button
                    text
                    theme="primary"
                    disabled={Boolean(row?.resource_count) || ['default'].includes(row?.name)}
                    onClick={() => handleDelete(row)}
                  >
                    { t('删除') }
                  </bk-button>
                </span>
              )
              : (
                <span
                  v-bk-tooltips={{
                    content: t('默认后端服务，不能删除'),
                    disabled: !['default'].includes(row?.name),
                  }}
                >
                  <bk-button
                    theme="primary"
                    text
                    disabled={['default'].includes(row?.name)}
                    onClick={() => handleDelete(row)}
                  >
                    { t('删除') }
                  </bk-button>
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

watch(() => route.query, () => {
  if (route.query?.name) {
    filterData.value.name = route.query.name as string;
  }
}, {
  deep: true,
  immediate: true,
});

watch(filterData, () => {
  tableRef.value!.fetchData(filterData.value);
}, { deep: true });

const getTableData = async (params: Record<string, any> = {}) => getBackendServiceList(apigwId.value, params);

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
    name: 'ResourceSetting',
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
    onConfirm: async () => {
      await deleteBackendService(apigwId.value, id);
      Message({
        message: t('删除成功'),
        theme: 'success',
      });
      tableRef.value!.fetchData(filterData.value);
    },
  });
};

const handleClearFilterKey = () => {
  filterData.value = {
    name: '',
    type: '',
  };
};

const handleBackendServiceAdded = () => {
  tableRef.value!.fetchData(filterData.value);
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
    margin-right: 5px;
  }

  .header {
    margin-bottom: 15px;

    .header-search {
      max-width: calc(100vw - 400px);
      min-width: 500px;
    }
  }

  :deep(.new-created){
    background-color: #f1fcf5 !important;
  }
}
</style>
