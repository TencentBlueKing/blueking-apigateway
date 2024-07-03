<template>
  <bk-loading :loading="isLoading" :opacity="1">
    <template v-if="resourceVersionList?.length">
      <div class="resource-info">
        <bk-input
          v-model="searchValue"
          style="width: 520px"
          clearable
          type="search"
          :placeholder="t('请输入后端服务、资源名称、前端请求路径搜索')"
        />
        <bk-table
          class="table-layout mt15"
          :data="curPageData"
          :key="tableDataKey"
          :pagination="pagination"
          :remote-pagination="true"
          :empty-text="emptyText"
          show-overflow-tooltip
          row-hover="auto"
          border="outer"
          :settings="settings"
          @page-limit-change="handlePageSizeChange"
          @page-value-change="handlePageChange"
          :row-class="isHighlight"
        >
          <bk-table-column prop="backend" :label="t('后端服务')">
            <template #default="{ row }">
              <div class="backend-td">
                <bk-button theme="primary" text>
                  {{ row?.proxy?.backend?.name }}
                </bk-button>
                <edit-line class="backend-edit" @click="handleEditStage(row.name)" fill="#1768EF" />
              </div>
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('资源名称')"
            prop="name"
            sort
          >
            <template #default="{ row }">
              <bk-button theme="primary" text @click="showDetails(row)">
                {{ row?.name }}
              </bk-button>
            </template>
          </bk-table-column>
          <bk-table-column
            prop="method"
            :label="t('前端请求方法')"
            :filter="{
              list: customMethodsList,
              checked: chooseMethod,
              filterFn: handleMethodFilter,
              btnSave: false,
            }"
          >
            <template #default="{ row }">
              <span class="ag-tag" :class="row.method?.toLowerCase()">{{row.method}}</span>
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('前端请求路径')"
            prop="path"
            sort
          ></bk-table-column>
          <bk-table-column
            prop="gateway_label_ids"
            :label="t('标签')"
            :filter="{
              list: labelsList,
              checked: chooseLabels,
              filterFn: handleMethodFilter,
              btnSave: false,
            }"
          >
            <template #default="{ row }">
              <template v-if="row?.gateway_label_ids?.length">
                <bk-tag
                  v-for="tag in labels?.filter((label) => {
                    if (row.gateway_label_ids?.includes(label.id))
                      return true;
                  })"
                  :key="tag.id"
                >{{ tag.name }}</bk-tag
                >
              </template>
              <template v-else>--</template>
            </template>
          </bk-table-column>
          <bk-table-column prop="plugins" :label="t('生效的插件')">
            <template #default="{ row }">
              <template v-if="row?.plugins?.length">
                <span v-for="p in row.plugins" :key="p?.id">
                  <span class="plugin-tag success" v-if="p?.binding_type === 'stage'">环</span>
                  <span class="plugin-tag info" v-if="p?.binding_type === 'resource'">资</span>
                  <span style="vertical-align: middle;">{{ p?.name }}</span>
                </span>
              </template>
              <span v-else>--</span>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('是否公开')" prop="is_public">
            <template #default="{ row }">
              <span :style="{ color: row.is_public ? '#FE9C00' : '#63656e' }">
                {{ row.is_public ? t('是') : t('否') }}
              </span>
            </template>
          </bk-table-column>
          <bk-table-column
            :label="t('操作')"
            prop="act"
            width="200"
          >
            <template #default="{ row }">
              <bk-button
                text
                theme="primary"
                class="mr10"
                @click="showDetails(row)"
              >
                {{ t('查看资源详情') }}
              </bk-button>
              <bk-button
                text
                theme="primary"
                @click="copyPath(row)"
              >
                {{ t('复制资源地址') }}
              </bk-button>
            </template>

          </bk-table-column>
          <template #empty>
            <TableEmpty
              :keyword="tableEmptyConf.keyword"
              :abnormal="tableEmptyConf.isAbnormal"
              @clear-filter="handleClearFilterKey"
            />
          </template>
        </bk-table>
      </div>
    </template>

    <template v-else>
      <div class="exception-empty">
        <bk-exception
          type="empty"
          scene="part"
          :description="t('当前环境尚未发布，暂无资源信息')"
        />
      </div>
    </template>
  </bk-loading>

  <!-- 资源详情 -->
  <resource-details ref="resourceDetailsRef" :info="info" @hidden="clearHighlight()" />

  <!-- 环境编辑 -->
  <edit-stage-sideslider ref="stageSidesliderRef" @hidden="clearHighlight()" />
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { getResourceVersionsInfo, getGatewayLabels, getStageList } from '@/http';
import { useCommon, useStage } from '@/store';
import resourceDetails from './resource-details.vue';
import TableEmpty from '@/components/table-empty.vue';
import editStageSideslider from '../comps/edit-stage-sideslider.vue';
import { EditLine } from 'bkui-vue/lib/icon';
import { copy } from '@/common/util';
import { useRoute } from 'vue-router';
import mitt from '@/common/event-bus';

const { t } = useI18n();
const route = useRoute();
const common = useCommon();
const stageStore = useStage();

const props = defineProps({
  stageAddress: String,
  stageId: Number,
  versionId: Number,
});

const searchValue = ref<string>('');
const info = ref<any>({});
const resourceDetailsRef = ref(null);
const stageSidesliderRef = ref(null);
const isReload = ref(false);
const emptyText = ref<string>('暂无数据');
const chooseMethod = ref<string[]>([]);
const tableDataKey = ref(-1);

// 网关标签
const labels = ref<any[]>([]);
const chooseLabels = ref<string[]>([]);

// 网关id
const apigwId = computed(() => common.apigwId);
const isLoading = ref(true);

const pagination = ref({
  current: 1,
  limit: 10,
  count: 0,
  abnormal: false,
});

const tableEmptyConf = ref<{keyword: string, isAbnormal: boolean}>({
  keyword: '',
  isAbnormal: false,
});

const getLabels = async () => {
  try {
    const res = await getGatewayLabels(apigwId.value);
    labels.value = res;
  } catch (e) {
    console.error(e);
  }
};

// const tableKey =  ref(-1);
// const curSelectMethod = ref('ALL');
// const customMethodsList = shallowRef(common.methodList);
const customMethodsList = computed(() => {
  return common.methodList?.map((item: any) => {
    return {
      text: item.name,
      value: item.id,
    };
  });
});

const labelsList = computed(() => {
  tableDataKey.value = +new Date();
  return labels.value?.map((item: any) => {
    return {
      text: item.name,
      value: item.id,
    };
  });
});

// const renderMethodsLabel = () => {
//   return h('div', { class: 'resource-setting-custom-label' }, [
//     h(
//       RenderCustomColumn,
//       {
//         key: tableKey.value,
//         hasAll: true,
//         columnLabel: t('前端请求方法'),
//         selectValue: curSelectMethod.value,
//         list: customMethodsList.value,
//         onSelected: (value: Record<string, string>) => {
//           handleSelectMethod(value);
//         },
//       },
//     ),
//   ]);
// };

// const handleSelectMethod = (payload: Record<string, string>) => {
//   const { id } = payload;
//   searchValue.value = id === 'ALL' ? undefined : id;

//   getPageData();
// };

const showDetails = (row: any) => {
  setHighlight(row.name);
  info.value = row;
  resourceDetailsRef.value?.showSideslider();
};

const copyPath = (row: any) => {
  copy(props.stageAddress.replace(/\/$/, '') + row?.path);
};

// 资源信息
const resourceVersionList = ref([]);

// 获取资源信息数据
const getResourceVersionsData = async (curStageData: any) => {
  isLoading.value = true;
  const curVersionId = curStageData?.resource_version?.id;
  resourceVersionList.value = [];
  if (curVersionId === undefined) {
    isReload.value = true;
    isLoading.value = false;
    return;
  }
  // 没有版本无需请求
  if (curVersionId === 0) {
    isLoading.value = false;
    emptyText.value = '环境没有发布，数据为空';
    return;
  }
  try {
    const res = await getResourceVersionsInfo(apigwId.value, curVersionId, { stage_id: curStageData?.id });
    pagination.value.count = res.resources.length;
    resourceVersionList.value = res.resources || [];
  } catch (e) {
    // 接口404处理
    resourceVersionList.value = [];
    console.error(e);
  } finally {
    isLoading.value = false;
    isReload.value = false;
    emptyText.value = '暂无数据';
  }
};

const isHighlight = (v: any) => {
  return v.highlight ? 'row-cls' : '';
};

const setHighlight = (name: string) => {
  curPageData.value?.forEach((item: any) => {
    if (item.name === name) {
      item.highlight = true;
    } else {
      item.highlight = false;
    }
  });
};

const clearHighlight = () => {
  curPageData.value?.forEach((item: any) => {
    item.highlight = false;
  });
};

// 编辑环境
const handleEditStage = (name: string) => {
  setHighlight(name);
  stageSidesliderRef.value?.handleShowSideslider('edit');
};

watch(
  () => searchValue.value,
  () => {
    pagination.value.current = 1;
    pagination.value.limit = 10;
  },
);

const getPageData = () => {
  if (!resourceVersionList.value?.length) {
    pagination.value.count = 0;
    return [];
  }

  isLoading.value = true;
  let curAllData = resourceVersionList.value;
  if (searchValue.value) {
    curAllData = curAllData?.filter((row: any) => {
      if (
        row?.proxy?.backend?.name?.toLowerCase()?.includes(searchValue.value)
      || row?.name?.toLowerCase()?.includes(searchValue.value)
      || row?.path?.toLowerCase()?.includes(searchValue.value)
      )  {
        return true;
      }
      return false;
    });

    updateTableEmptyConfig();
  };

  if (chooseMethod.value?.length) {
    curAllData = curAllData?.filter((row: any) => {
      if (chooseMethod.value?.includes(row?.method))  {
        return true;
      }
      return false;
    });

    updateTableEmptyConfig();
  }

  if (chooseLabels.value?.length) {
    curAllData = curAllData?.filter((row: any) => {
      const flag = chooseLabels.value?.some((item: any) => row?.gateway_label_ids?.includes(item));
      if (flag)  {
        return true;
      }
      return false;
    });

    updateTableEmptyConfig();
  }

  // 当前页数
  const page = pagination.value.current;
  // limit 页容量
  let startIndex = (page - 1) * pagination.value.limit;
  let endIndex = page * pagination.value.limit;
  if (startIndex < 0) {
    startIndex = 0;
  }
  if (endIndex > curAllData.length) {
    endIndex = curAllData.length;
  }
  pagination.value.count = curAllData.length;

  isLoading.value = false;
  return curAllData?.slice(startIndex, endIndex);
};

// 当前页数据
const curPageData = computed(() => {
  return getPageData();
});

const handleMethodFilter = () => true;

// 页码变化发生的事件
const handlePageChange = (current: number) => {
  pagination.value.current = current;
  getPageData();
};

// 条数变化发生的事件
const handlePageSizeChange = (limit: number) => {
  pagination.value.limit = limit;
  pagination.value.current = 1;
  getPageData();
};

const updateTableEmptyConfig = () => {
  tableEmptyConf.value.isAbnormal = pagination.value.abnormal;
  if (searchValue.value || chooseMethod.value?.length || chooseLabels.value?.length || !curPageData.value.length) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (searchValue.value || chooseMethod.value?.length || chooseLabels.value?.length) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const handleClearFilterKey = () => {
  searchValue.value = '';
  chooseMethod.value = [];
  chooseLabels.value = [];
  tableDataKey.value = +new Date();
  // handleSearchClear();
  pagination.value = Object.assign(pagination.value, {
    current: 1,
    limit: 10,
    count: resourceVersionList.value.length,
  });
  getPageData();
};

// const handleSearchClear = () => {
//   // curSelectMethod.value = 'ALL';
//   // tableKey.value = +new Date();
// };

const settings = {
  trigger: 'click',
  fields: [
    {
      name: t('后端服务'),
      field: 'backend',
      disabled: true,
    },
    {
      name: t('资源名称'),
      field: 'name',
    },
    {
      name: t('前端请求方法'),
      field: 'method',
    },
    {
      name: t('前端请求路径'),
      field: 'path',
    },
    {
      name: t('标签'),
      field: 'gateway_label_ids',
    },
    {
      name: t('生效的插件'),
      field: 'plugins',
    },
    {
      name: t('是否公开'),
      field: 'is_public',
    },
  ],
  checked: ['backend', 'name', 'method', 'path', 'gateway_label_ids', 'plugins', 'is_public'],
};

const init = async () => {
  const data = await getStageList(apigwId.value);
  const paramsStage = route.query.stage || 'prod';

  const curStageData = data.find((item: { name: string; }) => item.name === paramsStage)
  || stageStore.stageList[0];
  getResourceVersionsData(curStageData);
  getLabels();
};

// 切换环境重新获取资源信息
watch(() => stageStore.curStageId, (newV, oldV) => {
  if (oldV !== -1) { // 初始化时onMounted会请求，防止重复
    init();
  }
});

// 切换环境重新执行
onMounted(() => {
  init();
});
</script>

<style lang="scss" scoped>
.table-layout {
  :deep(.row-cls){
    td{
      background: #e1ecff !important;
    }
  }
  :deep(.bk-table-head) {
    scrollbar-gutter: auto;
  }
}
.exception-empty {
  height: 420px;
  display: flex;
  align-items: center;
  :deep(.bk-exception-description) {
    font-size: 14px;
    margin-top: 0px;
  }
  :deep(.bk-exception-img) {
    width: 220px;
    height: 130px;
  }
}
.plugin-tag {
  display: inline-block;
  vertical-align: middle;
  width: 18px;
  height: 16px;
  text-align: center;
  line-height: 16px;
  border-radius: 2px;
  font-family: MicrosoftYaHei;
  font-size: 10px;
  &.success {
    color: #14A568;
    background: #E4FAF0;
  }
  &.info {
    color: #3A84FF;
    background: #EDF4FF;
  }
}
.backend-td {
  display: flex;
  align-items: center;
  height: 100%;
  .backend-edit {
    margin-left: 4px;
    cursor: pointer;
    opacity: 0;
  }
  &:hover {
    .backend-edit {
      opacity: 1;
    }
  }
}
</style>
<style lang="scss">
.content-footer {
  justify-content: flex-end;
  .btn-filter-save.disabled {
    display: none !important;
  }
}
</style>
