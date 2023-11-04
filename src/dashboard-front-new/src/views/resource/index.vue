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
          :dropdown-list="exportDropData"
          @on-change="handleExport"></ag-dropdown>
      </div>
      <div class="flex-1 flex-row justify-content-end">
        <bk-input class="ml10 mr10 operate-input" placeholder="请输入网关名" v-model="filterData.query"></bk-input>
      </div>
    </div>
    <div class="flex-row resource-content">
      <div class="left-wraper" :style="{ width: isDetail ? isShowLeft ? '370px' : '0' : '100%' }">
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
            @row-mouse-enter="handleMouseEnter"
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
              <template #default="{ data }">
                <bk-tag :theme="methodsEnum[data?.method]">{{ data?.method }}</bk-tag>
              </template>
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
              width="100"
              v-if="!isDetail"
            >
              <template #default="{ data }">
                <section v-if="data?.docs.length">{{ data?.docs }}</section>
                <section v-else></section>
              </template>
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
        <div class="toggle-button" v-if="isDetail" @click="isShowLeft = !isShowLeft">
          <i class="icon apigateway-icon icon-ag-ag-arrow-left" :class="[{ 'is-left': !isShowLeft }]"></i>
        </div>
      </div>
      <div class="flex-1 right-wraper ml20" v-if="isDetail">
        <bk-tab
          v-model:active="active"
          type="card-tab"
        >
          <template #setting>
            <div class="close-btn" @click="handleShowList">
              <i class="icon apigateway-icon icon-ag-icon-close"></i>
            </div>
          </template>
          <bk-tab-panel
            v-for="item in panels"
            :key="item.name"
            :name="item.name"
            :label="item.label"
            render-directive="if"
          >
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
                @done="(v: boolean | any) => {
                  isComponentLoading = !!v
                }"
                @deleted-success="getList"
              />
            </bk-loading>
          </bk-tab-panel>
        </bk-tab>
      </div>
    </div>
    <!-- 批量删除dialog -->
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
    <!-- 导出dialog -->
    <bk-dialog
      :is-show="exportDialogConfig.isShow"
      width="600"
      :title="exportDialogConfig.title"
      theme="primary"
      quick-close
      :is-loading="exportDialogConfig.loading"
      @confirm="handleExportDownload"
      @closed="exportDialogConfig.isShow = false">
      <span class="rosource-number">{{ t('选择全部资源') }}</span>
      <bk-form>
        <bk-form-item label="导出内容">
          <bk-radio-group v-model="exportDialogConfig.exportFileDocType">
            <bk-radio label="resource">{{ t('资源配置') }}</bk-radio>
            <bk-radio label="docs">{{ t('资源文档') }}</bk-radio>
          </bk-radio-group>
        </bk-form-item>

        <bk-form-item label="导出格式" v-if="exportDialogConfig.exportFileDocType === 'resource'">
          <bk-radio-group v-model="exportParams.file_type">
            <bk-radio class="mt5" label="yaml"> {{ $t('YAML格式') }} </bk-radio>
            <bk-radio label="json"> {{ $t('JSON格式') }} </bk-radio>
          </bk-radio-group>
        </bk-form-item>
        <bk-form-item label="导出格式" v-else>
          <bk-radio-group v-model="exportParams.file_type">
            <bk-radio class="mt5" label="zip"> {{ $t('Zip') }} </bk-radio>
            <bk-radio label="tgz"> {{ $t('Tgz') }} </bk-radio>
          </bk-radio-group>
        </bk-form-item>
      </bk-form>
    </bk-dialog>
  </div>
</template>
<script setup lang="ts">
import { reactive, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { useQueryList, useSelection } from '@/hooks';
import {
  getResourceListData, deleteResources,
  batchDeleteResources, batchEditResources,
  exportResources, exportDocs,
} from '@/http';
import { Message } from 'bkui-vue';
import agDropdown from '@/components/ag-dropdown.vue';
import Detail from './detail.vue';
import PluginManage from '@/views/components/plugin-manage/index.vue';
import { IDialog, IDropList, MethodsEnum } from '@/types';
const props = defineProps({
  apigwId: {
    type: Number,
    default: 0,
  },
});

// 导出参数interface
interface IexportParams {
  export_type: string
  query?: string
  method?: string
  label_name?: string
  file_type?: string
  resource_ids?: Array<number>
}

interface IexportDialog extends IDialog {
  exportFileDocType: string
}

const methodsEnum: any = ref(MethodsEnum);
const { t } = useI18n();
// 批量下拉的item
const batchDropData = ref([{ value: 'edit', label: '编辑资源' }, { value: 'delete', label: '删除资源' }]);
// 导入下拉
const importDropData = ref([{ value: 'config', label: '资源配置' }, { value: 'doc', label: '资源文档' }]);
// 导出下拉
const exportDropData = ref<IDropList[]>([
  { value: 'all', label: t('全部资源') },
  { value: 'filtered', label: t('已筛选资源'), disabled: false },
  { value: 'selected', label: t('已选资源'), disabled: false }]);

const router = useRouter();

const filterData = ref({ query: '' });

// 导出参数
const exportParams: IexportParams = reactive({
  export_type: '',
  file_type: 'yaml',
});

// 是否批量
const isBatchDelete = ref(false);

// 是否展示详情
const isDetail = ref(false);
// 是否展示左边列表
const isShowLeft = ref(true);

// 当前点击资源ID
const resourceId = ref(0);

const active = ref('resourceInfo');

const isComponentLoading = ref(true);

// 批量删除dialog
const dialogData: IDialog = reactive({
  isShow: false,
  title: t(''),
  loading: false,
});

// 导出dialog
const exportDialogConfig: IexportDialog = reactive({
  isShow: false,
  title: t('请选择导出的格式'),
  loading: false,
  exportFileDocType: 'resource',
});

const batchEditData = ref({
  isPublic: true,
  allowApply: true,
});

// tab 选项卡
const panels = [
  { name: 'resourceDetail', label: t('资源配置'), component: Detail },
  { name: 'pluginManage', label: '插件管理', component: PluginManage },
  { name: 'resourceDoc', label: '资源文档', component: PluginManage },
];

const columns = [
  {
    label: t('请求路径'),
    field: 'path',
  },
  {
    label: t('请求方法'),
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

// 展示右边内容
const handleShowInfo = (id: number) => {
  resourceId.value = id;
  console.log('isDetail', isDetail.value);
  if (isDetail.value) {
    isComponentLoading.value = true;
    active.value = 'resourceInfo';
  } else {
    isDetail.value = true;
  }
};

// 显示列表
const handleShowList = () => {
  isDetail.value = false;
  isShowLeft.value = true;
};

// 处理批量编辑或删除
const handleBatchOperate = async (data: IDropList) => {
  dialogData.isShow = true;
  // 批量删除
  if (data.value === 'delete') {
    isBatchDelete.value = true;
    dialogData.title = t(`确定要删除以下${selections.value.length}个资源`);
  } else {
    // 批量编辑
    isBatchDelete.value = false;
    dialogData.title = t(`批量编辑资源共${selections.value.length}个`);
  }
};

// 处理导出弹窗显示
const handleExport = async ({ value }: {value: string}) => {
  console.log('data', value);
  exportParams.export_type = value;
  exportDialogConfig.isShow = true;
  switch (value) {
    case 'selected':
      exportParams.resource_ids = selections.value.map(e => e.id);
      break;
    default:
      exportParams.export_type = value;
      exportDialogConfig.isShow = true;
      break;
  }
  exportParams.export_type = value;
};

// 导出下载
const handleExportDownload = async () => {
  const params = exportParams;
  const fetchMethod = exportDialogConfig.exportFileDocType === 'resource' ? exportResources : exportDocs;
  try {
    const res = await fetchMethod(props.apigwId, params);
    if (res.success) {
      Message({
        message: t('导出成功'),
        theme: 'success',
      });
    }
    exportDialogConfig.isShow = false;
  } catch ({ error }: any) {
    Message({
      message: error.message,
      theme: 'error',
    });
  }
};
// 批量编辑确认
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
    // 批量编辑
    await batchEditResources(props.apigwId, params);
  }
  dialogData.isShow = false;
  Message({
    message: t(`${isBatchDelete.value ? '删除' : '编辑'}成功`),
    theme: 'success',
  });
  getList();
  resetSelections();
};

// 鼠标进入
const handleMouseEnter = (e: any, row: any) => {
  console.log('row', row);
};

// 监听table数据 如果未点击某行 则设置第一行的id为资源id
watch(
  () => tableData.value,
  (v: any) => {
    if (v.length) {
      resourceId.value = v[0].id;
    }
  },
  { immediate: true },
);

// 监听导出弹窗
watch(
  () => exportDialogConfig,
  (v: IexportDialog) => {
    if (v.exportFileDocType === 'docs') {
      exportParams.file_type = 'zip';
    } else {
      exportParams.file_type = 'yaml';
    }
  },
  { deep: true },
);

// 选中的值
watch(
  () => selections.value,
  (v: number[]) => {
    exportDropData.value.forEach((e: IDropList) => {
      // 已选资源
      if (e.value === 'selected') {
        e.disabled = !v.length;
      }
    });
  },
  { immediate: true, deep: true },
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
      position: relative;
      background: #fff;
      transition: all .15s;
      .toggle-button{
        align-items: center;
        background: #dcdee5;
        border-bottom-right-radius: 6px;
        border-top-right-radius: 6px;
        color: #fff;
        cursor: pointer;
        display: flex;
        font-size: 16px;
        height: 64px;
        justify-content: center;
        position: absolute;
        right: -14px;
        top: 50%;
        transform: translateY(-50%);
        width: 14px;
        .icon {
          transition: transform .15s !important;
          &.is-left {
            transform: rotate(180deg) !important;
          }
        }
      }
    }

    .right-wraper{
      background: #fff;
      transition: all .15s;
      .close-btn{
        align-items: center;
        border-radius: 50%;
        color: #c4c6cc;
        cursor: pointer;
        display: flex;
        font-size: 32px;
        height: 26px;
        justify-content: center;
        position: absolute;
        right: 5px;
        top: 5px;
        width: 26px;
      }
    }
  }
}
.rosource-number{
  color: #c4c6cc;
}
</style>
