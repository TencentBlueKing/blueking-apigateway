<template>
  <div class="resource-container p20">
    <bk-alert
      theme="warning"
      title="资源如有更新，需要“生成版本”并“发布到环境”才能生效"
    />
    <div class="operate flex-row justify-content-between mt10 mb10">
      <div class="flex-1 flex-row align-items-center">
        <div class="mr10">
          <bk-button
            theme="primary"
            @click="handleCreateResource"
          >
            {{ t('新建') }}
          </bk-button>
        </div>
        <ag-dropdown
          :text="t('批量')"
          :dropdown-list="batchDropData"
          @on-change="handleBatchOperate"
          :is-disabled="!selections.length"></ag-dropdown>
        <ag-dropdown
          :text="t('导入')"
          :dropdown-list="importDropData"
          @on-change="handleBatchOperate"></ag-dropdown>
        <ag-dropdown
          :text="t('导出')"
          :dropdown-list="batchDropData"
          @on-change="handleBatchOperate"></ag-dropdown>
      </div>
      <div class="flex-1 flex-row justify-content-end">
        <bk-input class="ml10 mr10 operate-input" placeholder="请输入网关名" v-model="filterData.query"></bk-input>
      </div>
    </div>
    <bk-loading
      :loading="isLoading"
    >
      <bk-table
        class="table-layout"
        :data="tableData"
        remote-pagination
        :pagination="pagination"
        show-overflow-tooltip
        @page-limit-change="handlePageSizeChange"
        @page-value-change="handlePageChange"
        @selection-change="handleSelectionChange"
        row-hover="auto"
        header-align="center"
      >
        <bk-table-column
          width="100"
          type="selection"
        />
        <bk-table-column
          :label="t('资源名称')"
          prop="name"
          sort
        >
        </bk-table-column>
        <bk-table-column
          :label="t('前端请求方法')"
          prop="method"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('前端请求路径')"
          prop="path"
          sort
        >
        </bk-table-column>
        <bk-table-column
          :label="t('后端服务')"
        >
          <template #default="{ data }">
            {{data?.backend?.name}}
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('文档')"
          prop="docs"
          sort
        >
        </bk-table-column>
        <bk-table-column
          :label="t('标签')"
          prop="labels"
          sort
        >
        </bk-table-column>
        <bk-table-column
          :label="t('更新时间')"
          prop="updated_time"
          sort
        >
        </bk-table-column>
        <bk-table-column
          :label="t('操作')"
        >
          <template #default="{ data }">
            <bk-button
              text
              theme="primary"
              @click="handleEditResource(data.id, 'edit')"
            >
              {{ t('编辑') }}
            </bk-button>

            <bk-button
              text
              theme="primary"
              class="pl10 pr10"
              @click="handleEditResource(data.id, 'clone')"
            >
              {{ t('克隆') }}
            </bk-button>

            <bk-pop-confirm
              :title="t('确认删除该资源？')"
              content="删除操作无法撤回，请谨慎操作！"
              width="288"
              trigger="click"
              @confirm="handleDeleteResource(data.id)"
            >
              <bk-button
                text
                theme="primary">
                {{ t('删除') }}
              </bk-button>
            </bk-pop-confirm>
          </template>
        </bk-table-column>
      </bk-table>
    </bk-loading>
    <bk-dialog
      :is-show="dialogData.isShow"
      width="600"
      :title="dialogData.title"
      theme="primary"
      quick-close
      :is-loading="dialogData.loading"
      @confirm="handleBatchConfirm"
      @closed="dialogData.isShow = false">
      <div class="delete-content" v-if="isBatchDelete">
        <bk-table
          row-hover="auto"
          :columns="columns"
          :data="selections"
          show-overflow-tooltip
          max-height="280"
        />
        <bk-alert
          class="mt10 mb10"
          theme="warning"
          title="删除资源后，需要生成新的版本，并发布到目标环境才能生效"
        />
      </div>
      <div v-else>
        <bk-form>
          <bk-form-item label="基本信息">
            <bk-checkbox
              v-model="batchEditData.isPublic"
              @change="handlePublicChange">
              {{ t('是否公开') }}
            </bk-checkbox>
            <bk-checkbox
              :disabled="!batchEditData.isPublic"
              v-model="batchEditData.allowApply">
              {{ t('允许申请权限') }}
            </bk-checkbox>
          </bk-form-item>
        </bk-form>
      </div>
    </bk-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { useQueryList, useSelection } from '@/hooks';
import { getResourceListData, deleteResources, batchDeleteResources, batchEditResources } from '@/http';
import { Message } from 'bkui-vue';
import agDropdown from '@/components/ag-dropdown.vue';
import { IDialog } from '@/types';
const props = defineProps({
  apigwId: {
    type: Number,
    default: 0,
  },
});

// 批量下拉的item
const batchDropData = ref([{ value: 'edit', label: '编辑资源' }, { value: 'delete', label: '删除资源' }]);
// 导入下拉
const importDropData = ref([{ value: 'config', label: '资源配置' }, { value: 'doc', label: '资源文档' }]);

const { t } = useI18n();

const router = useRouter();

const filterData = ref({ query: '' });

const isBatchDelete = ref(false);

const dialogData = ref<IDialog>({
  isShow: false,
  title: t(''),
  loading: false,
});

const batchEditData = ref({
  isPublic: true,
  allowApply: true,
});

const columns = [
  {
    label: '请求路径',
    field: 'path',
  },
  {
    label: '请求方法',
    field: 'method',
  },
];

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList(getResourceListData, filterData);

// checkbox hooks
const {
  selections,
  handleSelectionChange,
  resetSelections,
} = useSelection();

// isPublic为true allowApply才可选
const handlePublicChange = () => {
  batchEditData.value.allowApply = batchEditData.value.isPublic;
};

// 新建资源
const handleCreateResource = () => {
  router.push({
    name: 'apigwResourceCreate',
  });
};

// 编辑资源
const handleEditResource = (id: number, type: string) => {
  const name = type === 'edit' ? 'apigwResourceEdit' : 'apigwResourceClone';
  router.push({
    name,
    params: {
      resourceId: id,
    },
  });
};

// 删除资源
const handleDeleteResource = async (id: number) => {
  console.log('props.apigwId', props);
  await deleteResources(props.apigwId, id);
  Message({
    message: t('删除成功'),
    theme: 'success',
  });
  getList();
};

// 处理批量编辑或删除
const handleBatchOperate = async (data: {value: string, label: string}) => {
  dialogData.value.isShow = true;
  // 批量删除
  if (data.value === 'delete') {
    isBatchDelete.value = true;
    dialogData.value.title = t(`确定要删除以下${selections.value.length}个资源`);
  } else {
    // 批量编辑
    isBatchDelete.value = false;
    dialogData.value.title = t(`批量编辑资源共${selections.value.length}个`);
  }
};

const handleBatchConfirm = async () => {
  const ids = selections.value.map(e => e.id);
  if (isBatchDelete.value) {
    // 批量删除
    await batchDeleteResources(props.apigwId, { ids });
  } else {
    await batchEditResources(props.apigwId, { ids });
  }
  dialogData.value.isShow = false;
  Message({
    message: t('删除成功'),
    theme: 'success',
  });
  getList();
  resetSelections();
};
</script>
<style lang="scss" scoped>
.resource-container{
  .operate{
    &-input{
      width: 450px;
    }
  }
  .dialog-content{
    // max-height: 280px;
  }
}
</style>
