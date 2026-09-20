/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
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
  <div
    v-show="showTips"
    class="resource-alert-tips"
  >
    <AgIcon
      class="tips-icon"
      name="info-fill"
      color="#FF9C01"
      size="16"
    />
    <div class="tips-content">
      <!-- 资源版本提示与路由冲突汇总合并到同一个提示框内，两者显隐条件各自独立 -->
      <div
        v-if="needNewVersion"
        class="version-tips"
      >
        {{ versionMessage }}
        <BkButton
          text
          theme="primary"
          @click="handleCreateVersion"
        >
          {{ t('立即生成版本') }}
        </BkButton>
      </div>

      <template v-if="showConflictTips">
        <div class="conflict-title">
          {{ t('检测到 {count} 个资源存在路由冲突', { count: conflictRows.length }) }}
        </div>
        <div class="conflict-desc">
          {{ t('这些资源的请求方法与路径可能互相覆盖，实际请求可能命中非预期资源。') }}
          <span>{{ t('冲突最多的资源与 {count} 个资源重叠。', { count: maxConflictCount }) }}</span>
          <a
            class="tips-link"
            target="_blank"
            :href="envStore.env.DOC_LINKS.ROUTE_MATCH_RULES"
          >
            {{ t('查看路由匹配规则') }}
          </a>
          <span
            class="tips-toggle"
            @click="toggleExpanded"
          >
            {{ isExpanded ? t('收起') : t('展开') }}
            <AgIcon
              class="tips-toggle-icon"
              :class="{ 'is-expanded': isExpanded }"
              name="down-shape"
              size="12"
            />
          </span>
        </div>
        <div
          v-show="isExpanded"
          class="tips-table"
        >
          <AgTable
            :table-data="conflictRows"
            :columns="columns"
            row-class-name="cursor-pointer"
            :max-height="TABLE_MAX_HEIGHT"
            local-page
            :immediate="false"
            :show-pagination="false"
            :show-settings="false"
            :cache-identifier="TABLE_CACHE_IDENTIFIER"
            :cache-settings-in-local-storage="false"
            expand-on-row-click
            :expanded-row-keys="expandedRowKeys"
            @expand-change="handleExpandChange"
          >
            <template #expandedRow="{ row }">
              <div class="conflict-detail">
                <div class="detail-title">
                  {{ t('可能与以下 {count} 个资源冲突：', { count: row.conflicts.length }) }}
                </div>
                <div class="detail-list">
                  <div
                    v-for="item in getVisibleConflicts(row)"
                    :key="item.id"
                    class="detail-item"
                  >
                    <div
                      v-bk-tooltips="getDetailTooltip(item.name, item.id, 'name')"
                      class="detail-item-name"
                      @mouseenter="markDetailOverflow($event, item.id, 'name')"
                    >
                      {{ item.name }}
                    </div>
                    <div class="detail-item-path">
                      <BkTag :theme="getMethodTheme(item.method)">
                        {{ item.method }}
                      </BkTag>
                      <span
                        v-bk-tooltips="getDetailTooltip(item.path, item.id, 'path')"
                        class="detail-item-path-text"
                        @mouseenter="markDetailOverflow($event, item.id, 'path')"
                      >{{ item.path }}</span>
                    </div>
                  </div>
                </div>
                <div
                  v-if="!isShowAllDetail && getHiddenConflictCount(row) > 0"
                  class="detail-remaining"
                >
                  <span
                    class="tips-link"
                    @click="showAllDetail"
                  >
                    {{ t('显示剩余 {count} 个', { count: getHiddenConflictCount(row) }) }}
                  </span>
                </div>
              </div>
            </template>
          </AgTable>
        </div>
      </template>
    </div>
  </div>
</template>

<script lang="tsx" setup>
import type { PrimaryTableProps, TableRowData } from '@blueking/tdesign-ui';
import type { IResourcePathConflictGroupOutput } from '@/services/types/responses/gateways.ts';
import { getResourcePathConflicts } from '@/services/source/resource';
import { useEnv } from '@/stores';
import { useFeatureFlag } from '@/stores/useFeatureFlag';
import { METHOD_THEMES } from '@/enums';
import AgTable from '@/components/ag-table/Index.vue';
import AgIcon from '@/components/ag-icon/Index.vue';

interface IConflictPartner {
  id: number
  name: string
  method: string
  path: string
}

interface IConflictRow {
  id: number
  name: string
  method: string
  path: string
  conflicts: IConflictPartner[]
}

interface IProps {
  gatewayId: number
  // 资源是否有更新：仅据此显示版本提示，版本提示文案由后端返回，非空不代表有更新
  needNewVersion?: boolean
  versionMessage?: string
  // 由外层上下文决定是否展示，例如详情面板展开时隐藏；显隐统一由组件内部的 v-show 控制
  hidden?: boolean
}

interface IEmits {
  'create-version': []
}

// 明细卡片里会被省略号截断、需要 tooltip 兜底的字段
type IDetailField = 'name' | 'path';

const {
  gatewayId,
  needNewVersion = false,
  versionMessage = '',
  hidden = false,
} = defineProps<IProps>();
const emit = defineEmits<IEmits>();

const featureFlagStore = useFeatureFlag();
const envStore = useEnv();
const { t } = useI18n();

const conflictRows = ref<IConflictRow[]>([]);
const isExpanded = ref(false);
const isShowAllDetail = ref(false);
const expandedRowKeys = ref<Array<number>>([]);
// 明细卡片里的名称/路径是否被省略号截断
const detailOverflow = ref<Record<number, Partial<Record<IDetailField, boolean>>>>({});

// 展开行里的明细卡片默认展示的个数（宽屏下为 3 行），其余点击「显示剩余 N 个」后展开
const DEFAULT_VISIBLE_CARDS = 12;
// 紧凑表最大高度，超出后表格内部滚动
const TABLE_MAX_HEIGHT = 360;
// 与主表同处一个路由，表格设置的缓存 key 会退化成路由名而互相串用，
// 主表隐藏的列会把紧凑表的列一起隐藏掉，因此这里单独给一个标识
const TABLE_CACHE_IDENTIFIER = 'resource-path-conflicts';
// 冲突资源不超过该数量时不收起，直接展示明细
const COLLAPSE_THRESHOLD = 3;
// 明细卡片 tooltip 的最大宽度
const DETAIL_TOOLTIP_CLS = 'max-w-480px';
// 首次取到数据时才设置默认展开状态，后续刷新不覆盖用户的手动操作
let isExpandInitialized = false;

// 路由冲突汇总单独由 feature flag 控制，与版本提示的显隐互不影响
const showConflictTips = computed(() => featureFlagStore.isEnablePathConflictCheck && conflictRows.value.length > 0);
const showTips = computed(() => !hidden && (needNewVersion || showConflictTips.value));
const maxConflictCount = computed(
  () => conflictRows.value.reduce((max, row) => Math.max(max, row.conflicts.length), 0),
);
const columns = computed<PrimaryTableProps['columns']>(() => [
  {
    colKey: 'name',
    title: t('资源'),
    ellipsis: true,
    minWidth: 200,
  },
  {
    colKey: 'method',
    title: t('请求方法'),
    width: 140,
    cell: (_h: unknown, { row }: { row: TableRowData }) => (
      <bk-tag theme={METHOD_THEMES[row.method as keyof typeof METHOD_THEMES]}>
        {row.method}
      </bk-tag>
    ),
  },
  {
    colKey: 'path',
    title: t('请求路径'),
    ellipsis: true,
    minWidth: 260,
  },
  {
    colKey: 'conflicts',
    title: t('冲突数'),
    width: 200,
    cell: (_h: unknown, { row }: { row: TableRowData }) => (
      <span class="conflict-count">{t('与 {count} 个资源冲突', { count: row.conflicts.length })}</span>
    ),
  },
]);

/**
 * 把后端冲突组数据转换为「资源 -> 与其冲突的其他资源」。
 * 每个冲突组以 resources[0] 作为主行展示，组内其余资源作为该主行的冲突项；
 * 后端 normalized_path 组内两两互相冲突，literal_parameter 组仅保证基准资源与
 * 其他路径重叠、组内资源之间不保证两两冲突，因此只信任 resources[0] 为主行。
 */
const buildConflictRows = (conflicts: IResourcePathConflictGroupOutput[]): IConflictRow[] => (
  conflicts
    .flatMap((group) => {
      const primary = group.resources[0];
      if (!primary || primary.id === null) return [];
      return [{
        id: primary.id,
        name: primary.name || primary.path,
        method: primary.method,
        path: primary.path,
        conflicts: group.resources.slice(1).flatMap((r) => {
          if (r.id === null) return [];
          return [{
            id: r.id,
            name: r.name || r.path,
            method: r.method,
            path: r.path,
          }];
        }),
      }];
    })
    .sort((a, b) => b.conflicts.length - a.conflicts.length || a.path.localeCompare(b.path))
);

const fetchConflicts = async () => {
  // 未开启冲突检测时不请求，也不展示汇总
  if (!featureFlagStore.isEnablePathConflictCheck) {
    conflictRows.value = [];
    return;
  }

  try {
    const res = await getResourcePathConflicts(gatewayId);
    conflictRows.value = buildConflictRows(res?.conflicts ?? []);

    if (!isExpandInitialized && conflictRows.value.length) {
      isExpanded.value = conflictRows.value.length <= COLLAPSE_THRESHOLD;
      isExpandInitialized = true;
    }
  }
  catch (error) {
    conflictRows.value = [];
    console.log(error);
  }
};

watch(
  () => gatewayId,
  () => {
    isExpandInitialized = false;
    isShowAllDetail.value = false;
    expandedRowKeys.value = [];
    fetchConflicts();
  },
  { immediate: true },
);

// feature flag 是异步拉取的，拉取前挂载会走进空分支，开关变化时需要补一次检测
watch(
  () => featureFlagStore.isEnablePathConflictCheck,
  () => {
    isExpandInitialized = false;
    isShowAllDetail.value = false;
    expandedRowKeys.value = [];
    fetchConflicts();
  },
);

const getMethodTheme = (method: string) => METHOD_THEMES[method as keyof typeof METHOD_THEMES];

const getVisibleConflicts = (row: IConflictRow) => (
  isShowAllDetail.value ? row.conflicts : row.conflicts.slice(0, DEFAULT_VISIBLE_CARDS)
);

const getHiddenConflictCount = (row: IConflictRow) => Math.max(row.conflicts.length - DEFAULT_VISIBLE_CARDS, 0);

const isDetailOverflow = (id: number, field: IDetailField) => !!detailOverflow.value[id]?.[field];

// 未被截断时禁用 tooltip，避免短文本也弹层
const getDetailTooltip = (content: string, id: number, field: IDetailField) => ({
  content,
  extCls: DETAIL_TOOLTIP_CLS,
  disabled: !isDetailOverflow(id, field),
});

const markDetailOverflow = (event: MouseEvent, id: number, field: IDetailField) => {
  const el = event.currentTarget as HTMLElement;
  detailOverflow.value[id] = {
    ...detailOverflow.value[id],
    [field]: el.scrollWidth > el.clientWidth,
  };
};

const handleCreateVersion = () => {
  emit('create-version');
};

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value;
};

const showAllDetail = () => {
  isShowAllDetail.value = true;
};

// 一次只保留一行明细展开
const handleExpandChange = (
  expandedKeys: Array<string | number>,
  { currentRowData }: { currentRowData: TableRowData },
) => {
  expandedRowKeys.value = expandedKeys.includes(currentRowData.id) ? [currentRowData.id] : [];
  // 切换展开行时，明细卡片回到默认展示的数量
  isShowAllDetail.value = false;
};

defineExpose({ refresh: fetchConflicts });
</script>

<style lang="scss" scoped>
.resource-alert-tips {
  display: flex;
  padding: 8px 10px;
  color: #63656E;
  font-size: 12px;
  background-color: #FFF4E2;
  border: 1px solid #FFDFAC;
  border-radius: 2px;

  .tips-icon {
    flex-shrink: 0;
    align-self: flex-start;
    margin-right: 8px;
    line-height: 20px;
  }

  .tips-content {
    flex: 1;
    min-width: 0;

    > :first-child {
      margin-top: 0;
    }
  }

  .version-tips {
    line-height: 20px;
  }

  .conflict-title {
    margin-top: 12px;
    font-weight: 700;
    color: #FF9C01;
    line-height: 20px;
  }

  .conflict-desc {
    margin-top: 4px;
    line-height: 20px;
  }

  .tips-link {
    margin-left: 8px;
    color: #3A84FF;
    cursor: pointer;
  }

  .tips-toggle {
    display: inline-flex;
    align-items: center;
    margin-left: 8px;
    color: #3A84FF;
    cursor: pointer;

    .tips-toggle-icon {
      margin-left: 4px;
      transition: transform .3s;

      &.is-expanded {
        transform: rotate(180deg);
      }
    }
  }

  .tips-table {
    margin-top: 12px;
    overflow: hidden;
    background-color: #FFF;
    border-radius: 2px;

    :deep([data-colkey='__col_setting__']),
    :deep(.t-table__cell--fixed-right) {
      display: none;
    }

    :deep(colgroup col:last-child) {
      width: 0 !important;
      min-width: 0 !important;
    }
  }

  :deep(.conflict-count) {
    color: #FF9C01;
  }

  .conflict-detail {
    text-align: left;

    .detail-title {
      margin-bottom: 8px;
      color: #313238;
    }

    .detail-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .detail-remaining {
      margin-top: 8px;

      .tips-link {
        margin-left: 0;
      }
    }

    .detail-item {
      min-width: 200px;
      max-width: 320px;
      padding: 8px 12px;
      background-color: #FFF;
      border: 1px solid #DCDEE5;
      border-radius: 2px;
    }

    .detail-item-name {
      overflow: hidden;
      color: #313238;
      font-weight: 700;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .detail-item-path {
      display: flex;
      align-items: center;
      margin-top: 4px;
    }

    .detail-item-path-text {
      margin-left: 4px;
      overflow: hidden;
      color: #63656E;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}
</style>
