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
  <div>
    <div class="page-wrapper">
      <AgMcpTopBar
        v-model:search-value="searchValue"
        v-model:publish-time="filterData.order_by"
        class="mb-16px"
        :placeholder="t('搜索 MCP 名称、展示名、描述、环境、分类、标签')"
        :search-data="searchData"
        :is-show-publish-time="!isTableView"
        @sort-change="handleSortChange"
      >
        <template #mcpServerAdd>
          <BkButton
            theme="primary"
            @click="handleAddServerClick"
          >
            <Plus class="text-22px" />
            {{ t("新建") }}
          </BkButton>
        </template>
        <template #mcpServerTab>
          <div class="flex mcp-server-tab">
            <div
              v-for="tab of mcpStatusList"
              :key="tab.id"
              class="flex items-center mcp-server-tab-item"
              :class="[
                {
                  'is-active': tab.id === activeStatusTab,
                },
              ]"
              @click.stop="handleStatusTabChange(tab)"
            >
              <div
                v-show="['0', '1'].includes(tab.id)"
                class="mr-6px ag-dot"
                :class="[
                  {
                    'border-#2caf5e bg-#daf6e5': ['1'].includes(tab.id),
                  },
                  {
                    'border-#c4c6cc bg-#f5f7fa': ['0'].includes(tab.id),
                  },
                ]"
              />
              <div>{{ tab.name }}</div>
            </div>
          </div>
        </template>
        <template #mcpServerPreview>
          <div class="flex mcp-server-tab min-w-56px!">
            <div
              v-for="tab of mcpViewList"
              :key="tab.id"
              class="flex items-center mcp-server-tab-item p-0! min-w-24px!"
              :class="[
                {
                  'is-active': tab.id === activeViewTab,
                },
              ]"
              @click.stop="handlePreviewTabChange(tab)"
            >
              <AgIcon
                :name="tab.name"
                size="16"
                class="doc-qw icon-ag-qw"
              />
            </div>
          </div>
        </template>
      </AgMcpTopBar>
      <BkLoading
        :loading="isLoading"
        :z-index="99"
        color="#f5f7fb"
      >
        <template v-if="isTableView">
          <ServerCardTable
            ref="serverCardTableRef"
            v-model:search-value="searchValue"
            v-model:filter-data="filterData"
            v-model:search-data="searchData"
            :filter-condition="mcpFilterOptions"
            @delete="handleDelete"
            @edit="handleEdit"
            @enable="handleEnable"
            @suspend="handleSuspend"
            @clear-filter="handleClearFilter"
            @updated="handleServerUpdated"
          />
        </template>
        <div
          v-else
          ref="mcpListRef"
          class="mcp-server-list"
        >
          <template v-if="['searchEmpty', 'error'].includes(cardEmptyType) && mcpList.length < 1 && !isLoading">
            <TableEmpty
              background="#f5f7fa"
              :empty-type="cardEmptyType"
              @clear-filter="handleClearFilter"
              @refresh="handleRefresh"
            />
          </template>
          <template v-else>
            <AgMcpCard
              v-for="server in mcpList"
              :key="server.id"
              :server="server"
              @delete="handleDelete"
              @edit="handleEdit"
              @enable="handleEnable"
              @suspend="handleSuspend"
              @click="() => handleCardClick(server.id)"
            >
              <template #mcpStatus>
                <div
                  class="card-header-status"
                  :class="[
                    {
                      'bg-#65c389': server?.status,
                      'bg-#c4c6cc': !server?.status ,
                    },
                  ]"
                >
                  {{ t(server?.status === 1 ? "已启用" : "已停用") }}
                </div>
              </template>
            </AgMcpCard>
            <div
              class="flex items-center justify-center add-server-card"
              @click="handleAddServerClick"
            >
              <AgIcon
                name="add-small"
                size="40"
              />
            </div>
          </template>
        </div>
      </BkLoading>
      <CreateSlider
        ref="createSliderRef"
        :server-id="editingServerId"
        :category-list="mcpFilterOptions.categories"
        @updated="handleServerUpdated"
      />
    </div>
    <div
      v-intersection-observer="onIntersectionObserver"
      class="h-40px"
    />
  </div>
</template>

<script lang="ts" setup>
import { debounce } from 'lodash-es';
import { Message } from 'bkui-vue';
import { Plus } from 'bkui-vue/lib/icon';
import { vIntersectionObserver } from '@vueuse/components';
import {
  type IMCPServer,
  type IMCPServerFilterOptions,
  deleteServer,
  getMcpServerFilterOptions,
  getServers,
  patchServerStatus,
} from '@/services/source/mcp-server';
import { useFeatureFlag } from '@/stores';
import { usePopInfoBox } from '@/hooks';
import { filterSimpleEmpty } from '@/utils/filterEmptyValues';
import CreateSlider from './components/CreateSlider.vue';
import ServerCardTable from './components/ServerCardTable.vue';
import AgMcpTopBar from '@/components/ag-mcp-search-bar/Index.vue';
import AgMcpCard from '@/components/ag-mcp-card/Index.vue';
import TableEmpty from '@/components/table-empty/Index.vue';

type MCPServerType = Awaited<ReturnType<typeof getServers>>['results'][number];

interface IProps { gatewayId?: number }

const { gatewayId = 0 } = defineProps<IProps>();

const { t } = useI18n();
const router = useRouter();
const featureFlagStore = useFeatureFlag();

const createSliderRef = ref<InstanceType<typeof CreateSlider>>();
const serverCardTableRef = ref<InstanceType<typeof ServerCardTable>>();
const mcpListRef = ref<HTMLDivElement>(null);
const mcpList = ref<MCPServerType[]>([]);
const editingServerId = ref();
const activeStatusTab = ref('all');
const activeViewTab = ref('card');
const cardEmptyType = ref<'empty' | 'searchEmpty' | 'error'>('');
const isLoading = ref(true);
const pagination = ref({
  current: 1,
  limit: 0,
  count: 0,
  hasNoMore: false,
});
const filterData = ref<Partial<IMCPServer>>({
  order_by: '-updated_time',
  status: activeStatusTab.value,
});
const mcpFilterOptions = ref<IMCPServerFilterOptions>({
  stages: [],
  labels: [],
  categories: [],
});
const searchValue = ref([]);

const searchData = computed(() => [
  {
    name: t('模糊搜索'),
    id: 'keyword',
    placeholder: t('请输入MCP 名称，展示名，描述'),
    aa: 'aaa',
    children: [],
  },
  {
    name: t('环境'),
    id: 'stage_id',
    placeholder: t('请选择环境'),
    aa: 'aaa',
    children: mcpFilterOptions.value.stages,
    multiple: false,
  },
  {
    name: t('分类'),
    id: 'categories',
    placeholder: t('请选择分类'),
    children: mcpFilterOptions.value.categories.map((cg) => {
      return {
        name: cg.display_name,
        id: cg.name,
      };
    }),
    multiple: true,
  },
  {
    name: t('标签'),
    id: 'label',
    placeholder: t('请选择标签'),
    children: mcpFilterOptions.value.labels.map((label) => {
      return {
        name: label,
        id: label,
      };
    }),
    multiple: false,
  },
]);
const mcpStatusList = shallowRef([
  {
    name: t('全部'),
    id: 'all',
  },
  {
    name: t('已启用'),
    id: '1',
  },
  {
    name: t('已停用'),
    id: '0',
  },
]);
const mcpViewList = shallowRef([
  {
    name: 'cardd',
    id: 'card',
  },
  {
    name: 'shitu-liebiao',
    id: 'table',
  },
]);

const isShowNoticeAlert = computed(() => featureFlagStore.isEnabledNotice);
const isTableView = computed(() => activeViewTab.value.includes('table'));

const getSingleCardHeight = (): number => {
  if (isTableView.value) return;
  const firstCard = mcpListRef.value?.querySelector('.ag-mcp-card-wrapper');
  const addCard = mcpListRef.value?.querySelector('.add-server-card');

  // 如果有已渲染的卡片，取卡片最小高度，否则取添加卡片的高度
  if (firstCard) {
    // 卡片默认最小高度189px + 16px间距
    return 238 + 16;
  }
  return (addCard as HTMLElement)?.offsetHeight + 16;
};

const getCardsPerRow = (): number => {
  const wrapperWidth = window.innerWidth;
  if (wrapperWidth >= 1280) return 3; // 大屏：每行3个
  if (wrapperWidth < 1280 && wrapperWidth >= 768) return 2; // 中屏：每行2个
  return 1; // 小屏：每行1个
};

const calculateMaxVisibleCards = (): number => {
  // 表格视图无需计算
  if (isTableView.value) return;
  // 通知栏高度40px
  const noticeH = isShowNoticeAlert.value ? 40 : 0;
  // 获取页面可用高度（排除顶部导航/内边距）, 48px=页面内边距(24+24)，152px=顶部预留高度
  const wrapperHeight = window.innerHeight - 48 - 152 - noticeH;

  // 获取单卡片高度和每行卡片数
  const singleCardHeight = getSingleCardHeight();
  const cardsPerRow = getCardsPerRow();

  // 计算可展示行数
  const maxRows = Math.floor(wrapperHeight / singleCardHeight);

  // 计算最大可展示卡片数
  const maxCards = Math.max(maxRows * cardsPerRow, 3);

  // 预留一行空间用于触发加载更多
  return maxCards + cardsPerRow;
};

// 获取MCPServer列表
const fetchMcpServerList = async () => {
  const { hasNoMore, current, limit } = pagination.value;
  isLoading.value = true;

  if (hasNoMore) {
    isLoading.value = false;
    return;
  };

  try {
    const params = {
      limit,
      offset: limit * (current - 1),
      ...filterSimpleEmpty(filterData.value),
      status: activeStatusTab.value.includes('all') ? undefined : activeStatusTab.value,
      categories: Array.isArray(filterData.value?.categories)
        ? filterData.value.categories.join()
        : filterData.value?.categories,
    };
    const res = await getServers(gatewayId, params);
    const { results = [], count = 0 } = res ?? {};
    mcpList.value = current === 1 ? results : [...mcpList.value, ...results];
    pagination.value = {
      ...pagination.value,
      count,
      hasNoMore: mcpList.value.length >= count,
      current: current + 1,
    };
  }
  catch {
    cardEmptyType.value = 'error';
  }
  finally {
    setTimeout(() => {
      isLoading.value = false;
    }, 100);
  }
};

// 获取 MCPServer 搜索过滤选项（环境、标签、分类）
const fetchMcpServerFilterOptions = async () => {
  const res = await getMcpServerFilterOptions(gatewayId);
  if (res?.categories?.length) {
    // MCPServer筛选掉官方和精选分类
    res.categories = res?.categories.filter(cg => !['Official', 'Featured'].includes(cg.name));
  }
  if (res?.stages?.length) {
    res.stages = res?.stages.map((stage) => {
      return {
        ...stage,
        id: String(stage.id),
      };
    });
  }
  mcpFilterOptions.value = res ?? {};
};

const handleStatusTabChange = ({ id }: { id: string }) => {
  if (activeStatusTab.value === id) return;
  activeStatusTab.value = id;
  filterData.value.status = id;
  resetPagination();
};

const handlePreviewTabChange = ({ id }: { id: string }) => {
  if (activeViewTab.value === id) return;
  const oldViewType = activeViewTab.value;
  activeViewTab.value = id;
  // 仅当视图从卡片→表格 或 表格→卡片 时，才重置分页（避免重复请求）
  if (oldViewType.includes('card') !== id.includes('card')) {
    nextTick(() => {
      // 表格视图不需要页面滚动条
      const mcpEl = document.querySelector('.MCPServer-navigation-content .default-header-view');
      if (mcpEl) {
        mcpEl.style.overflowY = id.includes('card') ? 'auto' : 'hidden';
      }
      resetPagination();
    });
  }
};

const handleAddServerClick = () => {
  editingServerId.value = undefined;
  createSliderRef.value?.show();
};

// 卡片模式下发布时间或字母排序
const handleSortChange = (sort: string) => {
  filterData.value.order_by = sort;
  resetPagination();
};

const handleEdit = (id: number) => {
  editingServerId.value = id;
  createSliderRef.value?.show();
};

const handleSuspend = async (id: number) => {
  const server = mcpList.value.find(server => server.id === id);
  usePopInfoBox({
    isShow: true,
    type: 'warning',
    title: () => t('确认停用 {n}？', { n: server.name }),
    subTitle: t('停用后，{n} 下所有工具不可访问，请确认！', { n: server.name }),
    confirmText: t('确认停用'),
    cancelText: t('取消'),
    onConfirm: async () => {
      await patchServerStatus(gatewayId, id, { status: 0 });
      Message({
        theme: 'success',
        message: t('已停用'),
      });
      resetPagination();
    },
  });
};

const handleEnable = async (id: number) => {
  await patchServerStatus(gatewayId, id, { status: 1 });
  Message({
    theme: 'success',
    message: t('已启用'),
  });
  resetPagination();
};

const handleDelete = async (id: number) => {
  const server = mcpList.value.find(server => server.id === id);
  if (server) {
    usePopInfoBox({
      isShow: true,
      type: 'warning',
      title: () => t('确认停用 {n}？', { n: server.name }),
      subTitle: t('停用后，{n} 下所有工具不可访问，请确认！', { n: server.name }),
      confirmText: t('删除'),
      cancelText: t('取消'),
      confirmButtonTheme: 'danger',
      onConfirm: async () => {
        await deleteServer(gatewayId, id);
        Message({
          theme: 'success',
          message: t('删除成功'),
        });
        resetPagination();
      },
    });
  }
};

const handleServerUpdated = () => {
  // 如果是新建编辑mcp重置滚动条到顶部
  const mcpEl = document.querySelector('.MCPServer-navigation-content .default-header-view');
  if (mcpEl?.scrollTop > 0) {
    mcpEl.scrollTop = 0;
  }
  resetPagination();
};

const handleCardClick = (id: number) => {
  router.replace({
    name: 'MCPServerDetail',
    params: { serverId: id },
  });
};

const handleResize = debounce(() => {
  const newLimit = calculateMaxVisibleCards();
  if (pagination.value.limit !== newLimit) {
    pagination.value.limit = newLimit || 3;
    resetPagination();
  }
}, 300);

const onIntersectionObserver = ([entry]: IntersectionObserverEntry[]) => {
  // 表格视图时，禁用滚动加载
  if (isTableView.value) return;

  if (entry?.isIntersecting) {
    fetchMcpServerList();
  }
};

const resetPagination = () => {
  if (activeStatusTab.value.includes('all')) {
    delete filterData.value.status;
  }
  // 如果是表格视图, 且不是首次加载
  if (isTableView.value) {
    nextTick(() => {
      serverCardTableRef.value?.getList();
    });
    return;
  }

  // 保留上一次的limit
  const lastLimit = pagination.value.current > 1
    ? pagination.value.limit * (pagination.value.current - 1)
    : calculateMaxVisibleCards();
  pagination.value = Object.assign(pagination.value, {
    limit: lastLimit,
    current: 1,
    count: 0,
    hasNoMore: false,
  });
  fetchMcpServerList();
};

const handleSearch = () => {
  const params = { order_by: filterData.value.order_by || '-updated_time' };
  searchValue.value.forEach((option) => {
    if (option.values) {
      params[option.id] = !['categories'].includes(option.id)
        ? option.values?.[0]?.id
        : option.values.map(item => item.id);
    };
  });
  filterData.value = params;
  cardEmptyType.value = Object.keys(params).length > 0 ? 'searchEmpty' : 'empty';
  resetPagination();
};

const handleClearFilter = () => {
  filterData.value = {
    order_by: '-updated_time',
    status: activeStatusTab.value,
  };
  searchValue.value = [];
  cardEmptyType.value = '';
};

const handleRefresh = () => {
  resetPagination();
};

watch(
  () => searchValue.value,
  () => {
    handleSearch();
  },
);

onMounted(() => {
  pagination.value.limit = calculateMaxVisibleCards();
  window.addEventListener('resize', handleResize);
  fetchMcpServerFilterOptions();
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  handleResize?.cancel();
});
</script>

<style lang="scss" scoped>
.page-wrapper {
  padding: 24px;
  box-sizing: border-box;

  .mcp-server-tab-item.preview-tab-item {
    padding: 0;
  }

  :deep(.ag-dot) {
    display: inline-block;
    min-width: 8px;
    height: 8px;
    border-width: 1px;
    border-style: solid;
    border-radius: 50%;
  }

  .mcp-server-list {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    box-sizing: border-box;

    .add-server-card {
      min-height: 280px;
      color: #3a84ff;
      background-color: #f0f5ff;
      border: 1px dashed #699df4;
      border-radius: 2px;
      cursor: pointer;
      box-sizing: border-box;
    }

    :deep(.ag-mcp-card-wrapper) {
      .mcp-footer-content {
        left: 24px;
        right: 24px;
      }
    }
  }
}

@media (max-width: 767px) {
  .add-server-card,
  :deep(.ag-mcp-card-wrapper) {
    width: 100%;
  }
}

@media (min-width: 1280px) {
  .add-server-card,
  :deep(.ag-mcp-card-wrapper) {
    width: calc(33.3333% - 10.6667px);
  }
}

@media (max-width: 1320px) {
  :deep(.mcp-card-title) {
    min-width: 30px;
  }
}
</style>
