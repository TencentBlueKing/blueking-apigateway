<template>
  <ResourceSettingTopBar
    :latest="versionConfigs.needNewVersion"
    :current-source="curResource"
    :is-detail="isDetail"
    :show-new-tips="!!tableData?.length"
  />
  <div
    :class="['resource-container',
             'page-wrapper-padding',
             isDragging ? 'dragging' : '',
             isDetail && !isShowLeft ? 'welt' : '']"
    id="resourceId">
    <div
      class="resource-container-lf"
      id="resourceLf"
      :style="{ minWidth: isDetail ? isShowLeft ? '320px' : '0' : '100%' }">
      <bk-alert
        v-show="versionConfigs.needNewVersion && !isDetail"
        theme="warning"
        class="mb20"
      >
        <template #title>
          {{ versionConfigs.versionMessage }}
          <bk-button
            text
            theme="primary"
            v-if="versionConfigs.needNewVersion"
            @click="handleCreateResourceVersion">
            {{ t('立即生成版本') }}
          </bk-button>
        </template>
      </bk-alert>
      <div class="operate flex-row justify-content-between mb15">
        <div class="flex-1 flex-row align-items-center">
          <div class="mr8">
            <bk-button
              style="width: 142px;"
              v-show="isShowLeft"
              theme="primary"
              :class="{ 'super-big-button': isDetail }"
              @click="handleCreateResource"
            >
              {{ t('新建') }}
            </bk-button>
          </div>
          <ag-dropdown
            v-show="isShowLeft"
            :text="t('批量')"
            :dropdown-list="batchDropData"
            @on-change="handleBatchOperate"
            :is-disabled="!selections.length"></ag-dropdown>
          <ag-dropdown
            :text="t('更多')"
            v-show="isDetail && isShowLeft">
            <div class="nest-dropdown">
              <ag-dropdown
                :text="t('导入')"
                :is-text="true"
                placement="right-start"
                :dropdown-list="importDropData"
                @on-change="handleImport"></ag-dropdown>
              <ag-dropdown
                :text="t('导出')"
                :is-text="true"
                placement="right-start"
                :dropdown-list="exportDropData"
                @on-change="handleExport"></ag-dropdown>
            </div>
          </ag-dropdown>
          <section class="flex-row align-items-center" v-show="!isDetail">
            <ag-dropdown
              :text="t('导入')"
              :dropdown-list="importDropData"
              @on-change="handleImport"></ag-dropdown>
            <ag-dropdown
              :text="t('导出')"
              :dropdown-list="exportDropData"
              @on-change="handleExport"></ag-dropdown>
            <!-- <div class="mr8">
              <bk-button @click="handleCreateResourceVersion" :disabled="!versionConfigs.needNewVersion">
                {{ t('生成版本') }}
              </bk-button>
            </div> -->
          </section>
        </div>
        <div class="flex-1 flex-row justify-content-end">
          <bk-search-select
            v-show="!isDetail"
            v-model="searchValue"
            :data="searchData"
            unique-select
            style="width: 450px; background:#fff"
            :placeholder="t('请输入资源名称或选择条件搜索, 按Enter确认')"
            :value-split-code="'+'"
          />
        </div>
      </div>
      <bk-search-select
        v-show="isDetail && isShowLeft"
        v-model="searchValue"
        :data="searchData"
        unique-select
        style="background:#fff"
        class="mb15"
        :placeholder="t('请输入资源名称或选择条件搜索, 按Enter确认')"
        :value-split-code="'+'"
      />

      <div class="left-wraper" v-show="isShowLeft">
        <bk-loading :loading="isLoading">
          <bk-table
            class="table-layout"
            :data="tableData"
            remote-pagination
            :pagination="pagination"
            :key="tableDataKey"
            :show-overflow-tooltip="true"
            @page-limit-change="handlePageSizeChange"
            @page-value-change="handlePageChange"
            @select-all="handleSelecAllChange"
            @selection-change="handleSelectionChange"
            @row-mouse-enter="handleMouseEnter"
            @row-mouse-leave="handleMouseLeave"
            @column-sort="handleSortChange"
            :row-class="handleRowClass"
            border="outer"
            :settings="settings">
            <bk-table-column width="80" type="selection" align="center" fixed />
            <bk-table-column :label="t('资源名称')" width="160" prop="name" fixed>
              <template #default="{ row }">
                <div class="resource-name">
                  <div
                    v-bk-tooltips="{ content: row?.name, placement: 'right', delay: 300, }"
                    :class="['name', { 'name-updated': row?.has_updated }]"
                    @click="handleShowInfo(row.id)">
                    {{row?.name}}
                  </div>
                  <div
                    v-if="row?.has_updated"
                    v-bk-tooltips="{ content: '资源已更新', placement: 'right', delay: 300, }"
                    class="dot warning"
                  />
                </div>
              </template>
            </bk-table-column>
            <bk-table-column
              width="130"
              :label="t('后端服务')"
              prop="backend_name">
              <template #default="{ row }">
                {{row?.backend?.name}}
              </template>
            </bk-table-column>
            <bk-table-column
              prop="method"
              :label="t('前端请求方法')"
              :show-overflow-tooltip="false"
              :filter="{
                list: customMethodsList,
                checked: chooseMethod,
                filterFn: handleMethodFilter,
                btnSave: false,
              }"
              width="130">
              <template #default="{ row }">
                <bk-tag :theme="methodsEnum[row?.method]">{{ row?.method }}</bk-tag>
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('前端请求路径')"
              prop="path">
            </bk-table-column>
            <bk-table-column
              :label="t('插件数')"
              width="40"
              prop="plugin_count">
              <template #default="{ row }">
                <div class="plugin-num" @click="handleShowInfo(row.id, 'pluginManage')">
                  {{row?.plugin_count}}
                </div>
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('文档')"
              width="80"
              prop="docs">
              <template #default="{ row }">
                <section v-if="row?.docs?.length" @click="handleShowDoc(row)">
                  <span class="document-info">
                    <i class="bk-icon apigateway-icon icon-ag-document"></i>
                    {{ $t('详情') }}
                  </span>
                </section>
                <section v-else>
                  <span v-show="!row?.isDoc">--</span>
                  <i
                    class="bk-icon apigateway-icon icon-ag-plus plus-class"
                    v-bk-tooltips="t('添加文档')"
                    v-show="row?.isDoc"
                    @click="handleShowDoc(row)"></i>
                </section>
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('标签')"
              :show-overflow-tooltip="false"
              prop="labels"
              :filter="{
                list: labelsList,
                checked: chooseLabels,
                filterFn: handleMethodFilter,
                btnSave: false,
              }"
              min-width="180"
            >
              <template #default="{ row }">
                <span class="text-warp" v-if="!row?.isEditLabel" @click="handleEditLabel(row)">
                  <span
                    v-if="row?.labels?.length"
                    v-bk-tooltips="{ content: tipsContent(row?.labelText), theme: 'light', placement: 'left' }">
                    <template v-for="(item, index) in row?.labels" :key="item.id">
                      <span style="margin-left: 4px;" v-if="index < row.tagOrder">
                        <bk-tag @click="handleEditLabel(row)">
                          {{ item.name }}
                        </bk-tag>
                      </span>
                    </template>
                    <bk-tag
                      v-if="row.labels.length > row.tagOrder"
                      @click="handleEditLabel(row)"
                      class="tag-cls">
                      +{{ row.labels.length - row.tagOrder }}
                    </bk-tag>
                  </span>
                  <span v-else>--</span>
                  <i
                    v-show="row?.isDoc"
                    @click="handleEditLabel(row)"
                    class="icon apigateway-icon icon-ag-edit-small edit-icon"></i>
                </span>
                <section ref="selectCheckBoxParentRef" v-else>
                  <SelectCheckBox
                    :cur-select-label-ids="curLabelIds"
                    :resource-id="resourceId"
                    :labels-data="labelsData"
                    :width="selectCheckBoxParentRef?.offsetWidth"
                    force-focus
                    @close="(newLabelData) => {
                      handleCloseSelect(row, newLabelData)
                    }"
                    @update-success="handleUpdateLabelSuccess"
                    @label-add-success="getLabelsData"></SelectCheckBox>
                </section>
              </template>
            </bk-table-column>
            <bk-table-column
              :label="t('更新时间')"
              prop="updated_time"
              :sort="true">
            </bk-table-column>
            <bk-table-column
              :label="t('操作')"
              width="140"
              fixed="right"
              prop="act">
              <template #default="{ data }">
                <bk-button
                  text
                  theme="primary"
                  @click="handleEditResource(data.id, 'edit')">
                  {{ t('编辑') }}
                </bk-button>

                <bk-button
                  text
                  theme="primary"
                  class="pl10 pr10"
                  @click="handleEditResource(data.id, 'clone')">
                  {{ t('克隆') }}
                </bk-button>

                <bk-pop-confirm
                  :title="t('确认删除资源{resourceName}？', { resourceName: data?.name || '' })"
                  content="删除操作无法撤回，请谨慎操作！"
                  width="288"
                  trigger="click"
                  @confirm="handleDeleteResource(data.id)">
                  <bk-button
                    text
                    theme="primary">
                    {{ t('删除') }}
                  </bk-button>
                </bk-pop-confirm>
              </template>
            </bk-table-column>
            <template #empty>
              <TableEmpty
                :keyword="tableEmptyConf.keyword"
                :abnormal="tableEmptyConf.isAbnormal"
                @reacquire="getSearchResourceList"
                @clear-filter="handleClearFilterKey"
              />
            </template>
          </bk-table>
        </bk-loading>
      </div>

      <div
        :class="['toggle-button', 'toggle-button-lf', !isDetail ? 'active' : '']"
        v-show="isShowLeft"
        @click="handleToggleLf"
        :style="{ right: !isDetail ? '-24px' : '-22px' }">
        <i class="icon apigateway-icon icon-ag-ag-arrow-left"></i>
      </div>
    </div>

    <div class="demarcation-button" id="resourceLine" draggable="true" v-show="isDetail && isShowLeft">
      <span>......</span>
    </div>

    <div
      :class="['resource-container-rg', 'flex-1', isDragging ? 'dragging' : '']"
      id="resourceRg"
      v-show="isDetail">
      <div
        :class="['toggle-button', 'toggle-button-rg', !isShowLeft ? 'active' : '']"
        @click="handleToggleRg">
        <i class="icon apigateway-icon icon-ag-ag-arrow-left"></i>
      </div>
      <div class="right-wraper">
        <bk-tab
          v-model:active="active"
          type="card-tab"
          class="resource-tab-panel">
          <bk-tab-panel
            v-for="item in panels"
            :key="item.name"
            :name="item.name"
            :label="item.label"
            render-directive="if">
            <bk-loading :opacity="1" :loading="isComponentLoading">
              <!-- deleted-success 删除成功需要请求一次列表数据 更新详情 -->
              <component
                v-if="item.name === active && resourceId"
                :is="item.component"
                :resource-id="resourceId"
                :cur-resource="curResource"
                :apigw-id="apigwId"
                height="calc(100vh - 348px)"
                doc-root-class="doc-tab"
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
      <span class="resource-number">
        {{
          exportParams.export_type === 'all'
            ? t('已选择全部资源')
            : t('已选择{num}个资源', { num: selections.length })
        }}
      </span>
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
    <ResourceDocSideSlider
      v-model="docSliderConf.isShowDocSide"
      :resource="curResource"
      :title="docSliderConf.title"
      @fetch="handleSuccess"
      @on-update="handleUpdateTitle"
    ></ResourceDocSideSlider>
    <!-- 生成版本 -->
    <version-sideslider ref="versionSidesliderRef" @done="mitt.emit('on-update-plugin');" />
  </div>
</template>
<script setup lang="ts">
import { reactive, ref, watch, onMounted, onBeforeMount, shallowRef, h, computed, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter, useRoute } from 'vue-router';
import { cloneDeep, differenceBy } from 'lodash';
import { Message } from 'bkui-vue';

import { useQueryList, useSelection } from '@/hooks';
import {
  getResourceListData, deleteResources,
  batchDeleteResources, batchEditResources,
  exportResources, exportDocs, checkNeedNewVersion,
  getGatewayLabels,
} from '@/http';
import Detail from './detail.vue';
import VersionSideslider from './comps/version-sideslider.vue';
import SelectCheckBox from './comps/select-check-box.vue';
import AgDropdown from '@/components/ag-dropdown.vue';
import PluginManage from '@/views/components/plugin-manage/index.vue';
import ResourcesDoc from '@/views/components/resources-doc/index.vue';
import TableEmpty from '@/components/table-empty.vue';
// import RenderCustomColumn from '@/components/custom-table-header-filter';
import ResourceSettingTopBar from '@/components/resource-setting-top-bar.vue';
import mitt from '@/common/event-bus';
import { IDialog, IDropList, MethodsEnum } from '@/types';
import { is24HoursAgo } from '@/common/util';
import {  useCommon, useResourceVersion } from '@/store';
import ResourceDocSideSlider from '@/views/components/resource-doc-slider/index.vue';

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
  resource_filter_condition?: any
}

interface IexportDialog extends IDialog {
  exportFileDocType: string
}

type TableEmptyConfType = {
  keyword: string
  isAbnormal: boolean
};

const leftWidth = ref('320px');
const methodsEnum: any = ref(MethodsEnum);
const common = useCommon();
const resourceVersionStore = useResourceVersion();
const { t } = useI18n();
// 批量下拉的item
const batchDropData = ref([{ value: 'edit', label: t('编辑资源') }, { value: 'delete', label: t('删除资源') }]);
// 导入下拉
const importDropData = ref([{ value: 'config', label: t('资源配置') }, { value: 'doc', label: t('资源文档') }]);
interface ApigwIDropList extends IDropList {
  tooltips?: string;
}
// 导出下拉
const exportDropData = ref<ApigwIDropList[]>([
  { value: 'all', label: t('全部资源') },
  { value: 'filtered', label: t('已筛选资源'), disabled: false, tooltips: t('请先筛选资源') },
  { value: 'selected', label: t('已选资源'), disabled: false, tooltips: t('请先勾选资源') }]);

const route = useRoute();
const router = useRouter();
const chooseMethod = ref<string[]>([]);
const filterData = ref<any>({ keyword: '', order_by: '' });
const chooseLabels = ref<string[]>([]);
const tableEmptyConf = ref<TableEmptyConfType>({
  keyword: '',
  isAbnormal: false,
});

// ref
const versionSidesliderRef = ref(null);
const selectCheckBoxParentRef = ref(null);
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

const methodsTypeList = ref(common.methodList);

const searchValue = ref([]);
const searchData = shallowRef([
  // {
  //   name: t('模糊查询'),
  //   id: 'keyword',
  //   placeholder: t('请输入资源名称，前端请求路径'),
  // },
  {
    name: t('资源名称'),
    id: 'name',
    placeholder: t('请输入资源名称'),
  },
  {
    name: t('前端请求路径'),
    id: 'path',
    placeholder: t('请输入前端请求路径'),
  },
  {
    name: t('前端请求方法'),
    id: 'method',
    placeholder: t('请选择前端请求方法'),
    children: methodsTypeList.value,
    multiple: true,
  },
  {
    name: t('后端服务'),
    id: 'backend_name',
    placeholder: t('请输入后端服务'),
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
  { name: 'pluginManage', label: t('插件管理'), component: PluginManage },
  { name: 'resourcesDoc', label: t('资源文档'), component: ResourcesDoc },
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

// const customMethodsList = shallowRef(common.methodList);
const customMethodsList = computed(() => {
  if (!common.methodList?.length) {
    return [];
  }
  return common.methodList?.map((item: any) => {
    return {
      text: item.name,
      value: item.id,
    };
  });
});

const handleMethodFilter = () => true;

// const curSelectMethod = ref('ALL');

// const tableKey =  ref(-1);
const tableDataKey = ref(-1);

// const renderMethodsLabel = () => {
//   return h('div', { class: 'resource-setting-custom-label' }, [
//     h(
//       RenderCustomColumn,
//       {
//         key: tableKey.value,
//         hasAll: true,
//         columnLabel: t('前端请求方法'),
//         selectValue: curSelectMethod.value,
//         list: customMethodsList.value,
//         onSelected: (value: Record<string, string>) => {
//           handleSelectMethod(value);
//         },
//       },
//     ),
//   ]);
// };

// const handleSelectMethod = (payload: Record<string, string>) => {
//   const { id, name } = payload;
//   filterData.value.method = payload.id;
//   const hasMethodData = searchValue.value.find((item: Record<string, any>) => ['method'].includes(item.id));
//   if (hasMethodData) {
//     hasMethodData.values = [{
//       id,
//       name,
//     }];
//   } else {
//     searchValue.value.push({
//       id: 'method',
//       name: t('前端请求方法'),
//       values: [{
//         id,
//         name,
//       }],
//     });
//   }
//   if (['ALL'].includes(payload.id)) {
//     delete filterData.value.method;
//     searchValue.value = searchValue.value.filter((item: Record<string, any>) => !['method'].includes(item.id));
//   }
// };

const labelsList = computed(() => {
  if (!labelsData?.value.length) {
    return [];
  }
  tableDataKey.value = +new Date();
  return labelsData.value?.map((item: any) => {
    return {
      text: item.name,
      value: item.name,
    };
  });
});

// 计算当前视口高度下能展示多少表格行
const calcMaxTableLimit = (lineHeight = 42, heightTaken = 347) => {
  const viewportHeight = window.innerHeight;
  const heightToUse = viewportHeight - heightTaken;
  const limit = Math.floor(heightToUse / lineHeight);
  return limit > 0 ? limit : 1;
};

// 当前视口高度能展示最多多少条表格数据
const maxTableLimit = calcMaxTableLimit();

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList(getResourceListData, filterData, 0, false, {
  limitList: [maxTableLimit, 10, 20, 50, 100],
  limit: maxTableLimit,
});

// checkbox hooks
const {
  selections,
  handleSelectionChange,
  handleSelecAllChange,
  resetSelections,
} = useSelection();

const init = () => {
  handleShowVersion();
  getLabelsData();
};

const getSearchResourceList = async () => {
  refreshTableData();
};

const refreshTableData = () => {
  getList();
  updateTableEmptyConfig();
};

const handleClearFilterKey = () => {
  filterData.value = cloneDeep({ keyword: '', order_by: '' });
  searchValue.value = [];
  chooseMethod.value = [];
  chooseLabels.value = [];
};

const updateTableEmptyConfig = () => {
  tableEmptyConf.value.isAbnormal = pagination.value.abnormal;
  if ((searchValue.value.length || chooseMethod.value?.length || chooseLabels.value?.length)
  && !tableData.value.length) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (searchValue.value.length || chooseMethod.value?.length || chooseLabels.value?.length) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
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
  resourceVersionStore.setPageStatus({
    isDetail: false,
    isShowLeft: true,
  });
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
    width: 'auto',
  });
  handleSuccess();
};

const handleToggleLf = () => {
  if (isDetail.value) {
    isShowLeft.value = false;
  } else {
    isDetail.value = true;
    document.getElementById('resourceLf').style.width = leftWidth.value;
  }
};

const handleToggleRg = () => {
  if (isShowLeft.value) {
    isDetail.value = false;
    handleShowList();
  } else {
    isShowLeft.value = true;
  }
};

const isDragging = ref<boolean>(false);
const dragTwoColDiv = (contentId: string, leftBoxId: string, resizeId: string/* , rightBoxId: string */) => {
  const resize: any = document.getElementById(resizeId);
  const leftBox = document.getElementById(leftBoxId);
  // const rightBox = document.getElementById(rightBoxId);
  const box = document.getElementById(contentId);

  resize.onmousedown = function (e: any) {
    const startX = e.clientX;
    resize.left = resize.offsetLeft;
    isDragging.value = true;
    document.onmousemove = function (e) {
      const endX = e.clientX;
      let moveLen = resize.left + (endX - startX);
      const maxT = box.clientWidth - resize.offsetWidth;
      if (moveLen < 215) {
        moveLen = 0;
        isShowLeft.value = false;
        document.onmouseup(e);
      };
      if (moveLen > maxT - 770) {
        moveLen = maxT;
        handleShowList();
        document.onmouseup(e);
      };
      resize.style.left = moveLen;
      leftBox.style.width = `${moveLen}px`;
      // rightBox.style.width = `${box.clientWidth - moveLen - 5}px`;
      // rightBox.style.width = `calc(100% - ${moveLen + 21})px`;
    };
    document.onmouseup = function () {
      document.onmousemove = null;
      document.onmouseup = null;
      isDragging.value = false;
      resize.releaseCapture?.();
    };
    resize.setCapture?.();
    return false;
  };
};

const handleSortChange = ({ column, type }: Record<string, any>) => {
  const typeMap: Record<string, Function> = {
    asc: () => {
      filterData.value.order_by = column.field;
    },
    desc: () => {
      filterData.value.order_by = `-${column.field}`;
    },
    null: () => {
      delete filterData.value.order_by;
    },
  };
  return typeMap[type]();
};

// 展示右边内容
const handleShowInfo = (id: number, curActive = 'resourceInfo') => {
  resourceId.value = id;
  // curResource.value = tableData.value.find((e: any) => e.id === id);
  tableData.value?.forEach((item: any) => {
    if (item.id === id) {
      curResource.value = item;
      item.highlight = true;
    } else {
      item.highlight = false;
    }
  });

  if (isDetail.value) {
    isComponentLoading.value = true;
    active.value = curActive;
  } else {
    pagination.value.small = true;
    isDetail.value = true;
    document.getElementById('resourceLf').style.width = leftWidth.value;
    active.value = curActive;
  }
};

// 显示列表
const handleShowList = () => {
  isDetail.value = false;
  isShowLeft.value = true;
  pagination.value.small = false;
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
  switch (value) {
    case 'selected':
      exportParams.resource_ids = selections.value.map(e => e.id);
      exportParams.resource_filter_condition = undefined;
      break;
    case 'filtered':
      exportParams.resource_filter_condition = filterData.value;
      exportParams.resource_ids = undefined;
      break;
    case 'all':
      exportParams.resource_filter_condition = undefined;
      exportParams.resource_ids = undefined;
      break;
  }
  exportParams.export_type = value;
  exportDialogConfig.exportFileDocType = 'resource';
  exportDialogConfig.isShow = true;
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
        width: 'auto',
      });
    }
    exportDialogConfig.isShow = false;
  } catch ({ error }: any) {
    Message({
      message: error.message,
      theme: 'error',
      width: 'auto',
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
    width: 'auto',
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
    versionConfigs.versionMessage = error?.msg;
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
const handleCreateResourceVersion = async () => {
  versionSidesliderRef.value.showReleaseSideslider();
};

// 获取标签数据
const getLabelsData = async () => {
  const res = await getGatewayLabels(props.apigwId);
  res.forEach((e: any) => e.isEdited = false);
  labelsData.value = res;
};

// 未做变更关闭select下拉
const handleCloseSelect = (row: any, newLabelData: any = []) => {
  tableData.value.forEach((item) => {
    item.isEditLabel = false;
  });
  // 接收新的标签数据，检查标签的 name 是否有变化，有则重新获取列表数据
  // 用于修复标签更改名称后，SelectCheckBox 组件的 update-success 不能触发，列表中的标签名没有相应更新的 bug
  if (newLabelData.length > 0) {
    const diff = differenceBy(row.labels, newLabelData, 'name');
    if (diff.length > 0) {
      getList();
      init();
    }
  }
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

const handleRowClass = (v: any) => {
  const ret = [];
  if (!v.is24HoursAgo) {
    ret.push('row-cls-in-24hours');
  }
  if (v.highlight) {
    ret.push('row-cls-highlight');
  }
  return ret.join(' ');
};

const tipsContent = (data: any[]) => {
  return h('div', {}, [
    data.map((item: string) => h('div', { style: 'display: flex; align-items: center', class: 'mt5 tips-cls' }, [item])),
  ]);
};

const settings = {
  trigger: 'click',
  fields: [
    { name: t('资源名称'), field: 'name', disabled: true },
    { name: t('后端服务'), field: 'backend_name' },
    { name: t('前端请求方法'), field: 'method' },
    { name: t('前端请求路径'), field: 'path' },
    { name: t('插件数'), field: 'plugin_count' },
    { name: t('文档'), field: 'docs' },
    { name: t('标签'), field: 'labels' },
    { name: t('更新时间'), field: 'updated_time' },
    { name: t('操作'), field: 'act', disabled: true },
  ],
  checked: ['name', 'backend_name', 'method', 'path', 'plugin_count', 'docs', 'labels', 'updated_time', 'act'],
};

watch(
  () => isDetail.value,
  (v) => {
    if (!v) {
      tableData.value?.forEach((item: any) => {
        item.highlight = false;
      });
    }
  },
);

watch(
  () => isShowLeft.value,
  (v) => {
    const el = document.getElementById('resourceLf');
    if (!v) {
      el.style.width = '0px';
    } else {
      el.style.width = leftWidth.value;
    }
  },
);

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
      item.tagOrder = 1;
      item.labelText = item.labels?.map((label: any) => {
        return label.name;
      });
      item.isEditLabel = false;
    });

    updateTableEmptyConfig();
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
    filterData.value = {
      order_by: filterData.value.order_by,
      keyword: '',
    };
    if (!filterData.value.order_by) {
      delete filterData.value.order_by;
    }
    if (v.length) {
      v.forEach((e: any) => {
        if (e.id === e.name) {
          filterData.value.keyword = e.name;
        } else {
          if (e.id === 'method') {
            filterData.value[e.id] = e.values?.map((item: any) => item.id)?.join(',');
          } else {
            filterData.value[e.id] = e.values[0].id;
          }
        }
      });
    }
    exportDropData.value.forEach((e: IDropList) => {
      // 已选资源
      if (e.value === 'filtered') {
        e.disabled = !v.length;
      }
    });
    // curSelectMethod.value = filterData.value.method || 'ALL';
    // tableKey.value = +new Date();
    nextTick(() => {
      const choose = chooseMethod.value?.sort((a: any, b: any) => (a - b));
      const filter = filterData.value?.method?.split(',')?.sort((a: any, b: any) => (a - b));

      if (filter?.length && (choose?.join(',') !== filter?.join(','))) { // 值有变化时，同步给表头筛选
        chooseMethod.value = filterData.value?.method?.split(',');
        tableDataKey.value = +new Date();
      }

      if (!filter?.length && chooseMethod.value?.length) { // 清空筛选时，同步给表头筛选
        chooseMethod.value = [];
        tableDataKey.value = +new Date();
      }
    });

    updateTableEmptyConfig();
  },
  { immediate: true, deep: true },
);

watch(() => route, () => {
  if (route?.query?.backend_id) {
    const { backend_id } =  route?.query;
    filterData.value.backend_id = backend_id;
  }
}, { immediate: true, deep: true });

watch(
  () => [isDetail.value, isShowLeft.value],
  () => {
    resourceVersionStore.setPageStatus({
      isDetail: isDetail.value,
      isShowLeft: isShowLeft.value,
    });
  },
);

watch(
  () => chooseLabels.value,
  (v) => {
    if (!v?.length) { // 重置
      filterData.value.label_ids = undefined;
    } else { // 选择
      const ids: string[] = [];
      v?.forEach((name: string) => {
        const tagLabel = labelsData.value?.find((label: any) => label.name === name);
        if (tagLabel?.id) {
          ids?.push(tagLabel.id);
        }
      });
      filterData.value.label_ids = ids.join(',');
    }
  },
  { deep: true, immediate: true },
);

watch(
  () => chooseMethod.value,
  (v) => {
    if (!v?.length) { // 重置
      filterData.value.method = undefined;
      searchValue.value = searchValue.value.filter((item: Record<string, any>) => !['method'].includes(item.id));
    } else { // 选择
      filterData.value.method = v?.join(',');
      const hasMethodData = searchValue.value.find((item: Record<string, any>) => ['method'].includes(item.id));
      const method = v?.map((m: string) => {
        return { id: m, name: m };
      });
      if (hasMethodData) {
        hasMethodData.values = method;
      } else {
        searchValue.value.push({
          id: 'method',
          name: t('前端请求方法'),
          values: method,
        });
      }
    }
    getList();
  },
  { deep: true, immediate: true },
);

const recoverPageStatus = () => {
  const { isDetail: d, isShowLeft: l } = resourceVersionStore.getPageStatus;
  isDetail.value = d;
  isShowLeft.value = l;

  const el = document.getElementById('resourceLf');
  if (!l) {
    el.style.width = '0px';
  } else {
    el.style.width = leftWidth.value;
  }
};

onMounted(() => {
  init();
  dragTwoColDiv('resourceId', 'resourceLf', 'resourceLine'/* , 'resourceRg' */);
  // 监听其他组件是否触发了资源更新，获取最新的列表数据
  mitt.on('on-update-plugin', () => {
    pagination.value = Object.assign(pagination.value, { current: 0, limit: maxTableLimit });
    getList();
    handleShowVersion();
  });
  if (route.meta.pageStatus) {
    recoverPageStatus();
  }
});

onBeforeMount(() => {
  mitt.off('on-update-plugin');
});

</script>
<style lang="scss" scoped>
.resource-container{
  display: flex;
  align-items: flex-start;
  height: calc(100vh - 112px);
  .resource-container-lf,
  .resource-container-rg{
    position: relative;
  }
  .resource-container-rg {
    min-height: calc(100% + 40px);
    background: #fff;
    margin-top: -20px;
    margin-right: -24px;
    margin-bottom: -20px;
    &.dragging {
      &::before {
        content: ' ';
        position: absolute;
        z-index: 999;
        width: 2px;
        height: 100%;
        left: -1px;
        top: 0;
        background-color: #3a84ff;
      }
    }
  }
  .demarcation-button:hover + .resource-container-rg {
    &::before {
      content: ' ';
      position: absolute;
      z-index: 999;
      width: 2px;
      height: 100%;
      left: -1px;
      top: 0;
      background-color: #3a84ff;
    }
  }
  .demarcation-button {
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    cursor: col-resize;
    span {
      color: #63656E;
      transform: rotate(90deg);
      padding-bottom: 6px;
    }
  }
  .operate{
    &-input{
      width: 450px;
    }
  }
  .left-wraper{
    position: relative;
    background: #fff;

    .document-info{
      color: #3a84ff;
      font-size: 12px;
      cursor: pointer;
    }
    .plus-class{
      font-size: 14px;
      font-weight: bold;
      cursor: pointer;
      color: #979BA5;
      background: #EAEBF0;
      padding: 4px;
      &:hover {
        color: #3A84FF;
        background: #E1ECFF;
      }
    }

    .table-layout{
      :deep(.row-cls-in-24hours) {
        td {
          background: #f2fff4 !important;
        }
      }
      :deep(.row-cls-highlight) {
        td {
          background: #e1ecff !important;
        }
      }
      :deep(.bk-table-head) {
        scrollbar-color: transparent transparent;
      }
      :deep(.bk-table-body) {
        scrollbar-color: transparent transparent;
      }
      :deep(.resource-name) {
        display: flex;
        align-items: center;
        .name {
          color: #3a84ff;
          overflow: hidden;
          white-space: nowrap;
          text-overflow: ellipsis;
          cursor: pointer;
          &-updated {
            max-width: 112px;
          }
        }
        .dot {
          margin-left: 4px;
          cursor: pointer;
        }
      }
    }

    .text-warp {
      position: relative;
      cursor: pointer;
      .edit-icon {
        position: absolute;
        font-size: 24px;
        cursor: pointer;
        color: #3A84FF;
        top: -2px;
        // top: 8px;
        // right: -20px;
      }
      :deep(.bk-tag-text) {
        max-width: 80px;
      }
    }
    .tag-cls{
      cursor: pointer;
    }
  }

  .toggle-button{
    width: 16px;
    height: 28px;
    background: #FAFBFD;
    border: 1px solid #3A84FF;
    box-shadow: 0 2px 4px 0 #0000001a;
    border-radius: 4px 0 0 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #3A84FF;
    cursor: pointer;
    font-size: 12px;
    position: absolute;
    z-index: 99;
    transform: translateY(-50%);
    .icon {
      transition: transform .15s !important;
    }
    &:hover {
      background-color: #3a84ff;
      color: #fff;
    }
    &.active {
      background-color: #3a84ff;
      color: #fff;
    }
  }
  .toggle-button-lf {
    // right: -19px;
    top: -6px;
  }
  .toggle-button-rg {
    left: -1px;
    top: 0;
    transform: rotate(180deg) !important;
    border-radius: 4px 0 0 4px;
  }
}
.resource-number{
  color: #c4c6cc;
}

:deep(.bk-popover) {
  .bk-pop2-content {
    .bk-table-head-filter {
      .content-footer {
        display: none;
      }
    }
  }
}

.nest-dropdown {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.super-big-button {
  padding: 5px 58px;
}

.resource-tab-panel {
  :deep(.bk-tab-header-item) {
    padding: 0 24px !important;
  }
}

.resource-container.dragging {
  cursor: col-resize;
}
.welt {
  padding-left: 0px;
}
.ag-dot {
  width: 8px;
  height: 8px;
  display: inline-block;
  vertical-align: middle;
  border-radius: 50%;
  border: 1px solid #C4C6CC;
}

.tips-cls {
  background: #f0f1f5;
  padding: 3px 8px;
  border-radius: 2px;
  cursor: default;
  &:hover {
    background: #d7d9e1 !important;
  }
}
.doc-sides {
  :deep(.bk-modal-content) {
    max-height: calc(100vh - 52px);
    overflow: hidden;
  }
}
.plugin-num {
  color: #3a84ff;
  cursor: pointer;
}
</style>
<style lang="scss">
.content-footer {
  justify-content: flex-end;
  .btn-filter-save.disabled {
    display: none !important;
  }
}
</style>
