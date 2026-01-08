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
  <div>
    <div class="page-wrapper">
      <BkLoading
        :loading="isLoading"
        :z-index="99"
      >
        <div
          ref="serverListRef"
          class="server-list"
        >
          <ServerItemCard
            v-for="server in serverList"
            :key="server.id"
            :server="server"
            @delete="handleDelete"
            @edit="handleEdit"
            @enable="handleEnable"
            @suspend="handleSuspend"
            @click="() => handleCardClick(server.id)"
          />
          <!-- 添加按钮卡片 -->
          <div
            class="flex items-center justify-center add-server-card"
            @click="handleAddServerClick"
          >
            <AgIcon
              name="add-small"
              size="40"
            />
          </div>
        </div>
      </BkLoading>
      <CreateSlider
        ref="createSliderRef"
        :server-id="editingServerId"
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
import { Message } from 'bkui-vue';
import { vIntersectionObserver } from '@vueuse/components';
import {
  deleteServer,
  getServers,
  patchServerStatus,
} from '@/services/source/mcp-server';
import { useFeatureFlag } from '@/stores';
import { usePopInfoBox } from '@/hooks';
import CreateSlider from './components/CreateSlider.vue';
import ServerItemCard from '@/components/ag-mcp-card/Index.vue';

type MCPServerType = Awaited<ReturnType<typeof getServers>>['results'][number];

interface IProps { gatewayId?: number }

const { gatewayId = 0 } = defineProps<IProps>();

const { t } = useI18n();
const router = useRouter();
const featureFlagStore = useFeatureFlag();

const createSliderRef = ref<InstanceType<typeof CreateSlider>>();
const serverListRef = ref<HTMLDivElement>(null);
const serverList = ref<MCPServerType[]>([]);
const editingServerId = ref();
const isLoading = ref(true);
const pagination = ref({
  current: 1,
  limit: 0,
  count: 0,
  hasNoMore: false,
});

const isShowNoticeAlert = computed(() => featureFlagStore.isEnabledNotice);

const getSingleCardHeight = (): number => {
  const firstCard = serverListRef.value?.querySelector('.ag-mcp-card-wrapper');
  const addCard = serverListRef.value?.querySelector('.add-server-card');

  // 如果有已渲染的卡片，取卡片最小高度，否则取添加卡片的高度
  if (firstCard) {
    // 卡片默认最小高度189px + 16px间距
    return 189 + 16;
  }
  return (addCard as HTMLElement).offsetHeight + 16;
};

const getCardsPerRow = (): number => {
  const wrapperWidth = window.innerWidth;
  if (wrapperWidth >= 1280) return 3; // 大屏：每行3个
  if (wrapperWidth < 1280 && wrapperWidth >= 768) return 2; // 中屏：每行2个
  return 1; // 小屏：每行1个
};

const calculateMaxVisibleCards = (): number => {
  // 通知栏高度40px
  const noticeH = isShowNoticeAlert.value ? 40 : 0;
  // 获取页面可用高度（排除顶部导航/内边距）, 44px=页面内边距(20+24)，104px=顶部预留高度
  const wrapperHeight = window.innerHeight - 44 - 104 - noticeH;

  // 获取单卡片高度和每行卡片数
  const singleCardHeight = getSingleCardHeight();
  const cardsPerRow = getCardsPerRow();

  // 计算可展示行数
  const maxRows = Math.floor(wrapperHeight / singleCardHeight);

  // 计算最大可展示卡片数
  const maxCards = Math.max(maxRows * cardsPerRow, 3);

  // 预留一行空间用于触发加载更多
  return maxCards + getCardsPerRow();
};

const fetchServerList = async () => {
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
    };
    const res = await getServers(gatewayId, params);
    const { results = [], count = 0 } = res ?? {};
    serverList.value = current === 1 ? results : [...serverList.value, ...results];
    pagination.value = Object.assign(pagination.value, {
      count,
      hasNoMore: serverList.value.length >= count,
      current: current + 1,
    });
  }
  finally {
    setTimeout(() => {
      isLoading.value = false;
    }, 500);
  }
};

const handleAddServerClick = () => {
  editingServerId.value = undefined;
  createSliderRef.value?.show();
};

const handleEdit = (id: number) => {
  editingServerId.value = id;
  createSliderRef.value?.show();
};

const handleSuspend = async (id: number) => {
  const server = serverList.value.find(server => server.id === id);
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
  const server = serverList.value.find(server => server.id === id);
  if (server) {
    usePopInfoBox({
      isShow: true,
      type: 'warning',
      title: t('确定删除 {n}？', { n: server.name }),
      subTitle: () => t('删除后，{n} 不可恢复，请谨慎操作！', { n: server.name }),
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

const handleResize = () => {
  const newLimit = calculateMaxVisibleCards();
  if (pagination.value.limit !== newLimit) {
    pagination.value.limit = newLimit || 3;
    resetPagination();
  }
};

const onIntersectionObserver = ([entry]: IntersectionObserverEntry[]) => {
  if (entry?.isIntersecting) {
    fetchServerList();
  }
};

const resetPagination = () => {
  // 保留上一次的limit
  const lastLimit = pagination.value.limit * (pagination.value.current - 1);
  pagination.value = Object.assign(pagination.value, {
    limit: lastLimit,
    current: 1,
    count: 0,
    hasNoMore: false,
  });
  fetchServerList();
};

onMounted(() => {
  pagination.value.limit = calculateMaxVisibleCards();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
});
</script>

<style lang="scss" scoped>
.page-wrapper {
  padding: 20px 24px;

  .server-list {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    box-sizing: border-box;

    .add-server-card {
      min-height: 228px;
      color: #979ba5;
      border-radius: 2px;
      background-color: #ffffff;
      box-shadow: 0 2px 4px 0 #1919290d;
      cursor: pointer;

      &:hover {
        color: #3a84ff;
      }
    }

    :deep(.ag-mcp-card-wrapper) {
      padding: 20px 40px;

      .mcp-card-title {
        max-width: calc(100% - 80px);
      }

      .mcp-footer-content {
        right: 40px;
        left: 40px;
      }
    }
  }
}

@media (min-width: 768px) {
  .add-server-card {
    width: calc(50% - 24px);
  }

  :deep(.ag-mcp-card-wrapper) {
    width: calc(50% - 24px);
  }
}

@media (min-width: 1280px) {
  .add-server-card {
    width: calc(33.333% - 16px);
  }

  :deep(.ag-mcp-card-wrapper) {
    width: calc(33.333% - 16px);
  }
}

@media (max-width: 1320px) {
  :deep(.mcp-card-title) {
    min-width: 30px;
  }
}
</style>
