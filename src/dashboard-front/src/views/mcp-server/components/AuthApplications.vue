<template>
  <div class="auth">
    <bk-alert
      theme="info"
      class="mb16"
      :title="t('授权应用将会拥有这个 mcp server 工具列表对应接口的调用权限')"
      closable
    />

    <div class="flex-row align-items-center justify-content-between mb16">
      <bk-button theme="primary" @click="showAuthorizeDia">
        {{ t('主动授权') }}
      </bk-button>

      <bk-input
        v-model="filterData.bk_app_code"
        style="width: 400px"
        :placeholder="t('请输入应用 ID')"
        :clearable="true"
        type="search"
      />
    </div>

    <bk-loading :loading="isLoading">
      <bk-table
        size="small"
        ref="tableRef"
        class="audit-table"
        border="outer"
        :data="tableData"
        :pagination="pagination"
        :remote-pagination="true"
        :show-overflow-tooltip="true"
        @page-value-change="handlePageChange"
        @page-limit-change="handlePageSizeChange"
      >
        <bk-table-column :label="t('蓝鲸应用ID')" prop="bk_app_code" />
        <!-- <bk-table-column :label="t('过期时间')" prop="expires" /> -->
        <bk-table-column :label="renderTypeLabel">
          <template #default="{ row }">
            {{ getOpTypeText(row.grant_type) || '--'}}
          </template>
        </bk-table-column>
        <bk-table-column :label="t('操作')">
          <template #default="{ row }">
            <bk-pop-confirm
              placement="top"
              trigger="click"
              :content="t('确认删除？')"
              @confirm="handleDel(row?.id)">
              <bk-button text theme="primary">
                {{ t('删除') }}
              </bk-button>
            </bk-pop-confirm>
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

    <bk-dialog
      v-model:is-show="isShowAuth"
      :title="t('主动授权')"
      @closed="cancelAuth"
      width="480px"
      quick-close
    >
      <div class="auth-dialog">
        <p>{{ t('你将对指定的蓝鲸应用添加访问资源的权限') }}</p>
        <bk-form
          ref="formRef"
          form-type="vertical"
          class="form-main"
          :model="formData"
          :rules="rules"
        >
          <bk-form-item
            :label="t('蓝鲸应用ID')"
            property="bk_app_code"
            required
          >
            <bk-input v-model="formData.bk_app_code" :placeholder="t('请输入应用 ID')" :clearable="true" />
          </bk-form-item>
        </bk-form>
      </div>
      <template #footer>
        <bk-button theme="primary" :loading="authLoading" @click="submitAuth">
          {{ t('确定') }}
        </bk-button>
        <bk-button @click="cancelAuth">
          {{ t('取消') }}
        </bk-button>
      </template>
    </bk-dialog>
  </div>
</template>

<script lang="ts" setup>
import { h, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { Message } from 'bkui-vue';
// @ts-ignore
import { useQueryList } from '@/hooks';
// @ts-ignore
import { getMcpPermissions, authMcpPermissions, deleteMcpPermissions } from '@/http/mcp-market';
// @ts-ignore
import TableEmpty from '@/components/table-empty.vue';
// @ts-ignore
import { useCommon } from '@/store';
// @ts-ignore
import RenderCustomColumn from '@/components/custom-table-header-filter';

const props = defineProps({
  mcpServerId: {
    type: Number,
    default: 0,
    required: true,
  },
});

const { t } = useI18n();
const common = useCommon();

const isShowAuth = ref<boolean>(false);
const authLoading = ref<boolean>(false);
const formData = ref({ bk_app_code: '' });
const formRef = ref();
const filterData = ref<{[key: string]: any}>({
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
} = useQueryList(getMcpPermissions, filterData, props.mcpServerId);
const curSelectData = ref<{[key: string]: any}>({ grant_type: 'ALL' });
const tableEmptyConf = ref<{keyword: string, isAbnormal: boolean}>({
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
  formData.value = {
    bk_app_code: '',
  };
};

const submitAuth = async () => {
  try {
    authLoading.value = true;

    await formRef.value.validate();
    await authMcpPermissions(common.apigwId, props.mcpServerId, formData.value);

    Message({
      theme: 'success',
      message: t('操作成功'),
    });
    cancelAuth();
    refreshTableData();
  } catch (e) {
    console.log(e);
  } finally {
    authLoading.value = false;
  }
};

const handleDel = async (id: number) => {
  await deleteMcpPermissions(common.apigwId, props.mcpServerId, id);
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
  background: #FFFFFF;
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
