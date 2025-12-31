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
    <div class="banner">
      <img
        :src="bannerImg"
        alt="banner"
      >
    </div>
    <div class="main">
      <div class="top">
        <div class="flex-row align-items-center">
          <BkInput
            v-model="search"
            class="search-input"
            :placeholder="t('请输入 MCP 名称或描述搜索')"
            clearable
            type="search"
            @enter="handleSearch"
            @blur="getList"
            @clear="handleSearch"
            @input="handleInput"
          />
          <!-- <BkCheckbox v-model="isPublic">{{ t('仅展示官方') }}</BkCheckbox> -->
        </div>

        <!-- <div class="guide">
          <ag-icon name="document" size="14" />
          <span>{{ t('使用指引') }}</span>
          </div> -->
      </div>
      <div
        v-if="search"
        class="text-12px mb-16px"
      >
        <I18nT
          keypath="共找到 {0} 个结果"
          tag="span"
        >
          <strong class="color-#3A84FF">{{ mcpAllList.length }}</strong>
        </I18nT>
      </div>
      <template v-if="mcpList?.length">
        <div class="flex flex-wrap justify-start card-list">
          <ServerItemCard
            v-for="market of mcpList"
            :key="market.id"
            :server="market"
            :show-actions="false"
            @click="() => handleCardClick(market.id)"
          />
        </div>
      </template>
      <div
        v-else
        class="empty-wrapper"
      >
        <TableEmpty
          background="#f5f7fa"
          :empty-type="tableEmptyConf.emptyType"
          :abnormal="tableEmptyConf.isAbnormal"
          @refresh="getList"
          @clear-filter="handleClearFilterKey"
        />
      </div>
    </div>
    <!-- 触底翻页触发器 -->
    <div
      v-intersection-observer="onIntersectionObserver"
      class="h-40px"
    />
  </div>
</template>

<script lang="ts" setup>
import { type IMarketplaceItem, getMcpMarketplace } from '@/services/source/mcp-market';
import mcpBanner from '@/images/mcp-banner.jpg';
import mcpBannerEn from '@/images/mcp-banner-en.jpg';
import TableEmpty from '@/components/table-empty/Index.vue';
import ServerItemCard from '@/components/ag-mcp-card/Index.vue';
import { vIntersectionObserver } from '@vueuse/components';

const { t, locale } = useI18n();
const router = useRouter();

const search = ref('');
const isPublic = ref(false);
const mcpAllList = ref<IMarketplaceItem[]>([]);
const tableEmptyConf = ref({
  emptyType: '',
  isAbnormal: false,
});

const pagination = ref({
  current: 1,
  limit: 12,
  count: 0,
  hasNoMore: false,
});

const bannerImg = computed(() => {
  if (locale.value === 'zh-cn') {
    return mcpBanner;
  }
  return mcpBannerEn;
});

const mcpList = computed(() => {
  const list = mcpAllList.value.filter((item: IMarketplaceItem) => {
    if (isPublic.value) {
      return item.gateway.is_official;
    }
    return true;
  });
  updateTableEmptyConfig();
  return list;
});

const getList = async () => {
  if (pagination.value.hasNoMore) {
    return;
  }
  const res = await getMcpMarketplace({
    limit: pagination.value.limit,
    offset: pagination.value.limit * (pagination.value.current - 1),
    keyword: search.value,
  });

  if (pagination.value.current === 1) {
    mcpAllList.value = res.results;
  }
  else {
    mcpAllList.value = mcpAllList.value.concat(res.results);
  }

  pagination.value.count = res.count;
  pagination.value.current += 1;

  if (mcpAllList.value.length >= pagination.value.count) {
    pagination.value.hasNoMore = true;
  }
};

const handleInput = () => {
  if (!search.value) {
    handleSearch();
  }
};

const handleCardClick = (id: number) => {
  router.push({
    name: 'McpMarketDetails',
    params: { id },
  });
};

const updateTableEmptyConfig = () => {
  if (search.value) {
    tableEmptyConf.value.emptyType = 'searchEmpty';
    return;
  }
  tableEmptyConf.value.emptyType = 'empty';
};

const handleClearFilterKey = () => {
  search.value = '';
  pagination.value.current = 1;
  pagination.value.hasNoMore = false;
  getList();
};

const handleSearch = () => {
  pagination.value.current = 1;
  pagination.value.hasNoMore = false;
  getList();
};

const onIntersectionObserver = ([entry]: IntersectionObserverEntry[]) => {
  if (entry?.isIntersecting) {
    getList();
  }
};

onBeforeMount(() => {
  // 如果屏幕宽度小于1620px，那么每页显示9条数据（3列），否则每页显示12条数据（4列）
  if (window.innerWidth < 1620) {
    pagination.value.limit = 9;
  }
  else {
    pagination.value.limit = 12;
  }
});

</script>

<style lang="scss" scoped>
.banner {

  img {
    width: 100%;
    min-width: 1280px;
  }
}

.main {
  padding-bottom: 26px;
  margin: 0 auto;

  .top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 24px 0;

    .search-input {
      width: 800px;
      margin-right: 12px;
    }

    .guide {
      font-size: 12px;
      color: #3A84FF;
      cursor: pointer;
    }
  }

  :deep(.card-list) {
    box-sizing: border-box;

    .ag-mcp-card-wrapper {
      padding: 20px;

      .mcp-footer-content {
        right: 20px;
        left: 20px;
      }
    }
  }

  .empty-wrapper {
    padding-top: 120px;
  }
}

@media (max-width: 1619px) {

  .main {
    width: 1280px;
  }

  :deep(.card-list) {
    gap: 20px 25px;

    .ag-mcp-card-wrapper {
      width: 410px;

      .mcp-card-title {
        max-width: 240px;
      }
    }
  }
}

@media (min-width: 1620px) {

  .main {
    width: 1600px;
  }

  :deep(.card-list) {
    gap: 20px 26.67px;

    .ag-mcp-card-wrapper {
      width: 380px;

      .mcp-card-title {
        max-width: 216px;
      }
    }
  }
}
</style>
