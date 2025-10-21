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
      resizable
      :api-method="getTableData"
      :columns="columns"
      @clear-filter="handleClearFilter"
    />

    <!-- 日志抽屉 -->
    <ReleaseStageEvent
      ref="logDetailsRef"
      :history-id="historyId"
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
import { getReleaseHistories } from '@/services/source/release';
import {
  type IEventResponse,
  getDeployHistories,
} from '@/services/source/programmable';
import { useFeatureFlag, useGateway } from '@/stores';
import ReleaseStageEvent from '@/components/release-stage-event/Index.vue';
import ReleaseProgrammableEvent from '../components/ReleaseProgrammableEvent.vue';
import EditMember from '@/views/basic-info/components/EditMember.vue';
import TenantUserSelector from '@/components/tenant-user-selector/Index.vue';
import { t } from '@/locales';
import AgTable from '@/components/ag-table/Index.vue';
import type { PrimaryTableProps } from '@blueking/tdesign-ui';

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

const columns = computed<PrimaryTableProps['columns']>(() =>
  gatewayStore.isProgrammableGateway
    ? [
      {
        title: t('已发布的环境'),
        colKey: 'stage.name',
      },
      {
        colKey: 'type',
        title: t('类型'),
        width: 100,
        cell: (h, { row }: any) => <div>{getTextFromEnum(publishSourceEnum, row.source)}</div>,
      },
      {
        title: t('分支'),
        colKey: 'branch',
      },
      {
        title: 'commit_id',
        colKey: 'commit_id',
      },
      {
        title: t('版本号'),
        colKey: 'version',
      },
      {
        colKey: 'deployStatus',
        title: t('部署状态'),
        width: 120,
        cell: (h, { row }: any) => (
          <div>
            {
              row?.status === 'doing'
                ? <Spinner fill="#3A84FF" />
                : <span class={`dot ${row?.status}`}></span>
            }
            <span>{getTextFromEnum(publishStatusEnum, row?.status)}</span>
          </div>
        ),
      },
      {
        title: t('操作时间'),
        colKey: 'created_time',
      },
      {
        colKey: 'operator',
        title: t('操作人'),
        cell: (h, { row }: any) => (
          <div>
            {
              !featureFlagStore.isEnableDisplayName
                ? (
                  <EditMember
                    mode="detail"
                    width="600px"
                    field="created_by"
                    content={[row?.created_by]}
                  />
                )
                : (
                  <TenantUserSelector
                    mode="detail"
                    width="600px"
                    field="created_by"
                    content={[row?.created_by]}
                  />
                )
            }
          </div>
        ),
      },
      {
        colKey: 'actions',
        title: t('操作'),
        cell: (h, { row }: any) => (
          <bk-button text theme="primary" disabled={!row.deploy_id} onClick={() => showLogs(row.deploy_id, row)}>
            {t('发布日志')}
          </bk-button>
        ),
      },
    ]
    : [
      {
        title: t('已发布的环境'),
        colKey: 'stage.name',
      },
      {
        colKey: 'type',
        title: t('类型'),
        cell: (h, { row }: any) => <div>{getTextFromEnum(publishSourceEnum, row.source)}</div>,
      },
      {
        colKey: 'version',
        title: t('版本号'),
        cell: (h, { row }: any) => (
          <bk-button
            text
            theme="primary"
            onClick={() => goVersionList(row)}
          >
            {row.resource_version_display}
          </bk-button>
        ),
      },
      {
        colKey: 'actionStatus',
        title: t('操作状态'),
        cell: (h, { row }: any) => (
          <div>
            {
              row?.status === 'doing'
                ? <Spinner fill="#3A84FF" />
                : <span class={`dot ${row?.status}`}></span>
            }
            <span>{getTextFromEnum(publishStatusEnum, row?.status)}</span>
          </div>
        ),
      },
      {
        title: t('操作时间'),
        colKey: 'created_time',
      },
      {
        colKey: 'operator',
        title: t('操作人'),
        cell: (h, { row }: any) => (
          <div>
            {
              !featureFlagStore.isEnableDisplayName
                ? (
                  <EditMember
                    mode="detail"
                    width="600px"
                    field="created_by"
                    content={[row?.created_by]}
                  />
                )
                : (
                  <TenantUserSelector
                    mode="detail"
                    width="600px"
                    field="created_by"
                    content={[row?.created_by]}
                  />
                )
            }
          </div>
        ),
      },
      {
        title: t('耗时'),
        colKey: 'duration',
      },
      {
        colKey: 'actions',
        title: t('操作'),
        cell: (h, { row }: any) => (
          <bk-button text theme="primary" onClick={() => showLogs(row.id)}>
            {t('发布日志')}
          </bk-button>
        ),
      },
    ],
);

watch(() => gatewayStore.isProgrammableGateway, () => {
  clearInterval(timerId);
  timerId = setInterval(() => {
    tableRef.value!.fetchData(filterData.value);
  }, 1000 * 30);
}, { immediate: true });

watch(filterData, () => {
  tableRef.value!.fetchData(filterData.value);
}, { deep: true });

const getTableData = async (params: Record<string, any> = {}) =>
  gatewayStore.isProgrammableGateway
    ? getDeployHistories(apigwId.value, params)
    : getReleaseHistories(apigwId.value, params);

const showLogs = (id: number | string, row?: IEventResponse) => {
  // 可编程网关
  if (gatewayStore.isProgrammableGateway) {
    deployId.value = id as string;
    currentHistory.value = row;
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
