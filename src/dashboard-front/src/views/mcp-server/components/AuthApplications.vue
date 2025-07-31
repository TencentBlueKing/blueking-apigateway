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
  <div class="auth">
    <BkAlert
      theme="info"
      class="mb-16px"
      :title="t('授权应用将会拥有这个 mcp server 工具列表对应接口的调用权限')"
    />

    <div class="flex items-center justify-between mb-16px">
      <BkButton
        theme="primary"
        @click="showAuthorizeDia"
      >
        {{ t('主动授权') }}
      </BkButton>

      <BkInput
        v-model="filterData.bk_app_code"
        class="w-400px"
        :placeholder="t('请输入应用 ID')"
        clearable
        type="search"
      />
    </div>

    <BkLoading :loading="isLoading">
      <BkTable
        size="small"
        class="audit-table"
        border="outer"
        :data="tableData"
        :pagination="pagination"
        remote-pagination
        show-overflow-tooltip
        @page-value-change="handlePageChange"
        @page-limit-change="handlePageSizeChange"
      >
        <BkTableColumn
          :label="t('蓝鲸应用ID')"
          prop="bk_app_code"
        />
        <!-- <BkTableColumn :label="t('过期时间')" prop="expires" /> -->
        <BkTableColumn :label="renderTypeLabel">
          <template #default="{ row }">
            {{ getOpTypeText(row.grant_type) || '--' }}
          </template>
        </BkTableColumn>
        <BkTableColumn :label="t('操作')">
          <template #default="{ row }">
            <BkPopConfirm
              placement="top"
              trigger="click"
              :content="t('确认删除？')"
              @confirm="() => handleDel(row?.id)"
            >
              <BkButton
                text
                theme="primary"
              >
                {{ t('删除') }}
              </BkButton>
            </BkPopConfirm>
          </template>
        </BkTableColumn>
        <template #empty>
          <TableEmpty
            :keyword="tableEmptyConf.keyword"
            :abnormal="tableEmptyConf.isAbnormal"
            @reacquire="refreshTableData"
            @clear-filter="handleClearFilterKey"
          />
        </template>
      </BkTable>
    </BkLoading>

    <BkDialog
      v-model:is-show="isShowAuth"
      :title="t('主动授权')"
      width="480px"
      quick-close
      @closed="cancelAuth"
    >
      <div class="auth-dialog">
        <p>{{ t('你将对指定的蓝鲸应用添加访问资源的权限') }}</p>
        <BkForm
          ref="formRef"
          form-type="vertical"
          class="form-main"
          :model="formData"
          :rules="rules"
        >
          <BkFormItem
            :label="t('蓝鲸应用ID')"
            property="bk_app_code"
            required
          >
            <BkInput
              v-model="formData.bk_app_code"
              :placeholder="t('请输入应用 ID')"
              clearable
            />
          </BkFormItem>
        </BkForm>
      </div>
      <template #footer>
        <BkButton
          theme="primary"
          :loading="authLoading"
          @click="submitAuth"
        >
          {{ t('确定') }}
        </BkButton>
        <BkButton @click="cancelAuth">
          {{ t('取消') }}
        </BkButton>
      </template>
    </BkDialog>
  </div>
</template>

<script lang="ts" setup>
import { Message } from 'bkui-vue';
import { useQueryList } from '@/hooks';
import { authMcpPermissions, deleteMcpPermissions, getMcpPermissions } from '@/services/source/mcp-market';
import TableEmpty from '@/components/table-empty/Index.vue';
import RenderCustomColumn from '@/components/custom-table-header-filter/index.tsx';
import { useGateway } from '@/stores';

interface IProps { mcpServerId?: number }

const { mcpServerId = 0 } = defineProps<IProps>();

const { t } = useI18n();
const gatewayStore = useGateway();

const isShowAuth = ref(false);
const authLoading = ref(false);
const formData = ref({ bk_app_code: '' });
const formRef = ref();
const filterData = ref<{ [key: string]: any }>({
  bk_app_code: '',
  grant_type: '',
});
const tableKey = ref(-1);

const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList({
  apiMethod: getMcpPermissions,
  filterData,
  id: mcpServerId,
});

const curSelectData = ref<{ [key: string]: any }>({ grant_type: 'ALL' });
const tableEmptyConf = ref<{
  keyword: string
  isAbnormal: boolean
}>({
  keyword: '',
  isAbnormal: false,
});

const OperateRecordType = ref([
  {
    name: t('授权'),
    id: 'grant',
  },
  {
    name: t('申请'),
    id: 'apply',
  },
]);
const rules = {
  bk_app_code: [
    {
      required: true,
      message: t('请输入应用 ID'),
      trigger: 'blur',
    },
  ],
};

const getOpTypeText = (type: string) => {
  return (
    (
      OperateRecordType.value.find((item: Record<string, string>) => item.id === type) || {}
    )?.name || ''
  );
};

const renderTypeLabel = () => {
  return h('div', { class: 'operate-records-custom-label' }, [
    h(
      RenderCustomColumn,
      {
        key: tableKey.value,
        hasAll: true,
        columnLabel: t('操作类型'),
        selectValue: curSelectData.value.grant_type,
        list: OperateRecordType.value,
        onSelected: (payload: Record<string, string>) => {
          const curData = {
            id: 'grant_type',
            name: t('操作类型'),
          };
          handleFilterData(payload, curData);
        },
      },
    ),
  ]);
};

const showAuthorizeDia = () => {
  isShowAuth.value = true;
};

const cancelAuth = () => {
  isShowAuth.value = false;
  formData.value = { bk_app_code: '' };
};

const submitAuth = async () => {
  try {
    authLoading.value = true;

    await formRef.value.validate();
    await authMcpPermissions(gatewayStore.currentGateway!.id!, mcpServerId, formData.value);

    Message({
      theme: 'success',
      message: t('操作成功'),
    });
    cancelAuth();
    refreshTableData();
  }
  finally {
    authLoading.value = false;
  }
};

const handleDel = async (id: number) => {
  await deleteMcpPermissions(gatewayStore.currentGateway!.id!, mcpServerId, id);
  Message({
    theme: 'success',
    message: t('删除成功'),
  });
  refreshTableData();
};

const updateTableEmptyConfig = () => {
  tableEmptyConf.value.isAbnormal = pagination.value.abnormal;
  if (filterData.value.bk_app_code || filterData.value.grant_type) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const refreshTableData = async () => {
  await getList();
  updateTableEmptyConfig();
};

const resetSearch = () => {
  filterData.value.bk_app_code = '';
  filterData.value.grant_type = '';
  curSelectData.value.grant_type = 'ALL';
  tableKey.value = +new Date();
};

const handleClearFilterKey = () => {
  isLoading.value = true;
  resetSearch();
};

const handleFilterData = (payload: Record<string, string>, curData: Record<string, string>) => {
  filterData.value[curData.id] = payload.id;

  if (['ALL'].includes(payload.id)) {
    delete filterData.value[curData.id];
  }
};

watch(
  () => filterData.value,
  () => {
    updateTableEmptyConfig();
  },
  { deep: true },
);

</script>

<style lang="scss" scoped>
.auth {
  padding: 16px 24px 24px;
  background: #FFF;
}

.auth-dialog {

  p {
    font-size: 14px;
    color: #4D4F56;
  }

  .form-main {
    margin-top: 8px;
  }
}
</style>
