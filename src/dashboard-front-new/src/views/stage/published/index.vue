<template>
  <div class="page-wrapper-padding publish-container">
    <div class="operate flex-row justify-content-between mb20">
      <div class="flex-1 flex-row align-items-center">
        <bk-date-picker
          ref="datePickerRef"
          use-shortcut-text
          format="yyyy-MM-dd HH:mm:ss"
          :shortcuts="shortcutsRange"
          clearable
          v-model="dateValue"
          style="width: 100%;"
          type="datetimerange"
          @change="handleChange"
          @pick-success="handleComfirm"
        >
        </bk-date-picker>
      </div>
      <div class="flex-1 flex-row justify-content-end">
        <bk-input class="ml10 mr10 operate-input" placeholder="请输入环境、版本标题或版本号" v-model="filterData.keyword"></bk-input>
      </div>
    </div>
    <bk-loading
      :loading="isLoading"
    >
      <bk-table
        class="table-layout"
        :data="tableData"
        remote-pagination
        :pagination="pagination"
        show-overflow-tooltip
        @page-limit-change="handlePageSizeChange"
        @page-value-change="handlePageChange"
        row-hover="auto"
      >
        <bk-table-column
          :label="t('已发布的环境')"
          prop="stage.name"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('类型')"
        >
          <template #default="{ data }">
            {{ publishSourceEnum[data?.source] }}
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('版本号')"
          prop="resource_version_display"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('操作状态')"
        >
          <template #default="{ data }">
            <spinner v-if="data?.status === 'doing'" fill="#3A84FF" />
            <span v-else :class="['dot', data?.status]"></span>
            {{ publishStatusEnum[data?.status] }}
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('操作时间')"
          prop="created_time"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('操作人')"
          prop="created_by"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('耗时')"
          prop="duration"
        >
        </bk-table-column>
        <bk-table-column
          :label="t('操作')"
        >
          <template #default="{ data }">
            <!-- <bk-button text theme="primary" @click="showDetails(data.id)">
              {{ t("查看详情") }}
            </bk-button> -->
            <bk-button text theme="primary" @click="showLogs(data.id)">
              {{ t("操作日志") }}
            </bk-button>
          </template>
        </bk-table-column>
      </bk-table>
    </bk-loading>

    <!-- 日志抽屉 -->
    <log-details ref="logDetailsRef" :history-id="historyId" />

    <!-- 详情 -->
    <publish-details ref="detailsRef" :id="detailId" />
  </div>
</template>

<script setup lang="ts">
import { useQueryList, useDatePicker } from '@/hooks';
import { ref, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { PublishSourceEnum, PublishStatusEnum } from '@/types';
import logDetails from '@/components/log-details/index.vue';
import publishDetails from './comps/publish-details.vue';
import { Spinner } from 'bkui-vue/lib/icon';
import {
  getReleaseHistories,
} from '@/http';
const { t } = useI18n();
const filterData = ref({ keyword: '' });
const datePickerRef = ref(null);
const publishSourceEnum: any = ref(PublishSourceEnum);
const publishStatusEnum: any = ref(PublishStatusEnum);

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
  logDetailsRef.value?.showSideslider();
};

let timeId: any = null;
onMounted(() => {
  timeId = setInterval(() => {
    getList();
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
}

.dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 2px;
    &.success {
      border: 1px solid #3FC06D;
      background: #E5F6EA;
    }
    &.failure {
      border: 1px solid #EA3636;
      background: #FFE6E6;
    }
  }
</style>
