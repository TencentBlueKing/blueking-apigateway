<template>
  <div class="app-content">
    <div class="ag-top-header approval-history-wrapper">
      <bk-form class="fl flex-nowrap approval-history-item" form-type="inline">
        <bk-form-item :label="t('选择时间')" class="ag-form-item-datepicker">
          <bk-date-picker
            style="width: 320px;"
            v-model="initDateTimeRange"
            :placeholder="t('选择日期时间范围')"
            :type="'datetimerange'"
            :shortcuts="datepickerShortcuts"
            :shortcut-close="true"
            :use-shortcut-text="true"
            @clear="handleTimeClear"
            :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange"
            @pick-success="handleTimeChange">
          </bk-date-picker>
        </bk-form-item>
        <bk-form-item :label="t('授权维度')">
          <bk-select
            v-model="searchParams.dimension"
            style="width: 150px;">
            <bk-option
              v-for="option of dimensionList"
              :key="option.id"
              :id="option.id"
              :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="t('蓝鲸应用ID')" class="app-id-item">
          <bk-input
            :clearable="true"
            v-model="keyword"
            :placeholder="t('请输入应用ID，按Enter搜索')"
            :right-icon="'bk-icon icon-search'"
            @enter="handleSearch">
          </bk-input>
        </bk-form-item>
      </bk-form>
    </div>

    <bk-table
      style="margin-top: 15px;"
      border="outer"
      class="ag-apply-table"
      ref="permissionTable"
      :data="permissionRecordList"
      :size="'medium'"
      :pagination="pagination"
      v-bkloading="{ isLoading: isDataLoading }"
      @page-limit-change="handlePageLimitChange"
      @expand-change="handlePageExpandChange"
      @page-change="handlePageChange"
      @row-click="handleRowClick">
      <!-- <div slot="empty">
        <table-empty
          :keyword="tableEmptyConf.keyword"
          :abnormal="tableEmptyConf.isAbnormal"
          @reacquire="getApigwPermissionRecordList"
          @clear-filter="clearFilterKey"
        />
      </div> -->
      <bk-table-column type="expand" width="30" class="ag-expand-cell">
        <template #default="props">
          <div
            class="bk-alert m20 bk-alert-info"
            v-if="props.row.grant_dimension === 'api'"
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
            :data="props.row.handled_resources"
            :outer-border="false"
            :header-cell-style="{ background: '#fafbfd', borderRight: 'none' }"
            ext-cls="ag-expand-table">
            <!-- <div slot="empty">
              <table-empty empty />
            </div> -->
            <bk-table-column type="index" label="" width="60"></bk-table-column>
            <bk-table-column prop="name" :label="t('资源名称')"></bk-table-column>
            <bk-table-column prop="path" :label="t('请求路径')"></bk-table-column>
            <bk-table-column prop="method" :label="t('请求方法')"></bk-table-column>
            <bk-table-column prop="method" :label="t('审批状态')">
              <template #default="prop">
                <template v-if="prop.row['apply_status'] === 'rejected'">
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
        <template #default="props">
          <span>{{props.row.grant_dimension_display || '--'}}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="t('权限期限')" props="expire_days_display">
        <template #default="props">
          <span>{{props.row.expire_days_display || '--'}}</span>
        </template>
      </bk-table-column>
      <bk-table-column :label="t('申请人')" prop="applied_by"></bk-table-column>
      <bk-table-column width="200" :label="t('审批时间')" prop="handled_time"></bk-table-column>
      <bk-table-column :label="t('审批人')" prop="handled_by"></bk-table-column>
      <bk-table-column :label="t('审批状态')" prop="status">
        <template #default="props">
          <span class="ag-dot default mr5 vm" v-if="props.row['status'] === 'rejected'"></span>
          <span class="ag-dot success mr5 vm" v-else></span>
          {{statusMap[props.row.status]}}
        </template>
      </bk-table-column>
      <bk-table-column :label="t('操作')" width="100">
        <template #default="props">
          <bk-button
            class="mr10"
            theme="primary"
            text
            @click.stop.prevent="handleShowRecord(props.row)">
            {{ t('详情') }}
          </bk-button>
        </template>
      </bk-table-column>
    </bk-table>

    <bk-sideslider
      :quick-close="true"
      :title="detailSliderConf.title"
      :width="600"
      v-model:is-show="detailSliderConf.isShow">
      <template #default>
        <div class="p30">
          <section class="ag-kv-list">
            <div class="item">
              <div class="key"> {{ t('蓝鲸应用ID：') }} </div>
              <div class="value">{{curRecord.bk_app_code}}</div>
            </div>
            <div class="item">
              <div class="key"> {{ t('申请人：') }} </div>
              <div class="value">{{curRecord.applied_by}}</div>
            </div>
            <div class="item">
              <div class="key"> {{ t('授权维度：') }} </div>
              <div class="value">{{curRecord.grant_dimension_display || '--'}}</div>
            </div>
            <div class="item">
              <div class="key"> {{ t('权限期限：') }} </div>
              <div class="value">{{curRecord.expire_days_display || '--'}}</div>
            </div>
            <div class="item">
              <div class="key"> {{ t('申请理由：') }} </div>
              <div class="value">{{curRecord.reason || '--'}}</div>
            </div>
            <div class="item">
              <div class="key"> {{ t('申请时间：') }} </div>
              <div class="value">{{curRecord.applied_time}}</div>
            </div>
            <div class="item">
              <div class="key"> {{ t('审批人：') }} </div>
              <div class="value">{{curRecord.handled_by}}</div>
            </div>

            <div class="item">
              <div class="key"> {{ t('审批时间：') }} </div>
              <div class="value">{{curRecord.handled_time}}</div>
            </div>

            <div class="item">
              <div class="key"> {{ t('审批状态：') }} </div>
              <div class="value" style="line-height: 22px; padding-top: 10px">
                {{statusMap[curRecord.status]}}
              </div>
            </div>

            <div class="item">
              <div class="key"> {{ t('审批内容：') }} </div>
              <div class="value" style="line-height: 22px; padding-top: 10px">{{curRecord.comment}}</div>
            </div>
            <div class="item">
              <div class="key"> {{ t('资源信息：') }} </div>
              <div class="value" style="line-height: 22px; padding-top: 10px">
                <bk-table
                  :size="'small'"
                  :data="curRecord.handled_resources"
                  :header-cell-style="{ background: '#fafbfd', borderRight: 'none' }"
                  ext-cls="ag-expand-table">
                  <!-- <div slot="empty">
                    <table-empty empty />
                  </div> -->
                  <bk-table-column prop="name" :label="t('资源名称')"></bk-table-column>
                  <bk-table-column prop="method" :label="t('审批状态')">
                    <template #default="prop">
                      <template v-if="prop.row['apply_status'] === 'rejected'">
                        <span class="ag-dot default mr5 vm"></span> {{ t('驳回') }}
                      </template>
                      <template v-else>
                        <span class="ag-dot success mr5 vm"></span> {{ t('通过') }}
                      </template>
                    </template>
                  </bk-table-column>
                </bk-table>
                <!-- <bk-table style="margin-top: 5px;"
                    :data="curRecord.resourceList"
                    :size="'small'">
                    <bk-table-column :label="t('请求路径')" prop="path" :show-overflow-tooltip="true"></bk-table-column>
                    <bk-table-column :label="t('请求方法')" prop="method" :show-overflow-tooltip="true"></bk-table-column>
                </bk-table> -->
                <div
                  class="ag-alert warning mt10"
                  v-if="curRecord.resourceList.length
                    && curRecord.resourceList.length > curRecord.resource_ids.length"
                >
                  <i class="apigateway-icon icon-ag-info"></i>
                  <p> {{ t('部分资源已被删除') }} </p>
                </div>
                <div
                  class="ag-alert warning mt10"
                  v-if="!curRecord.resourceList.length && curRecord.resource_ids.length">
                  <i class="apigateway-icon icon-ag-info"></i>
                  <p> {{ t('资源已被删除') }} </p>
                </div>
              </div>
            </div>
          </section>
        </div>
      </template>
    </bk-sideslider>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, computed, watch, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import { useCommon, useAccessLog } from '@/store';
import { sortByKey } from '@/common/util';
import { getPermissionRecords, getResourceListData } from '@/http';

const { t } = useI18n();
const common = useCommon();
const accessLog = useAccessLog();

const { datepickerShortcuts } = accessLog;

const keyword = ref<string>('');
const isPageLoading = ref<boolean>(true);
const isDataLoading = ref<boolean>(false);
const permissionRecordList = ref<any>([]);
const shortcutSelectedIndex = ref<number>(-1);
const curRecord = ref<any>({
  bk_app_code: '',
  applied_by: '',
  applied_time: '',
  handled_by: '',
  handled_time: '',
  status: '',
  comment: '',
  resourceList: [],
  resource_ids: [],
});

const pagination = reactive({
  current: 1,
  count: 0,
  limit: 10,
});
const searchParams = reactive<any>({
  dimension: '',
  bk_app_code: '',
  time_start: '',
  time_end: '',
});
const statusMap = reactive<any>({
  approved: t('全部通过'),
  partial_approved: t('部分通过'),
  rejected: t('全部驳回'),
  pending: t('未审批'),
});
//  const grantTypes = ref<any>([
//   {
//     id: 'initialize',
//     name: t('主动授权'),
//   },
//   {
//     id: 'record',
//     name: t('申请审批'),
//   },
//  ]);
const dimensionList = ref<any>([
  {
    id: 'api',
    name: t('按网关'),
  },
  {
    id: 'resource',
    name: t('按资源'),
  },
]);
// const recordActionDialogConf = ref<any>({
//   isShow: false,
//   title: t('通过审批'),
//   isLoading: false,
// });
// const curAction = ref<any>({
//   ids: [],
//   status: '',
//   comment: '',
// });
const detailSliderConf = reactive<any>({
  title: '',
  isShow: false,
});
const resourceList = ref<any>([]);
const initDateTimeRange = ref<any>([]);
const tableEmptyConf = reactive<any>({
  keyword: '',
  isAbnormal: false,
});
const curExpandRow = ref<any>({});
const permissionTable = ref();

const apigwId = computed(() => common.apigwId);

const updateTableEmptyConfig = () => {
  if (keyword.value || searchParams.dimension || searchParams.time_start) {
    tableEmptyConf.keyword = 'placeholder';
    return;
  }
  tableEmptyConf.keyword = '';
};

// const clearFilterKey = () => {
//   keyword.value = '';
//   searchParams.dimension = '';
//   initDateTimeRange.value = [];
//   handleTimeClear();
// };

const handleRowClick = (row: any) => {
  permissionTable.value?.toggleRowExpansion(row);
  curExpandRow.value = row;
};

const handleShowRecord = (data: any) => {
  curRecord.value = data;
  detailSliderConf.title = `${t('申请应用：')}${data.bk_app_code}`;
  curRecord.value.resourceList = [];

  const results: any = [];
  curRecord.value?.resource_ids.forEach((resourceId: any) => {
    resourceList.value.forEach((item: any) => {
      if (item.id === resourceId) {
        results.push(item);
      }
    });
  });

  curRecord.value.resourceList = sortByKey(results, 'path');
  detailSliderConf.isShow = true;
};

const handleTimeClear = () => {
  shortcutSelectedIndex.value = -1;
  searchParams.time_start = '';
  searchParams.time_end = '';
};

const handleShortcutChange = (value: any, index: number) => {
  shortcutSelectedIndex.value = index;
};

const handleTimeChange = () => {
  nextTick(() => {
    searchParams.time_start = parseInt((+new Date(`${initDateTimeRange.value[0]}`)) / 1000);
    searchParams.time_end = parseInt((+new Date(`${initDateTimeRange.value[1]}`)) / 1000);
  });
};

const handleSearch = () => {
  searchParams.bk_app_code = keyword.value;
};

const handlePageChange = (newPage: number) => {
  pagination.current = newPage;
  getApigwPermissionRecordList(newPage);
};

const handlePageLimitChange = (limit: any) => {
  pagination.limit = limit;
  pagination.current = 1;
  getApigwPermissionRecordList(pagination.current);
};

const getSearchTimeRange = () => {
  const timeRange = datepickerShortcuts[shortcutSelectedIndex.value].value();
  return {
    time_start: parseInt((+new Date(timeRange[0])) / 1000),
    time_end: parseInt((+new Date(timeRange[1])) / 1000),
  };
};

const handlePageExpandChange = (row: any) => {
  if (curExpandRow.value !== row) {
    permissionTable.value?.toggleRowExpansion(curExpandRow.value, false);
  }
  curExpandRow.value = row;
};

const getApigwResources = async () => {
  const pageParams = {
    no_page: true,
    order_by: 'path',
  };

  try {
    const res = await getResourceListData(apigwId.value, pageParams);

    resourceList.value = res.results;
  } catch (e) {
    console.error(e);
  }
};

const getApigwPermissionRecordList = async (page?: any) => {
  const curPage = page || pagination.current;
  let pageParams = {
    limit: pagination.limit,
    offset: pagination.limit * (curPage - 1),
    bk_app_code: searchParams.bk_app_code,
    time_start: searchParams.time_start,
    time_end: searchParams.time_end,
    grant_dimension: searchParams.dimension,
  };

  // 选择的是时间快捷项，需要实时计算时间值
  if (shortcutSelectedIndex.value !== -1) {
    const searchTimeRange = getSearchTimeRange();
    pageParams = { ...pageParams, ...searchTimeRange };
  }

  isDataLoading.value = true;
  try {
    const res = await getPermissionRecords(apigwId.value, pageParams);
    res.results.forEach((item: any) => {
      const hasApprovedItem = item.handled_resources.find((resource: any) => resource.apply_status === 'approved');
      const hasRejectedItem = item.handled_resources.find((resource: any) => resource.apply_status === 'rejected');

      if (hasApprovedItem && !hasRejectedItem) {
        item.statusText = t('全部通过');
      } else if (hasApprovedItem && hasRejectedItem) {
        item.statusText = t('部分通过');
      } else if (!hasApprovedItem && hasRejectedItem) {
        item.statusText = t('全部驳回');
      } else {
        item.statusText = '--';
      }
    });
    permissionRecordList.value = res.results;
    pagination.count = res.count;
    updateTableEmptyConfig();
    tableEmptyConf.isAbnormal = false;
  } catch (e) {
    tableEmptyConf.isAbnormal = true;
    console.error(e);
  } finally {
    isPageLoading.value = false;
    isDataLoading.value = false;
    // this.$store.commit('setMainContentLoading', false);
  }
};

const init = () => {
  getApigwPermissionRecordList();
  getApigwResources();
};

init();

watch(
  () => keyword.value,
  (newVal, oldVal) => {
    if (oldVal && !newVal) {
      handleSearch();
    }
  },
);

watch(
  () => searchParams,
  () => {
    pagination.current = 1;
    pagination.count = 0;
    getApigwPermissionRecordList();
  },
  {
    deep: true,
  },
);
</script>

<style lang="scss" scoped>
.app-content {
  padding: 24px;
  .ag-top-header {
    min-height: 32px;
    margin-bottom: 20px;
    position: relative;
  }
}
.ag-resource-radio {
  label {
    display: block;
    margin-bottom: 10px;
  }
}

.ag-transfer-box {
  padding: 20px;
  background: #FAFBFD;
  border: 1px solid #F0F1F5;
  border-radius: 2px;
}

.ag-dl {
  padding: 15px 40px 5px 30px;
}

.ag-link {
  .apigateway-icon {
    cursor: pointer;
    color: #737987;
    font-size: 16px;
    margin-left: 5px;
  }
}

.ag-user-type {
  width: 560px;
  height: 80px;
  background: #FAFBFD;
  border-radius: 2px;
  border: 1px solid #DCDEE5;
  padding: 17px 20px 0 20px;
  position: relative;
  overflow: hidden;

  .apigateway-icon {
    font-size: 80px;
    position: absolute;
    color: #ECF2FC;
    top: 15px;
    right: 20px;
    z-index: 0;
  }

  strong {
    font-size: 14px;
    margin-bottom: 10px;
    line-height: 1;
    display: block;
  }

  p {
    font-size: 12px;
    color: #63656E;
  }
}

.approval-history-wrapper {
  .flex-nowrap.fl {
    display: flex;
    flex-wrap: nowrap;
    :deep(.bk-label) {
        white-space: nowrap;
    }
    .bk-form-item {
        display: flex;
        flex-wrap: nowrap;
    }
  }
  .approval-history-item {
    width: 100%;
    .app-id-item {
      flex: 1;
      :deep(.bk-form-content) {
        width: 100%;
        max-width: 320px;
      }
    }
  }
}
</style>
