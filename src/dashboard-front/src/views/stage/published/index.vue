<template>
  <div class="page-wrapper-padding publish-container">
    <div class="operate flex-row mb20">
      <div class="flex-row align-items-center">
        <bk-date-picker
          ref="datePickerRef"
          use-shortcut-text
          format="yyyy-MM-dd HH:mm:ss"
          :shortcuts="shortcutsRange"
          clearable
          v-model="dateValue"
          style="width: 500px"
          type="datetimerange"
          :shortcut-selected-index="shortcutSelectedIndex"
          :key="dateKey"
          @change="handleChange"
          @clear="handleClear"
          @pick-success="handlePickSuccess">
        </bk-date-picker>
      </div>
      <div class="flex-row justify-content-end">
        <bk-input
          v-model="filterData.keyword"
          :placeholder="t('请输入已发布的环境或版本号')"
          class="ml10 mr10 operate-input"
          style="width: 500px"
<<<<<<< HEAD
        />
=======
          :placeholder="t('请输入已发布的环境或版本号')"
          v-model="filterData.keyword">
        </bk-input>
>>>>>>> ft_tenant
      </div>
    </div>
    <bk-loading :loading="isLoading">
      <bk-table
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
<<<<<<< HEAD
      >
=======
        row-hover="auto"
        border="outer">
        <bk-table-column
          :label="t('已发布的环境')"
          prop="stage.name"
        >
        </bk-table-column>
        <bk-table-column :label="t('类型')">
          <template #default="{ data }">
            {{ getTextFromEnum(publishSourceEnum, data?.source) }}
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('版本号')"
          prop="resource_version_display"
        >
          <template #default="{ row }">
            <bk-button text theme="primary" @click="goVersionList(row)">
              {{ row?.resource_version_display }}
            </bk-button>
          </template>
        </bk-table-column>
        <bk-table-column :label="t('操作状态')">
          <template #default="{ data }">
            <spinner v-if="data?.status === 'doing'" fill="#3A84FF" />
            <span v-else :class="['dot', data?.status]"></span>
            {{ getTextFromEnum(publishStatusEnum, data?.status) }}
          </template>
        </bk-table-column>
        <bk-table-column :label="t('操作时间')" prop="created_time">
        </bk-table-column>
        <bk-table-column :label="t('操作人')">
          <template #default="{ row }">
            <bk-user-display-name :user-id="row.created_by" />
          </template>
        </bk-table-column>
        <bk-table-column :label="t('耗时')" prop="duration">
        </bk-table-column>
        <bk-table-column :label="t('操作')">
          <template #default="{ data }">
            <!-- <bk-button text theme="primary" @click="showDetails(data.id)">
              {{ t("查看详情") }}
            </bk-button> -->
            <bk-button text theme="primary" @click="showLogs(data.id)">
              {{ t("发布日志") }}
            </bk-button>
          </template>
        </bk-table-column>
>>>>>>> ft_tenant
        <template #empty>
          <TableEmpty
            :keyword="tableEmptyConf.keyword"
            :abnormal="tableEmptyConf.isAbnormal"
            @reacquire="getList"
            @clear-filter="handleClearFilterKey"
          />
        </template>
      </bk-table>
    </bk-loading>

    <!-- 日志抽屉 -->
    <log-details ref="logDetailsRef" :history-id="historyId" />

    <!-- 可编程网关日志抽屉 -->
    <EventSlider
      ref="programmableLogDetailsRef"
      :deploy-id="deployId"
      :history="currentHistory"
    />

    <!-- 详情 -->
    <publish-details ref="detailsRef" :id="detailId" />
  </div>
</template>

<<<<<<< HEAD
<script lang="tsx" setup>
import {
  computed,
=======
<script setup lang="ts">
import {
  onMounted,
>>>>>>> ft_tenant
  onUnmounted,
  ref,
  watch,
} from 'vue';
import { useRouter } from 'vue-router';

import {
  useDatePicker,
  useQueryList,
} from '@/hooks';
import { useI18n } from 'vue-i18n';
import logDetails from '@/components/log-details/index.vue';
import publishDetails from './comps/publish-details.vue';
import { Spinner } from 'bkui-vue/lib/icon';
import { getReleaseHistories } from '@/http';
import TableEmpty from '@/components/table-empty.vue';
import EventSlider from '@/components/programmable-deploy-events-slider/index.vue';
import { useCommon } from '@/store';
import {
  getDeployHistories,
  type IEventResponse,
} from '@/http/programmable';

type Enums = typeof publishSourceEnum | typeof publishStatusEnum;

const { t } = useI18n();
const router = useRouter();
const common = useCommon();

const filterData = ref({
  keyword: '',
  time_start: '',
  time_end: '',
});
const tableEmptyConf = ref<{keyword: string, isAbnormal: boolean}>({
  keyword: '',
  isAbnormal: false,
});
const shortcutSelectedIndex = ref(-1);
const datePickerRef = ref(null);
const dateKey = ref('dateKey');
const publishSourceEnum = Object.freeze({
  gateway_enable: '网关启用',
  gateway_disable: '网关停用',
  version_publish: '版本发布',
  plugin_bind: '插件绑定',
  plugin_update: '插件更新',
  plugin_unbind: '插件解绑',
  stage_disable: '环境下架',
  stage_delete: '环境删除',
  stage_update: '环境更新',
  backend_update: '服务更新',
});
const publishStatusEnum = Object.freeze({
  success: '执行成功',
  failure: '执行失败',
  doing: '执行中',
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
  common.isProgrammableGateway ? getDeployHistories : getReleaseHistories,
  filterData,
  null,
  false,
  undefined,
  false,
);

// datepicker 时间选择器 hooks 适用于列表筛选
const {
  shortcutsRange,
  dateValue,
  handleChange,
  handleClear,
  handleComfirm,
} = useDatePicker(filterData);

const historyId = ref<number>();
const currentHistory = ref<IEventResponse>();
const deployId = ref<string>();
const logDetailsRef = ref(null);
const programmableLogDetailsRef = ref(null);
const detailId = ref();
const detailsRef = ref(null);

let timerId: any = null;

const columns = computed(() =>
  common.isProgrammableGateway
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
        render: ({ row }: any) =>
          <div>
            {
              row?.status === 'doing'
              ? <Spinner fill="#3A84FF" />
              : <span class={`dot ${row?.status}`}></span>
            }
            <span>{getTextFromEnum(publishStatusEnum, row?.status)}</span>
          </div>,
      },
      {
        label: t('操作时间'),
        field: 'created_time',
      },
      {
        label: t('操作人'),
        field: 'created_by',
      },
      {
        label: t('操作'),
        render: ({ row }: any) =>
          <bk-button text theme="primary" disabled={!row.deploy_id} onClick={() => showLogs(row.deploy_id, row)}>
            {t("发布日志")}
          </bk-button>,
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
        render: ({ row }: any) => <bk-button
          text theme="primary" onClick={() => goVersionList(row)}
        >{row.resource_version_display}</bk-button>,
      },
      {
        label: t('操作状态'),
        render: ({ row }: any) =>
          <div>
            {
              row?.status === 'doing'
              ? <Spinner fill="#3A84FF" />
              : <span class={`dot ${row?.status}`}></span>
            }
            <span>{getTextFromEnum(publishStatusEnum, row?.status)}</span>
          </div>,
      },
      {
        label: t('操作时间'),
        field: 'created_time',
      },
      {
        label: t('操作人'),
        field: 'created_by',
      },
      {
        label: t('耗时'),
        field: 'duration',
      },
      {
        label: t('操作'),
        render: ({ row }: any) =>
          <bk-button text theme="primary" onClick={() => showLogs(row.id)}>
            {t("发布日志")}
          </bk-button>,
      },
    ],
);

watch(() => filterData.value, () => {
  updateTableEmptyConfig();
}, {
  deep: true,
});

watch(() => common.isProgrammableGateway, () => {
  if (common.isProgrammableGateway) {
    getList(getDeployHistories);
  } else {
    getList(getReleaseHistories);
  }
  clearInterval(timerId);
  timerId = setInterval(() => {
    getList(common.isProgrammableGateway ? getDeployHistories : getReleaseHistories, false);
  }, 1000 * 30);
}, { immediate: true });

const showLogs = (id: number | string, row?: IEventResponse) => {
  // 可编程网关
  if (common.isProgrammableGateway) {
    deployId.value = id as string;
    currentHistory.value = row;
    programmableLogDetailsRef.value?.showSideslider();
  } else {
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
  if (isSearch || !tableData.value.length) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (isSearch) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const goVersionList = (data: any) => {
  router.push({
    name: 'apigwResourceVersion',
    query: {
      version: data?.resource_version_display,
    },
  });
};

// 从枚举对象中获取文本
const getTextFromEnum = (e: Enums, key?: unknown) => {
  if (!key) return '--';
  return t(e[key as keyof Enums]);
};

const handlePickSuccess = () => {
  handleComfirm();
};

onUnmounted(() => {
  clearInterval(timerId);
});

</script>

<style lang="scss" scoped>
.publish-container{
  .operate{
    &-input{
      width: 450px;
    }
  }
  .table-layout{
    :deep(.bk-table-head) {
      // scrollbar-gutter: auto;
      padding-right: 0;
      scrollbar-color: transparent transparent;
    }
    :deep(.bk-table-body) {
      // scrollbar-gutter: auto;
      // #fafbfd
      scrollbar-color: transparent transparent;
    }
  }
}
</style>
