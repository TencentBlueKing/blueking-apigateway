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
            :keyword="tableEmptyConf.keyword"
            :abnormal="tableEmptyConf.isAbnormal"
            @reacquire="getList"
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
import { useGateway } from '@/stores';
import ReleaseStageEvent from '@/components/release-stage-event/Index.vue';
import ReleaseProgrammableEvent from '../components/ReleaseProgrammableEvent.vue';

type Enums = typeof publishSourceEnum | typeof publishStatusEnum;

const { t } = useI18n();
const router = useRouter();
const gatewayStore = useGateway();

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
  handleComfirm,
} = useDatePicker(filterData);

const shortcutSelectedIndex = ref(-1);
const dateKey = ref('dateKey');

const tableEmptyConf = ref({
  keyword: '',
  isAbnormal: false,
});

const publishSourceEnum = {
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
        field: 'created_by',
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
        field: 'created_by',
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

watch(() => filterData.value, () => {
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
    query: { version: data?.resource_version_display },
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
