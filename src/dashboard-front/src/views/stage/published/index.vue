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
          class="ml10 mr10 operate-input"
          style="width: 500px"
          placeholder="请输入已发布的环境或版本号"
          v-model="filterData.keyword">
        </bk-input>
      </div>
    </div>
    <bk-loading :loading="isLoading">
      <bk-table
        class="table-layout"
        :data="tableData"
        remote-pagination
        :pagination="pagination"
        show-overflow-tooltip
        @page-limit-change="handlePageSizeChange"
        @page-value-change="handlePageChange"
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
        <bk-table-column :label="t('操作人')" prop="created_by">
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

    <!-- 详情 -->
    <publish-details ref="detailsRef" :id="detailId" />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

import { useQueryList, useDatePicker } from '@/hooks';
import { useI18n } from 'vue-i18n';
import logDetails from '@/components/log-details/index.vue';
import publishDetails from './comps/publish-details.vue';
import { Spinner } from 'bkui-vue/lib/icon';
import {
  getReleaseHistories,
} from '@/http';
import TableEmpty from '@/components/table-empty.vue';
import { Message } from 'bkui-vue';

const router = useRouter();

const { t } = useI18n();
const filterData = ref({ keyword: '' });
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
} = useQueryList(getReleaseHistories, filterData);

// datepicker 时间选择器 hooks 适用于列表筛选
const {
  shortcutsRange,
  dateValue,
  handleChange,
  handleClear,
  handleComfirm,
} = useDatePicker(filterData);

const historyId = ref();
const logDetailsRef = ref(null);
const detailId = ref();
const detailsRef = ref(null);

// const showDetails = (id: string) => {
//   detailId.value = id;
//   detailsRef.value?.showSideslider();
// };

const showLogs = (id: string) => {
  historyId.value = id;
  console.error('id', id);
  logDetailsRef.value?.showSideslider();
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

type Enums = typeof publishSourceEnum | typeof publishStatusEnum;
// 从枚举对象中获取文本
const getTextFromEnum = (e: Enums, key?: unknown) => {
  if (!key) return '--';
  return t(e[key as keyof Enums]);
};

const handlePickSuccess = () => {
  const internalValue = datePickerRef.value?.internalValue;
  if (internalValue) {
    dateValue.value = internalValue;
    handleComfirm();
  } else {
    Message({ theme: 'warning', message: t('输入的时间错误'), delay: 2000, dismissable: false });
  }
};

watch(() => filterData.value, () => {
  updateTableEmptyConfig();
}, {
  deep: true,
});


let timeId: any = null;
onMounted(() => {
  timeId = setInterval(() => {
    getList(getReleaseHistories, false);
  }, 1000 * 30);
});
onUnmounted(() => {
  clearInterval(timeId);
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
