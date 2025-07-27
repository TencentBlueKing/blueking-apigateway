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
  <div class="page-wrapper-padding">
    <div class="permission">
      <BkTab
        v-model:active="filterData.state"
        type="unborder-card"
        class="tab"
        @change="handleTabChange"
      >
        <BkTabPanel
          v-for="item in panels"
          :key="item.name"
          :name="item.name"
        >
          <template #label>
            <div class="flex items-center">
              {{ item.label }}
              <div class="count">
                <div
                  v-if="item.name === 'unprocessed' && Number(lastCount) > 0"
                  class="text"
                  :class="[filterData.state === item.name ? 'on' : 'off']"
                >
                  {{ lastCount }}
                </div>
              </div>
            </div>
          </template>
        </BkTabPanel>
      </BkTab>

      <div class="main">
        <div class="search-wrapper">
          <BkForm class="flex">
            <BkFormItem
              :label="t('蓝鲸应用ID')"
              class="mb-20px flex-grow-1"
              label-width="100"
              label-position="left"
            >
              <BkInput
                v-model="filterData.bk_app_code"
                clearable
                type="search"
                :placeholder="t('请输入应用ID')"
              />
            </BkFormItem>
            <BkFormItem
              label="MCP Server"
              class="mb-20px flex-grow-1"
              label-width="140"
            >
              <BkSelect
                v-model="filterData.mcp_server_id"
                :clearable="false"
              >
                <BkOption
                  v-for="option of mcpList"
                  :id="option.id"
                  :key="option.id"
                  :name="option.name"
                />
              </BkSelect>
            </BkFormItem>
            <BkFormItem
              :label="t('申请人')"
              class="mb-20px flex-grow-1"
              label-width="100"
            >
              <BkSelect
                v-model="filterData.applied_by"
                clearable
                :placeholder="t('请选择用户')"
              >
                <BkOption
                  v-for="option of applicantList"
                  :id="option"
                  :key="option"
                  :name="option"
                />
              </BkSelect>
            </BkFormItem>
          </BkForm>
        </div>

        <BkLoading :loading="isLoading">
          <BkTable
            :key="tableKey"
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
            <BkTableColumn :label="renderTypeLabel">
              <template #default="{ row }">
                <!-- {{ getOpTypeText(row?.mcp_server?.id) || '--' }} -->
                {{ row?.mcp_server?.name }}
              </template>
            </BkTableColumn>
            <BkTableColumn
              :label="t('申请人')"
              prop="applied_by"
            />
            <BkTableColumn
              :label="t('申请时间')"
              prop="applied_time"
            />
            <BkTableColumn
              :label="t('审批状态')"
              prop="status"
            >
              <template #default="{ row }">
                <div
                  v-if="row.status === 'pending'"
                  class="perm-apply-dot"
                >
                  <Loading
                    class="mr5"
                    loading
                    size="mini"
                    mode="spin"
                    theme="primary"
                  />
                  {{ statusMap[row?.status as keyof typeof statusMap] }}
                </div>

                <div
                  v-else
                  class="perm-apply-dot"
                >
                  <span
                    class="dot"
                    :class="[row?.status]"
                  />
                  {{ statusMap[row?.status as keyof typeof statusMap] }}
                </div>
              </template>
            </BkTableColumn>
            <BkTableColumn
              v-if="filterData.state === 'unprocessed'"
              :label="t('操作')"
            >
              <template #default="{ row }">
                <div>
                  <BkButton
                    text
                    theme="primary"
                    class="mr-10px"
                    @click="() => handleApprove(row, 'approved')"
                  >
                    {{ t('通过') }}
                  </BkButton>
                  <BkButton
                    text
                    theme="primary"
                    @click="() => handleApprove(row, 'rejected')"
                  >
                    {{ t('驳回') }}
                  </BkButton>
                </div>
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
      </div>
    </div>
  </div>

  <BkDialog
    theme="primary"
    :width="600"
    :quick-close="false"
    :header-position="'left'"
    :title="applyActionDialogConf.title"
    :is-show="applyActionDialogConf.isShow"
    :loading="applyActionDialogConf.isLoading"
    @confirm="handleSubmitApprove"
    @closed="applyActionDialogConf.isShow = false"
  >
    <BkForm
      ref="approveForm"
      :label-width="90"
      :model="curAction"
      :rules="rules"
      class="mt-10px mr-20px mb-30px"
    >
      <BkFormItem
        :label="t('备注')"
        required
        :property="'comment'"
      >
        <BkInput
          v-model="curAction.comment"
          type="textarea"
          :placeholder="t('请输入备注')"
          :rows="4"
          :maxlength="100"
        />
      </BkFormItem>
    </BkForm>
  </BkDialog>
</template>

<script lang="ts" setup>
import { Loading, Message } from 'bkui-vue';
import { useQueryList } from '@/hooks';
import {
  getMcpAppPermissionApply,
  getMcpPermissionsApplicant,
  updateMcpPermissions,
} from '@/services/source/mcp-market.ts';
import { getServers } from '@/services/source/mcp-server';
import TableEmpty from '@/components/table-empty/Index.vue';
import RenderCustomColumn from '@/components/custom-table-header-filter';
import { useGateway } from '@/stores';

const { t } = useI18n();
const gatewayStore = useGateway();
const route = useRoute();

const columnKey = ref(-1);
const tableKey = ref(0);
const defaultMcpId = ref(0);
const filterData = ref({
  bk_app_code: '',
  applied_by: '',
  mcp_server_id: 0,
  state: 'unprocessed',
});

const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList({
  apiMethod: getMcpAppPermissionApply,
  filterData,
});

const lastCount = ref(0);
const panels = ref([
  {
    name: 'unprocessed',
    label: '待审批',
  },
  {
    name: 'processed',
    label: '已审批',
  },
]);
const statusMap = reactive({
  approved: t('通过'),
  rejected: t('驳回'),
  pending: t('未审批'),
});
const mcpList = ref([]);
const applicantList = ref([]);
const approveForm = ref();
const applyActionDialogConf = reactive({
  isShow: false,
  isLoading: false,
  title: t('通过申请'),
});
const curAction = ref({
  id: 0,
  status: '',
  comment: '',
});
const tableEmptyConf = ref<{
  keyword: string
  isAbnormal: boolean
}>({
  keyword: '',
  isAbnormal: false,
});

const rules = reactive({
  comment: [
    {
      required: true,
      message: t('必填项'),
      trigger: 'blur',
    },
  ],
});

const getMcpList = async () => {
  const res = await getServers(gatewayStore.currentGateway!.id!);
  mcpList.value = res.results;
};
getMcpList();

const getApplicant = async () => {
  const response = await getMcpPermissionsApplicant(gatewayStore.currentGateway!.id!, filterData.value.mcp_server_id);
  applicantList.value = response?.applicants || [];
};

const handleTabChange = (name: string) => {
  if (name === filterData.value.state) {
    return;
  }

  handleClearFilterKey();
  tableKey.value = +new Date();
};

const updateTableEmptyConfig = () => {
  tableEmptyConf.value.isAbnormal = pagination.value.abnormal;
  const { bk_app_code, applied_by, mcp_server_id } = filterData.value;
  if (bk_app_code || applied_by || mcp_server_id !== defaultMcpId.value) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const resetSearch = () => {
  filterData.value.bk_app_code = '';
  filterData.value.applied_by = '';
  filterData.value.mcp_server_id = defaultMcpId.value;
  columnKey.value = +new Date();
};

const handleClearFilterKey = () => {
  isLoading.value = true;
  resetSearch();
};

const refreshTableData = async () => {
  await getList();
  updateTableEmptyConfig();
};

// const getOpTypeText = (type: string) => {
//   return (
//     (
//       mcpList.value.find((item: Record<string, string>) => item.id === type) || {}
//     )?.name || ''
//   );
// };

const renderTypeLabel = () => {
  return h('div', { class: 'operate-records-custom-label' }, [
    h(
      RenderCustomColumn,
      {
        key: columnKey.value,
        hasAll: false,
        columnLabel: 'MCP Server',
        selectValue: filterData.value.mcp_server_id,
        list: mcpList.value,
        onSelected: (payload: Record<string, string>) => {
          const curData = {
            id: 'mcp_server_id',
            name: 'MCP Server',
          };
          handleFilterData(payload, curData);
        },
      },
    ),
  ]);
};

const handleFilterData = (payload: Record<string, string>, curData: Record<string, string>) => {
  filterData.value[curData.id] = payload.id;

  if (['ALL'].includes(payload.id)) {
    delete filterData.value[curData.id];
  }
};

const handleApprove = (row: any, status: string) => {
  curAction.value = {
    id: row.id,
    status,
    comment: status === 'approved' ? t('通过') : t('驳回'),
  };
  if (status === 'approved') {
    applyActionDialogConf.title = t('通过申请');
  }
  else {
    applyActionDialogConf.title = t('驳回申请');
  }
  applyActionDialogConf.isShow = true;
};

const handleSubmitApprove = async () => {
  try {
    applyActionDialogConf.isLoading = true;

    await approveForm.value?.validate();
    await updateMcpPermissions(
      gatewayStore.currentGateway!.id!,
      filterData.value.mcp_server_id,
      curAction.value.id,
      curAction.value,
    );
    Message({
      message: t('操作成功'),
      theme: 'success',
    });
    refreshTableData();
    applyActionDialogConf.isShow = false;
  }
  catch (e: unknown) {
    Message({
      message: e?.error?.message,
      theme: 'error',
    });
  }
  finally {
    applyActionDialogConf.isLoading = true;
  }
};

watch(
  () => tableData.value,
  (list) => {
    if (filterData.value.state === 'unprocessed') {
      lastCount.value = list?.length || 0;
    }

    updateTableEmptyConfig();
  },
);

watch(
  () => route.query.serverId,
  (val) => {
    if (val) {
      filterData.value.mcp_server_id = Number(val) || 0;
      defaultMcpId.value = Number(val) || 0;
    }
  },
  { immediate: true },
);

watch(
  () => filterData.value.mcp_server_id,
  (val) => {
    if (val) {
      getApplicant();
    }
  },
  { immediate: true },
);

</script>

<style lang="scss" scoped>
.permission {
  background: #FFF;
  border-radius: 2px;
  box-shadow: 0 2px 4px 0 #1919290d;

  .tab {
    padding-left: 24px;
  }

  .main {
    padding: 6px 24px 42px;
  }
}

.count {
  display: flex;
  width: 20px;

  .text {
    padding: 2px 8px;
    margin-left: 8px;
    font-size: 12px;
    line-height: 12px;
    border-radius: 8px;

    &.on {
      color: #3A84FF;
      background: #E1ECFF;
    }

    &.off {
      color: #4D4F56;

      // background: #C4C6CC;
    }
  }
}

:deep(.perm-apply-dot) {

  .dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    margin-right: 3px;
    border-radius: 50%;

    &.approved {
      background: #e6f6eb;
      border: 1px solid #43c472;
    }

    &.rejected {
      background: #FFE6E6;
      border: 1px solid #EA3636;
    }
  }
}
</style>
