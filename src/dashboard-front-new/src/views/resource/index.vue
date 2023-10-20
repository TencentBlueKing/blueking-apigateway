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
    <div class="flex-row resource-content">
      <div class="left-wraper" :style="{ width: isDetail ? '370px' : '100%' }">
        <!-- <bk-table
          v-if="isDetail"
          class="table-layout-left"
          :data="tableData"
          remote-pagination
          :pagination="pagination"
          show-overflow-tooltip
          @page-limit-change="handlePageSizeChange"
          @page-value-change="handlePageChange"
          @selection-change="handleSelectionChange"
          row-hover="auto"
        >
          <bk-table-column
            width="100"
            type="selection"
          />
          <bk-table-column
            :label="t('资源名称')"
          >
            <template #default="{ data }">
              <bk-button
                text
                theme="primary"
                @click="handleEditResource(data.id, 'edit')"
              >
                {{data?.name}}
              </bk-button>
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('后端服务')"
          >
            <template #default="{ data }">
              {{data?.backend?.name}}
            </template>
          </bk-table-column>
        </bk-table> -->
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
          >
            <bk-table-column
              width="80"
              type="selection"
            />
            <bk-table-column
              :label="t('资源名称')"
            >
              <template #default="{ data }">
                <bk-button
                  text
                  theme="primary"
                  @click="handleShowInfo(data.id)"
                >
                  {{data?.name}}
                </bk-button>
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('前端请求方法')"
              prop="method"
              width="120"
              v-if="!isDetail"
            >
            </bk-table-column>
            <bk-table-column
              width="120"
              :label="t('后端服务')"
            >
              <template #default="{ data }">
                {{data?.backend?.name}}
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('前端请求路径')"
              prop="path"
              v-if="!isDetail"
            >
            </bk-table-column>
            <bk-table-column
              :label="t('文档')"
              prop="docs"
              width="100"
              v-if="!isDetail"
            >
            </bk-table-column>
            <bk-table-column
              :label="t('标签')"
              prop="labels"
              v-if="!isDetail"
            >
              <template #default="{ data }">
                <bk-tag v-for="item in data?.labels" :key="item.id">{{ item.name }}</bk-tag>
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('更新时间')"
              prop="updated_time"
              v-if="!isDetail"
            >
            </bk-table-column>
            <bk-table-column
              :label="t('操作')"
              width="140"
              v-if="!isDetail"
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
      </div>
      <div class="flex-1 right-wraper ml20" v-if="isDetail">
        <bk-tab
          v-model:active="active"
          type="card-tab"
          @change="handleTabChange"
        >
          <bk-tab-panel
            v-for="item in panels"
            :key="item.name"
            :name="item.name"
            :label="item.label"
            render-directive="if"
          >
            <!-- <router-view
              :ref="item.name"
              :stage-id="stageData.id"
              :key="routeIndex"
              :version-id="stageData.resource_version.id"
            ></router-view> -->
            <bk-loading
              :opacity="1"
              :loading="isComponentLoading"
            >
              <!-- deleted-success 删除成功需要请求一次列表数据 更新详情 -->
              <component
                v-if="item.name === active && resourceId"
                :is="item.component"
                :resource-id="resourceId"
                :apigw-id="apigwId"
                ref="componentRef"
                @done="(v: boolean) => {
                  isComponentLoading = v
                }"
                @deleted-success="getList"
              />
            </bk-loading>
          </bk-tab-panel>
        </bk-tab>
      </div>
    </div>
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
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { useQueryList, useSelection } from '@/hooks';
import { getResourceListData, deleteResources, batchDeleteResources, batchEditResources } from '@/http';
import { Message } from 'bkui-vue';
import agDropdown from '@/components/ag-dropdown.vue';
import Detail from './detail.vue';
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

// 是否批量
const isBatchDelete = ref(false);

// 是否展示详情
const isDetail = ref(false);

// 当前点击资源ID
const resourceId = ref(0);

const active = ref('resourceInfo');

const isComponentLoading = ref(true);

const dialogData = ref<IDialog>({
  isShow: false,
  title: t(''),
  loading: false,
});

const batchEditData = ref({
  isPublic: true,
  allowApply: true,
});

// tab 选项卡
const panels = [
  { name: 'resourceDetail', label: t('资源配置'), component: Detail },
  { name: 'pluginManage', label: '插件管理', routeName: 'apigwStagePluginManage' },
  { name: 'resourceDoc', label: '资源文档', routeName: 'apigwStageVariableManage' },
];

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

// 选项卡切换
const handleTabChange = (name: string) => {
  const curPanel = panels.find(item => item.name === name);
  router.push({
    name: curPanel.routeName,
    params: {
      id: props.apigwId,
    },
  });
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

// 展示右边内容
const handleShowInfo = (id: number) => {
  resourceId.value = id;
  if (isDetail.value) {
    isComponentLoading.value = true;
    active.value = 'resourceInfo';
  } else {
    isDetail.value = true;
  }
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
    const params = {
      ids,
      is_public: batchEditData.value.isPublic,
      allow_apply_permission: batchEditData.value.allowApply,
    };
    await batchEditResources(props.apigwId, params);
  }
  dialogData.value.isShow = false;
  Message({
    message: t(`${isBatchDelete.value ? '删除' : '编辑'}成功`),
    theme: 'success',
  });
  getList();
  resetSelections();
};

// 监听table数据 如果未点击某行 则设置第一行的id为资源id
watch(
  () => tableData.value,
  (v: any) => {
    if (v.length) {
      console.log(111, v);
      resourceId.value = v[0].id;
    }
  },
  { immediate: true },
);
</script>
<style lang="scss" scoped>
.resource-container{
  height: 100%;
  .operate{
    &-input{
      width: 450px;
    }
  }
  .dialog-content{
    // max-height: 280px;
  }
  .resource-content{
    height: calc(100% - 90px);
    min-height: 600px;
    .left-wraper{
      width: 370px;
      background: #fff;
      transition: all .15s;
    }

    .right-wraper{
      background: #fff;
      transition: all .15s;
    }
  }
}
</style>
