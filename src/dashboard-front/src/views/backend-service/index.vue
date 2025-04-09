<template>
  <div class="backend-service-container page-wrapper-padding">
    <div class="header flex-row justify-content-between mb15">
      <div class="header-btn flex-row ">
        <span class="mr10">
          <bk-button
            v-bk-tooltips="{
              content: t('当前有版本正在发布，请稍后再进行后端服务修改'),
              disabled: !hasPublishingStage,
            }"
            :disabled="hasPublishingStage"
            class="mr5 w80"
            theme="primary"
            @click="handleAdd"
          >
            {{ t('新建') }}
          </bk-button>
        </span>
      </div>
      <div class="header-search">
        <bk-input class="search-input w500" :placeholder="t('请输入服务名称')" v-model="filterData.name" />
      </div>
    </div>
    <div class="backend-service-content">
      <bk-loading :loading="isLoading">
        <bk-table
          :row-class="isNewCreate"
          class="table-layout" :data="tableData" remote-pagination :pagination="pagination" show-overflow-tooltip
          @page-limit-change="handlePageSizeChange" @page-value-change="handlePageChange" row-hover="auto"
          border="outer">
          <bk-table-column :label="t('后端服务名称')" prop="name">
            <template #default="{ data }">
              <bk-button text theme="primary" @click="handleEdit(data)">
                {{ data?.name }}
              </bk-button>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('描述')" prop="description">
            <template #default="{ data }">
              {{ data?.description || '--' }}
            </template>
          </bk-table-column>
          <bk-table-column :label="t('关联的资源')" prop="resource_count">
            <template #default="{ data }">
              <span v-if="data?.resource_count === 0">{{ data?.resource_count }}</span>
              <bk-button v-else text theme="primary" @click="handleResource(data)">
                {{ data?.resource_count }}
              </bk-button>
            </template>
          </bk-table-column>
          <bk-table-column :label="t('更新时间')" prop="updated_time"></bk-table-column>
          <bk-table-column :label="t('操作')" width="150">
            <template #default="{ data }">
              <bk-button
                v-bk-tooltips="{
                  content: t('当前有版本正在发布，请稍后再进行后端服务修改'),
                  disabled: !hasPublishingStage
                }"
                :disabled="hasPublishingStage"
                class="mr25"
                text
                theme="primary"
                @click="handleEdit(data)"
              >
                {{ t('编辑') }}
              </bk-button>
              <span
                v-if="data?.resource_count !== 0"
                v-bk-tooltips="{
                  // content: t(`${data?.name === 'default' ? '默认后端服务，且' : '服务'}被${data?.resource_count}个资源引用了，不能删除`),
                  content: data?.name === 'default'
                    ? t('默认后端服务，且被{resourceCount}个资源引用了，不能删除', { resourceCount: data?.resource_count })
                    : t('服务被{resourceCount}个资源引用了，不能删除', { resourceCount: data?.resource_count }),
                  disabled: data?.resource_count === 0
                }"
              >
                <bk-button
                  :disabled="data?.resource_count !== 0 || data?.name === 'default'"
                  text
                  theme="primary" @click="handleDelete(data)"
                >
                  {{ t('删除') }}
                </bk-button>
              </span>
              <span
                v-else
                v-bk-tooltips="{
                  content: t('默认后端服务，不能删除'),
                  disabled: data?.name !== 'default'
                }">
                <bk-button
                  theme="primary" text
                  :disabled="data?.name === 'default'" @click="handleDelete(data)">
                  {{ t('删除') }}
                </bk-button>
              </span>
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
    </div>

    <addBackendService
      :base="baseInfo"
      :edit-id="backendServiceId"
      ref="addBackendServiceRef"
      @done="getList()"
    />
    <!-- <bk-dialog
      :is-show="isBackDialogShow"
      class="sideslider-close-back-dialog-cls"
      width="0"
      height="0"
      dialog-type="show">
    </bk-dialog> -->
  </div>
</template>

<script setup lang="ts">
import {
  computed,
  onBeforeMount,
  ref,
  watch,
} from 'vue';
import { useI18n } from 'vue-i18n';
import {
  InfoBox,
  Message,
} from 'bkui-vue';
import { useRouter } from 'vue-router';
import { useCommon } from '@/store';
import { timeFormatter } from '@/common/util';
import { useQueryList } from '@/hooks';
import {
  deleteBackendService,
  getBackendServiceList,
  getStageList,
} from '@/http';
import TableEmpty from '@/components/table-empty.vue';
import addBackendService from '@/views/backend-service/add.vue';

const { t } = useI18n();
const common = useCommon();
const router = useRouter();
const { apigwId } = common; // 网关id

const addBackendServiceRef = ref(null);
const backendServiceId = ref<number | undefined>();
// 基础信息
const baseInfo = ref({
  name: '',
  description: '',
});
const filterData = ref({ name: '', type: '' });
const tableEmptyConf = ref({
  keyword: '',
  isAbnormal: false,
});

const stageList = ref<{ release: { status: string } }[]>([]);

const hasPublishingStage = computed(() => {
  return stageList.value.some(item => item?.release?.status === 'doing');
});

// 列表hooks
const {
  tableData,
  pagination,
  isLoading,
  handlePageChange,
  handlePageSizeChange,
  getList,
} = useQueryList(getBackendServiceList, filterData);


const isNewCreate = (row: any) => {
  return isWithinTime(row?.updated_time) ? 'new-created' : '';
};

// 判断后端服务新建时间是否在24h之内
const isWithinTime = (date: string) => {
  const str = timeFormatter(date);
  const targetTime = new Date(str);
  const currentTime = new Date();
  // 计算两个时间之间的毫秒差
  const diff = currentTime.getTime() - targetTime.getTime();
  // 24 小时的毫秒数
  const twentyFourHours = 24 * 60 * 60 * 1000;
  return diff < twentyFourHours;
};

// 新建btn
const handleAdd = () => {
  if (hasPublishingStage.value) {
    return;
  }

  baseInfo.value = {
    name: '',
    description: '',
  };
  backendServiceId.value = undefined;
  addBackendServiceRef.value?.show();
};

// 点击名称/编辑
const handleEdit = async (data: any) => {
  baseInfo.value = {
    name: data.name,
    description: data.description,
  };

  backendServiceId.value = data.id;
  addBackendServiceRef.value?.show();
};

// 点击关联的资源数
const handleResource = (data: any) => {
  console.log(data);
  const params = {
    name: 'apigwResource',
    params: {
      id: apigwId,
    },
    query: {
      backend_id: data.id,
    },
  };
  router.push(params);
};

// 点击删除
const handleDelete = (item: any) => {
  InfoBox({
    title: t(`确定删除【${item.name}】该服务?`),
    infoType: 'warning',
    subTitle: t('删除操作无法撤回，请谨慎操作'),
    onConfirm: async () => {
      try {
        await deleteBackendService(apigwId, item.id);
        Message({
          message: t('删除成功'),
          theme: 'success',
        });
        getList();
      } catch (error) {
        console.log('error', error);
      }
    },
  });
};

const handleClearFilterKey = () => {
  filterData.value = { name: '', type: '' };
  getList();
  updateTableEmptyConfig();
};

const updateTableEmptyConfig = () => {
  tableEmptyConf.value.isAbnormal = pagination.value.abnormal;
  if (filterData.value.name && !tableData.value.length) {
    tableEmptyConf.value.keyword = 'placeholder';
    return;
  }
  if (filterData.value.name) {
    tableEmptyConf.value.keyword = '$CONSTANT';
    return;
  }
  tableEmptyConf.value.keyword = '';
};

const getStageListData = async () => {
  stageList.value = await getStageList(apigwId);
};

watch(
  () => tableData.value, () => {
    updateTableEmptyConfig();
  },
  { deep: true },
);

onBeforeMount(async () => {
  await getStageListData();
});

</script>

<style lang="scss" scoped>
.w80 {
  width: 80px;
}
.w500 {
  width: 500px;
}
:deep(.new-created){
  background-color: #f1fcf5 !important;
}
.table-layout {
  :deep(.bk-table-body) {
    table {
      tbody {
        tr {
          td {
            background-color: rgba(0,0,0,0);
          }
        }
      }
    }
  }
  :deep(.bk-table-head) {
    scrollbar-color: transparent transparent;
  }
  :deep(.bk-table-body) {
    scrollbar-color: transparent transparent;
  }
}
.ag-host-input {
  width: 80px;
  line-height: 30px;
  font-size: 12px;
  color: #63656E;
  outline: none;
  padding: 0 10px;
  text-align: center;
}
</style>
