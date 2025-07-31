/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

<template>
  <BkLoading
    :loading="isLoading"
    :opacity="1"
  >
    <template v-if="resourceVersionList?.length">
      <div class="resource-info">
        <BkInput
          v-model="searchValue"
          class="w-520px"
          clearable
          type="search"
          :placeholder="t('请输入后端服务、资源名称、前端请求路径搜索')"
        />
        <BkTable
          :key="tableDataKey"
          class="table-layout"
          :data="tableData"
          :pagination="pagination"
          remote-pagination
          :empty-text="emptyText"
          show-overflow-tooltip
          row-hover="auto"
          border="outer"
          :settings="settings"
          :row-class="isHighlight"
          @page-limit-change="handlePageSizeChange"
          @page-value-change="handlePageChange"
        >
          <BkTableColumn
            prop="backend"
            :label="t('后端服务')"
          >
            <template #default="{ row }">
              <div
                class="backend-td"
                @click="() => handleCheckStage({
                  resourceName: row.name,
                  backendName: row.proxy?.backend?.name,
                })"
              >
                <BkButton
                  theme="primary"
                  text
                >
                  {{ row.proxy?.backend?.name ?? '--' }}
                </BkButton>
              </div>
            </template>
          </BkTableColumn>
          <BkTableColumn
            :label="t('资源名称')"
            prop="name"
            sort
          >
            <template #default="{ row }">
              <BkButton
                theme="primary"
                text
                @click="() => showDetails(row)"
              >
                {{ row?.name }}
              </BkButton>
            </template>
          </BkTableColumn>
          <BkTableColumn
            prop="method"
            :label="t('前端请求方法')"
            :filter="{
              list: methodsList || [{ text: '', value: '' }],
              checked: chooseMethod,
              filterFn: handleMethodFilter,
              btnSave: false,
            }"
          >
            <template #default="{ row }">
              <span
                class="ag-tag"
                :class="row.method?.toLowerCase()"
              >{{ row.method }}</span>
            </template>
          </BkTableColumn>
          <BkTableColumn
            :label="t('前端请求路径')"
            prop="path"
            sort
          />
          <BkTableColumn
            prop="gateway_label_ids"
            :label="t('标签')"
            :filter="{
              list: labelsList || [{ text: '', value: '' }],
              checked: chooseLabels,
              filterFn: handleMethodFilter,
              btnSave: false,
            }"
          >
            <template #default="{ row }">
              <template v-if="row?.gateway_label_ids?.length">
                <BkTag
                  v-for="tag in labels?.filter((label) => {
                    if (row.gateway_label_ids?.includes(label.id))
                      return true;
                  })"
                  :key="tag.id"
                >
                  {{ tag.name }}
                </BkTag>
              </template>
              <template v-else>
                --
              </template>
            </template>
          </BkTableColumn>
          <BkTableColumn
            prop="plugins"
            :label="t('生效的插件')"
          >
            <template #default="{ row }">
              <template v-if="row?.plugins?.length">
                <span
                  v-for="p in row.plugins"
                  :key="p?.id"
                >
                  <span
                    v-if="p?.binding_type === 'stage'"
                    class="plugin-tag success"
                  >环</span>
                  <span
                    v-if="p?.binding_type === 'resource'"
                    class="plugin-tag info"
                  >资</span>
                  <span class="v-middle">{{ p?.name }}</span>
                </span>
              </template>
              <span v-else>--</span>
            </template>
          </BkTableColumn>
          <BkTableColumn
            :label="t('是否公开')"
            prop="is_public"
          >
            <template #default="{ row }">
              <span :style="{ color: row.is_public ? '#FE9C00' : '#63656e' }">
                {{ row.is_public ? t('是') : t('否') }}
              </span>
            </template>
          </BkTableColumn>
          <BkTableColumn
            :label="t('操作')"
            prop="act"
            width="200"
          >
            <template #default="{ row }">
              <BkButton
                text
                theme="primary"
                class="mr-10px"
                @click="() => showDetails(row)"
              >
                {{ t('查看资源详情') }}
              </BkButton>
              <BkButton
                text
                theme="primary"
                @click="() => copyPath(row)"
              >
                {{ t('复制资源地址') }}
              </BkButton>
            </template>
          </BkTableColumn>
          <template #empty>
            <TableEmpty
              :keyword="tableEmptyConf.keyword"
              :abnormal="tableEmptyConf.isAbnormal"
              @clear-filter="handleClearFilterKey"
            />
          </template>
        </BkTable>
      </div>
    </template>

    <template v-else>
      <div class="exception-empty">
        <BkException
          type="empty"
          scene="part"
          :description="t('当前环境尚未发布，暂无资源信息')"
        />
      </div>
    </template>
  </BkLoading>

  <!-- 资源详情 -->
  <ResourceDetails
    ref="resourceDetailsRef"
    :info="info"
    @hidden="clearHighlight"
  />

  <!-- 环境编辑 -->
  <CreateStage
    ref="stageSidesliderRef"
    :stage-id="stageId"
    @hidden="clearHighlight"
  />
</template>

<script setup lang="ts">
import { getGatewayLabels } from '@/services/source/gateway';
import {
  type IStageListItem,
  getStageList,
} from '@/services/source/stage';
import { getVersionDetail } from '@/services/source/resource';
import ResourceDetails from './ResourceDetails.vue';
import TableEmpty from '@/components/table-empty/Index.vue';
import CreateStage from '../../components/CreateStage.vue';
import { copy } from '@/utils';
import { useRouteParams } from '@vueuse/router';

interface IProps {
  stageAddress: string
  stageId: number
  versionId: number
}

const {
  stageAddress,
  stageId,
  // versionId,
} = defineProps<IProps>();

const { t } = useI18n();
const gatewayId = useRouteParams('id', 0, { transform: Number });

const searchValue = ref('');
const info = ref<any>({});
const resourceDetailsRef = ref();
const stageSidesliderRef = ref();
const isReload = ref(false);
const emptyText = ref('暂无数据');
const chooseMethod = ref<string[]>([]);
const tableDataKey = ref(-1);

// 网关标签
const labels = ref<any[]>([]);
const chooseLabels = ref<string[]>([]);
const isLoading = ref(true);

// 资源信息
const resourceVersionList = ref([]);
const tableData = ref<any[]>([]);
const stageList = ref<IStageListItem[]>([]);

const pagination = ref({
  current: 1,
  limit: 10,
  count: 0,
  abnormal: false,
});

const tableEmptyConf = ref({
  keyword: '',
  isAbnormal: false,
});

const methodsList = [
  {
    text: 'GET',
    value: 'GET',
  },
  {
    text: 'POST',
    value: 'POST',
  },
  {
    text: 'PUT',
    value: 'PUT',
  },
  {
    text: 'PATCH',
    value: 'PATCH',
  },
  {
    text: 'DELETE',
    value: 'DELETE',
  },
  {
    text: 'HEAD',
    value: 'HEAD',
  },
  {
    text: 'OPTIONS',
    value: 'OPTIONS',
  },
  {
    text: 'ANY',
    value: 'ANY',
  },
];

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

const labelsList = computed(() => {
  if (!labels.value?.length) {
    return [];
  }
  tableDataKey.value = +new Date();
  return labels.value?.map((item: any) => {
    return {
      text: item.name,
      value: item.name,
    };
  });
});

watch(resourceVersionList, () => {
  getPageData();
});

watch(
  searchValue,
  () => {
    pagination.value.current = 1;
    pagination.value.limit = 10;
  },
);

watch(
  () => stageId,
  async () => {
    if (stageId) {
      await init();
      getPageData();
    }
  },
  { immediate: true },
);

const getLabels = async () => {
  labels.value = await getGatewayLabels(gatewayId.value);
};

const showDetails = (row: any) => {
  setHighlight(row.name);
  info.value = row;
  resourceDetailsRef.value?.showSideslider();
};

const copyPath = (row: any) => {
  copy(stageAddress.replace(/\/$/, '') + row?.path);
};

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
    const res = await getVersionDetail(gatewayId.value, curVersionId, { stage_id: curStageData?.id });
    res.resources?.forEach((item: any) => {
      item.gateway_label_names = [];
      item?.gateway_label_ids?.forEach((id: string) => {
        const tagLabel = labels.value?.find((label: any) => label.id === id);
        if (tagLabel) {
          item.gateway_label_names?.push(tagLabel.name);
        }
      });
    });
    pagination.value.count = res.resources.length;
    resourceVersionList.value = res.resources || [];
  }
  catch (e) {
    // 接口404处理
    resourceVersionList.value = [];
    console.error(e);
  }
  finally {
    isLoading.value = false;
    isReload.value = false;
    emptyText.value = '暂无数据';
  }
};

const isHighlight = (v: any) => {
  return v.highlight ? 'row-cls' : '';
};

const setHighlight = (name: string) => {
  tableData.value?.forEach((item: any) => {
    item.highlight = item.name === name;
  });
};

const clearHighlight = () => {
  tableData.value?.forEach((item: any) => {
    item.highlight = false;
  });
};

// 查看环境
const handleCheckStage = ({ resourceName, backendName }: {
  resourceName: string
  backendName: string
}) => {
  setHighlight(resourceName);
  // 可传入 add | edit | check
  stageSidesliderRef.value?.handleShowSideslider('check', { backendName });
};

function getPageData() {
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
      ) {
        return true;
      }
      return false;
    });

    updateTableEmptyConfig();
  }

  if (chooseMethod.value?.length) {
    curAllData = curAllData?.filter((row: any) => {
      return !!chooseMethod.value?.includes(row?.method);
    });

    updateTableEmptyConfig();
  }

  if (chooseLabels.value?.length) {
    curAllData = curAllData?.filter((row: any) => {
      const flag = chooseLabels.value?.some((item: any) => row?.gateway_label_names?.includes(item));
      return !!flag;
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
  tableData.value = curAllData?.slice(startIndex, endIndex);
}

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
  if (searchValue.value || chooseMethod.value?.length || chooseLabels.value?.length || !tableData.value.length) {
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
  pagination.value = Object.assign(pagination.value, {
    current: 1,
    limit: 10,
    count: resourceVersionList.value.length,
  });
  getPageData();
};

async function init() {
  stageList.value = await getStageList(gatewayId.value);
  const curStageData = stageList.value.find((item: { id: number }) => item.id === Number(stageId));
  if (curStageData) {
    await getLabels();
    // 依赖 getLabels() 获取的标签列表，需在这之后请求
    await getResourceVersionsData(curStageData);
  }
}

defineExpose({ reload: init });
</script>

<style lang="scss" scoped>
.table-layout {
  margin-top: 15px;

  :deep(.row-cls){

    td {
      background: #e1ecff !important;
    }
  }

  :deep(.bk-table-head) {
    scrollbar-gutter: auto;
  }
}

.exception-empty {
  display: flex;
  height: 420px;
  align-items: center;

  :deep(.bk-exception-description) {
    margin-top: 0;
    font-size: 14px;
  }

  :deep(.bk-exception-img) {
    width: 220px;
    height: 130px;
  }
}

.plugin-tag {
  display: inline-block;
  width: 18px;
  height: 16px;
  font-size: 10px;
  line-height: 16px;
  text-align: center;
  vertical-align: middle;
  border-radius: 2px;

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
    opacity: 0%;
  }

  &:hover {

    .backend-edit {
      opacity: 100%;
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
