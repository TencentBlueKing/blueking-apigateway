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
  <div class="app-content apigw-access-manager-wrapper flex">
    <div
      class="left-system-nav"
      :class="[{ 'is-expand': !isExpand }]"
    >
      <div class="left-wrapper">
        <RenderSystem
          ref="systemFilterRef"
          :list="systemList"
          @on-select="handleSelect"
        />
      </div>
      <div
        class="handle-icon"
        @click="isExpand = !isExpand"
      >
        <i class="apigateway-icon icon-ag-down-small" />
      </div>
    </div>
    <div
      class="right-wrapper"
      :class="[{ 'is-expand': !isExpand }]"
    >
      <BkAlert
        v-if="needNewVersion && syncEsbToApigwEnabled"
        class="m-b-15px"
        theme="warning"
        :title="
          t(
            '组件配置有更新，新增组件或更新组件请求方法、请求路径、权限级别、用户认证，需同步到网关才能生效'
          )
        "
      />
      <div class="mb-16px flex justify-between">
        <div class="action-wrapper">
          <BkButton
            theme="primary"
            @click="handleCreate"
          >
            {{ t("新建组件") }}
          </BkButton>
          <BkButton
            :disabled="selections.length < 1"
            @click="handleBatchDelete"
          >
            {{ t("批量删除") }}
          </BkButton>
          <BkButton
            v-if="syncEsbToApigwEnabled"
            :disabled="isReleasing"
            :icon="isReleasing ? 'loading' : ''"
            @click="handleNavRoute('SyncApigwAccess')"
          >
            <span
              v-bk-tooltips="{
                content: t('组件正在同步及发布中，请不要重复操作'),
                disabled: !isReleasing,
              }"
            >
              {{ isReleasing ? t("正在同步中") : t("同步到网关") }}
            </span>
          </BkButton>
        </div>
        <div class="flex justify-between items-center component-flex">
          <BkSearchSelect
            v-model="searchValue"
            :data="searchData"
            unique-select
            :placeholder="t('请输入组件名称、请求路径，按Enter搜索')"
            :value-split-code="'+'"
          />
          <i
            v-if="syncEsbToApigwEnabled"
            v-bk-tooltips="t('查看同步历史')"
            class="apigateway-icon icon-ag-cc-history history-icon"
            @click="handleNavRoute('SyncHistory')"
          />
        </div>
      </div>
      <BkLoading
        :loading="isLoading"
        :opacity="1"
      >
        <BkTable
          ref="comTableRef"
          border="outer"
          :data="tableData"
          :size="'small'"
          :is-row-select-enable="setDefaultSelect"
          :pagination="pagination"
          :columns="getTableColumns"
          :max-height="clientHeight"
          remote-pagination
          show-overflow-tooltip
          @select="handleSelectionChange"
          @select-all="handleSelectAllChange"
          @page-limit-change="handlePageSizeChange"
          @page-value-change="handlePageChange"
          @row-mouse-enter="handleRowEnter"
          @row-mouse-leave="handleRowLeave"
        >
          <template #empty>
            <TableEmpty
              :is-loading="isLoading"
              :empty-type="tableEmptyConfig.emptyType"
              :abnormal="tableEmptyConfig.isAbnormal"
              @refresh="getList"
              @clear-filter="handleClearFilterKey"
            />
          </template>
        </BkTable>
      </BkLoading>
    </div>

    <!-- 新建/编辑 -->
    <AddComponentSlider
      v-model:slider-params="sliderConfig"
      v-model:detail-data="formData"
      :init-data="initData"
      :system-list="systemList"
      @sys-select="handleSysSelect"
      @confirm="handleConfirm"
    />
  </div>
</template>

<script lang="tsx" setup>
import { cloneDeep } from 'lodash-es';
import { Message, OverflowTitle, Table } from 'bkui-vue';
import type { ISearchValue } from 'bkui-lib/search-select/utils';
import {
  useMaxTableLimit,
  usePopInfoBox,
  useQueryList,
  useSelection,
} from '@/hooks';
import {
  type IComponentItem,
  checkEsbNeedNewVersion,
  deleteComponentByBatch,
  getComponentsDetail,
  getEsbComponents,
  getFeatures,
  getReleaseStatus,
} from '@/services/source/componentManagement';
import { getSystems } from '@/services/source/system';
import AddComponentSlider from './components/AddComponent.vue';
import RenderSystem from './components/RenderSystem.vue';
import TableEmpty from '@/components/table-empty/Index.vue';

type ISystemFilterMethod = {
  setSelected: (value: number) => void
  updateTableEmptyConfig: () => void
};

const router = useRouter();
const { t, locale } = useI18n();
const { maxTableLimit, clientHeight } = useMaxTableLimit({ allocatedHeight: 256 });
const {
  selections,
  handleSelectionChange,
  handleSelectAllChange,
  resetSelections,
} = useSelection();

const systemFilterRef = ref<InstanceType<typeof RenderSystem> & ISystemFilterMethod>();

const getDefaultData = () => {
  return {
    system_id: '',
    name: '',
    description: '',
    method: '',
    path: '',
    component_codename: '',
    permission_level: '',
    timeout: 30,
    is_active: true,
    config_fields: [],
    verified_user_required: true,
  };
};

const searchData = shallowRef([
  {
    name: t('组件名称'),
    id: 'name',
    placeholder: t('请输入组件名称'),
  },
  {
    name: t('请求路径'),
    id: 'path',
    placeholder: t('请输入请求路径'),
  },
]);
const comTableRef = ref<InstanceType<typeof Table> & { clearSelection: () => void }>();
const searchValue = ref([]);
const searchParams = ref({
  name: '',
  path: '',
});
const sliderConfig = ref({
  isShow: false,
  title: '',
});
const formData = ref(getDefaultData());
const needNewVersion = ref(false);
const syncEsbToApigwEnabled = ref(false);
const isReleasing = ref(false);
const isCursor = ref(false);
const isOverflow = ref(false);
const isExpand = ref(true);
const cursorId = ref('');
const curSelectSystemId = ref('*');
const systemList = ref([]);
const requestQueue = reactive(['system', 'component']);
const deleteDialogConf = reactive({
  loading: false,
  ids: [],
});
const tableEmptyConfig = reactive({
  emptyType: '',
  isAbnormal: false,
});
let initData = reactive({});

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList({
  apiMethod: getEsbComponents,
  filterData: searchParams,
  initialPagination: {
    limitList: [
      maxTableLimit,
      10,
      20,
      50,
      100,
    ],
    limit: maxTableLimit,
  },
  needApigwId: false,
});

const getTableColumns = computed(() => {
  const tableColumn = [
    {
      type: 'selection',
      width: 60,
      align: 'center',
    },
    {
      label: t('系统名称'),
      field: 'system_name',
      render: ({ row }: { row?: Partial<IComponentItem> }) => {
        return (
          <span>
            {row?.system_name || '--' }
          </span>
        );
      },
    },
    {
      label: t('组件名称'),
      field: 'name',
      showOverflowTooltip: true,
      render: ({ row }: { row?: Partial<IComponentItem> }) => {
        return (
          <div class="flex items-center">
            <div
              v-bk-tooltips={{
                placement: 'top',
                content: row?.name,
                disabled: !row?.name || !isOverflow.value,
              }}
              class="truncate"
            >
              { row?.name || '--' }
            </div>
            {
              syncEsbToApigwEnabled.value && row.is_created && (
                <div class={`ag-tag primary m-l-5px ${locale.value === 'en' ? 'min-w-56px' : 'min-w-44px'}`}>
                  { t('新创建') }
                </div>
              )
            }
            {
              syncEsbToApigwEnabled.value && row.has_updated && (
                <div class={`ag-tag success m-l-5px ${locale.value === 'en' ? 'min-w-56px' : 'min-w-44px'}`}>
                  { t('有更新') }
                </div>
              )
            }
          </div>
        );
      },
    },
    {
      label: t('请求方法'),
      field: 'method',
      width: 90,
      render: ({ row }: { row?: Partial<IComponentItem> }) => {
        return (
          <OverflowTitle type="tips">{ row.method || '--' }</OverflowTitle>
        );
      },
    },
    {
      label: t('请求路径'),
      field: 'path',
      render: ({ row }: { row?: Partial<IComponentItem> }) => {
        return (
          <OverflowTitle type="tips">{ row.path || '--' }</OverflowTitle>
        );
      },
    },
    {
      label: t('更新时间'),
      field: 'updated_time',
      width: 260,
    },
    {
      label: t('操作'),
      field: 'operate',
      fixed: 'right',
      width: 100,
      render: ({ row }: { row?: Partial<IComponentItem> }) => {
        return (
          <div>
            <BkButton
              class="m-r-10px"
              theme="primary"
              text
              onClick={() => handleEdit(row)}
            >
              { t('编辑') }
            </BkButton>
            <BkButton
              theme="primary"
              text
              disabled={row.is_official}
              onClick={() => handleDelete(row)}
            >
              {
                row.is_official
                  ? (
                    <span v-bk-tooltips={t('官方组件，不可删除')}>
                      { t('删除') }
                    </span>
                  )
                  : t('删除')
              }
            </BkButton>
          </div>
        );
      },
    },
  ];
  return tableColumn;
});

const handleSelect = ({ id }: { id: number }) => {
  curSelectSystemId.value = id;
  getSystemName(id);
  getList();
};

const setDefaultSelect = ({ row }: IComponentItem) => {
  return !row?.is_official;
};

const handleSysSelect = (
  value: number,
  option: {
    id: number
    name: string
  },
) => {
  const tempList = formData.value?.component_codename?.split('.');
  let customStr = '';
  if (tempList.length === 3) {
    [, , customStr] = tempList;
  }
  formData.value.component_codename = `generic.${option.lowerName}.${customStr}`;
  systemFilterRef.value?.setSelected(value);
};

const checkNeedNewVersion = async () => {
  const res = await checkEsbNeedNewVersion();
  needNewVersion.value = res?.need_new_release;
};

const getSystemList = async () => {
  try {
    const res = await getSystems();
    systemList.value = Object.freeze(res);
    // 获取组件是否需要发版本更新
    checkNeedNewVersion();
    // 子组件状态更新
    nextTick(() => {
      systemFilterRef.value?.updateTableEmptyConfig();
    });
  }
  finally {
    if (requestQueue.length > 0) {
      requestQueue.shift();
    }
  }
};

const handleConfirm = () => {
  resetSelections(comTableRef.value);
  getList();
  getSystemList();
};

const handleCreate = () => {
  let curSystemName = '';
  const curSystem = systemList.value?.find(({ id }: { id: string }) => id === curSelectSystemId.value);
  if (curSystem) {
    curSystemName = curSystem?.name?.toLocaleLowerCase();
  }
  formData.value = Object.assign(getDefaultData(), {
    id: 0,
    method: 'GET',
    permission_level: 'unlimited',
    system_id: curSelectSystemId.value === '*' ? '' : curSelectSystemId.value,
    component_codename: !curSystemName ? 'generic.{system_name}' : `generic.${curSystemName}.`,
  });
  sliderConfig.value = Object.assign({}, {
    isShow: true,
    loading: false,
    title: t('新建组件'),
  });
  initData = cloneDeep(formData.value);
};

const handleEdit = async (payload: IComponentItem) => {
  sliderConfig.value = Object.assign({}, {
    isShow: true,
    loading: true,
    title: t('编辑组件'),
  });
  try {
    const res = await getComponentsDetail(payload?.id);
    const configData = Object.assign({}, {
      ...res,
      method: res.method || '*',
      config_fields: res?.config_fields ?? [],
    });
    const keysToRemove = ['doc_link', 'system_name'];
    formData.value = Object.entries(configData).reduce((acc, [key, value]) => {
      if (!keysToRemove.includes(key)) acc[key] = value;
      return acc;
    }, {});
  }
  finally {
    sliderConfig.value.loading = false;
    initData = cloneDeep(formData.value);
  }
};

const handleConfirmDelete = () => {
  usePopInfoBox({
    isShow: true,
    title: t('确认删除？'),
    type: 'warning',
    subTitle: t('该操作不可恢复，是否继续？'),
    confirmText: t('删除'),
    confirmButtonTheme: 'danger',
    onConfirm: async () => {
      try {
        deleteDialogConf.loading = true;
        await deleteComponentByBatch({ ids: deleteDialogConf.ids });
        Message({
          message: t('删除成功'),
          theme: 'success',
        });
        selections.value = [];
        getList();
        getSystemList();
      }
      finally {
        deleteDialogConf.loading = false;
      }
    },
    onCancel: () => {
      deleteDialogConf.ids = [];
    },
  });
};

const handleBatchDelete = () => {
  deleteDialogConf.ids = selections.value?.map(item => item.id);
  handleConfirmDelete();
};

const handleDelete = ({ id }: { id: number }) => {
  deleteDialogConf.ids?.push(id);
  handleConfirmDelete();
};

const getStatus = async () => {
  try {
    const res = await getReleaseStatus();
    isReleasing.value = res?.is_releasing;
    if (isReleasing.value) {
      setTimeout(() => {
        getStatus();
      }, 5000);
    }
  }
  catch (e) {
    console.warn(e);
    return false;
  }
};

const handleNavRoute = (name: string) => {
  router.push({ name });
};

const handleRowEnter = (e, row) => {
  const truncateNode = e.target?.querySelector('.truncate');
  if (truncateNode) {
    isOverflow.value = truncateNode?.scrollWidth > truncateNode.clientWidth;
  }
  cursorId.value = row?.id;
  isCursor.value = true;
};

const handleRowLeave = () => {
  cursorId.value = '';
  isCursor.value = false;
  isOverflow.value = false;
};

const getFeature = async () => {
  const params = {
    limit: 10000,
    offset: 0,
  };
  const res = await getFeatures(params);
  syncEsbToApigwEnabled.value = res?.SYNC_ESB_TO_APIGW_ENABLED;
};

const handleClearFilterKey = () => {
  searchValue.value = [];
  getList();
};

const getSystemName = (id: number) => {
  if (id && id !== '*') {
    const curSystem = systemList.value?.find(item => item?.id === curSelectSystemId.value);
    searchParams.value.system_name = curSystem?.name;
  }
};

const updateTableEmptyConfig = () => {
  tableEmptyConfig.isAbnormal = pagination.value.abnormal;
  const filterParams = Object.values(searchParams.value).filter(item => item !== '');
  if (filterParams?.length && !tableData.value?.length) {
    tableEmptyConfig.emptyType = 'searchEmpty';
    return;
  }
  if (filterParams?.length) {
    tableEmptyConfig.emptyType = 'empty';
    return;
  }
  tableEmptyConfig.emptyType = '';
};

const init = () => {
  getSystemList();
  getStatus();
  getFeature();
};
init();

watch(
  () => searchValue.value,
  () => {
    searchParams.value = Object.assign(searchParams.value, {
      name: '',
      path: '',
      system_name: '',
    });
    searchValue.value.forEach((item: ISearchValue) => {
      searchParams.value[item.id] = item.values[0].id;
    });
    getSystemName(curSelectSystemId.value);
    updateTableEmptyConfig();
  },
  { deep: true },
);

watch(
  () => tableData.value, () => {
    updateTableEmptyConfig();
  },
  { deep: true },
);
</script>

<style lang="scss" scoped>
.apigw-access-manager-wrapper {
  background-color: #ffffff;

  &.app-content {
    min-height: calc(100vh - 104px);
    padding: 0;
  }

  .left-system-nav {
    position: relative;
    max-height: calc(100vh - 104px);
    background: #ffffff;
    width: 300px;

    &.is-expand {
      width: 0;

      .left-wrapper {
        width: 0;
      }

      .handle-icon i {
        transform: rotate(270deg);
      }
    }
  }

  .left-wrapper {
    padding: 10px 0;
    margin-right: 16px;
    width: 300px;
    overflow: hidden;
    height: 100%;
    background-color: #f6f7fb;
  }

  .handle-icon {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    right: -16px;
    width: 16px;
    height: 64px;
    background: #dcdee5;
    border-radius: 0 4px 4px 0;
    cursor: pointer;
    display: flex;
    align-items: center;

    i {
      display: inline-block;
      margin-left: -5px;
      font-size: 24px;
      color: #fff;
      transform: rotate(90deg);
    }
  }

  .action-wrapper {
    .bk-button {
      margin-right: 4px;
    }
  }

  .right-wrapper {
    padding: 0 10px;
    margin: 24px;
    width: calc(100% - 348px);

    &.is-expand {
      margin-left: 20px;
      width: calc(100% - 40px);
    }
  }

  .component-flex {
    .bk-search-select {
      width: 450px;
      background: #ffffff;
      margin-right: 10px;
    }

    .history-icon {
      cursor: pointer;
      display: inline-block;
      height: 32px;
      line-height: 32px;
      width: 30px;
      border: 1px solid #c4c6cc;
      border-radius: 2px;
      background-color: #ffffff;
      color: #979ba5;

      &:hover {
        border-color: #979ba5;
        color: #63656e;
      }
    }
  }

  .bk-table {
    .api-name,
    .docu-link {
      max-width: 200px;
      display: inline-block;
      word-break: break-all;
      overflow: hidden;
      white-space: nowrap;
      text-overflow: ellipsis;
      vertical-align: bottom;
    }

    .copy-icon {
      font-size: 14px;
      cursor: pointer;
      &:hover {
        color: #3a84ff;
      }
    }
  }
}

:deep(.path-wrapper) {
  position: relative;
  display: flex;
  width: 100%;

  .path-text {
    width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .path-icon {
    position: absolute;
    right: 0px;
    cursor: pointer;
    color: #3a84ff;
  }
}
</style>

<style>
.tippy-content {
  max-width: 550px;
}
</style>
