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
          :shortcuts="shortcutsRange"
          clearable
          class="w-500px!"
          type="datetimerange"
          :shortcut-selected-index="shortcutSelectedIndex"
          @change="handleChange"
          @clear="handleClear"
          @pick-success="handlePickSuccess"
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
    <BkLoading :loading="isLoading">
      <BkTable
        class="table-layout"
        :data="tableData"
        remote-pagination
        :pagination="pagination"
        show-overflow-tooltip
        :columns="columns"
        border="outer"
        row-hover="auto"
        @page-limit-change="handlePageSizeChange"
        @page-value-change="handlePageChange"
      >
        <template #empty>
          <TableEmpty
            :empty-type="tableEmptyConf.emptyType"
            :abnormal="tableEmptyConf.isAbnormal"
            @refresh="getList"
            @clear-filter="handleClearFilterKey"
          />
        </template>
      </BkTable>
    </BkLoading>

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
import {
  useDatePicker,
  useQueryList,
} from '@/hooks';
import { Spinner } from 'bkui-vue/lib/icon';
import { getReleaseHistories } from '@/services/source/release';
import TableEmpty from '@/components/table-empty/Index.vue';
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

type Enums = typeof publishSourceEnum | typeof publishStatusEnum;

const router = useRouter();
const gatewayStore = useGateway();
const featureFlagStore = useFeatureFlag();

const filterData = ref({
  keyword: '',
  time_start: '',
  time_end: '',
});

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList(
  {
    apiMethod: gatewayStore.isProgrammableGateway ? getDeployHistories : getReleaseHistories,
    filterData,
    filterNoResetPage: false,
    immediate: false,
  },
);

// datepicker 时间选择器 hooks 适用于列表筛选
const {
  shortcutsRange,
  dateValue,
  handleChange,
  handleClear,
  handleConfirm,
} = useDatePicker(filterData);

const shortcutSelectedIndex = ref(-1);
const dateKey = ref('dateKey');

const tableEmptyConf = ref({
  emptyType: '',
  isAbnormal: false,
});

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
  success: '执行成功',
  failure: '执行失败',
  doing: '执行中',
};

const historyId = ref<number>();
const currentHistory = ref<IEventResponse>();
const deployId = ref<string>();
const logDetailsRef = ref();
const programmableLogDetailsRef = ref();

let timerId: any = null;

const columns = computed(() =>
  gatewayStore.isProgrammableGateway
    ? [
      {
        label: t('已发布的环境'),
        field: 'stage.name',
      },
      {
        label: t('类型'),
        width: 100,
        render: ({ row }: any) => <div>{getTextFromEnum(publishSourceEnum, row.source)}</div>,
      },
      {
        label: t('分支'),
        field: 'branch',
      },
      {
        label: 'commit_id',
        field: 'commit_id',
      },
      {
        label: t('版本号'),
        field: 'version',
      },
      {
        label: t('部署状态'),
        width: 120,
        render: ({ row }: any) => (
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
        label: t('操作时间'),
        field: 'created_time',
      },
      {
        label: t('操作人'),
        render: ({ row }: any) => (
          <div>
            {
              !featureFlagStore.isTenantMode
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
        label: t('操作'),
        render: ({ row }: any) => (
          <BkButton text theme="primary" disabled={!row.deploy_id} onClick={() => showLogs(row.deploy_id, row)}>
            {t('发布日志')}
          </BkButton>
        ),
      },
    ]
    : [
      {
        label: t('已发布的环境'),
        field: 'stage.name',
      },
      {
        label: t('类型'),
        render: ({ row }: any) => <div>{getTextFromEnum(publishSourceEnum, row.source)}</div>,
      },
      {
        label: t('版本号'),
        render: ({ row }: any) => (
          <BkButton
            text
            theme="primary"
            onClick={() => goVersionList(row)}
          >
            {row.resource_version_display}
          </BkButton>
        ),
      },
      {
        label: t('操作状态'),
        render: ({ row }: any) => (
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
        label: t('操作时间'),
        field: 'created_time',
      },
      {
        label: t('操作人'),
        render: ({ row }: any) => (
          <div>
            {
              !featureFlagStore.isTenantMode
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
        label: t('耗时'),
        field: 'duration',
      },
      {
        label: t('操作'),
        render: ({ row }: any) => (
          <BkButton text theme="primary" onClick={() => showLogs(row.id)}>
            {t('发布日志')}
          </BkButton>
        ),
      },
    ],
);

watch(tableData, () => {
  updateTableEmptyConfig();
}, { deep: true });

watch(() => gatewayStore.isProgrammableGateway, () => {
  if (gatewayStore.isProgrammableGateway) {
    getList(getDeployHistories);
  }
  else {
    getList(getReleaseHistories);
  }
  clearInterval(timerId);
  timerId = setInterval(() => {
    getList(gatewayStore.isProgrammableGateway ? getDeployHistories : getReleaseHistories, false);
  }, 1000 * 30);
}, { immediate: true });

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

const handleClearFilterKey = () => {
  filterData.value = Object.assign(filterData.value, {
    keyword: '',
    time_start: '',
    time_end: '',
  });
  dateValue.value = [];
  shortcutSelectedIndex.value = -1;
  dateKey.value = String(+new Date());
  getList();
  updateTableEmptyConfig();
};

const updateTableEmptyConfig = () => {
  tableEmptyConf.value.isAbnormal = pagination.value.abnormal;
  const isSearch = dateValue.value.length > 0 || filterData.value.keyword;
  if (isSearch && !tableData.value.length) {
    tableEmptyConf.value.emptyType = 'searchEmpty';
    return;
  }
  if (isSearch) {
    tableEmptyConf.value.emptyType = 'empty';
    return;
  }
  tableEmptyConf.value.emptyType = '';
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

  .table-layout {

    :deep(.bk-table-head) {
      padding-right: 0;
      scrollbar-color: transparent transparent;
    }

    :deep(.bk-table-body) {
      scrollbar-color: transparent transparent;
    }
  }
}
</style>
