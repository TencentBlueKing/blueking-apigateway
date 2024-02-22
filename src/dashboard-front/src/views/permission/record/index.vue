<template>
  <div class="permission-record-container page-wrapper-padding">
    <div class="header ">
      <bk-form class="flex-row">
        <bk-form-item :label="t('选择时间')" class="ag-form-item-datepicker mb15" label-width="85">
          <bk-date-picker
            class="w320" v-model="initDateTimeRange" :placeholder="t('选择日期时间范围')" :key="dateKey"
            :type="'datetimerange'" :shortcuts="datepickerShortcuts" :shortcut-close="true" :use-shortcut-text="true"
            @clear="handleTimeClear" :shortcut-selected-index="shortcutSelectedIndex"
            @shortcut-change="handleShortcutChange" @pick-success="handleTimeChange">
          </bk-date-picker>
        </bk-form-item>
        <bk-form-item :label="t('授权维度')" class="mb15" label-width="108">
          <bk-select v-model="filterData.grant_dimension" class="w150">
            <bk-option v-for="option of dimensionList" :key="option.id" :id="option.id" :name="option.name">
            </bk-option>
          </bk-select>
        </bk-form-item>
        <bk-form-item :label="t('蓝鲸应用ID')" class="mb15" label-width="119">
          <bk-input clearable v-model="filterData.bk_app_code" :placeholder="t('请输入应用ID，按Enter搜索')" class="w320">
          </bk-input>
        </bk-form-item>
      </bk-form>
    </div>
    <div class="record-content">
      <bk-loading :loading="isLoading">
        <bk-table
          ref="tableRef"
          size="small"
          class="perm-record-table"
          :data="tableData"
          :columns="table.headers"
          :pagination="pagination"
          :remote-pagination="true"
          :row-style="{ cursor: 'pointer' }"
          @row-click="handleRowClick"
          @page-limit-change="handlePageSizeChange"
          @page-value-change="handlePageChange"
        >
          <template #expandRow="row">
            <div class="record-expand-alert" v-if="['api'].includes(row.grant_dimension)">
              <bk-alert theme="info" :title="t('网关下所有资源的权限，包括未来新创建的资源')" />
            </div>
            <div v-else>
              <bk-table
                :max-height="378"
                :size="'small'"
                :data="row.handled_resources"
                :header-border="false"
                :outer-border="false"
                :header-cell-style="{ background: '#fafbfd', borderRight: 'none' }"
                class="ag-expand-table">
                <bk-table-column type="index" label="#" width="60" />
                <bk-table-column prop="name" :label="t('资源名称')" />
                <bk-table-column prop="path" :label="t('请求路径')"/>
                <bk-table-column prop="method" :label="t('请求方法')" />
                <bk-table-column prop="apply_status" :label="t('审批状态')" >
                  <template #default="childData">
                    <div class="perm-record-dot">
                      <template v-if="['rejected'].includes(childData?.data?.apply_status)">
                        <span  class="ag-dot default mr5"></span> {{ t('驳回') }}
                      </template>
                      <template v-else>
                      <span  class="ag-dot success mr5"></span> {{ t('通过') }}
                      </template>
                    </div>
                  </template>
                </bk-table-column>
              </bk-table>
            </div>
          </template>
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
    </div>

    <!-- 详情sideslider -->
    <bk-sideslider
      :quick-close="true"
      :title="detailSliderConf.title"
      :width="600"
      v-model:isShow="detailSliderConf.isShow">
      <template #default>
        <div class="p30">
          <div class="ag-kv-list">
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
              <div class="value pt10 lh22">
                {{statusMap[curRecord.status as keyof typeof statusMap]}}
              </div>
            </div>
            <div class="item">
              <div class="key"> {{ t('审批内容：') }} </div>
              <div class="value pt10 lh22">{{curRecord.comment}}</div>
            </div>
            <div class="item">
              <div class="key"> {{ t('资源信息：') }} </div>
              <div class="value pt10 lh22">
                <bk-table
                  :size="'small'"
                  :data="curRecord.handled_resources"
                  :border="['outer']"
                  ext-cls="ag-expand-table">
                  <bk-table-column prop="name" :label="t('资源名称')"></bk-table-column>
                  <bk-table-column prop="method" :label="t('审批状态')">
                    <template #default="prop">
                      <template v-if="prop.row['apply_status'] === 'rejected'">
                        <span class="ag-dot default mr5 "></span> {{ t('驳回') }}
                      </template>
                      <template v-else>
                        <span class="ag-dot success mr5 "></span> {{ t('通过') }}
                      </template>
                    </template>
                  </bk-table-column>
                </bk-table>
                <!-- <bk-alert
                  theme="warning" :title="t('部分资源已被删除')"
                  v-if="curRecord.resourceList.length && curRecord.resourceList.length > curRecord.resource_ids.length">
                </bk-alert>
                <bk-alert
                  theme="warning" :title="t('资源已被删除')"
                  v-if="!curRecord.resourceList.length && curRecord.resource_ids.length">
                </bk-alert> -->
              </div>
            </div>
          </div>
        </div>
      </template>

    </bk-sideslider>
  </div>
</template>

<script setup lang="tsx">
import { nextTick, reactive, ref, watch, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { getPermissionRecordList } from '@/http';
import { useCommon } from '@/store';
import { useQueryList } from '@/hooks';
import { sortByKey } from '@/common/util';
import TableEmpty from '@/components/table-empty.vue';

const { t } = useI18n();

const tableEmptyConf = ref<{keyword: string, isAbnormal: boolean}>({
  keyword: '',
  isAbnormal: false,
});
const filterData = ref({
  bk_app_code: '',
  grant_dimension: '',
  time_start: '',
  time_end: '',
});
const initDateTimeRange = ref([]);
const resourceList = ref([]);
const shortcutSelectedIndex = ref<number>(-1);
const dateKey = ref('dateKey');
const curRecord = ref({
  bk_app_code: '',
  applied_by: '',
  applied_time: '',
  handled_by: '',
  handled_time: '',
  status: '',
  comment: '',
  resourceList: [],
  resource_ids: [],
  grant_dimension_display: '',
  expire_days_display: 0,
  reason: '',
  handled_resources: [],
});
const detailSliderConf = reactive({
  title: '',
  isShow: false,
});
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
const tableRef = ref();
const table = ref({
  headers: [],
});
const setTableHeader = () => {
  const columns =  [
    {
      type: 'expand',
      width: 30,
      minWidth: 30
    },
    {
      field: 'bk_app_code',
      label: t('蓝鲸应用ID'),
    },
    {
      field: 'grant_dimension_display',
      label: t('授权维度'),
      render: ({ data }: Record<string, any>) => {
        return data.grant_dimension_display || '--'
      }
     },
    {
      field: 'expire_days_display',
      label: t('权限期限'),
      render: ({ data }: Record<string, any>) => {
        return data.expire_days_display || '--'
      }
    },
    { field: 'applied_by', label: t('申请人') },
    { field: 'handled_time', label: t('审批时间') },
    { field: 'handled_by', label: t('审批人') },
    {
      field: 'status',
      label: t('审批状态'),
      render: ({ data }: Record<string, any>) => {
        if(['rejected'].includes(data?.status)) {
          return (
            <div class="perm-record-dot">
              <div class="ag-dot default mr5" />
              {statusMap[data?.status as keyof typeof statusMap]}
            </div>
          )
        } else {
          return (
            <div class="perm-record-dot">
              <span class="ag-dot success mr5" />
              {statusMap[data?.status as keyof typeof statusMap]}
            </div>
          )
        }
      }
     },
    {
      field: 'operate',
      label: t('操作'),
      render: ({ data }: Record<string, any>) => {
        return (
          <div>
            <bk-button
              class="mr10"
              theme="primary"
              text
              onClick={(e:Event) => {handleShowRecord(e,data)}}
            >
              { t('详情') }
            </bk-button>
          </div>
        );
      },
    },
  ];
  table.value.headers = columns;
};
// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList(getPermissionRecordList, filterData);

const handleRowClick = (e: Event, row: Record<string, any>) => {
  e.stopPropagation();
  row.isExpand = !row.isExpand;
  nextTick(() => {
    tableRef.value.setRowExpand(row,  row.isExpand);
  });
};

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
// 展示详情
const handleShowRecord = (e: Event, data: any) => {
  e.stopPropagation();
  curRecord.value = data;
  detailSliderConf.title = `${t('申请应用：')}${data.bk_app_code}`;
  curRecord.value.resourceList = [];
  const results: any[] = [];
  curRecord.value.resource_ids.forEach((resourceId) => {
    resourceList.value.forEach((item: { id: any; }) => {
      if (item.id === resourceId) {
        results.push(item);
      }
    });
  });

  curRecord.value.resourceList = sortByKey(results, 'path');
  detailSliderConf.isShow = true;
};

const handleClearFilterKey = async() => {
  filterData.value =Object.assign({}, {
    bk_app_code: '',
    grant_dimension: '',
    time_start: '',
    time_end: '',
  });
  shortcutSelectedIndex.value = -1;
  initDateTimeRange.value = [];
  dateKey.value = String(+new Date());
  await getList();
  updateTableEmptyConfig();
};

const updateTableEmptyConfig = () => {
  const searchParams = {
    ...filterData.value,
  };
  const list = Object.values(searchParams).filter(item => item !== '');
  if (list.length && !tableData.value.length) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (list.length) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const init = () => {
  setTableHeader();
};

watch(() => filterData.value, () => {
  updateTableEmptyConfig()
}, {
  deep: true
})

onMounted(() => {
  init();
});
</script>

<style lang="scss" scoped>
.h60{
  height: 60px;
}
.w150 {
  width: 150px;
}

.w320 {
  width: 320px;
}
.record-content {
  height: calc(100% - 90px);
  min-height: 600px;
}

.ag-kv-list {
	border: 1px solid #F0F1F5;
	border-radius: 2px;
	background: #FAFBFD;
	padding: 10px 20px;

	.item {
		display: flex;
		font-size: 14px;
		border-bottom: 1px dashed #DCDEE5;
		min-height: 40px;
		line-height: 40px;

		&:last-child {
			border-bottom: none;
		}

		.key {
			min-width: 130px;
			padding-right: 24px;
			color: #63656E;
			text-align: right;
		}

		.value {
			color: #313238;
			flex: 1;
		}
	}
}
.lh22 {
  line-height: 22px;
}
.w320 {
  width: 320px;
}

.record-expand-alert {
  padding: 20px;
  line-height: 60px;
  background-color: #fafafa;
}

:deep(.record-content){
  .bk-exception{
    height: 280px;
    max-height: 280px;
    justify-content: center;
  }
}

:deep(.perm-record-dot) {
  .mr5 {
    margin-right: 5px;
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
}

:deep(.perm-record-table) ,
:deep(.ag-expand-table) {
  tr {
    background-color: #fafbfd;
  }
  th {
    .head-text {
      font-weight: bold !important;
      color: #63656E !important;
    }
  }
  td,
  th {
    padding: 0 !important;
    height: 42px !important;
  }
}

:deep(.ag-expand-table) {
  .bk-fixed-bottom-border {
    display: none;
  }
}
</style>
