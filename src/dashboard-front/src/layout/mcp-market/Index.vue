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
    <div
      v-if="isBannerVisible"
      class="banner-wrapper"
    >
      <img
        ref="bannerRef"
        :src="bannerImg"
        alt="banner"
        class="banner"
        loading="lazy"
        @error="bannerLoaded = true"
      >
      <AgIcon
        name="icon-close"
        class="banner-close"
        size="20"
        @click="handleCloseBanner"
      />
    </div>
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
                content: categorize.display_name ?? '',
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
        <!-- 顶部操作栏：吸顶固定，不随卡片列表滚动 -->
        <div class="mcp-market-top-bar">
          <AgMcpTopBar
            v-model:publish-time="filterData.order_by"
            :selections="selections"
            @batch-copy="handleBatchCopy"
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
        </div>
        <!-- 卡片区域内容 -->
        <BkLoading
          :loading="isLoading && !isLoadMore"
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
                :show-public="false"
                :oauth2-tooltip="t('已开启 OAuth2 公开客户端模式，用户通过浏览器授权即可使用')"
                @selection-change="handleSelectionChange"
                @checked="(isChecked: boolean) => handleChecked(isChecked, server)"
                @click.stop="() => handleView(server.id)"
              >
                <template #externalTag>
                  <BkTag
                    v-if="server?.is_official"
                    theme="success"
                    class="h-18px"
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
                <template #mcpCopyConfig>
                  <BkButton
                    text
                    class="mr-16px color-#979ba5! copy-config-btn"
                    @click.stop="handleCopyConfig(server)"
                  >
                    <AgIcon
                      name="copy"
                      class="mr-4px"
                      size="16"
                    />
                    {{ t("复制配置") }}
                  </BkButton>
                </template>
              </AgMcpCard>
            </template>
          </div>
        </BkLoading>
        <!-- 复制 MCP 配置 -->
        <AgMcpCopyConfigDialog
          v-model:is-show="isShowConfig"
          :loading="copyConfigLoading"
          :list="mcpConfigList"
        />
        <!-- 触底翻页触发器 -->
        <div
          ref="bottomTriggerRef"
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
  type IMarketplaceItemWithUIState,
  getMcpBatchCopyConfigList,
  getMcpMarketplace,
  getMcpMarketplaceCategories,
} from '@/services/source/mcp-market';
import { type IPagination, type ITableEmptyType } from '@/types/common';
import { vIntersectionObserver } from '@vueuse/components';
import { useFeatureFlag } from '@/stores';
import { useMcpBatchCopyConfig } from '@/hooks';
import { filterSimpleEmpty } from '@/utils/filterEmptyValues';
import mcpBanner from '@/images/mcp-banner.jpg';
import mcpBannerEn from '@/images/mcp-banner-en.jpg';
import TableEmpty from '@/components/table-empty/Index.vue';
import AgMcpCard from '@/components/ag-mcp-card/Index.vue';
import AgMcpTopBar from '@/components/ag-mcp-search-bar/Index.vue';
import AgMcpCopyConfigDialog from '@/components/ag-mcp-card/components/CopyConfigDialog.vue';

const { t, locale } = useI18n();
const router = useRouter();
const featureFlagStore = useFeatureFlag();
// 批量复制配置hooks
const {
  copyConfigLoading,
  mcpConfigList,
  fetchMcpBatchCopyConfigList,
} = useMcpBatchCopyConfig({
  fetchApi: getMcpBatchCopyConfigList,
});

const bannerRef = ref<HTMLImageElement | null>(null);
const mcpCategorizeRef = ref<HTMLDivElement | null>(null);
const isLoading = ref(false);
const bannerLoaded = ref(false);
// 标记 banner 是否展示（支持关闭）
const isBannerVisible = ref(true);
// 标记首次数据加载是否完成
const isFirstLoad = ref(true);
// 标记Banner加载完成后是否已初始化过分页
const isBannerLoadedInit = ref(false);
// 标记是否正在切换分类（用于冻结计数显示）
const isSwitchingCategory = ref(false);
// 触底触发器元素，重置分页后需要按真实位置重新校准就绪状态
const bottomTriggerRef = ref<HTMLDivElement | null>(null);
// 触底触发器是否已就绪：只有触发器离开过视口，再次进入视口才认为是用户滚动到底，
// 用于忽略重置分页后因列表高度塌陷而补发的触底回调
const isBottomTriggerArmed = ref(true);
// 显示复制 MCP Server 接入配置
const isShowConfig = ref(false);
const mcpCategorizeWidth = ref(0);
const cachedViewportHeight = ref(0);
const activeStatusTab = ref('all');
const activeCategoryName = ref('all');
const cardEmptyType = ref<ITableEmptyType>('empty');
const filterData = ref({
  order_by: '-updated_time',
  keyword: '',
});
const mcpMarketList = ref<IMarketplaceItemWithUIState[]>([]);
// 标记当前是否为触底加载更多（翻页时避免展示全列表 loading 遮罩导致闪屏）
const isLoadMore = ref(false);
const categoriesList = ref<IMCPMarketCategory[]>([]);
const pagination = ref<IPagination & { hasNoMore?: boolean }>({
  current: 1,
  limit: 0,
  count: 0,
  hasNoMore: false,
});
// 批量复制内容
const selections = ref<Map<number, IMarketplaceItemWithUIState>>(new Map());

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
      return '...';
    }
    return pagination.value.count ?? 0;
  }

  return categoriesList.value?.reduce((accumulator: number, current: IMCPMarketCategory) => {
    return accumulator + (current.mcp_server_count ?? 0);
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

const handleBannerLoad = () => {
  bannerLoaded.value = true;
  // 图片加载完成后重新计算分页limit（列表内容不变，保留已选中的 MCP Server）
  if (!isBannerLoadedInit.value) {
    isBannerLoadedInit.value = true;
    resetPagination(true);
  }
};

const handleCloseBanner = () => {
  isBannerVisible.value = false;
  // banner 关闭后高度变化，重新计算可视区域卡片数（列表内容不变，保留已选中的 MCP Server）
  nextTick(() => {
    resetPagination(true);
  });
};

// 获取banner高度的方法，增加图片加载监听
const getBannerHeight = () => {
  if (!bannerRef.value) return 0;

  // 若图片已加载，直接返回高度
  if (bannerLoaded.value) {
    return bannerRef.value.offsetHeight;
  }

  // 监听图片加载事件
  bannerRef.value.addEventListener('load', handleBannerLoad, { once: true });

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
  const { hasNoMore = false, current = 1, limit = 0 } = pagination.value;
  // 并发保护：加载中或已无更多数据时直接返回，
  // 防止滚动过程中 IntersectionObserver 连续回调导致同一页被重复请求、重复拼接
  if (isLoading.value || hasNoMore) return;
  isLoadMore.value = current > 1;
  isLoading.value = true;
  cardEmptyType.value = Object.keys(filterSimpleEmpty(filterData.value)).length > 0 ? 'searchEmpty' : 'empty';

  try {
    const params = {
      limit,
      offset: limit * (current - 1),
      ...getFilterParams.value,
    };
    const res = await getMcpMarketplace(params);
    const { results = [], count = 0 } = res ?? {};
    // 只有翻页追加时才需要按 id 去重（避免分页交界处重复渲染）；
    // 重置分页（第一页）必须直接用接口返回的列表整体替换，否则切换分类时
    // 新分类里已在旧列表中展示过的项会被过滤掉，列表高度骤变、触底触发器被带进视口，
    // 进而又补发一次第二页请求（表现为切换分类调用两次接口）
    const list = current === 1
      ? results as unknown as IMarketplaceItemWithUIState[]
      : (results as unknown as IMarketplaceItemWithUIState[])
        .filter(item => !mcpMarketList.value.some(exist => exist.id === item.id));
    mcpMarketList.value = current === 1 ? list : [...mcpMarketList.value, ...list];
    pagination.value = {
      ...pagination.value,
      count,
      hasNoMore: mcpMarketList.value.length >= count,
      current: current + 1,
    };
    // 处理每个分类下官方/精选筛选结果
    if (activeCategoryName.value && !activeStatusTab.value.includes('all')) {
      const curCate = categoriesList.value.find((cat: IMCPMarketCategory) => cat.name === activeCategoryName.value);
      if (curCate) {
        curCate.mcp_server_count = count;
      }
    }
  }
  catch {
    // 仅首屏加载失败时展示错误空态，翻页失败保留已有列表，避免整页内容被替换造成闪屏
    if (current === 1) {
      cardEmptyType.value = 'error';
    }
  }
  finally {
    isFirstLoad.value = false;
    isLoading.value = false;
  }
};

const fetchCategoryList = async () => {
  const extraCategories = ['Official', 'Featured'] as const;
  // 如果右侧选择了全部，分类接口的categories不需要传
  const params = { ...getFilterParams.value };
  if ((extraCategories as readonly string[]).includes(activeStatusTab.value)) {
    params.categories = activeStatusTab.value;
  }
  else {
    delete params.categories;
  }
  const res = await getMcpMarketplaceCategories(params);
  categoriesList.value = (res ?? []).filter(cg => !['Official', 'Featured'].includes(cg.name));
  mcpCategorizeWidth.value = mcpCategorizeRef.value?.offsetWidth ?? 0;
};

/**
 * 重新校准触底触发器的就绪状态
 */
const syncBottomTriggerArmedState = () => {
  const rect = bottomTriggerRef.value?.getBoundingClientRect();
  if (!rect) return;

  // getBoundingClientRect 会强制刷新布局，此处读到的即为列表渲染后的最终位置
  const viewportHeight = document.documentElement.clientHeight || window.innerHeight || 0;
  isBottomTriggerArmed.value = rect.top >= viewportHeight || rect.bottom <= 0;
};

/**
 * 重置分页并重新拉取列表
 * @param keepSelections 是否保留已勾选的 MCP Server：默认保留并回填，
 *                       仅切换分类（以及列表为空展示 TableEmpty 时）清空
 */
const resetPagination = async (keepSelections = true) => {
  // 重置分页后，滚动距离重置
  const mcpEl = document.querySelector('.McpMarket-navigation-content .container-content') as HTMLElement | null;
  if (mcpEl && mcpEl.scrollTop > 0) {
    mcpEl.scrollTop = 0;
  }
  pagination.value = Object.assign(pagination.value, {
    current: 1,
    limit: calculateMaxVisibleCards(),
    hasNoMore: false,
  });
  // getList 会用接口返回的新对象整体替换列表，重新渲染时卡片 is_checked 由 true 变 false，
  // BkCheckbox 会因此 emit change(false) 把 selections 删空，且该 flush 发生在 await 之后的同步代码之前，
  // 所以必须在请求前先快照选中项，请求完成后再回填
  const selectionsSnapshot = keepSelections ? new Map(selections.value) : null;
  if (!keepSelections) {
    selections.value.clear();
  }
  try {
    await getList();
  }
  finally {
    // 列表渲染完成后重新校准触底触发器，避免列表塌陷补发的回调再发一次请求
    nextTick(syncBottomTriggerArmedState);
  }
  // 保留选中时，刷新后的列表需要同步卡片勾选态
  if (selectionsSnapshot) {
    // 列表为空（展示 TableEmpty）时没有卡片可回显，不清空选中，
    // 否则搜索无结果会把已勾选项清掉，导致后续搜索无法回显
    if (mcpMarketList.value.length < 1) {
      return;
    }
    selections.value.clear();
    mcpMarketList.value.forEach((item) => {
      item.is_checked = selectionsSnapshot.has(item.id);
      if (item.is_checked) {
        selections.value.set(item.id, item);
      }
    });
    // 不在当前列表中的已选项（翻页未加载、搜索未命中等）继续保留
    selectionsSnapshot.forEach((item, id) => {
      if (!selections.value.has(id)) {
        selections.value.set(id, item);
      }
    });
  }
};

const fetchInitData = () => {
  Promise.allSettled([fetchCategoryList(), resetPagination()]);
};

const handleCategoryChange = async (value: string) => {
  if (value === activeCategoryName.value) return;

  isSwitchingCategory.value = true;
  activeCategoryName.value = value;

  try {
    // 切换分类会更换列表内容，清空已勾选的 MCP Server
    await resetPagination(false);
  }
  finally {
    isSwitchingCategory.value = false;
  }
};

const handleTopTabChange = (value: string) => {
  if (value === activeStatusTab.value) return;
  activeStatusTab.value = value;
  fetchInitData();
};

const handleSortChange = (sort: string) => {
  filterData.value.order_by = sort;
  resetPagination();
};

const handleMouseenter = (e: MouseEvent, row: IMCPMarketCategory) => {
  const cell = (e.target as HTMLElement)?.closest('.truncate') as HTMLElement | null;
  if (cell) {
    row.isOverflow = cell.scrollWidth > cell.offsetWidth;
  }
};

const handleMouseleave = (_: MouseEvent, row: IMCPMarketCategory) => {
  row.isOverflow = false;
};

const handleView = (id: number) => {
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
  selections.value.clear();
};

const handleRefresh = () => {
  fetchInitData();
};

const onIntersectionObserver = ([entry]: IntersectionObserverEntry[]) => {
  if (!entry?.isIntersecting) {
    // 触发器离开视口
    isBottomTriggerArmed.value = true;
    return;
  }

  // 首屏未完成、正在加载中，或触发器未就绪（列表高度塌陷补发的回调）→ 不触发；
  // 仅用户滚动到底部时才加载更多
  if (isFirstLoad.value || isLoading.value || !isBottomTriggerArmed.value) return;

  isBottomTriggerArmed.value = false;
  getList();
};

const handleChecked = (isChecked: boolean, row: IMarketplaceItemWithUIState) => {
  row.is_checked = isChecked;
  if (isChecked) {
    selections.value.set(row.id, row);
  }
  else {
    selections.value.delete(row.id);
  }
};

const handleCopyConfig = (row: IMarketplaceItemWithUIState) => {
  isShowConfig.value = true;
  fetchMcpBatchCopyConfigList({ row });
};

const handleBatchCopy = () => {
  isShowConfig.value = true;
  fetchMcpBatchCopyConfigList({ selections: selections.value });
};

const handleSelectionChange = (selection: IMarketplaceItemWithUIState[]) => {
  selections.value.clear();
  selection.forEach(item => selections.value.set(item.id, item));
};

const handleResize = debounce(() => {
  const newViewportHeight = window.innerHeight;
  // 仅当视口高度变化超过 30px 时才重新计算
  if (Math.abs(newViewportHeight - (cachedViewportHeight.value || 0)) > 30) {
    cachedViewportHeight.value = newViewportHeight;
    const newLimit = calculateMaxVisibleCards();
    if (pagination.value.limit !== newLimit) {
      pagination.value.limit = newLimit || 3;
      resetPagination(true);
    }
  }
}, 500);

// 搜索只过滤展示，保留已勾选项并回填当前列表中命中的数据
const handleSearch = debounce(() => fetchInitData(), 300);

watch(
  () => filterData.value.keyword,
  () => {
    handleSearch();
  },
);

onMounted(() => {
  window.addEventListener('resize', handleResize);
  fetchInitData();
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  handleResize?.cancel();
  bannerRef.value?.removeEventListener('load', handleBannerLoad);
  bannerRef.value = null;
});
</script>

<style lang="scss" scoped>
.mcp-market-wrapper {
  width: 80%;
  min-width: 1200px;
  margin: 0 auto;
  box-sizing: border-box;

  .banner-wrapper {
    position: relative;
    margin-top: 24px;

    .banner {
      display: block;
      width: 100%;
      border-radius: 2px;
      box-shadow: 0 2px 4px 0 #1919290d;
    }

    .banner-close {
      position: absolute;
      top: 12px;
      right: 12px;
      color: #979ba5;
      background-color: #f0f1f5;
      border-radius: 50%;

      &:hover {
        background-color: #dcdee5;
        cursor: pointer;
      }
    }
  }

  .main {
    width: 100%;
    padding: 24px 0;

    .mcp-categorize {
      position: sticky;
      top: 24px;
      align-self: flex-start;
      background-color: #fff;
      border-radius: 2px;
      box-shadow: 0 2px 4px 0 #1919290d;
      overflow: hidden;

      .mcp-categorize-item {
        display: flex;
        height: 36px;
        padding: 0 12px;
        cursor: pointer;
        box-sizing: border-box;
        transition: background-color 0.2s;
        align-items: center;
        justify-content: space-between;

        .mcp-categorize-content {
          display: flex;
          height: 36px;
          font-size: 14px;
          flex: 1;
          align-items: center;

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
          height: 16px;
          min-width: fit-content;
          padding: 0 6px;
          font-size: 10px;
          color: #4d4f56;
          background-color: #f0f1f5;
          border-radius: 8px;
          align-items: center;
          gap: 0 4px;
        }

        &.active {
          color: #3a84ff;
          background-color: #e1ecff;
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

      .mcp-market-top-bar {
        position: sticky;
        top: 0;
        z-index: 10;
        padding: 24px 0 16px;
        margin-top: -24px;
        background-color: #f5f7fb;
      }

      .mcp-market-list {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
        background-color: #f5f7fb;

        .ag-mcp-card-wrapper {
          width: calc(33.3333% - 10.6667px);

          &:hover {

            .copy-config-btn {
              color: #1768ef !important;
            }
          }
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
