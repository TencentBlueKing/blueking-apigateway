<template>
  <div class="resource-container p20">
    <bk-alert
      v-if="versionConfigs.needNewVersion"
      theme="warning"
      :title="versionConfigs.versionMessage"
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
          @on-change="handleImport"></ag-dropdown>
        <ag-dropdown
          :text="t('导出')"
          :dropdown-list="exportDropData"
          @on-change="handleExport"></ag-dropdown>
        <div class="mr10">
          <bk-button
            @click="handleCreateResourceVersion"
          >
            {{ t('生成版本') }}
          </bk-button>
        </div>
      </div>
      <div class="flex-1 flex-row justify-content-end">
        <!-- <bk-input class="ml10 mr10 operate-input" placeholder="请输入网关名" v-model="filterData.query"></bk-input> -->
        <bk-search-select
          v-model="searchValue"
          :data="searchData"
          unique-select
          style="width: 450px"
          placeholder="请选择或输入"
          :value-split-code="'+'"
        />
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
            @select-all="handleSelecAllChange"
            @selection-change="handleSelectionChange"
            @row-mouse-enter="handleMouseEnter"
            @row-mouse-leave="handleMouseLeave"
            row-hover="auto"
            :row-class="is24HoursAgoClsFunc"
          >
            <bk-table-column
              width="80"
              type="selection"
              align="center"
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
              width="80"
              v-if="!isDetail"
            >
              <template #default="{ data }">
                <section v-if="data?.docs.length" @click="handleShowDoc(data)">
                  <span class="document-info">
                    <i class="bk-icon apigateway-icon icon-ag-document"></i>
                    {{ $t('详情') }}
                  </span>
                </section>
                <section v-else>
                  <span v-show="!data?.isDoc">--</span>
                  <i
                    class="bk-icon apigateway-icon icon-ag-plus plus-class"
                    v-bk-tooltips="t('添加文档')"
                    v-show="data?.isDoc"
                    @click="handleShowDoc(data)"></i>
                </section>
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('标签')"
              prop="labels"
              width="280"
              v-if="!isDetail"
            >
              <template #default="{ data }">
                <section class="text-warp" v-if="!data?.isEditLabel" @click="handleEditLabel(data)">
                  <section
                    v-if="data?.labels.length"
                    v-bk-tooltips="{ content: data?.labelText.join(';') }">
                    <span v-for="(item, index) in data?.labels" :key="item.id">
                      <bk-tag @click="handleEditLabel(data)" v-if="index < data.tagOrder">{{ item.name }}</bk-tag>
                    </span>
                    <bk-tag
                      v-if="data.labels.length > data.tagOrder"
                      class="tag-cls">
                      +{{ data.labels.length - data.tagOrder }}
                      <!-- ... -->
                    </bk-tag>
                  </section>
                  <section v-else>--</section>
                  <i
                    v-show="data?.isDoc"
                    @click="handleEditLabel(data)"
                    class="icon apigateway-icon icon-ag-edit-small edit-icon"></i>
                </section>
                <section v-else>
                  <SelectCheckBox
                    :cur-select-label-ids="curLabelIds"
                    :resource-id="resourceId"
                    :labels-data="labelsData"
                    @close="handleCloseSelect"
                    @update-success="handleUpdateLabelSuccess"
                    @label-add-success="getLabelsData"></SelectCheckBox>
                </section>
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
                  :title="t(`确认删除资源${data?.name}？`)"
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
                :cur-resource="curResource"
                :apigw-id="apigwId"
                height="calc(100vh - 348px)"
                ref="componentRef"
                @done="(v: boolean | any) => {
                  isComponentLoading = !!v
                }"
                @deleted-success="handleDeleteSuccess"
                @on-jump="(id: number | any) => {
                  handleShowInfo(id)
                }"
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

    <!-- 文档侧边栏 -->
    <bk-sideslider
      v-model:isShow="docSliderConf.isShowDocSide"
      quick-close
      :title="docSliderConf.title"
      width="780"
      ext-cls="doc-sideslider-cls">
      <template #default>
        <ResourcesDoc
          :cur-resource="curResource" @fetch="handleSuccess" @on-update="handleUpdateTitle"></ResourcesDoc>
      </template>
    </bk-sideslider>
    <!-- 生成版本 -->
    <version-sideslider ref="versionSidesliderRef" />
  </div>
</template>
<script setup lang="ts">
import { reactive, ref, watch, onMounted, shallowRef } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { useQueryList, useSelection } from '@/hooks';
import {
  getResourceListData, deleteResources,
  batchDeleteResources, batchEditResources,
  exportResources, exportDocs, checkNeedNewVersion,
  getGatewayLabels,
} from '@/http';
import { Message } from 'bkui-vue';
import Detail from './detail.vue';
import VersionSideslider from './comps/version-sideslider.vue';
import SelectCheckBox from './comps/select-check-box.vue';
import AgDropdown from '@/components/ag-dropdown.vue';
import PluginManage from '@/views/components/plugin-manage/index.vue';
import ResourcesDoc from '@/views/components/resources-doc/index.vue';
import { IDialog, IDropList, MethodsEnum } from '@/types';
import { cloneDeep } from 'lodash';
import { is24HoursAgo } from '@/common/util';
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

const filterData = ref<any>({ keyword: '' });

// ref
const versionSidesliderRef = ref(null);
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

// 当前点击的资源
const curResource: any = ref({});

const active = ref('resourceInfo');

const isComponentLoading = ref(true);

const searchValue = ref([]);
const searchData = shallowRef([
  {
    name: '模糊查询',
    id: 'keyword',
    placeholder: '请输入资源名称，前端请求路径',
  },
  {
    name: '资源名称',
    id: 'name',
    placeholder: '请输入资源名称',
  },
]);

// 标签数据
const labelsData = ref<any[]>([]);

// 当前点击行的选中的标签
const curLabelIds = ref<number[]>([]);

// 当前点击行的选中的标签备份
const curLabelIdsbackUp = ref<number[]>([]);

// 文档侧边栏数据
const docSliderConf: any = reactive({
  isShow: false,
  title: t('文档详情'),
  isLoading: false,
  isEdited: false,
  languages: 'zh',
});

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

// 是否需要alert信息栏
const versionConfigs = reactive({
  needNewVersion: false,
  versionMessage: '',
});

const batchEditData = ref({
  isPublic: true,
  allowApply: true,
});

// const showEdit = ref(false);
// const optionName = ref('');
// const inputRef = ref(null);

// tab 选项卡
const panels = [
  { name: 'resourceDetail', label: t('资源配置'), component: Detail },
  { name: 'pluginManage', label: '插件管理', component: PluginManage },
  { name: 'resourcesDoc', label: '资源文档', component: ResourcesDoc },
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
  handleSelecAllChange,
  resetSelections,
} = useSelection();

const init =  () => {
  handleShowVersion();
  getLabelsData();
};

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
  curResource.value = tableData.value.find((e: any) => e.id === id);
  console.log('curResource.value', curResource.value);
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
  exportParams.export_type = value;
  exportDialogConfig.exportFileDocType = 'resource';
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

// 处理导入跳转
const handleImport = (v: IDropList) => {
  const routerName = v.value === 'doc' ? 'apigwResourceImportDoc' : 'apigwResourceImport';
  router.push({
    name: routerName,
  });
};

// 鼠标进入
const handleMouseEnter = (e: any, row: any) => {
  setTimeout(() => {
    row.isDoc = true;
  }, 100);
};

// 鼠标离开
const handleMouseLeave = (e: any, row: any) => {
  setTimeout(() => {
    row.isDoc = false;
  }, 100);
};

// 展示文档
const handleShowDoc = (data: any, languages = 'zh') => {
  curResource.value = data;
  resourceId.value = data.id;   // 资源id
  docSliderConf.isShowDocSide = true;
  docSliderConf.title = `${t('文档详情')}【${data.name}】`;
  docSliderConf.languages = languages;
};

// 改变侧栏边title
const handleUpdateTitle = (type: string, isUpdate?: boolean) => {
  if (type === 'cancel') {
    docSliderConf.title = `${t('文档详情')}【${curResource.value.name}】`;
  } else {
    docSliderConf.title = `${isUpdate ? t('更新') : t('创建')}【${curResource.value.name}】`;
  }
};

// 处理保存成功 删除成功 重新请求列表
const handleSuccess = () => {
  getList();
  handleShowVersion();
};

// 获取资源是否需要发版本更新
const handleShowVersion = async () => {
  try {
    const res = await checkNeedNewVersion(props.apigwId);
    versionConfigs.needNewVersion = res.need_new_version;
    versionConfigs.versionMessage = res.msg;
  } catch (error: any) {
    versionConfigs.needNewVersion = false;
    versionConfigs.versionMessage = error.msg;
  }
};

// 处理标签点击
const handleEditLabel = (data: any) => {
  resourceId.value = data.id;
  tableData.value.forEach((item) => {
    item.isEditLabel = false;
  });
  curLabelIds.value = data.labels.map((item: any) => item.id);
  curLabelIdsbackUp.value = cloneDeep(curLabelIds.value);
  data.isEditLabel = true;
};

// 生成版本功能
const handleCreateResourceVersion = () => {
  versionSidesliderRef.value.showReleaseSideslider();
};

// 获取标签数据
const getLabelsData = async () => {
  const res = await getGatewayLabels(props.apigwId);
  res.forEach((e: any) => e.isEdited = false);
  labelsData.value = res;
};

// 未做变更关闭select下拉
const handleCloseSelect = () => {
  tableData.value.forEach((item) => {
    item.isEditLabel = false;
  });
};

// 更新成功
const handleUpdateLabelSuccess = () => {
  getList();
  init();
};

// 删除成功
const handleDeleteSuccess = () => {
  getList();
  handleShowList();
};

const is24HoursAgoClsFunc = (v: any) => {
  return v.is24HoursAgo ? '' : 'row-cls';
};

// 监听table数据 如果未点击某行 则设置第一行的id为资源id
watch(
  () => tableData.value,
  (v: any) => {
    if (v.length) {
      resourceId.value = v[0].id;
    }
    // 设置显示的tag值
    tableData.value.forEach((item: any) => {
      item.is24HoursAgo = is24HoursAgo(item.created_time);
      item.tagOrder = '3';
      item.labelText = item.labels.map((label: any) => {
        return label.name;
      });
      item.isEditLabel = false;
    });
    console.log('tableData.value', tableData.value);
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

// Search Select选中的值
watch(
  () => searchValue.value,
  (v: any[]) => {
    if (v.length) {
      v.forEach((e: any) => {
        if (e.id === e.name) {
          filterData.value.keyword = e.name;
        } else {
          filterData.value[e.id] = e.values[0].id;
        }
      });
    } else {
      getList();
    }
  },
);

onMounted(() => {
  init();
});
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
      .document-info{
        color: #3a84ff;
        font-size: 12px;
        cursor: pointer;
      }
      .plus-class{
        font-size: 12px;
        cursor: pointer;
        color: #979BA5;
        background: #EAEBF0;
        padding: 5px;
        &:hover {
          color: #3A84FF;
          background: #E1ECFF;
        }
      }

      .table-layout{
        :deep(.row-cls){
          td{
            background: #F2FFF4 !important;
          }
        }
      }

      .text-warp{
        position: relative;
        cursor: pointer;
        .edit-icon{
          position: absolute;
          font-size: 24px;
          cursor: pointer;
          color: #3A84FF;
          top: 8px;
          right: -20px;
        }
      }
      .tag-cls{
        cursor: pointer;
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
