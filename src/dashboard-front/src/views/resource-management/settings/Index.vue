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
      :show-new-tips="!!tableData.length"
    />
    <div
      id="resourceId"
      class="resource-container page-wrapper-padding"
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
          <AgTable
            ref="tableRef"
            v-model:selected-row-keys="selectedRowKeys"
            v-model:table-data="tableData"
            :source="getTableData"
            :columns="columns"
            row-key="id"
            :filter-row="null"
            hover
            @filter-change="handleFilterChange"
            @select-change="handleSelectChange"
            @sort-change="handleSortChange"
          />
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
                  @done="isComponentLoading = false"
                  @deleted-success="handleDeleteSuccess"
                  @on-jump="(id: number | any) => handleShowInfo(id)"
                  @on-update-plugin="handleUpdatePlugin"
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
            :columns="deleteTableColumns"
            :data="selectedRows"
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
        :selections="selectedRows"
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
      <CreateResourceVersion
        ref="createResourceVersionRef"
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

<script setup lang="tsx">
import {
  cloneDeep,
  differenceBy,
} from 'lodash-es';
import { Message } from 'bkui-vue';
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
import CreateResourceVersion from '@/components/create-resource-version/Index.vue';
import VersionDiff from '@/components/version-diff/Index.vue';
import SelectCheckBox from './components/SelectCheckBox.vue';
import AgDropdown from '@/components/ag-dropdown/Index.vue';
import PluginManage from '@/components/plugin-manage/Index.vue';
import ResourceDocViewer from './components/ResourceDocViewer.vue';
import AgTable from '@/components/ag-table/Index.vue';
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
import { type PrimaryTableProps } from '@blueking/tdesign-ui';

interface ApigwIDropList extends IDropList { tooltips?: string }

interface IProps { gatewayId?: number }

const { gatewayId = 0 } = defineProps<IProps>();

const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const gatewayStore = useGateway();
const resourceVersionStore = useResourceVersion();
const resourceSettingStore = useResourceSetting();

const tableData = ref<any[]>([]);
const tableRef = useTemplateRef('tableRef');
const tableQueries = ref<Record<string, any>>({});
const selectedRowKeys = ref<number[]>([]);
const selectedRows = ref<any[]>([]);

const leftWidth = ref('320px');
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

const createResourceVersionRef = ref();
const selectCheckBoxParentRef = ref();
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
const curResource = ref<any>({});

const active = ref('resourceInfo');

const isComponentLoading = ref(false);

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
const docSliderConf = reactive({
  isShow: false,
  title: t('文档详情'),
  isLoading: false,
  isEdited: false,
  languages: 'zh',
  isShowDocSide: false,
});

// 批量删除dialog
const dialogData = reactive<IDialog>({
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
const showBatch = ref(false);

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

const deleteTableColumns = [
  {
    label: t('请求路径'),
    field: 'path',
  },
  {
    label: t('请求方法'),
    field: 'method',
  },
];

const customMethodsList = computed(() => {
  const methods = HTTP_METHODS.map(item => ({
    label: item.name,
    value: item.id,
  }));

  return [
    {
      label: 'All',
      checkAll: true,
    },
    ...methods,
  ];
});

const labelsList = computed(() => {
  if (!labelsData.value.length) {
    return [];
  }

  return labelsData.value?.map((item: any) => ({
    label: item.name,
    value: item.id,
  }));
});

const columns = computed<PrimaryTableProps['columns']>(() => {
  const cols: PrimaryTableProps['columns'] = [
    {
      colKey: 'name',
      title: t('资源名称'),
      minWidth: 170,
      fixed: 'left',
      ellipsis: {
        props: { placement: 'right' },
        content: (h, { row }) => row.name,
      },
      cell: (h, { row }) => (
        <div class="resource-name">
          <div
            class={
              [
                'name color-#3A84FF cursor-pointer overflow-hidden whitespace-nowrap text-ellipsis',
                { 'name-updated': row.has_updated },
              ]
            }
            onClick={() => handleShowInfo(row.id)}
          >
            <span
              v-bk-tooltips={{
                content: row.name,
                placement: 'right',
                delay: 300,
              }}
            >
              {row.name}
            </span>
            {row.has_updated
              ? (
                <div
                  v-bk-tooltips={{
                    content: t('资源已更新'),
                    placement: 'right',
                    delay: 300,
                  }}
                  class="inline-block w-8px h-8px ml-4px cursor-pointer border-1px border-solid border-#ff9c01 rounded-1/2 bg-#fff3e1"
                >
                </div>
              )
              : ''}
          </div>
        </div>
      ),
    },
    {
      colKey: 'backend.name',
      title: '后端服务',
      width: 130,
    },
    {
      colKey: 'method',
      title: '前端请求方法',
      width: 130,
      cell: (h, { row }) => (
        <bk-tag theme={METHOD_THEMES[row.method as keyof typeof METHOD_THEMES]}>
          {row.method}
        </bk-tag>
      ),
      filter: {
        type: 'multiple',
        showConfirmAndReset: true,
        resetValue: [],
        list: customMethodsList.value,
      },
    },
    {
      colKey: 'path',
      title: '前端请求路径',
      minWidth: 250,
      ellipsis: true,
    },
    {
      colKey: 'plugin_count',
      title: '插件数',
      width: 80,
      cell: (h, { row }) => (
        <bk-button
          text
          theme="primary"
          class="plugin-num"
          onClick={() => handleShowInfo(row.id, 'pluginManage')}
        >
          {row.plugin_count}
        </bk-button>
      ),
    },
    {
      colKey: 'docs',
      title: t('文档'),
      width: 80,
      cell: (h, { row }) => (
        <div>
          {row.docs?.length
            ? (
              <bk-button text theme="primary" onClick={() => handleShowDoc(row)}>
                <ag-icon name="document" />
                { t('详情') }
              </bk-button>
            )
            : (
              <section class="group">
                <ag-icon
                  v-bk-tooltips={t('添加文档')}
                  name="plus"
                  size="14"
                  class="hidden group-hover:inline p-4px color-#979ba5 cursor-pointer bg-#eaebf0 hover:color-#3a84ff hover:bg-#e1ecff"
                  onClick={() => handleShowDoc(row)}
                />
                <span class="inline group-hover:hidden">--</span>
              </section>
            )}
        </div>
      ),
    },
    {
      colKey: 'label_ids',
      title: t('标签'),
      width: 300,
      filter: {
        type: 'multiple',
        showConfirmAndReset: true,
        resetValue: [],
        list: labelsList.value,
      },
      cell: (h, { row }) => (
        <>
          {!row.isEditLabel
            ? (
              <div
                class="flex items-center gap-4px group"
                onClick={() => handleEditLabel(row)}
              >
                {
                  row.labels?.length
                    ? (
                      <div class="flex items-center gap-4px">
                        { row.labels.map(item => (
                          <bk-tag key={item.id} onClick={() => handleEditLabel(row)}>
                            { item.name }
                          </bk-tag>
                        ))}
                        {
                          row.labels.length > row.tagOrder
                            ? (
                              <bk-tag
                                class="tag-cls"
                                onClick={() => handleEditLabel(row)}
                              >
                                +
                                { row.labels.length - row.tagOrder }
                              </bk-tag>
                            )
                            : ''
                        }
                      </div>
                    )
                    : (<span>--</span>)
                }
                <ag-icon
                  name="edit-small"
                  class="hidden group-hover:inline hover:cursor-pointer hover:color-#3a84ff"
                  size="22"
                  onClick={() => handleEditLabel(row)}
                />
              </div>
            )
            : (
              <section ref="selectCheckBoxParentRef">
                <SelectCheckBox
                  cur-select-label-ids={curLabelIds.value}
                  labels-data={labelsData.value}
                  resource-id={resourceId.value}
                  width={selectCheckBoxParentRef?.offsetWidth}
                  force-focus
                  onClose={newLabelData => handleCloseSelect(row, newLabelData)}
                  onUpdateSuccess={() => handleUpdateLabelSuccess()}
                  onLabelAddSuccess={() => getLabelsData()}
                />
              </section>
            )}
        </>
      ),
    },
    {
      colKey: 'updated_time',
      title: t('更新时间'),
      minWidth: 220,
      sorter: true,
    },
    {
      colKey: 'act',
      title: t('操作'),
      fixed: 'right',
      width: 150,
      cell: (h, { row }) => (
        <div class="flex gap-12px">
          <bk-button
            text
            theme="primary"
            onClick={() => handleEditResource(row.id, 'edit')}
          >
            { t('编辑') }
          </bk-button>
          <bk-button
            class="px-10px"
            text
            theme="primary"
            onClick={() => handleEditResource(row.id, 'clone')}
          >
            { t('克隆') }
          </bk-button>
          <bk-pop-confirm
            content={t('删除操作无法撤回，请谨慎操作')}
            title={t('确认删除资源{resourceName}？', { resourceName: row.name || '' })}
            trigger="click"
            width="288"
            onConfirm={() => handleDeleteResource(row.id)}
          >
            <bk-button
              text
              theme="primary"
            >
              { t('删除') }
            </bk-button>
          </bk-pop-confirm>
        </div>
      ),
    },
  ];
  if (showBatch.value) {
    cols.unshift({
      colKey: 'row-select',
      type: 'multiple',
      width: 80,
      fixed: 'left',
    });
  }
  return cols;
});

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
    if (!v) {
      el.style.width = '0px';
    }
    else {
      el.style.width = leftWidth.value;
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
  selectedRowKeys,
  () => {
    exportDropData.value.forEach((e: IDropList) => {
      // 已选资源
      if (e.value === 'selected') {
        e.disabled = !selectedRowKeys.value.length;
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
    tableQueries.value = {
      order_by: tableQueries.value.order_by,
      keyword: '',
    };

    if (route.query?.backend_id) {
      const { backend_id } = route.query;
      tableQueries.value.backend_id = backend_id;
    }
    else {
      delete tableQueries.value.backend_id;
    }

    if (!tableQueries.value.order_by) {
      delete tableQueries.value.order_by;
    }

    if (v.length) {
      v.forEach((e: any) => {
        if (e.id === e.name) {
          tableQueries.value.keyword = e.name;
        }
        else {
          if (e.id === 'method') {
            tableQueries.value[e.id] = e.values?.map((item: any) => item.id)?.join(',');
          }
          else {
            tableQueries.value[e.id] = e.values[0].id;
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
  },
  {
    immediate: true,
    deep: true,
  },
);

watch(tableQueries, () => {
  tableRef.value!.fetchData(tableQueries.value);
}, { deep: true });

watch(
  () => route.query,
  () => {
    if (route.query?.backend_id) {
      const { backend_id } = route.query;
      tableQueries.value.backend_id = backend_id;
    }
    if (resourceSettingStore.previousPagination) {
      nextTick(() => {
        const { current, pageSize } = resourceSettingStore.previousPagination;
        tableRef.value?.setPagination({
          current,
          pageSize,
        });
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

const init = () => {
  handleShowVersion();
  getLabelsData();
};

// const handleClearFilterKey = () => {
//   tableQueries.value = {};
//   searchValue.value = [];
// };

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
    document.getElementById('resourceLf').style.width = leftWidth.value;
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
      const maxT = box.clientWidth - resize.offsetWidth;
      if (moveLen < 215) {
        moveLen = 0;
        isShowLeft.value = false;
        document.onmouseup(e);
      }
      if (moveLen > maxT - 770) {
        moveLen = maxT;
        handleShowList();
        document.onmouseup(e);
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

// 展示右边内容
const handleShowInfo = (id: number, curActive = 'resourceInfo') => {
  resourceId.value = id;
  handleOutBatch();
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
    // pagination.value.small = true;
    isDetail.value = true;
    document.getElementById('resourceLf').style.width = leftWidth.value;
    active.value = curActive;
  }
};

const handleUpdatePlugin = () => {
  tableRef.value!.fetchData(tableQueries.value);
  handleShowVersion();
  isComponentLoading.value = false;
};

// 显示列表
const handleShowList = () => {
  isDetail.value = false;
  isShowLeft.value = true;
  // pagination.value.small = false;
};

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
      disabled: !selectedRowKeys.value.length,
      tooltips: t('请先勾选资源'),
    },
  ];
};

// 退出批量操作
const handleOutBatch = () => {
  showBatch.value = false;
  selectedRowKeys.value = [];
  selectedRows.value = [];
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
  if (!selectedRowKeys.value?.length) {
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
    dialogData.title = t('确定要删除以下{count}个资源', { count: selectedRowKeys.value.length });
  }
  else {
    // 批量编辑
    isBatchDelete.value = false;
    dialogData.title = t('批量编辑资源（共{count}个）', { count: selectedRowKeys.value.length });
  }
};

// 处理导出弹窗显示
const handleExport = async ({ value }: { value: string }) => {
  switch (value) {
    case 'selected':
      exportParams.resource_ids = [...selectedRowKeys.value];
      exportParams.resource_filter_condition = undefined;
      break;
    case 'filtered':
      exportParams.resource_filter_condition = tableQueries.value;
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
    await fetchMethod(gatewayId, params);
    Message({
      message: t('导出成功'),
      theme: 'success',
      width: 'auto',
    });
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
  const ids = [...selectedRowKeys.value];
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
  tableRef.value!.fetchData(tableQueries.value);
  selectedRowKeys.value = [];
  selectedRows.value = [];
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
  tableRef.value!.fetchData(tableQueries.value);
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
  createResourceVersionRef.value.showReleaseSideslider();
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
      tableRef.value!.fetchData(tableQueries.value);
      init();
    }
  }
};

// 更新成功
const handleUpdateLabelSuccess = () => {
  tableRef.value!.fetchData(tableQueries.value);
  init();
};

// 删除成功
const handleDeleteSuccess = () => {
  tableRef.value!.fetchData(tableQueries.value);
  handleShowList();
};

const handleUpdateLabelsChange = (v: boolean) => {
  if (!v) {
    batchEditData.value.labelIds = [];
  }
};

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
  tableRef.value!.fetchData(tableQueries.value, { resetPage: true });
  handleShowVersion();
};

onBeforeRouteLeave((to) => {
  if (to.name === 'ResourceEdit') {
    const { current, pageSize } = tableRef.value!.getPagination();
    resourceSettingStore.setPagination({
      current,
      pageSize,
    });
  }
  else {
    resourceSettingStore.setPagination(null);
  }
});

const getTableData = async (params: Record<string, any> = {}) => getResourceList(gatewayId, params);

const handleFilterChange: PrimaryTableProps['onFilterChange'] = (filterValue) => {
  Object.entries(filterValue).forEach(([colKey, checkValues]) => {
    if (checkValues.length) {
      if (colKey === 'method') {
        Object.assign(tableQueries.value, { method: checkValues.join(',') });
        const methodSearchItem = searchValue.value.find(searchItem => searchItem.id === 'method');
        if (methodSearchItem) {
          methodSearchItem.values = checkValues.map((item: string) => ({
            id: item,
            name: item,
          }));
        }
        else {
          searchValue.value.push({
            id: 'method',
            name: t('前端请求方法'),
            values: checkValues.map((item: string) => ({
              id: item,
              name: item,
            })),
          });
        }
      }
      else if (colKey === 'label_ids') {
        Object.assign(tableQueries.value, { label_ids: checkValues.join(',') });
      }
      else {
        Object.assign(tableQueries.value, { [colKey]: checkValues });
      }
    }
    else {
      if (colKey === 'method') {
        const methodSearchItemIndex = searchValue.value.findIndex(searchItem => searchItem.id === 'method');
        if (methodSearchItemIndex > -1) {
          searchValue.value.splice(methodSearchItemIndex, 1);
        }
      }
      delete tableQueries.value[colKey];
    }
  });
};

const handleSelectChange: PrimaryTableProps['onSelectChange'] = (selectedRowKeys, options) => {
  selectedRows.value = options.selectedRowData;
};

const handleSortChange: PrimaryTableProps['onSortChange'] = (sort) => {
  if (!sort) {
    delete tableQueries.value.order_by;
    return;
  }
  const { sortBy: colKey, descending } = sort;
  if (colKey === 'updated_time') {
    tableQueries.value.order_by = descending ? `-${colKey}` : colKey;
  }
};

onMounted(() => {
  // setTimeout(() => {
  init();
  dragTwoColDiv(
    'resourceId',
    'resourceLf',
    'resourceLine',
    // 'resourceRg',
  );
  if (route.meta.pageStatus) {
    recoverPageStatus();
  }
  // });
});

</script>

<style lang="scss" scoped>
.resource-container {
  display: flex;
  align-items: flex-start;
  height: calc(100% - 112px);

  // overflow-y: auto;

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
          height: 8px;
          min-width: 8px;
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
