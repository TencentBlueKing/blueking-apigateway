<template>
  <div class="app-content apigw-access-manager-wrapper">
    <div class="wrapper">
      <bk-form form-type="inline">
        <bk-form-item :label="$t('选择时间')">
          <bk-date-picker
            ref="topDatePicker"
            style="width: 320px;"
            v-model="dateTimeRange"
            :placeholder="$t('选择日期时间范围')"
            :type="'datetimerange'"
            :shortcuts="datepickerShortcuts"
            :shortcut-close="true"
            :use-shortcut-text="true"
            :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange"
            @clear="handleTimeClear"
            @pick-success="handleTimeChange">
          </bk-date-picker>
        </bk-form-item>
      </bk-form>
      <ag-loader
        :offset-top="0"
        :offset-left="0"
        loader="stage-loader"
        :is-loading="false">
        <bk-table
          style="margin-top: 16px;"
          :data="componentList"
          size="small"
          :pagination="pagination"
          v-bkloading="{ isLoading, opacity: 1 }"
          remote-pagination
          @page-value-change="handlePageChange"
          @page-limit-change="handlePageLimitChange">
          <template #empty>
            <div>
              <table-empty
                :keyword="tableEmptyConf.keyword"
                :abnormal="tableEmptyConf.isAbnormal"
                @reacquire="getComponents(true)"
                @clear-filter="clearFilterKey"
              />
            </div>
          </template>

          <bk-table-column label="ID" prop="resource_version_title">
            <template #default="{ data }">
              <bk-button theme="primary" class="mr10" text @click="handleVersion(data?.id)">
                {{data?.id || '--'}}
              </bk-button>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('同步时间')" prop="created_time"></bk-table-column>
          <bk-table-column :label="$t('同步版本号（版本标题）')" prop="resource_version_name">
            <template #default="{ data }">
              {{data?.resource_version_display || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('操作人')" prop="component_name">
            <template #default="{ data }">
              {{data?.created_by || '--'}}
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('操作结果')">
            <template #default="{ data }">
              <template v-if="data?.status === 'releasing'">
                <round-loading />
                {{ $t('同步中') }}
              </template>
              <template v-else>
                <span :class="`ag-dot ${data?.status} mr5`"></span> {{ statusMap[data?.status] }}
              </template>
            </template>
          </bk-table-column>
          <bk-table-column :label="$t('操作日志')" prop="message"></bk-table-column>
        </bk-table>
      </ag-loader>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import { getSyncHistory } from '@/http';

const router = useRouter();
const { t } = useI18n();

const datepickerShortcuts = [
  {
    text: t('最近5分钟'),
    value() {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 5 * 60 * 1000);
      return [start, end];
    },
  },
  {
    text: t('最近1小时'),
    value() {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 60 * 60 * 1000);
      return [start, end];
    },
  },
  {
    text: t('最近6小时'),
    value() {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 6 * 60 * 60 * 1000);
      return [start, end];
    },
  },
  {
    text: t('最近12小时'),
    value() {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 12 * 60 * 60 * 1000);
      return [start, end];
    },
  },
  {
    text: t('最近1天'),
    value() {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 24 * 60 * 60 * 1000);
      return [start, end];
    },
  },
  {
    text: t('最近7天'),
    value() {
      const end = new Date();
      const start = new Date();
      start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
      return [start, end];
    },
  },
];

const STATUS_MAP = {
  success: t('成功'),
  failure: t('失败'),
  pending: t('待同步'),
  releasing: t('同步中'),
};

const topDatePicker = ref();

const componentList = ref<any>([]);
const pagination = reactive<any>({
  current: 1,
  count: 0,
  limit: 10,
});
const requestQueue = reactive<any>(['component']);
const isLoading = ref<boolean>(false);
const dateTimeRange = ref<any>([]);
const shortcutSelectedIndex = ref<number>(-1);
const searchParams = ref<any>({ time_start: '', time_end: '' });
const statusMap = ref<any>(STATUS_MAP);
const tableEmptyConf = ref<any>({
  keyword: '',
  isAbnormal: false,
});


const formatDatetime = (timeRange: any) => {
  if (!timeRange[0] || !timeRange[1]) {
    return [];
  }
  return [
    (+new Date(`${timeRange[0]}`)) / 1000,
    (+new Date(`${timeRange[1]}`)) / 1000,
  ];
};

const setSearchTimeRange = () => {
  let timeRange = dateTimeRange.value;

  // 选择的是时间快捷项，需要实时计算时间值
  if (shortcutSelectedIndex.value !== -1) {
    timeRange = datepickerShortcuts[shortcutSelectedIndex.value].value();
  }

  if (timeRange?.length) {
    const formatTimeRange = formatDatetime(timeRange);
    searchParams.value.time_start = formatTimeRange[0] || '';
    searchParams.value.time_end = formatTimeRange[1] || '';
  }
};

const updateTableEmptyConfig = () => {
  const isEmpty = dateTimeRange.value?.some(Boolean);
  if (isEmpty) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const getComponents = async (loading = false) => {
  isLoading.value = loading;
  setSearchTimeRange();
  const pageParams = {
    limit: pagination.limit,
    offset: pagination.limit * (pagination.current - 1),
    ...searchParams.value,
  };
  try {
    const res = await getSyncHistory(pageParams);
    pagination.count = res?.count;
    componentList.value = res?.results;
    updateTableEmptyConfig();
    tableEmptyConf.value.isAbnormal = false;
  } catch (e) {
    tableEmptyConf.value.isAbnormal = true;
    console.log(e);
  } finally {
    if (requestQueue?.length > 0) {
      requestQueue?.shift();
    }
    isLoading.value = false;
  }
};

const handlePageLimitChange = (limit: number) => {
  pagination.limit = limit;
  pagination.current = 1;
  getComponents();
};

const handlePageChange = (page: number) => {
  pagination.current = page;
  getComponents();
};

const handleVersion = (id: string) => {
  router.push({
    name: 'syncVersion',
    query: { id },
  });
};

const handleShortcutChange = (value: string, index: number) => {
  shortcutSelectedIndex.value = index;
};

const handleTimeClear = () => {
  pagination.current = 1;
  shortcutSelectedIndex.value = -1;
  nextTick(() => {
    getComponents();
  });
};

const handleTimeChange = () => {
  pagination.current = 1;
  nextTick(() => {
    getComponents();
  });
};

const clearFilterKey = () => {
  dateTimeRange.value = [];
  topDatePicker.value?.handleClear();
};

const init = () => {
  getComponents();
};

// watch(
//   () => requestQueue,
//   (value) => {
//     if (value?.length < 1) {
//       this.$store.commit('setMainContentLoading', false);
//     }
//   },
// );

init();

</script>

<style lang="scss" scoped>
.apigw-access-manager-wrapper {
  display: flex;
  justify-content: flex-start;
  .wrapper {
    padding: 0 10px;
    width: 100%;
  }
  .search-wrapper {
    display: flex;
    justify-content: space-between;
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
.apigw-access-manager-slider-cls {
  .tips {
    line-height: 24px;
    font-size: 12px;
    color: #63656e;
    i {
      position: relative;
      top: -1px;
      margin-right: 3px;
    }
  }
  .timeout-append {
    width: 36px;
    font-size: 12px;
    text-align: center;
  }
}

.ag-flex {
  display: flex;
}
.ag-auto-text {
  vertical-align: middle;
}
.ag-tag.success {
  width: 44px;
}
</style>
