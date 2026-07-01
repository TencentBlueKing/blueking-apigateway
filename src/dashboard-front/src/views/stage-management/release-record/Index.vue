/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
  <div class="page-wrapper-padding publish-container">
    <div class="operate">
      <div class="flex items-center">
        <BkDatePicker
          :key="dateKey"
          v-model="dateValue"
          use-shortcut-text
          format="yyyy-MM-dd HH:mm:ss"
          clearable
          class="w-500px!"
          type="datetimerange"
          :placeholder="t('选择日期时间范围')"
          :shortcuts="shortcutsRange"
          :shortcut-selected-index="shortcutSelectedIndex"
          @change="handleChange"
          @shortcut-change="handleShortcutChange"
          @clear="handleClear"
          @pick-success="handlePickSuccess"
          @selection-mode-change="handleSelectionModeChange"
        />
      </div>
      <div class="flex justify-end">
        <BkInput
          v-model="filterData.keyword"
          :placeholder="t('请输入已发布的环境或版本号')"
          class="operate-input"
        />
      </div>
    </div>

    <AgTable
      ref="tableRef"
      show-settings
      show-cell-empty-content
      :api-method="getTableData"
      :columns="columns"
      @clear-filter="handleClearFilter"
    />

    <!-- 日志抽屉 -->
    <ReleaseStageEvent
      ref="logDetailsRef"
      :history-id="historyId"
      @release-success="handleReleaseSuccess"
    />

    <!-- 可编程网关日志抽屉 -->
    <ReleaseProgrammableEvent
      ref="programmableLogDetailsRef"
      :deploy-id="deployId"
      :history="currentHistory"
    />
  </div>
</template>

<script lang="tsx" setup>
import { useDatePicker } from '@/hooks';
import { Spinner } from 'bkui-vue/lib/icon';
import type { PrimaryTableProps, TableRowData } from '@blueking/tdesign-ui';
import { getReleaseHistories } from '@/services/source/release';
import {
  type IEventResponse,
  getDeployHistories,
} from '@/services/source/programmable';
import { useFeatureFlag, useGateway } from '@/stores';
import { t } from '@/locales';
import ReleaseStageEvent from '@/components/release-stage-event/Index.vue';
import ReleaseProgrammableEvent from '../components/ReleaseProgrammableEvent.vue';
import AgTable from '@/components/ag-table/Index.vue';
import CopyButton from '@/components/copy-button/Index.vue';

type Enums = typeof publishSourceEnum | typeof publishStatusEnum;

const router = useRouter();
const gatewayStore = useGateway();
const featureFlagStore = useFeatureFlag();

const filterData = ref({
  keyword: '',
  time_start: '',
  time_end: '',
});

// datepicker 时间选择器 hooks 适用于列表筛选
const {
  dateValue,
  shortcutsRange,
  shortcutSelectedIndex,
  handleChange,
  handleClear,
  handleConfirm,
  handleShortcutChange,
  handleSelectionModeChange,
} = useDatePicker(filterData);

const dateKey = ref('dateKey');

const tableRef = useTemplateRef('tableRef');

const publishSourceEnum = {
  gateway_enable: t('网关启用'),
  gateway_disable: t('网关停用'),
  version_publish: t('版本发布'),
  plugin_bind: t('插件绑定'),
  plugin_update: t('插件更新'),
  plugin_unbind: t('插件解绑'),
  stage_disable: t('环境下架'),
  stage_delete: t('环境删除'),
  stage_update: t('环境更新'),
  backend_update: t('服务更新'),
};
const publishStatusEnum = {
  success: t('执行成功'),
  failure: t('执行失败'),
  doing: t('执行中'),
};

const historyId = ref<number>();
const currentHistory = ref<IEventResponse>();
const deployId = ref<string>();
const logDetailsRef = ref();
const programmableLogDetailsRef = ref();

let timerId: any = null;

const apigwId = computed(() => gatewayStore.apigwId);
const isProgrammableGateway = computed(() => gatewayStore.isProgrammableGateway);
const columns = computed(() => {
  // 普通网关列
  const normalGatewayColumns: PrimaryTableProps['columns'] = [
    {
      title: t('已发布的环境'),
      colKey: 'stage.name',
      ellipsis: true,
    },
    {
      colKey: 'type',
      title: t('类型'),
      ellipsis: true,
      cell: (_: unknown, { row }: { row: TableRowData }) => (
        <span>{getTextFromEnum(publishSourceEnum, row.source)}</span>
      ),
    },
    {
      colKey: 'version',
      title: t('版本号'),
      ellipsis: true,
      width: 200,
      cell: (_: unknown, { row }: { row: TableRowData }) => (
        <span
          class="color-#3a84ff cursor-pointer"
          onClick={() => goVersionList(row)}
        >
          {row.resource_version_display}
        </span>
      ),
    },
    {
      colKey: 'status',
      title: t('操作状态'),
      cell: (_: unknown, { row }: { row: TableRowData }) => (
        <div>
          {
            row?.status === 'doing'
              ? <Spinner fill="#3a84ff" />
              : <span class={`dot ${row?.status}`}></span>
          }
          <span>{getTextFromEnum(publishStatusEnum, row?.status)}</span>
        </div>
      ),
    },
    {
      title: t('操作时间'),
      colKey: 'created_time',
      width: 260,
    },
    {
      colKey: 'created_by',
      title: t('操作人'),
      cell: (h: unknown, { row }: { row: TableRowData }) => {
        return (
          !featureFlagStore.isEnableDisplayName
            ? <span>{row.created_by || '--'}</span>
            : <span><bk-user-display-name user-id={row.created_by} /></span>
        );
      },
    },
    {
      title: t('耗时'),
      colKey: 'duration',
      ellipsis: true,
    },
    {
      colKey: 'actions',
      title: t('操作'),
      fixed: 'right' as const,
      cell: (_: unknown, { row }: { row: TableRowData }) => (
        <bk-button text theme="primary" onClick={() => showLogs(row.id)}>
          {t('发布日志')}
        </bk-button>
      ),
    },
  ];

  // 可编程网关列
  const programmableGatewayColumns: PrimaryTableProps['columns'] = [
    {
      title: t('已发布的环境'),
      colKey: 'stage.name',
      ellipsis: true,
    },
    {
      colKey: 'type',
      title: t('类型'),
      ellipsis: true,
      cell: (_: unknown, { row }: { row: TableRowData }) => (
        <span>{getTextFromEnum(publishSourceEnum, row.source)}</span>
      ),
    },
    {
      title: t('分支'),
      colKey: 'branch',
      ellipsis: true,
    },
    {
      title: 'commit_id',
      colKey: 'commit_id',
      cell: (_: unknown, { row }: { row: TableRowData }) => (
        <div v-bk-tooltips={row?.commit_id}>
          { row?.commit_id ? (row.commit_id.length > 8 ? `${row.commit_id.slice(0, 8)}...` : row.commit_id) : '--' }
          <CopyButton class="ml-4px" source={row?.commit_id} />
        </div>
      ),
    },
    {
      title: t('版本号'),
      colKey: 'version',
      ellipsis: true,
      width: 200,
    },
    {
      colKey: 'deployStatus',
      title: t('部署状态'),
      cell: (_: unknown, { row }: { row: TableRowData }) => (
        <div>
          {
            row?.status === 'doing'
              ? <Spinner fill="#3a84ff" />
              : <span class={`dot ${row?.status}`}></span>
          }
          <span>{getTextFromEnum(publishStatusEnum, row?.status)}</span>
        </div>
      ),
    },
    {
      title: t('操作时间'),
      colKey: 'created_time',
      width: 260,
    },
    {
      colKey: 'created_by',
      title: t('操作人'),
      ellipsis: true,
      cell: (h: unknown, { row }: { row: TableRowData }) => {
        return (
          !featureFlagStore.isEnableDisplayName
            ? <span>{row.created_by || '--'}</span>
            : <span><bk-user-display-name user-id={row.created_by} /></span>
        );
      },
    },
    {
      colKey: 'actions',
      title: t('操作'),
      fixed: 'right' as const,
      cell: (_: unknown, { row }: { row: TableRowData }) => (
        <bk-button text theme="primary" disabled={!row.deploy_id} onClick={() => showLogs(row.deploy_id, row)}>
          {t('发布日志')}
        </bk-button>
      ),
    },
  ];

  return isProgrammableGateway.value ? programmableGatewayColumns : normalGatewayColumns;
});

watch(() => isProgrammableGateway.value, () => {
  clearInterval(timerId);
  timerId = setInterval(() => {
    tableRef.value!.fetchData(filterData.value);
  }, 1000 * 30);
}, { immediate: true });

watch(filterData, () => {
  tableRef.value!.fetchData(filterData.value);
}, { deep: true });

const getTableData = async (params: Record<string, any> = {}) =>
  isProgrammableGateway.value
    ? getDeployHistories(apigwId.value, params)
    : getReleaseHistories(apigwId.value, params);

const showLogs = (id: number | string, row?: TableRowData) => {
  // 可编程网关
  if (isProgrammableGateway.value) {
    deployId.value = id as string;
    currentHistory.value = row as IEventResponse;
    programmableLogDetailsRef.value?.showSideslider();
  }
  else {
    // 普通网关
    historyId.value = id as number;
    currentHistory.value = undefined;
    logDetailsRef.value?.showSideslider();
  }
};

const handleClearFilter = () => {
  filterData.value = {
    keyword: '',
    time_start: '',
    time_end: '',
  };
  dateValue.value = [];
  shortcutSelectedIndex.value = -1;
  dateKey.value = String(+new Date());
  tableRef.value!.fetchData(filterData.value, { resetPage: true });
};

const goVersionList = (data: any) => {
  router.push({
    name: 'ResourceVersion',
    query: { version: data?.resource_version_display },
  });
};

// 从枚举对象中获取文本
const getTextFromEnum = (e: Enums, key?: unknown) => {
  if (!key) return '--';
  return e[key as keyof Enums];
};

const handlePickSuccess = () => {
  handleConfirm();
};

const handleReleaseSuccess = () => {
  tableRef.value!.fetchData(filterData.value);
};

onUnmounted(() => {
  clearInterval(timerId);
});

</script>

<style lang="scss" scoped>
.publish-container{

  .operate{
    display: flex;
    margin-bottom: 20px;

    .operate-input {
      width: 500px;
      margin-inline: 10px;
    }
  }
}
</style>
