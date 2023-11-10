<template>
  <div class="permission-record-container p20">
    <div class="header ">
      <bk-form class="flex-row">
        <bk-form-item :label="t('选择时间')" class="ag-form-item-datepicker" label-width="85">
          <bk-date-picker
            style="width: 320px;" v-model="initDateTimeRange" :placeholder="t('选择日期时间范围')"
            :type="'datetimerange'" :shortcuts="datepickerShortcuts" :shortcut-close="true" :use-shortcut-text="true"
            @clear="handleTimeClear" :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange" @pick-success="handleTimeChange">
          </bk-date-picker>
        </bk-form-item>
        <bk-form-item :label="t('授权维度')" class="mb10" label-width="108">
          <bk-select v-model="filterData.grant_dimension" class="w150">
            <bk-option v-for="option of dimensionList" :key="option.id" :id="option.id" :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="t('蓝鲸应用ID')" class="mb10" label-width="119">
          <bk-input clearable v-model="filterData.bk_app_code" :placeholder="t('请输入应用ID，按Enter搜索')" class="w320">
          </bk-input>
        </bk-form-item>
      </bk-form>
    </div>
    <div class="record-content">
      <bk-loading :loading="isLoading">
        <bk-table
          class="table-layout" :data="tableData" remote-pagination :pagination="pagination" show-overflow-tooltip
          @page-limit-change="handlePageSizeChange" @page-value-change="handlePageChange"
          @row-mouse-enter="handleMouseEnter" row-hover="auto">
          <bk-table-column type="expand" width="30" class="ag-expand-cell">
            <template #expandRow="row">
              <div
                class="bk-alert m20 bk-alert-info"
                v-if="row.grant_dimension === 'api'"
                style="display: block; text-align: center; line-height: 30px;">
                <div class="bk-alert-wraper">
                  <i class="bk-icon icon-info" style="display: inline-block; margin-right: 1px;"></i>
                  <div class="bk-alert-content" style="display: inline-block;">
                    <div class="bk-alert-title">
                      {{ t('网关下所有资源的权限，包括未来新创建的资源') }}
                    </div>
                  </div>
                </div>
              </div>
              <bk-table
                v-else
                :max-height="378"
                :size="'small'"
                :data="row.handled_resources"
                :outer-border="false"
                :header-cell-style="{ background: '#fafbfd', borderRight: 'none' }"
                ext-cls="ag-expand-table">
                <bk-table-column type="index" label="" width="60"></bk-table-column>
                <bk-table-column prop="name" :label="t('资源名称')"></bk-table-column>
                <bk-table-column prop="path" :label="t('请求路径')"></bk-table-column>
                <bk-table-column prop="method" :label="t('请求方法')"></bk-table-column>
                <bk-table-column prop="method" :label="t('审批状态')">
                  <template #default="{ data }">
                    <template v-if="data.apply_status === 'rejected'">
                      <span class="ag-dot default mr5 vm"></span> {{ t('驳回') }}
                    </template>
                    <template v-else>
                      <span class="ag-dot success mr5 vm"></span> {{ t('通过') }}
                    </template>
                  </template>
                </bk-table-column>
              </bk-table>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('蓝鲸应用ID')" prop="bk_app_code"></bk-table-column>
          <bk-table-column :label="t('授权维度')" prop="grant_dimension_display">
            <template #default="{ data }">
              {{ data?.grant_dimension_display || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('权限期限')" prop="expire_days_display">
            <template #default="{ data }">
              {{ data?.expire_days_display || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('申请人')" prop="applied_by"></bk-table-column>
          <bk-table-column :label="t('审批时间')" prop="handled_time" width="200"></bk-table-column>
          <bk-table-column :label="t('审批人')" prop="handled_by"></bk-table-column>
          <bk-table-column :label="t('审批状态')" prop="status">
            <template #default="{ data }">
              <span class="ag-dot default mr5 vm" v-if="data?.status === 'rejected'"></span>
              <span class="ag-dot success mr5 vm" v-else></span>
              {{statusMap[data?.status as keyof typeof statusMap]}}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('操作')" width="100">
            <template #default="{ data }">
              <bk-button class="mr10" theme="primary" text @click.stop.prevent="handleShowRecord(data)">
                {{ t('详情') }}
              </bk-button>
            </template>
          </bk-table-column>
        </bk-table>
      </bk-loading>

    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, reactive, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { getPermissionApplyList } from '@/http';
import { useCommon } from '@/store';
import { useQueryList } from '@/hooks';
const { t } = useI18n();
const common = useCommon();

const { apigwId } = common; // 网关id

const filterData = ref({
  bk_app_code: '',
  grant_dimension: '',
  time_start: '',
  time_end: '',
});
const initDateTimeRange = ref([]);
const shortcutSelectedIndex = ref<number>(-1);
const dimensionList = reactive([
  { id: 'api', name: t('按网关') },
  { id: 'resource', name: t('按资源') },
]);
const statusMap = reactive({
  approved: t('全部通过'),
  partial_approved: t('部分通过'),
  rejected: t('全部驳回'),
  pending: t('未审批'),
});
// 日期 快捷方式设置
const datepickerShortcuts = reactive([
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
]);

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  // getList,
} = useQueryList(getPermissionApplyList, filterData);

// 日期清除
const handleTimeClear = () => {
  shortcutSelectedIndex.value = -1;
  filterData.value.time_start = '';
  filterData.value.time_end = '';
};
// 日期快捷方式改变触发
const handleShortcutChange = (value: any, index: any) => {
  shortcutSelectedIndex.value = index;
};
// 日期快捷方式改变触发
const handleTimeChange = () => {
  nextTick(() => {
    const startStr: any = (+new Date(`${initDateTimeRange.value[0]}`)) / 1000;
    const endStr: any = (+new Date(`${initDateTimeRange.value[1]}`)) / 1000;
    // eslint-disable-next-line radix
    const satrt: any = parseInt(startStr);
    // eslint-disable-next-line radix
    const end: any = parseInt(endStr);
    filterData.value.time_start = satrt;
    filterData.value.time_end = end;
  });
};

const handleShowRecord = (data: any) => {
  console.log(data);
};

// 鼠标进入
const handleMouseEnter = (e: any, row: any) => {
  console.log('row', row);
};

const init = () => {
  console.log(tableData);
  console.log(apigwId);
};
init();
</script>

<style lang="scss" scoped>
.w150 {
  width: 150px;
}

.w320 {
  width: 320px;
}
.ag-dot {
    width: 8px;
    height: 8px;
    display: inline-block;
    vertical-align: middle;
    background: #C4C6CC;
    border-radius: 50%;

    &.default {
        background: #f0f1f5;
        border: 1px solid #c9cad2;
    }

    &.primary,
    &.releasing,
    &.pending {
        background: #f0f1f5;
        border: 1px solid #c9cad2;
    }

    &.success {
        background: #E5F6EA;
        border: 1px solid #3FC06D;
    }
  }
.record-content {
  height: calc(100% - 90px);
  min-height: 600px;
}
</style>
