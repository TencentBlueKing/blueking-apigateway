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
  <div v-show="!gatewayStore.isProgrammableGateway">
    <ResourceSettingTopBar
      :current-source="curResource"
      :is-detail="isDetail"
      :latest="versionConfigs.needNewVersion"
      :show-new-tips="!!tableData?.length"
    />
    <div
      id="resourceId"
      class="resource-container page-wrapper-padding pb-0!"
      :class="[
        isDragging ? 'dragging' : '',
        isDetail && !isShowLeft ? 'welt' : ''
      ]"
    >
      <div
        id="resourceLf"
        :style="{ minWidth: isDetail ? isShowLeft ? '320px' : '0' : '100%' }"
        class="resource-container-lf"
      >
        <BkAlert
          v-show="versionConfigs.needNewVersion && !isDetail"
          class="mb-20px"
          theme="warning"
        >
          <template #title>
            {{ versionConfigs.versionMessage }}
            <BkButton
              v-if="versionConfigs.needNewVersion"
              text
              theme="primary"
              @click="handleCreateResourceVersion"
            >
              {{ t('立即生成版本') }}
            </BkButton>
          </template>
        </BkAlert>
        <div class="operate">
          <div class="flex-grow-1 flex items-center">
            <div class="mr-8px">
              <BkButton
                v-show="isShowLeft && !showBatch"
                class="w-142px"
                :class="{ 'super-big-button': isDetail }"
                theme="primary"
                @click="handleCreateResource"
              >
                {{ t('新建') }}
              </BkButton>
            </div>
            <BkButton
              v-show="!showBatch"
              class="mr-8px"
              @click="handleShowBatch"
            >
              {{ t('批量操作') }}
            </BkButton>
            <div
              v-show="showBatch"
              class="batch-status"
            >
              <BkButton
                class="mr-8px"
                @click="() => handleBatchOperate('edit')"
              >
                {{ t('编辑资源') }}
              </BkButton>
              <BkButton
                class="mr-8px"
                @click="() => handleBatchOperate('delete')"
              >
                {{ t('删除资源') }}
              </BkButton>
            </div>
            <AgDropdown
              v-show="isDetail && isShowLeft"
              :text="t('更多')"
            >
              <div class="nest-dropdown">
                <AgDropdown
                  :dropdown-list="importDropData"
                  is-text
                  :text="t('导入')"
                  placement="right-start"
                  @on-change="handleImport"
                />
                <AgDropdown
                  :dropdown-list="exportDropData"
                  is-text
                  :text="t('导出')"
                  placement="right-start"
                  @on-change="handleExport"
                />
              </div>
            </AgDropdown>
            <section
              v-show="!isDetail"
              class="flex items-center"
            >
              <AgDropdown
                v-show="!showBatch"
                :dropdown-list="importDropData"
                :text="t('导入')"
                @on-change="handleImport"
              />
              <AgDropdown
                :dropdown-list="exportDropData"
                :text="t('导出')"
                @on-change="handleExport"
              />
            </section>

            <span
              v-show="!isDetail"
              class="split-line"
              :class="[showBatch ? 'batch' : '']"
            />

            <div
              v-show="!showBatch && !isDetail"
              class="operate-btn-wrapper"
            >
              <BkButton
                class="operate-btn mr-8px"
                @click="handleShowDiff"
              >
                <AgIcon name="chayiduibi-shixin" />
                {{ t('与历史版本对比') }}
              </BkButton>

              <BkBadge
                v-if="versionConfigs.needNewVersion"
                dot
                position="top-right"
                theme="danger"
              >
                <BkButton
                  v-bk-tooltips="{
                    content: t('资源有更新，可生成新版本'),
                  }"
                  class="operate-btn"
                  @click="handleCreateResourceVersion"
                >
                  <AgIcon name="version" />
                  {{ t('生成版本') }}
                </BkButton>
              </BkBadge>
              <BkButton
                v-else
                v-bk-tooltips="{
                  content: t('资源无更新，无需生成版本'),
                }"
                disabled
                class="operate-btn"
              >
                <AgIcon name="version" />
                {{ t('生成版本') }}
              </BkButton>
            </div>
            <BkButton
              v-show="showBatch"
              class="operate-btn"
              outline
              theme="primary"
              @click="handleOutBatch"
            >
              <AgIcon name="chahao" />
              {{ t('退出批量编辑') }}
            </BkButton>
          </div>
          <div class="search-select-wrap">
            <BkSearchSelect
              v-show="!isDetail"
              v-model="searchValue"
              :data="searchData"
              :placeholder="t('请输入资源名称或选择条件搜索, 按Enter确认')"
              :value-split-code="'+'"
              class="w-full! bg-#fff!"
              unique-select
            />
          </div>
        </div>
        <BkSearchSelect
          v-show="isDetail && isShowLeft"
          v-model="searchValue"
          :data="searchData"
          :placeholder="t('请输入资源名称或选择条件搜索, 按Enter确认')"
          :value-split-code="'+'"
          class="mb-15px bg-#fff"
          unique-select
        />

        <div
          v-show="isShowLeft"
          class="left-wrapper"
        >
          <BkLoading :loading="isLoading">
            <BkTable
              :data="tableData"
              :pagination="pagination"
              :row-class="handleRowClass"
              :settings="settings"
              :max-height="tableConfig.clientHeight"
              show-overflow-tooltip
              border="outer"
              class="table-layout"
              remote-pagination
              row-key="id"
              :size="settings.size"
              :row-height="settings.height"
              @page-limit-change="handlePageSizeChange"
              @page-value-change="handlePageChange"
              @select-all="handleSelectAllChange"
              @selection-change="handleSelectionChange"
              @row-mouse-enter="handleMouseEnter"
              @row-mouse-leave="handleMouseLeave"
              @column-sort="handleSortChange"
              @setting-change="handleSettingChange"
            >
              <BkTableColumn
                v-if="showBatch"
                align="center"
                fixed="left"
                type="selection"
                width="80"
              />
              <BkTableColumn
                :label="t('资源名称')"
                fixed="left"
                prop="name"
                width="170"
              >
                <template #default="{ row }">
                  <div class="resource-name">
                    <div
                      v-bk-tooltips="{ content: row?.name, placement: 'right', delay: 300, }"
                      class="name"
                      :class="[{ 'name-updated': row?.has_updated }]"
                      @click="handleShowInfo(row.id)"
                    >
                      {{ row?.name }}
                    </div>
                    <div
                      v-if="row?.has_updated"
                      v-bk-tooltips="{ content: '资源已更新', placement: 'right', delay: 300, }"
                      class="dot warning"
                    />
                  </div>
                </template>
              </BkTableColumn>
              <BkTableColumn
                :label="t('后端服务')"
                prop="backend_name"
                width="130"
              >
                <template #default="{ row }">
                  {{ row?.backend?.name }}
                </template>
              </BkTableColumn>
              <BkTableColumn
                :filter="{
                  list: customMethodsList,
                  checked: chooseMethod,
                  filterFn: handleMethodFilter,
                  btnSave: false,
                }"
                :label="t('前端请求方法')"
                :show-overflow-tooltip="false"
                prop="method"
                width="130"
              >
                <template #default="{ row }">
                  <BkTag :theme="METHOD_THEMES[row?.method]">
                    {{ row?.method }}
                  </BkTag>
                </template>
              </BkTableColumn>
              <BkTableColumn
                :label="t('前端请求路径')"
                prop="path"
              />
              <BkTableColumn
                :label="t('插件数')"
                prop="plugin_count"
                width="40"
              >
                <template #default="{ row }">
                  <div
                    class="plugin-num"
                    @click="() => handleShowInfo(row.id, 'pluginManage')"
                  >
                    {{ row?.plugin_count }}
                  </div>
                </template>
              </BkTableColumn>
              <BkTableColumn
                :label="t('文档')"
                prop="docs"
                width="80"
              >
                <template #default="{ row }">
                  <section
                    v-if="row?.docs?.length"
                    @click="() => handleShowDoc(row)"
                  >
                    <span class="document-info">
                      <AgIcon
                        name="document"
                        class="bk-icon"
                      />
                      {{ t('详情') }}
                    </span>
                  </section>
                  <section v-else>
                    <span v-show="!row?.isDoc">--</span>
                    <AgIcon
                      v-show="row?.isDoc"
                      v-bk-tooltips="t('添加文档')"
                      name="plus"
                      class="bk-icon plus-class"
                      @click="() => handleShowDoc(row)"
                    />
                  </section>
                </template>
              </BkTableColumn>
              <BkTableColumn
                :filter="{
                  list: labelsList,
                  checked: chooseLabels,
                  filterFn: handleMethodFilter,
                  btnSave: false,
                }"
                :label="t('标签')"
                :show-overflow-tooltip="false"
                min-width="180"
                prop="labels"
              >
                <template #default="{ row }">
                  <span
                    v-if="!row?.isEditLabel"
                    class="text-warp"
                    @click="() => handleEditLabel(row)"
                  >
                    <span
                      v-if="row?.labels?.length"
                      v-bk-tooltips="{ content: tipsContent(row?.labelText), theme: 'light', placement: 'left' }"
                    >
                      <template
                        v-for="(item, index) in row?.labels"
                        :key="item.id"
                      >
                        <span
                          v-if="index < row.tagOrder"
                          class="ml-4px"
                        >
                          <BkTag @click="() => handleEditLabel(row)">
                            {{ item.name }}
                          </BkTag>
                        </span>
                      </template>
                      <BkTag
                        v-if="row.labels.length > row.tagOrder"
                        class="tag-cls"
                        @click="() => handleEditLabel(row)"
                      >
                        +{{ row.labels.length - row.tagOrder }}
                      </BkTag>
                    </span>
                    <span v-else>--</span>
                    <AgIcon
                      v-show="row?.isDoc"
                      name="edit-small"
                      class="icon edit-icon"
                      size="24"
                      @click="() => handleEditLabel(row)"
                    />
                  </span>
                  <section
                    v-else
                    ref="selectCheckBoxParentRef"
                  >
                    <SelectCheckBox
                      :cur-select-label-ids="curLabelIds"
                      :labels-data="labelsData"
                      :resource-id="resourceId"
                      :width="selectCheckBoxParentRef?.offsetWidth"
                      force-focus
                      @close="(newLabelData) => {
                        handleCloseSelect(row, newLabelData)
                      }"
                      @update-success="handleUpdateLabelSuccess"
                      @label-add-success="getLabelsData"
                    />
                  </section>
                </template>
              </BkTableColumn>
              <BkTableColumn
                :label="t('更新时间')"
                sort
                prop="updated_time"
              />
              <BkTableColumn
                :label="t('操作')"
                fixed="right"
                prop="act"
                width="150"
              >
                <template #default="{ data }">
                  <div class="flex gap-12px">
                    <BkButton
                      text
                      theme="primary"
                      @click="() => handleEditResource(data.id, 'edit')"
                    >
                      {{ t('编辑') }}
                    </BkButton>
                    <BkButton
                      class="px-10px"
                      text
                      theme="primary"
                      @click="() => handleEditResource(data.id, 'clone')"
                    >
                      {{ t('克隆') }}
                    </BkButton>
                    <BkPopConfirm
                      :content="t('删除操作无法撤回，请谨慎操作')"
                      :title="t('确认删除资源{resourceName}？', { resourceName: data?.name || '' })"
                      trigger="click"
                      width="288"
                      @confirm="() => handleDeleteResource(data.id)"
                    >
                      <BkButton
                        text
                        theme="primary"
                      >
                        {{ t('删除') }}
                      </BkButton>
                    </BkPopConfirm>
                  </div>
                </template>
              </BkTableColumn>
              <template #empty>
                <TableEmpty
                  :abnormal="tableEmptyConf.isAbnormal"
                  :keyword="tableEmptyConf.keyword"
                  @reacquire="getSearchResourceList"
                  @clear-filter="handleClearFilterKey"
                />
              </template>
            </BkTable>
          </BkLoading>
        </div>

        <div
          v-show="isShowLeft"
          class="toggle-button toggle-button-lf"
          :class="[!isDetail ? 'active' : '']"
          :style="{ right: !isDetail ? '-24px' : '-22px' }"
          @click="handleToggleLf"
        >
          <AgIcon
            class="icon"
            name="ag-arrow-left"
          />
        </div>
      </div>

      <div
        v-show="isDetail && isShowLeft"
        id="resourceLine"
        class="demarcation-button"
        draggable="true"
      >
        <span>......</span>
      </div>

      <div
        v-show="isDetail"
        id="resourceRg"
        class="resource-container-rg flex-grow-1"
        :class="[isDragging ? 'dragging' : '']"
      >
        <div
          class="toggle-button toggle-button-rg"
          :class="[!isShowLeft ? 'active' : '']"
          @click="handleToggleRg"
        >
          <AgIcon
            name="ag-arrow-left"
            class="icon"
          />
        </div>
        <div class="right-wraper">
          <BkTab
            v-model:active="active"
            class="resource-tab-panel"
            type="card-tab"
          >
            <BkTabPanel
              v-for="item in panels"
              :key="item.name"
              :label="item.label"
              :name="item.name"
              render-directive="if"
            >
              <BkLoading
                :loading="isComponentLoading"
                :opacity="1"
              >
                <!-- deleted-success 删除成功需要请求一次列表数据 更新详情 -->
                <component
                  :is="item.component"
                  v-if="item.name === active && resourceId"
                  :gateway-id="gatewayId"
                  :cur-resource="curResource"
                  :resource-id="resourceId"
                  doc-root-class="doc-tab"
                  height="calc(100vh - 348px)"
                  @done="(v: boolean | any) => {
                    isComponentLoading = !!v
                  }"
                  @deleted-success="handleDeleteSuccess"
                  @on-jump="(id: number | any) => handleShowInfo(id)"
                />
              </BkLoading>
            </BkTabPanel>
          </BkTab>
        </div>
      </div>

      <!-- 批量删除dialog -->
      <BkDialog
        :is-loading="dialogData.loading"
        :is-show="dialogData.isShow"
        :title="dialogData.title"
        quick-close
        theme="primary"
        width="600"
        @closed="handleBatchCancel"
        @confirm="handleBatchConfirm"
      >
        <div
          v-if="isBatchDelete"
          class="delete-content"
        >
          <BkTable
            :columns="columns"
            :data="selections"
            max-height="280"
            row-hover="auto"
            show-overflow-tooltip
          />
          <BkAlert
            :title="t('删除资源后，需要生成新的版本，并发布到目标环境才能生效')"
            class="my-10px"
            theme="warning"
          />
        </div>
        <div v-else>
          <BkForm>
            <BkFormItem :label="t('基本信息')">
              <BkCheckbox
                v-model="batchEditData.isPublic"
                @change="handlePublicChange"
              >
                {{ t('是否公开') }}
              </BkCheckbox>
              <BkCheckbox
                v-model="batchEditData.allowApply"
                :disabled="!batchEditData.isPublic"
              >
                {{ t('允许申请权限') }}
              </BkCheckbox>
            </BkFormItem>
            <BkFormItem :label="t('是否修改标签')">
              <div class="edit-labels-container">
                <BkSwitcher
                  v-model="batchEditData.isUpdateLabels"
                  theme="primary"
                  @change="handleUpdateLabelsChange"
                />
                <SelectCheckBox
                  v-if="batchEditData.isUpdateLabels"
                  v-model="batchEditData.labelIds"
                  bath-edit
                  :cur-select-label-ids="[]"
                  :labels-data="labelsData"
                  class="select-labels"
                  @update-success="getLabelsData"
                  @label-add-success="getLabelsData"
                />
              </div>
            </BkFormItem>
          </BkForm>
        </div>
      </BkDialog>

      <!-- 资源配置导出 -->
      <ExportResourceDialog
        v-model:dialog-config="exportDialogConfig"
        v-model:dialog-params="exportParams"
        :selections="selections"
        :is-show-export-content="false"
        @confirm="handleExportDownload"
      />

      <!-- 文档侧边栏 -->
      <ResourceDocSlider
        v-model="docSliderConf.isShowDocSide"
        :resource="curResource"
        :title="docSliderConf.title"
        @fetch="handleSuccess"
        @on-update="handleUpdateTitle"
      />

      <!-- 生成版本 -->
      <VersionSlider
        ref="versionSliderRef"
        @done="handleVersionCreated"
      />

      <!-- 版本对比 -->
      <BkSideslider
        v-model:is-show="diffSliderConf.isShow"
        quick-close
        :title="diffSliderConf.title"
        :width="diffSliderConf.width"
      >
        <template #default>
          <div class="p-20px pure-diff">
            <VersionDiff
              :source-id="diffSourceId"
              :target-id="diffTargetId"
            />
          </div>
        </template>
      </BkSideslider>
    </div>
  </div>
  <PageNotFound v-if="gatewayStore.isProgrammableGateway" />
</template>

<script setup lang="ts">
import {
  cloneDeep,
  differenceBy,
  uniqueId,
} from 'lodash-es';
import { Message } from 'bkui-vue';
import {
  type ITableSettings,
  useMaxTableLimit,
  useQueryList,
  useSelection,
  useTableSetting,
} from '@/hooks';
import {
  exportDocs,
  getGatewayLabels,
} from '@/services/source/gateway';
import {
  batchDeleteResources,
  batchEditResources,
  checkNeedNewVersion,
  deleteResources,
  exportResources,
  getResourceList,
  getVersionList,
} from '@/services/source/resource';
import ResourceDetail from './components/ResourceDetail.vue';
import VersionSlider from './components/VersionSlider.vue';
import VersionDiff from '@/components/version-diff/Index.vue';
import SelectCheckBox from './components/SelectCheckBox.vue';
import AgDropdown from '@/components/ag-dropdown/Index.vue';
import PluginManage from '@/components/plugin-manage/Index.vue';
import ResourceDocViewer from './components/ResourceDocViewer.vue';
import TableEmpty from '@/components/table-empty/Index.vue';
import ResourceSettingTopBar from './components/TopBar.vue';
import PageNotFound from '@/views/404.vue';
// import mitt from '@/common/event-bus';
import {
  type IDialog,
  type IDropList,
  type IExportDialog,
  type IExportParams,
} from '@/types/common';
import { isAfter24h } from '@/utils';
import {
  useGateway,
  useResourceSetting,
  useResourceVersion,
} from '@/stores';
import ResourceDocSlider from '../components/ResourceDocSlider.vue';
import ExportResourceDialog from '../components/ExportResourceDialog.vue';
import { HTTP_METHODS } from '@/constants';
import { METHOD_THEMES } from '@/enums';

interface ApigwIDropList extends IDropList { tooltips?: string }

type TableEmptyConfType = {
  keyword: string
  isAbnormal: boolean
};

interface IProps { gatewayId?: number }

const { gatewayId = 0 } = defineProps<IProps>();

const { t } = useI18n();
const gatewayStore = useGateway();
const resourceVersionStore = useResourceVersion();
const resourceSettingStore = useResourceSetting();

const leftWidth = ref('320px');
// 批量下拉的item
// const batchDropData = ref([{ value: 'edit', label: t('编辑资源') }, { value: 'delete', label: t('删除资源') }]);
// 导入下拉
const importDropData = ref([{
  value: 'config',
  label: t('资源配置'),
},
{
  value: 'doc',
  label: t('资源文档'),
}]);
// 导出下拉
const exportDropData = ref<ApigwIDropList[]>([
  {
    value: 'all',
    label: t('全部资源'),
  },
  {
    value: 'filtered',
    label: t('已筛选资源'),
    disabled: false,
    tooltips: t('请先筛选资源'),
  },
  // { value: 'selected', label: t('已选资源'), disabled: false, tooltips: t('请先勾选资源') },
]);

const route = useRoute();
const router = useRouter();

const tableDataKey = ref(uniqueId());
const chooseMethod = ref<string[]>([]);
const filterData = ref<{
  keyword?: string
  order_by?: string
  backend_id?: string
  [key: string]: any
}>({
  keyword: '',
  order_by: '',
  backend_id: '',
});
const chooseLabels = ref<string[]>([]);
const tableEmptyConf = ref<TableEmptyConfType>({
  keyword: '',
  isAbnormal: false,
});

const versionSliderRef = ref();
const selectCheckBoxParentRef = ref(null);
// 导出参数
const exportParams: IExportParams = reactive({
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
    children: HTTP_METHODS,
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
const exportDialogConfig = reactive<IExportDialog>({
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
  isUpdateLabels: false,
  labelIds: [],
});

// 版本对比抽屉
const diffSliderConf = reactive({
  isShow: false,
  width: 1040,
  title: t('版本资源对比'),
});
const diffSourceId = ref();
const diffTargetId = ref();
const isDragging = ref(false);

// const showEdit = ref(false);
// const optionName = ref('');
// const inputRef = ref(null);
const initLimitList = ref([10, 20, 50, 100]);
const tableConfig = ref({
  clientHeight: 0,
  maxTableLimit: 0,
});

// tab 选项卡
const panels = [
  {
    name: 'resourceDetail',
    label: t('资源配置'),
    component: ResourceDetail,
  },
  {
    name: 'pluginManage',
    label: t('插件管理'),
    component: PluginManage,
  },
  {
    name: 'resourcesDoc',
    label: t('资源文档'),
    component: ResourceDocViewer,
  },
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

const customMethodsList = computed(() => HTTP_METHODS.map((item) => {
  return {
    text: item.name,
    value: item.id,
  };
}));

const handleMethodFilter = () => true;

// const curSelectMethod = ref('ALL');

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

  tableDataKey.value = uniqueId();

  return labelsData.value?.map((item: any) => {
    return {
      text: item.name,
      value: item.name,
    };
  });
});

// 当前视口高度能展示最多多少条表格数据
const getMaxTableLimit = () => {
  tableConfig.value = useMaxTableLimit({
    allocatedHeight: 256,
    className: route.name as string,
  });
};
getMaxTableLimit();

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList({
  apiMethod: getResourceList,
  filterData,
  id: 0,
  filterNoResetPage: false,
  initialPagination: {
    limitList: [
      tableConfig.value.maxTableLimit,
      ...initLimitList.value,
    ],
    limit: tableConfig.value.maxTableLimit,
  },
});

// checkbox hooks
const {
  selections,
  handleSelectionChange,
  handleSelectAllChange,
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
  filterData.value = cloneDeep({
    keyword: '',
    order_by: '',
  });
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
  router.push({ name: 'ResourceCreate' });
};

// 编辑资源
const handleEditResource = (id: number, type: string) => {
  const name = type === 'edit' ? 'ResourceEdit' : 'ResourceClone';
  resourceVersionStore.setPageStatus({
    isDetail: false,
    isShowLeft: true,
  });
  router.push({
    name,
    params: { resourceId: id },
  });
};

// 删除资源
const handleDeleteResource = async (id: number) => {
  await deleteResources(gatewayId, id);
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
  }
  else {
    isDetail.value = true;
    const resourceDom = document.getElementById('resourceLf');
    if (resourceDom) {
      resourceDom.style.width = leftWidth.value;
    }
  }
};

const handleToggleRg = () => {
  if (isShowLeft.value) {
    isDetail.value = false;
    handleShowList();
  }
  else {
    isShowLeft.value = true;
  }
};

const dragTwoColDiv = (contentId: string, leftBoxId: string, resizeId: string/* , rightBoxId: string */) => {
  const resize: any = document.getElementById(resizeId);
  const leftBox = document.getElementById(leftBoxId);
  // const rightBox = document.getElementById(rightBoxId);
  const box = document.getElementById(contentId);

  resize.onmousedown = function (e: MouseEvent) {
    const startX = e.clientX;
    resize.left = resize.offsetLeft;
    isDragging.value = true;
    document.onmousemove = function (e) {
      const endX = e.clientX;
      let moveLen = resize.left + (endX - startX);
      const maxT = (box?.clientWidth ?? 0) - resize.offsetWidth;
      if (moveLen < 215) {
        moveLen = 0;
        isShowLeft.value = false;
        document.onmouseup?.(e);
      }
      if (moveLen > maxT - 770) {
        moveLen = maxT;
        handleShowList();
        document.onmouseup?.(e);
      }
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
  const typeMap: Record<string, any> = {
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

const handleSettingChange = (resourceSetting: ITableSettings) => {
  const {
    checked,
    size,
    height,
  } = resourceSetting;
  const isExistDiff = isDiffSize(resourceSetting);
  changeTableSetting(resourceSetting);
  if (!isExistDiff) {
    return;
  }
  settings.value = Object.assign(settings.value, {
    checked,
    size,
    height,
  });
  getResizeTable();
};

const getResizeTable = async () => {
  await getMaxTableLimit();
  pagination.value = Object.assign(pagination.value, {
    current: 1,
    offset: 0,
    limit: tableConfig.value.maxTableLimit,
    limitList: [...initLimitList.value, tableConfig.value.maxTableLimit],
  });
};

// 展示右边内容
const handleShowInfo = (id: number, curActive = 'resourceInfo') => {
  resourceId.value = id;
  handleOutBatch();
  // curResource.value = tableData.value.find((e: any) => e.id === id);
  tableData.value?.forEach((item: any) => {
    if (item.id === id) {
      curResource.value = item;
      item.highlight = true;
    }
    else {
      item.highlight = false;
    }
  });

  if (isDetail.value) {
    isComponentLoading.value = true;
    active.value = curActive;
  }
  else {
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

const showBatch = ref<boolean>(false);
// 进入批量操作
const handleShowBatch = () => {
  showBatch.value = true;
  handleShowList();
  exportDropData.value = [
    {
      value: 'all',
      label: t('全部资源'),
    },
    {
      value: 'selected',
      label: t('已选资源'),
      disabled: !selections.value.length,
      tooltips: t('请先勾选资源'),
    },
  ];
};

// 退出批量操作
const handleOutBatch = () => {
  showBatch.value = false;
  selections.value = [];
  exportDropData.value = [
    {
      value: 'all',
      label: t('全部资源'),
    },
    {
      value: 'filtered',
      label: t('已筛选资源'),
      disabled: !searchValue.value.length || !tableData.value.length,
      tooltips: t('请先筛选资源'),
    },
  ];

  tableDataKey.value = uniqueId();
};

// 版本对比
const handleShowDiff = async () => {
  try {
    const response = await getVersionList(gatewayId, {
      offset: 0,
      limit: 10,
    });
    if (!response.results.length) {
      diffSourceId.value = 'current';
    }
    else {
      diffSourceId.value = response.results[0]?.id || '';
    }
    diffSliderConf.width = window.innerWidth <= 1280 ? 1040 : 1280;
    diffSliderConf.isShow = true;
  }
  catch {
    Message({
      message: t('操作失败，请稍后再试！'),
      theme: 'error',
      width: 'auto',
    });
  }
};

// 处理批量编辑或删除
const handleBatchOperate = async (type: string) => {
  if (!selections.value?.length) {
    Message({
      message: t('请先勾选资源'),
      theme: 'warning',
      width: 'auto',
    });
    return;
  }

  dialogData.isShow = true;
  // 批量删除
  if (type === 'delete') {
    isBatchDelete.value = true;
    dialogData.title = t('确定要删除以下{count}个资源', { count: selections.value.length });
  }
  else {
    // 批量编辑
    isBatchDelete.value = false;
    dialogData.title = t('批量编辑资源（共{count}个）', { count: selections.value.length });
  }
};

// 处理导出弹窗显示
const handleExport = async ({ value }: { value: string }) => {
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
    const res = await fetchMethod(gatewayId, params);
    if (res.success) {
      Message({
        message: t('导出成功'),
        theme: 'success',
        width: 'auto',
      });
    }
    exportDialogConfig.isShow = false;
  }
  catch (e) {
    if (exportDialogConfig.exportFileDocType === 'docs') {
      const fileReader = new FileReader();
      fileReader.readAsText(e as Blob, 'utf-8');
      fileReader.onload = function () {
        const blobError = JSON.parse(fileReader.result as string);
        Message({
          message: blobError?.error?.message || t('导出失败'),
          theme: 'error',
          width: 'auto',
        });
      };
    }
    else {
      const error = e as Error;
      Message({
        message: error?.message || t('导出失败'),
        theme: 'error',
        width: 'auto',
      });
    }
  }
};
// 批量编辑确认
const handleBatchConfirm = async () => {
  const ids = selections.value.map(e => e.id);
  if (isBatchDelete.value) {
    // 批量删除
    await batchDeleteResources(gatewayId, { ids });
  }
  else {
    const params = {
      ids,
      is_public: batchEditData.value.isPublic,
      allow_apply_permission: batchEditData.value.allowApply,
      is_update_labels: batchEditData.value.isUpdateLabels,
      label_ids: batchEditData.value.labelIds,
    };
    // 批量编辑
    await batchEditResources(gatewayId, params);
  }
  dialogData.isShow = false;
  batchEditData.value.isUpdateLabels = false;
  batchEditData.value.labelIds = [];
  Message({
    message: t(`${isBatchDelete.value ? '删除' : '编辑'}成功`),
    theme: 'success',
    width: 'auto',
  });
  getList();
  resetSelections();
};

const handleBatchCancel = () => {
  dialogData.isShow = false;
  batchEditData.value.isUpdateLabels = false;
};

// 处理导入跳转
const handleImport = (v: IDropList) => {
  const routerName = v.value === 'doc' ? 'ResourceImportDoc' : 'ResourceImport';
  router.push({ name: routerName });
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
  resourceId.value = data.id; // 资源id
  docSliderConf.isShowDocSide = true;
  docSliderConf.title = `${t('文档详情')}【${data.name}】`;
  docSliderConf.languages = languages;
};

// 改变侧栏边title
const handleUpdateTitle = (type: string, isUpdate?: boolean) => {
  if (type === 'cancel') {
    docSliderConf.title = `${t('文档详情')}【${curResource.value.name}】`;
  }
  else {
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
    const res = await checkNeedNewVersion(gatewayId);
    versionConfigs.needNewVersion = res.need_new_version;
    versionConfigs.versionMessage = res.msg;
  }
  catch (error: any) {
    versionConfigs.needNewVersion = false;
    versionConfigs.versionMessage = error?.msg;
  }
};

// 处理标签点击
const handleEditLabel = (data: any) => {
  resourceId.value = data.id;
  tableData.value.forEach((item: Record<string, any>) => {
    item.isEditLabel = false;
  });
  curLabelIds.value = data.labels.map((item: any) => item.id);
  curLabelIdsbackUp.value = cloneDeep(curLabelIds.value);
  data.isEditLabel = true;
};

// 生成版本功能
const handleCreateResourceVersion = async () => {
  const response = await getVersionList(gatewayId, {
    offset: 0,
    limit: 10,
  });
  if (!response.results.length) {
    diffSourceId.value = 'current';
  }
  else {
    diffSourceId.value = response.results[0]?.id || '';
  }
  versionSliderRef.value.showReleaseSideslider();
};

// 获取标签数据
const getLabelsData = async () => {
  const res = await getGatewayLabels(gatewayId);
  res.forEach((e: any) => e.isEdited = false);
  labelsData.value = res;
};

// 未做变更关闭select下拉
const handleCloseSelect = (row: any, newLabelData: any = []) => {
  tableData.value.forEach((item: Record<string, any>) => {
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

const handleUpdateLabelsChange = (v: boolean) => {
  if (!v) {
    batchEditData.value.labelIds = [];
  }
};

const handleRowClass = (v: any) => {
  const ret = [];
  if (!v.isAfter24h) {
    ret.push('row-cls-in-24hours');
  }
  if (v.highlight) {
    ret.push('row-cls-highlight');
  }
  return ret.join(' ');
};

const tipsContent = (data: any[]) => {
  return h('div', {}, [
    data.map((item: string) => h('div', {
      style: 'display: flex; align-items: center; margin-top: 5px;',
      class: 'tips-cls',
    }, [item])),
  ]);
};

const settings = shallowRef({
  trigger: 'click',
  fields: [
    {
      name: t('资源名称'),
      field: 'name',
      disabled: true,
    },
    {
      name: t('后端服务'),
      field: 'backend_name',
    },
    {
      name: t('前端请求方法'),
      field: 'method',
    },
    {
      name: t('前端请求路径'),
      field: 'path',
    },
    {
      name: t('插件数'),
      field: 'plugin_count',
    },
    {
      name: t('文档'),
      field: 'docs',
    },
    {
      name: t('标签'),
      field: 'labels',
    },
    {
      name: t('更新时间'),
      field: 'updated_time',
    },
    {
      name: t('操作'),
      field: 'act',
      disabled: true,
    },
  ],
  size: 'small',
  height: 42,
  checked: ['name', 'backend_name', 'method', 'path', 'plugin_count', 'docs', 'labels', 'updated_time', 'act'],
});

const { changeTableSetting, isDiffSize } = useTableSetting(settings, route.name);

watch(
  isDetail,
  (v) => {
    if (!v) {
      tableData.value?.forEach((item: any) => {
        item.highlight = false;
      });
    }
  },
);

watch(
  isShowLeft,
  (v) => {
    const el = document.getElementById('resourceLf');
    if (el) {
      if (!v) {
        el.style.width = '0px';
      }
      else {
        el.style.width = leftWidth.value;
      }
    }
  },
);

// 监听table数据 如果未点击某行 则设置第一行的id为资源id
watch(
  tableData,
  (v: any) => {
    if (v.length && resourceId.value === 0) {
      // if (v.length) {
      resourceId.value = v[0].id;
    }
    // 设置显示的tag值
    tableData.value.forEach((item: any) => {
      item.isAfter24h = isAfter24h(item.created_time);
      item.tagOrder = 1;
      item.labelText = item.labels?.map((label: any) => {
        return label.name;
      });
      item.isEditLabel = false;
    });

    exportDropData.value.forEach((e: IDropList) => {
      if (e.value === 'filtered') {
        e.disabled = !v.length || !searchValue.value.length;
      }
    });

    updateTableEmptyConfig();
  },
  { immediate: true },
);

// 监听导出弹窗
watch(
  () => exportDialogConfig,
  (v: IExportDialog) => {
    if (v.exportFileDocType === 'docs') {
      exportParams.file_type = 'zip';
    }
    else {
      exportParams.file_type = 'yaml';
    }
  },
  { deep: true },
);

// 选中的值
watch(
  selections,
  (v: number[]) => {
    exportDropData.value.forEach((e: IDropList) => {
      // 已选资源
      if (e.value === 'selected') {
        e.disabled = !v.length;
      }
    });
  },
  {
    immediate: true,
    deep: true,
  },
);

// Search Select选中的值
watch(
  searchValue,
  (v: any[]) => {
    filterData.value = {
      order_by: filterData.value.order_by,
      keyword: '',
    };

    if (route.query?.backend_id) {
      const { backend_id } = route.query;
      filterData.value.backend_id = backend_id;
    }
    else {
      delete filterData.value.backend_id;
    }

    if (!filterData.value.order_by) {
      delete filterData.value.order_by;
    }
    pagination.value.offset = 0;
    pagination.value.current = 0;
    if (v.length) {
      v.forEach((e: any) => {
        if (e.id === e.name) {
          filterData.value.keyword = e.name;
        }
        else {
          if (e.id === 'method') {
            filterData.value[e.id] = e.values?.map((item: any) => item.id)?.join(',');
          }
          else {
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
      }

      if (!filter?.length && chooseMethod.value?.length) { // 清空筛选时，同步给表头筛选
        chooseMethod.value = [];
      }

      tableDataKey.value = uniqueId();
    });

    updateTableEmptyConfig();
  },
  {
    immediate: true,
    deep: true,
  },
);

watch(
  () => route.query,
  () => {
    if (route.query?.backend_id) {
      const { backend_id } = route.query;
      filterData.value.backend_id = backend_id;
    }
    if (resourceSettingStore.previousPagination) {
      nextTick(() => {
        pagination.value.current = resourceSettingStore.previousPagination?.current ?? 1;
        pagination.value.offset = resourceSettingStore.previousPagination?.offset ?? 0;
      });
    }
  },
  {
    immediate: true,
    deep: true,
  },
);

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
  chooseLabels,
  (v) => {
    if (!v?.length) { // 重置
      filterData.value.label_ids = undefined;
    }
    else { // 选择
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
  {
    deep: true,
    immediate: true,
  },
);

watch(
  () => chooseMethod.value,
  (v) => {
    if (!v?.length) { // 重置
      filterData.value.method = undefined;
      searchValue.value = searchValue.value.filter((item: Record<string, any>) => !['method'].includes(item.id));
    }
    else { // 选择
      filterData.value.method = v?.join(',');
      const hasMethodData = searchValue.value.find((item: Record<string, any>) => ['method'].includes(item.id));
      const method = v?.map((m: string) => {
        return {
          id: m,
          name: m,
        };
      });
      if (hasMethodData) {
        hasMethodData.values = method;
      }
      else {
        searchValue.value.push({
          id: 'method',
          name: t('前端请求方法'),
          values: method,
        });
      }
    }
    getList();
  },
  {
    deep: true,
    immediate: true,
  },
);

const recoverPageStatus = () => {
  const { isDetail: d, isShowLeft: l } = resourceVersionStore.getPageStatus;
  isDetail.value = d;
  isShowLeft.value = l;

  const el = document.getElementById('resourceLf');
  if (!l) {
    el.style.width = '0px';
  }
  else {
    el.style.width = leftWidth.value;
  }
};

const handleVersionCreated = () => {
  getList();
  handleShowVersion();
};

onBeforeRouteLeave((to) => {
  if (to.name === 'ResourceEdit') {
    const { current, offset } = pagination.value;
    resourceSettingStore.setPagination({
      current,
      offset,
    });
  }
  else {
    resourceSettingStore.setPagination(null);
  }
});

onMounted(() => {
  // setTimeout(() => {
  init();
  dragTwoColDiv(
    'resourceId',
    'resourceLf',
    'resourceLine',
    // 'resourceRg',
  );
  // 监听其他组件是否触发了资源更新，获取最新的列表数据
  // mitt.on('on-update-plugin', () => {
  //   pagination.value = Object.assign(pagination.value, {
  //     current: 0,
  //     limit: maxTableLimit,
  //   });
  //   getList();
  //   handleShowVersion();
  // });
  if (route.meta.pageStatus) {
    recoverPageStatus();
  }
  // });
});

// onBeforeMount(() => {
//   mitt.off('on-update-plugin');
// });

</script>

<style lang="scss" scoped>
.resource-container {
  display: flex;
  align-items: flex-start;
  height: calc(100% - 112px);

  .resource-container-lf,
  .resource-container-rg{
    position: relative;
  }

  .resource-container-rg {
    min-height: calc(100% + 40px);
    margin-top: -20px;
    margin-right: -24px;
    margin-bottom: -20px;
    background: #fff;

    &.dragging {

      &::before {
        position: absolute;
        top: 0;
        left: -1px;
        z-index: 999;
        width: 2px;
        height: 100%;
        background-color: #3a84ff;
        content: ' ';
      }
    }
  }

  .demarcation-button:hover + .resource-container-rg {

    &::before {
      position: absolute;
      top: 0;
      left: -1px;
      z-index: 999;
      width: 2px;
      height: 100%;
      background-color: #3a84ff;
      content: ' ';
    }
  }

  .demarcation-button {
    display: flex;
    height: 100%;
    cursor: col-resize;
    justify-content: center;
    align-items: center;

    span {
      padding-bottom: 6px;
      color: #63656E;
      transform: rotate(90deg);
    }
  }

  .operate {
    display: flex;
    justify-content: space-between;
    margin-bottom: 15px;
    gap: 8px;

    .operate-input{
      width: 450px;
    }

    .search-select-wrap {
      flex-grow: 1;
      max-width: 450px;
    }
  }

  .left-wrapper {
    position: relative;
    background: #fff;

    .document-info{
      font-size: 12px;
      color: #3a84ff;
      cursor: pointer;
    }

    .plus-class{
      padding: 4px;
      font-size: 14px;
      font-weight: bold;
      color: #979BA5;
      cursor: pointer;
      background: #EAEBF0;

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
          overflow: hidden;
          color: #3a84ff;
          text-overflow: ellipsis;
          white-space: nowrap;
          cursor: pointer;

          .name-updated {
            max-width: 112px;
          }
        }

        .dot {
          display: inline-block;
          min-width: 8px;
          height: 8px;
          margin-left: 4px;
          vertical-align: middle;
          cursor: pointer;
          border: 1px solid #C4C6CC;
          border-radius: 50%;

          &.warning {
            background: #fff3e1;
            border: 1px solid #ff9c01;
          }
        }
      }
    }

    .text-warp {
      position: relative;
      cursor: pointer;

      .edit-icon {
        position: absolute;
        top: -2px;
        font-size: 24px;
        color: #3A84FF;
        cursor: pointer;

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

  .toggle-button {
    position: absolute;
    z-index: 99;
    display: flex;
    width: 16px;
    height: 28px;
    font-size: 12px;
    color: #3A84FF;
    cursor: pointer;
    background: #FAFBFD;
    border: 1px solid #3A84FF;
    border-radius: 4px 0 0 4px;
    transform: translateY(-50%);
    box-shadow: 0 2px 4px 0 #0000001a;
    align-items: center;
    justify-content: center;

    .icon {
      transition: transform .15s !important;
    }

    &:hover {
      color: #fff;
      background-color: #3a84ff;
    }

    &.active {
      color: #fff;
      background-color: #3a84ff;
    }
  }

  .toggle-button-lf {
    // right: -19px;
    top: -6px;
  }

  .toggle-button-rg {
    top: 0;
    left: -1px;
    border-radius: 4px 0 0 4px;
    transform: rotate(180deg) !important;
  }
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
  padding-left: 0;
}

.tips-cls {
  padding: 3px 8px;
  cursor: default;
  background: #f0f1f5;
  border-radius: 2px;

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

.edit-labels-container {

  .select-labels {
    display: inline-block;
    width: 240px;
    margin-top: 0 !important;
    margin-left: 16px;
  }
}

.split-line {
  width: 1px;
  height: 14px;
  margin-right: 8px;
  background-color: #C4C6CC;

  &.batch {
    margin-right: 12px;
    margin-left: 4px;
  }
}

.operate-btn-wrapper,
.batch-status {
  display: flex;
}

.operate-btn {

  .apigateway-icon {
    margin-right: 8px;

    &.icon-ag-chahao {
      font-size: 14px;
    }
  }
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
