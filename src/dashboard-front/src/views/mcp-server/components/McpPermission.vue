<template>
  <div class="page-wrapper-padding">
    <div class="permission">
      <bk-tab v-model:active="filterData.state" @change="handleTabChange" type="unborder-card" class="tab">
        <bk-tab-panel
          v-for="item in panels"
          :key="item.name"
          :name="item.name"
        >
          <template #label>
            <div class="flex-row align-items-center">
              {{ item.label }}
              <div class="count">
                <div
                  :class="['text', filterData.state === item.name ? 'on' : 'off']"
                  v-if="item.name === 'unprocessed' && Number(lastCount) > 0">
                  {{ lastCount }}
                </div>
              </div>
            </div>
          </template>
        </bk-tab-panel>
      </bk-tab>

      <div class="main">
        <div class="search-wrapper">
          <bk-form class="flex-row">
            <bk-form-item :label="t('蓝鲸应用ID')" class="mb20 flex-1" label-width="100" label-position="left">
              <bk-input
                clearable
                type="search"
                v-model="filterData.bk_app_code"
                :placeholder="t('请输入应用ID')">
              </bk-input>
            </bk-form-item>
            <bk-form-item label="MCP Server" class="mb20 flex-1" label-width="140">
              <bk-select v-model="filterData.mcp_server_id" :clearable="false">
                <bk-option
                  v-for="option of mcpList"
                  :key="option.id"
                  :id="option.id"
                  :name="option.name">
                </bk-option>
              </bk-select>
            </bk-form-item>
            <bk-form-item :label="t('申请人')" class="mb20 flex-1" label-width="100">
              <bk-select v-model="filterData.applied_by" clearable :placeholder="t('请选择用户')">
                <bk-option
                  v-for="option of applicantList"
                  :key="option"
                  :id="option"
                  :name="option">
                </bk-option>
              </bk-select>
            </bk-form-item>
          </bk-form>
        </div>

        <bk-loading :loading="isLoading">
          <bk-table
            size="small"
            ref="tableRef"
            class="audit-table"
            border="outer"
            :key="tableKey"
            :data="tableData"
            :pagination="pagination"
            :remote-pagination="true"
            :show-overflow-tooltip="true"
            @page-value-change="handlePageChange"
            @page-limit-change="handlePageSizeChange"
          >
            <bk-table-column :label="t('蓝鲸应用ID')" prop="bk_app_code" />
            <bk-table-column :label="renderTypeLabel">
              <template #default="{ row }">
                <!-- {{ getOpTypeText(row?.mcp_server?.id) || '--' }} -->
                {{ row?.mcp_server?.name }}
              </template>
            </bk-table-column>
            <bk-table-column :label="t('申请人')" prop="applied_by" />
            <bk-table-column :label="t('申请时间')" prop="applied_time" />
            <bk-table-column :label="t('审批状态')" prop="status">
              <template #default="{ row }">
                <div class="perm-apply-dot" v-if="row.status === 'pending'">
                  <Loading class="mr5" loading size="mini" mode="spin" theme="primary" />
                  {{ statusMap[row?.status as keyof typeof statusMap] }}
                </div>

                <div class="perm-apply-dot" v-else>
                  <span :class="['dot', row?.status]" />
                  {{ statusMap[row?.status as keyof typeof statusMap] }}
                </div>
              </template>
            </bk-table-column>
            <bk-table-column :label="t('操作')" v-if="filterData.state === 'unprocessed'">
              <template #default="{ row }">
                <bk-button text theme="primary" class="mr10" @click="handleApprove(row, 'approved')">
                  {{ t('通过') }}
                </bk-button>
                <bk-button text theme="primary" @click="handleApprove(row, 'rejected')">
                  {{ t('驳回') }}
                </bk-button>
              </template>
            </bk-table-column>
            <template #empty>
              <TableEmpty
                :keyword="tableEmptyConf.keyword"
                :abnormal="tableEmptyConf.isAbnormal"
                @reacquire="refreshTableData"
                @clear-filter="handleClearFilterKey"
              />
            </template>
          </bk-table>
        </bk-loading>
      </div>
    </div>
  </div>

  <bk-dialog
    theme="primary"
    :width="600"
    :quick-close="false"
    :header-position="'left'"
    :title="applyActionDialogConf.title"
    :is-show="applyActionDialogConf.isShow"
    :loading="applyActionDialogConf.isLoading"
    @confirm="handleSubmitApprove"
    @closed="applyActionDialogConf.isShow = false">
    <bk-form
      :label-width="90"
      :model="curAction"
      :rules="rules"
      ref="approveForm"
      class="mt10 mr20 mb30">
      <bk-form-item
        :label="t('备注')"
        :required="true"
        :property="'comment'">
        <bk-input
          type="textarea"
          :placeholder="t('请输入备注')"
          v-model="curAction.comment"
          :rows="4"
          :maxlength="100">
        </bk-input>
      </bk-form-item>
    </bk-form>
  </bk-dialog>
</template>

<script lang="ts" setup>
import { h, ref, reactive, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { Message, Loading } from 'bkui-vue';
import { useRoute } from 'vue-router';
// @ts-ignore
import { useCommon } from '@/store';
// @ts-ignore
import { useQueryList } from '@/hooks';
// @ts-ignore
import {
  getMcpAppPermissionApply,
  updateMcpPermissions,
  getMcpPermissionsApplicant,
} from '@/http/mcp-market';
import {
  getServers,
} from '@/http/mcp-server';
// @ts-ignore
import TableEmpty from '@/components/table-empty.vue';
// @ts-ignore
import RenderCustomColumn from '@/components/custom-table-header-filter';

const { t } = useI18n();
const common = useCommon();
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
} = useQueryList(getMcpAppPermissionApply, filterData);
const lastCount = ref<number>(0);
const panels = ref([
  { name: 'unprocessed', label: '待审批' },
  { name: 'processed', label: '已审批' },
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
const tableEmptyConf = ref<{keyword: string, isAbnormal: boolean}>({
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
  const res = await getServers(common.apigwId);
  mcpList.value = res.results;
};
getMcpList();

const getApplicant = async () => {
  const response = await getMcpPermissionsApplicant(common.apigwId, filterData.value.mcp_server_id);
  applicantList.value = response?.applicants || [];
};
getApplicant();

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
  } else {
    applyActionDialogConf.title = t('驳回申请');
  }
  applyActionDialogConf.isShow = true;
};

const handleSubmitApprove = async () => {
  try {
    applyActionDialogConf.isLoading = true;

    await approveForm.value?.validate();
    await updateMcpPermissions(common.apigwId, filterData.value.mcp_server_id, curAction.value.id, curAction.value);
    Message({
      message: t('操作成功'),
      theme: 'success',
    });
    refreshTableData();
    applyActionDialogConf.isShow = false;
  } catch ({ error }: any) {
    Message({
      message: error.message,
      theme: 'error',
    });
  } finally {
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

</script>

<style lang="scss" scoped>
.permission {
  border-radius: 2px;
  background: #FFFFFF;
  box-shadow: 0 2px 4px 0 #1919290d;
  .tab {
    padding-left: 24px;
  }
  .main {
    padding: 6px 24px 42px;
  }
}

.count {
  width: 20px;
  display: flex;
  .text {
    padding: 2px 8px;
    font-size: 12px;
    line-height: 12px;
    border-radius: 8px;
    margin-left: 8px;
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
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
    margin-right: 3px;
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
