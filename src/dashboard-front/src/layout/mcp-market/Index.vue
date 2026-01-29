/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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
  <div class="mcp-market-wrapper">
    <img
      ref="bannerRef"
      :src="bannerImg"
      alt="banner"
      class="banner"
      loading="lazy"
      @error="bannerLoaded = true"
    >
    <div class="flex gap-16px main">
      <div
        ref="mcpCategorizeRef"
        class="bg-white min-w-200px h-100% mcp-categorize"
      >
        <div
          class="mcp-categorize-item mcp-categorize-all"
          :class="[{
            'active': activeCategoryName.includes('all')
          }]"
          @click.stop="handleCategoryChange('all')"
        >
          <div class="mcp-categorize-content">
            <svg class="icon svg-icon w-16px">
              <use xlink:href="#icon-ag-quanbu" />
            </svg>
            <div class="categorize-text">
              {{ t("全部") }}
            </div>
          </div>
          <div class="categorize-count">
            {{ categoriesCount }}
          </div>
        </div>

        <div
          v-for="categorize of categoriesList"
          :key="categorize.name"
          class="gap-8px mcp-categorize-item"
          :class="[{
            'active': activeCategoryName === categorize.name
          }]"
          @click.stop="handleCategoryChange(categorize.name)"
        >
          <div class="mcp-categorize-content">
            <div class="w-14px flex items-center justify-center">
              <div class="icon-circle" />
            </div>
            <div
              v-bk-tooltips="{
                placement:'top',
                content: categorize.display_name,
                disabled: !categorize.isOverflow,
              }"
              class="truncate categorize-text"
              @mouseenter="(e: MouseEvent) => handleMouseenter(e, categorize)"
              @mouseleave="(e: MouseEvent) => handleMouseleave(e, categorize)"
            >
              {{ categorize.display_name }}
            </div>
          </div>
          <div class="categorize-count">
            {{ categorize.mcp_server_count }}
          </div>
        </div>
      </div>
      <div
        class="right"
        :style="{ width: `calc(100% - ${mcpCategorizeWidth}px)` }"
      >
        <AgMcpTopBar
          v-model:publish-time="filterData.order_by"
          class="mb-16px"
          @sort-change="handleSortChange"
        >
          <template #mcpServerTab>
            <div class="flex mcp-server-tab">
              <div
                v-for="tab of mcpTabList"
                :key="tab.id"
                class="flex items-center mcp-server-tab-item min-w-48px!"
                :class="[
                  {
                    'is-active': tab.id === activeStatusTab,
                  },
                ]"
                @click.stop="handleTopTabChange(tab.id)"
              >
                <div>{{ tab.name }}</div>
              </div>
            </div>
          </template>
          <template #customSearch>
            <BkInput
              v-model="filterData.keyword"
              :placeholder="t('搜索 MCP 名称、展示名、描述')"
              clearable
            />
          </template>
        </AgMcpTopBar>
        <!-- 卡片区域内容 -->
        <BkLoading
          :loading="isLoading"
          :z-index="99"
          color="#f5f7fb"
          :class="[
            { 'mt-100px': mcpMarketList.length < 1 && !isFirstLoad },
            { 'min-h-200px': isLoading }
          ]"
        >
          <div class="mcp-market-list">
            <template v-if="mcpMarketList.length < 1 && !isLoading">
              <TableEmpty
                background="#f5f7fa"
                :empty-type="cardEmptyType"
                @clear-filter="handleClearFilter"
                @refresh="handleRefresh"
              />
            </template>
            <template v-else>
              <AgMcpCard
                v-for="server of mcpMarketList"
                :key="server.id"
                :server="server"
                :show-actions="false"
                @click="() => handleCardClick(server.id)"
              >
                <template
                  v-if="server?.is_official"
                  #officialTag
                >
                  <BkTag
                    theme="success"
                    class="ml-8px"
                  >
                    {{ t("官方") }}
                  </BkTag>
                </template>
                <template
                  v-if="server?.is_featured"
                  #mcpStatus
                >
                  <div class="bg-#f8b64f featured card-header-status">
                    {{ t('精选') }}
                  </div>
                </template>
              </AgMcpCard>
            </template>
          </div>
        </BkLoading>
        <!-- 触底翻页触发器 -->
        <div
          v-intersection-observer="onIntersectionObserver"
          class="h-40px"
        />
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { debounce } from 'lodash-es';
import {
  type IMCPMarketCategory,
  type IMarketplaceItem,
  getMcpMarketplace,
  getMcpMarketplaceCategories,
} from '@/services/source/mcp-market';
import { type IPagination } from '@/types/common';
import { vIntersectionObserver } from '@vueuse/components';
import { useFeatureFlag } from '@/stores';
import { filterSimpleEmpty } from '@/utils/filterEmptyValues';
import mcpBanner from '@/images/mcp-banner.jpg';
import mcpBannerEn from '@/images/mcp-banner-en.jpg';
import TableEmpty from '@/components/table-empty/Index.vue';
import AgMcpCard from '@/components/ag-mcp-card/Index.vue';
import AgMcpTopBar from '@/components/ag-mcp-search-bar/Index.vue';

const { t, locale } = useI18n();
const router = useRouter();
const featureFlagStore = useFeatureFlag();

const bannerRef = ref<HTMLImageElement>(null);
const mcpCategorizeRef = ref<HTMLDivElement>(null);
const isLoading = ref(false);
const bannerLoaded = ref(false);
// 标记首次数据加载是否完成
const isFirstLoad = ref(true);
// 标记Banner加载完成后是否已初始化过分页
const isBannerLoadedInit = ref(false);
// 标记是否正在切换分类（用于冻结计数显示）
const isSwitchingCategory = ref(false);
const mcpCategorizeWidth = ref(0);
const cachedViewportHeight = ref(0);
const activeStatusTab = ref('all');
const activeCategoryName = ref('all');
const cardEmptyType = ref<'empty' | 'searchEmpty' | 'error'>('');
const filterData = ref({
  order_by: '-updated_time',
  keyword: '',
});
const mcpMarketList = ref<IMarketplaceItem[]>([]);
const categoriesList = ref<IMCPMarketCategory[]>([]);

const pagination = ref<Omit<IPagination, 'hasNoMore'>>({
  current: 1,
  limit: 0,
  count: 0,
  hasNoMore: false,
});

const isShowNoticeAlert = computed(() => featureFlagStore.isEnabledNotice);
const bannerImg = computed(() => {
  if (locale.value === 'zh-cn') {
    return mcpBanner;
  }
  return mcpBannerEn;
});
const categoriesCount = computed(() => {
  if (activeCategoryName.value.includes('all')) {
    // 正在切换分类时，返回空/加载占位（避免显示旧值）
    if (isSwitchingCategory.value) {
      return 0;
    }
    return pagination.value.count ?? 0;
  }

  return categoriesList.value?.reduce((accumulator: number, current: IMCPMarketCategory) => {
    return accumulator + current.mcp_server_count;
  }, 0) ?? 0;
});
const mcpTabList = computed(() => [
  {
    name: t('全部'),
    id: 'all',
  },
  {
    name: t('官方'),
    id: 'Official',
  },
  {
    name: t('精选'),
    id: 'Featured',
  },
]);
// 获取筛选条件
const getFilterParams = computed(() => {
  const categorySegments = [
    activeCategoryName.value === 'all' ? undefined : activeCategoryName.value,
    activeStatusTab.value === 'all' ? undefined : activeStatusTab.value,
  ].filter(Boolean);

  const categoryParam = categorySegments.length > 0 ? categorySegments.join(',') : undefined;
  const params = {
    ...filterSimpleEmpty(filterData.value),
    ...(categoryParam ? { categories: categoryParam } : {}),
  };

  return params;
});

// 获取banner高度的方法，增加图片加载监听
const getBannerHeight = () => {
  if (!bannerRef.value) return 0;

  // 若图片已加载，直接返回高度
  if (bannerLoaded.value) {
    return bannerRef.value.offsetHeight;
  }

  // 监听图片加载事件
  bannerRef.value.addEventListener('load', () => {
    bannerLoaded.value = true;
    // 图片加载完成后重新计算分页limit
    if (!isBannerLoadedInit.value) {
      isBannerLoadedInit.value = true;
      resetPagination();
    }
  }, { once: true });

  // 加载中先返回默认高度（或图片的固有高度）
  return bannerRef.value.naturalHeight || 0;
};

/**
 * 计算可视区域可展示的最大卡片数量
 * @returns {number} 最大卡片数（预留一行用于加载更多）
 * @description 计算逻辑：页面可用高度 = 视口高度 - 页面边距 - 导航栏高度 - banner高度 - 通知栏高度
 *              最大行数 = 页面可用高度 / 单卡片高度（含间距）
 *              最大卡片数 = 行数 * 每行卡片数 + 预留行卡片数
 */
const calculateMaxVisibleCards = () => {
  // 通知栏高度40px
  const noticeH = isShowNoticeAlert.value ? 40 : 0;
  // banner图高度
  const bannerH = getBannerHeight();
  // 获取页面可用高度（排除顶部导航/内边距）, 40px=页面边距(24+16)，52px=导航栏高度
  const pageH = window.innerHeight - 40 - 52 - bannerH - noticeH;

  // 获取单卡片最小高度和每行卡片数
  const singleCardHeight = 238 + 16;
  const cardsPerRow = 3;

  // 计算可展示行数
  const maxRows = Math.floor(pageH / singleCardHeight);

  // 计算最大可展示卡片数
  const maxCards = Math.max(maxRows * cardsPerRow, 3);

  // 预留一行空间用于触发加载更多
  return maxCards + cardsPerRow;
};

const getList = async () => {
  const { hasNoMore, current, limit } = pagination.value;
  isLoading.value = true;
  cardEmptyType.value = Object.keys(filterSimpleEmpty(filterData.value)).length > 0 ? 'searchEmpty' : 'empty';

  if (hasNoMore) {
    isLoading.value = false;
    return;
  };

  try {
    const params = {
      limit,
      offset: limit * (current - 1),
      ...getFilterParams.value,
    };
    const res = await getMcpMarketplace(params);
    const { results = [], count = 0 } = res ?? {};
    mcpMarketList.value = current === 1 ? results : [...mcpMarketList.value, ...results];
    pagination.value = {
      ...pagination.value,
      count,
      hasNoMore: mcpMarketList.value.length >= count,
      current: current + 1,
    };
    // 处理每个分类筛选结果
    if (activeCategoryName.value) {
      const curCate = categoriesList.value.find(cat => cat.name === activeCategoryName.value);
      if (curCate) {
        curCate.mcp_server_count = count;
      }
    }
  }
  catch {
    cardEmptyType.value = 'error';
  }
  finally {
    isFirstLoad.value = false;
    setTimeout(() => {
      isLoading.value = false;
    }, 100);
  }
};

const fetchCategoryList = async () => {
  const res = await getMcpMarketplaceCategories(getFilterParams.value);
  categoriesList.value = (res ?? []).filter(cg => !['Official', 'Featured'].includes(cg.name));
  mcpCategorizeWidth.value = mcpCategorizeRef.value?.offsetWidth;
};

const resetPagination = async () => {
  // 重置分页后，滚动距离重置
  const mcpEl = document.querySelector('.McpMarket-navigation-content .container-content');
  if (mcpEl?.scrollTop > 0) {
    mcpEl.scrollTop = 0;
  }
  pagination.value = Object.assign(pagination.value, {
    current: 1,
    limit: calculateMaxVisibleCards(),
    hasNoMore: false,
  });
  await getList();
};

const handleCategoryChange = async (value: string) => {
  if (value === activeCategoryName.value) return;

  isSwitchingCategory.value = true;
  activeCategoryName.value = value;

  try {
    await resetPagination();
  }
  finally {
    isSwitchingCategory.value = false;
  }
};

const handleTopTabChange = (value: string) => {
  if (value === activeStatusTab.value) return;
  activeStatusTab.value = value;
  resetPagination();
  fetchCategoryList();
};

const handleSortChange = (sort: string) => {
  filterData.value.order_by = sort;
  resetPagination();
};

const handleSearch = () => {
  resetPagination();
  fetchCategoryList();
};

const handleMouseenter = (e: MouseEvent & { target: HTMLElement }, row: IMarketplaceItem) => {
  const cell = e.target.closest('.truncate');
  if (cell) {
    row.isOverflow = cell.scrollWidth > cell.offsetWidth;
  }
};

const handleMouseleave = (_: MouseEvent, row: IMarketplaceItem) => {
  row.isOverflow = false;
};

const handleCardClick = (id: number) => {
  router.push({
    name: 'McpMarketDetails',
    params: { id },
  });
};

const handleClearFilter = () => {
  filterData.value = {
    order_by: '-updated_time',
    keyword: '',
  };
};

const handleRefresh = () => {
  resetPagination();
};

const onIntersectionObserver = ([entry]: IntersectionObserverEntry[]) => {
  // 首次加载未完成 → 不触发；仅加载更多时触发
  if (entry?.isIntersecting && !isFirstLoad.value) {
    getList();
  }
};

const handleResize = debounce(() => {
  const newViewportHeight = window.innerHeight;
  // 仅当视口高度变化超过 30px 时才重新计算
  if (Math.abs(newViewportHeight - (cachedViewportHeight.value || 0)) > 30) {
    cachedViewportHeight.value = newViewportHeight;
    const newLimit = calculateMaxVisibleCards();
    if (pagination.value.limit !== newLimit) {
      pagination.value.limit = newLimit || 3;
      resetPagination();
    }
  }
}, 500);

watch(
  () => filterData.value.keyword,
  () => {
    handleSearch();
  },
);

onMounted(() => {
  window.addEventListener('resize', handleResize);
  Promise.allSettled([fetchCategoryList()])
    .then(() => {
      // 分类加载完成后再初始化分页，避免分类数据缺失
      resetPagination();
    });
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  handleResize?.cancel();
  if (bannerRef.value) {
    bannerRef.value.removeEventListener('load', () => {
    });
  }
});
</script>

<style lang="scss" scoped>
.mcp-market-wrapper {
  box-sizing: border-box;

  .banner {
    width: 100%;
    min-width: 1280px;
  }

  .main {
    padding: 24px;

    .mcp-categorize {
      position: sticky;
      top: 24px;

      .mcp-categorize-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 36px;
        padding: 0 12px;
        transition: background-color 0.2s;
        box-sizing: border-box;
        cursor: pointer;

        .mcp-categorize-content {
          flex: 1;
          display: flex;
          align-items: center;
          font-size: 14px;
          height: 36px;

          .icon-circle {
            width: 4px;
            height: 4px;
            background-color: #d9d9d9;
          }

          .categorize-text {
            max-width: 120px;
            margin-left: 8px;
          }
        }

        .categorize-count {
          display: flex;
          align-items: center;
          gap: 0 4px;
          height: 16px;
          padding: 0 6px;
          border-radius: 8px;
          font-size: 10px;
          color: #4d4f56;
          background-color: #f0f1f5;
          min-width: fit-content;
        }

        &.active {
          background-color: #e1ecff;
          color: #3a84Ff;
        }

        &:hover:not(.active) {
          background-color: #f9fafc;
        }

        &.mcp-categorize-all {
          border-bottom: 1px solid #eaebf0;
        }
      }
    }

    .right {
      position: relative;
      box-sizing: border-box;

      :deep(.mcp-market-list) {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        background-color: #f5f7fb;

        .ag-mcp-card-wrapper {
          width: calc(33.3333% - 10.6667px);
        }
      }

      .empty-wrapper {
        position: absolute;
        padding-top: 120px;
      }
    }
  }
}
</style>
