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
  <div class="page-wrapper-padding model-service-container">
    <BkAlert
      class="model-service-alert"
      closable
      theme="info"
      :title="t('模型服务用于管理你的大模型后端连接信息（如地址、密钥、模型名称等）。配置完成后，即可通过网关统一调用这些模型')"
    />
    <div class="flex justify-between items-center header">
      <BkButton
        class="new-btn"
        theme="primary"
        @click="handleAdd"
      >
        {{ t('新建') }}
      </BkButton>
      <BkInput
        v-model="filterData.name"
        class="search-input"
        :placeholder="t('请输入模型服务名称')"
        clearable
        @enter="handleSearch"
      />
    </div>
    <div class="model-service-content">
      <AgTable
        ref="tableRef"
        show-settings
        resizable
        :api-method="getTableData"
        :columns="columns"
        @clear-filter="handleClearFilterKey"
      />
    </div>
    <AddModelService
      ref="addModelServiceRef"
      @done="handleModelServiceAdded"
    />
  </div>
</template>

<script setup lang="tsx">
import type { PrimaryTableProps, TableRowData } from '@blueking/tdesign-ui';
import { Message } from 'bkui-vue';
import AgTable from '@/components/ag-table/Index.vue';
import { usePopInfoBox } from '@/hooks';
import {
  deleteBackendService,
  getBackendServiceList,
} from '@/services/source/backend-services.ts';
import { useGateway } from '@/stores';
import AddModelService from './components/AddModelService.vue';

const { t } = useI18n();
const gatewayStore = useGateway();
const router = useRouter();

const filterData = ref({
  name: '',
});

const tableRef = useTemplateRef('tableRef');
const addModelServiceEl = useTemplateRef<InstanceType<typeof AddModelService> & {
  show: (serviceId?: number) => Promise<void>
  showClone: (serviceId: number) => Promise<void>
}>(
  'addModelServiceRef',
);

const gatewayId = computed(() => gatewayStore.apigwId);

const columns = computed<PrimaryTableProps['columns']>(() => [
  {
    title: t('名称'),
    colKey: 'name',
    ellipsis: true,
    cell: (h: any, { row }: { row: any }) => (
      <span
        class="color-#3a84ff cursor-pointer"
        onClick={() => handleEdit(row)}
      >
        { row.name }
      </span>
    ),
  },
  {
    title: t('描述'),
    colKey: 'description',
    ellipsis: true,
    cell: (h: any, { row }: { row: any }) => <span>{ row.description || '--' }</span>,
  },
  {
    title: t('关联资源数'),
    colKey: 'resource_count',
    cell: (h: any, { row }: { row: any }) => {
      return !row.resource_count || gatewayStore.isProgrammableGateway
        ? (
          <span>
            { row.resource_count || '--' }
          </span>
        )
        : (
          <bk-button
            text
            theme="primary"
            onClick={() => handleResource(row.id)}
          >
            { row.resource_count }
          </bk-button>
        );
    },
  },
  {
    title: t('更新时间'),
    colKey: 'updated_time',
    width: 260,
  },
  {
    title: t('操作'),
    colKey: 'operation',
    fixed: 'right',
    width: 210,
    cell: (h: any, { row }: { row: any }) => (
      <div class="flex gap-12px">
        <bk-button
          text
          theme="primary"
          onClick={() => handleEdit(row)}
        >
          { t('编辑') }
        </bk-button>
        <bk-button
          text
          theme="primary"
          onClick={() => handleClone(row)}
        >
          { t('克隆') }
        </bk-button>
        {
          row.resource_count
            ? (
              <span
                v-bk-tooltips={{
                  content: row.name === 'default'
                    ? t('默认后端服务，且被{resourceCount}个资源引用了，不能删除', {
                      resourceCount: row.resource_count,
                    })
                    : t('服务被{resourceCount}个资源引用了，不能删除', {
                      resourceCount: row.resource_count,
                    }),
                }}
              >
                <bk-button
                  text
                  theme="primary"
                  disabled={Boolean(row.resource_count) || row.name === 'default'}
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
                  disabled: row.name !== 'default',
                }}
              >
                <bk-button
                  text
                  theme="primary"
                  disabled={row.name === 'default'}
                  onClick={() => handleDelete(row)}
                >
                  { t('删除') }
                </bk-button>
              </span>
            )
        }
      </div>
    ),
  },
]);

watch(filterData, () => {
  tableRef.value?.fetchData(filterData.value, { resetPage: true });
}, { deep: true });

// 不是 AI 网关，跳转到 standard 后端服务页面
watch(() => gatewayStore.currentGateway, () => {
  if (([0, 1] as any[]).includes(gatewayStore.currentGateway?.kind)) {
    router.replace({ name: 'BackendService' });
  }
}, { deep: true });

const getTableData = (params: Record<string, any> = {}) => getBackendServiceList(gatewayId.value, {
  ...params,
  kind: 'ai',
});

const handleAdd = () => {
  addModelServiceEl.value?.show();
};

const handleEdit = (row: TableRowData) => {
  addModelServiceEl.value?.show(row.id);
};

const handleClone = (row: TableRowData) => {
  addModelServiceEl.value?.showClone(row.id);
};

const handleSearch = () => {
  tableRef.value?.fetchData(filterData.value, { resetPage: true });
};

const handleClearFilterKey = () => {
  filterData.value.name = '';
};

// 点击关联的资源数
const handleResource = (id: number) => {
  const params = {
    name: 'ResourceSetting',
    params: { id: gatewayId.value },
    query: { backend_id: id },
  };
  router.push(params);
};

const handleDelete = (row: TableRowData) => {
  usePopInfoBox({
    isShow: true,
    type: 'warning',
    title: t(`确定删除【${row.name}】该服务？`),
    subTitle: t('删除操作无法撤回，请谨慎操作'),
    confirmText: t('删除'),
    confirmButtonTheme: 'danger',
    onConfirm: async () => {
      await deleteBackendService(gatewayId.value, row.id);
      Message({
        message: t('删除成功'),
        theme: 'success',
      });
      tableRef.value?.fetchData(filterData.value);
    },
  });
};

const handleModelServiceAdded = () => {
  tableRef.value?.fetchData(filterData.value);
};

</script>

<style lang="scss" scoped>
.model-service-container {
  overflow: hidden;

  .model-service-alert {
    margin-bottom: 24px;
  }

  .header {
    margin-bottom: 16px;

    .new-btn {
      min-width: 80px;
    }

    .search-input {
      width: 30%;
      min-width: 300px;
    }
  }
}
</style>
