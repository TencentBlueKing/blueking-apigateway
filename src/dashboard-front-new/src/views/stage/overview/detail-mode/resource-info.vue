<template>
  <div class="resource-info">
    <bk-input
      v-model="searchValue"
      style="width: 520px"
      clearable
      type="search"
      :placeholder="t('请输入后端服务名称、资源名称、请求路径或选择条件搜索')"
    />
    <bk-loading :loading="isLoading">
      <bk-table
        class="table-layout mt15"
        :data="curPageData"
        remote-pagination
        :pagination="pagination"
        :empty-text="emptyText"
        show-overflow-tooltip
        row-hover="auto"
        border="outer"
        settings
        @page-limit-change="handlePageSizeChange"
        @page-value-change="handlePageChange"
      >
        <bk-table-column :label="t('后端服务')">
          <template #default="{ data }">
            {{ data?.proxy?.backend?.name }}
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('资源名称')"
          prop="name"
          sort
        ></bk-table-column>
        <bk-table-column
          :label="t('前端请求方法')"
          prop="method"
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
        <bk-table-column :label="t('标签')">
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
        <bk-table-column
          :label="t('生效的插件')"
        >
          <template #default="{ data }">
            <template v-if="data?.plugins?.length">
              <span v-for="p in data.plugins" :key="p?.id">
                <bk-tag theme="success" v-if="p?.binding_type === 'stage'">环</bk-tag>
                <bk-tag theme="info" v-if="p?.binding_type === 'resource'">资</bk-tag>
                {{ p?.name }}
              </span>
            </template>
            <span v-else>--</span>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('是否公开')"
          prop="is_public"
        >
          <template #default="{ row }">
            <span :style="{ color: row.is_public ? '#FE9C00' : '#63656e' }">
              {{ row.is_public ? t('是') : t('否') }}
            </span>
          </template>
        </bk-table-column>
        <bk-table-column
          :label="t('操作')"
          prop="name"
        >
          <bk-button
            text
            theme="primary"
            class="mr10"
          >
            {{ t('查看资源详情') }}
          </bk-button>
          <bk-button
            text
            theme="primary"
          >
            {{ t('复制资源地址') }}
          </bk-button>
        </bk-table-column>
      </bk-table>
    </bk-loading>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { getResourceVersionsInfo, getGatewayLabels } from '@/http';
import { useCommon, useStage } from '@/store';

const { t } = useI18n();
const common = useCommon();
const stageStore = useStage();

const props = defineProps<{
  versionId: number;
}>();

const searchValue = ref<string>('');

const isReload = ref(false);
const emptyText = ref<string>('暂无数据');

// 网关标签
const labels = ref<any[]>([]);

// 网关id
const { apigwId } = common;
const isLoading = ref(false);

const pagination = ref({
  current: 1,
  limit: 10,
  count: 0,
});

const getLabels = async () => {
  try {
    const res = await getGatewayLabels(apigwId);
    labels.value = res;
  } catch (e) {
    console.log(e);
  }
};

// 资源信息
const resourceVersionList = ref([]);

watch(
  () => props.versionId,
  () => {
    if (isReload.value) {
      // 页面强制刷新 versionId 为空处理
      getResourceVersionsData();
    }
  },
);

// 获取资源信息数据
const getResourceVersionsData = async () => {
  isLoading.value = true;
  if (props.versionId === undefined) {
    isReload.value = true;
    return;
  }
  // 没有版本无需请求
  if (props.versionId === 0) {
    isLoading.value = false;
    emptyText.value = '环境没有发布，数据为空';
    return;
  }
  try {
    const res = await getResourceVersionsInfo(apigwId, props.versionId, { stage_id: stageStore.curStageId });
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
getResourceVersionsData();
getLabels();

// 当前页数据
const curPageData = computed(() => {
  let allData = resourceVersionList.value;
  if (searchValue.value) {
    allData = allData?.filter((row: any) => {
      if (
        row?.proxy?.backend?.name?.toLowerCase()?.includes(searchValue.value)
      || row?.name?.toLowerCase()?.includes(searchValue.value)
      || row?.path?.toLowerCase()?.includes(searchValue.value)
      )  {
        return true;
      }
      return false;
    });
  }

  // 当前页数
  const page = pagination.value.current;
  // limit 页容量
  let startIndex = (page - 1) * pagination.value.limit;
  let endIndex = page * pagination.value.limit;
  if (startIndex < 0) {
    startIndex = 0;
  }
  if (endIndex > allData.length) {
    endIndex = allData.length;
  }
  return allData.slice(startIndex, endIndex);
});

// 页码变化发生的事件
const handlePageChange = (current: number) => {
  isLoading.value = true;
  pagination.value.current = current;
  setTimeout(() => {
    isLoading.value = false;
  }, 200);
};

// 条数变化发生的事件
const handlePageSizeChange = (limit: number) => {
  isLoading.value = true;
  pagination.value.limit = limit;
  setTimeout(() => {
    isLoading.value = false;
  }, 200);
};
</script>

<style lang="scss" scoped></style>
