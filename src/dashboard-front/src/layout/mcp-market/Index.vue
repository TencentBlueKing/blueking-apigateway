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
      <template v-if="mcpList?.length">
        <div class="card-list">
          <div
            v-for="item in mcpList"
            :key="item.id"
            class="card"
            @click="() => goDetails(item.id)"
          >
            <div class="pt-18px pb-16px flex items-baseline header">
              <div class="max-w-[calc(100%-115px)] color-#313238 font-bold mr-16px title">
                <BkOverflowTitle
                  type="tips"
                  class="lh-22px mb-12px text-18px"
                >
                  {{ item.title }}
                </BkOverflowTitle>
                <BkOverflowTitle
                  type="tips"
                  class="text-14px"
                >
                  {{ item.name }}
                </BkOverflowTitle>
              </div>
              <BkTag
                v-if="item.gateway.is_official"
                theme="success"
                class="mr8"
              >
                {{ t('官方') }}
              </BkTag>
              <BkTag theme="info">
                {{ item.stage?.name }}
              </BkTag>
            </div>
            <div class="content">
              <div class="info-item">
                <div class="label">
                  {{ t('访问地址') }}：
                </div>
                <div class="value flex-row align-items-center">
                  <BkOverflowTitle style="width: calc(100% - 28px)">
                    {{ item.url }}
                  </BkOverflowTitle>
                  <div
                    class="copy-wrapper"
                    @click.stop="() => handleCopy(item.url)"
                  >
                    <AgIcon
                      name="copy"
                      size="14"
                      class="icon"
                    />
                  </div>
                </div>
              </div>
              <div class="info-item">
                <div class="label">
                  {{ t('工具数量') }}：
                </div>
                <div class="value">
                  {{ item.tools_count }}
                </div>
              </div>
              <div
                v-if="isEnablePrompt"
                class="info-item"
              >
                <div class="label">
                  {{ t('Prompt 数量') }}：
                </div>
                <div class="value">
                  {{ item.prompts_count }}
                </div>
              </div>
              <div class="info-item">
                <div class="label">
                  {{ t('MCP描述') }}：
                </div>
                <div class="value">
                  {{ item.description }}
                </div>
              </div>
              <div class="info-item">
                <div class="label">
                  {{ t('MCP标签') }}：
                </div>
                <div class="value">
                  <BkTag
                    v-for="label in item.labels"
                    :key="label"
                    class="mr8"
                  >
                    {{ label }}
                  </BkTag>
                </div>
              </div>
            </div>
          </div>
        </div>
        <BkPagination
          v-model="pagination.current"
          class="mt-24px"
          align="center"
          :count="pagination.count"
          :limit="pagination.limit"
          :limit-list="[10, 12, 20, 50, 100]"
          size="small"
          @change="handlePaginationChange"
          @limit-change="handlePaginationLimitChange"
        />
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
  </div>
</template>

<script lang="ts" setup>
import AgIcon from '@/components/ag-icon/Index.vue';
import { type IMarketplaceItem, getMcpMarketplace } from '@/services/source/mcp-market';
import { copy } from '@/utils';
import { useFeatureFlag } from '@/stores';
import mcpBanner from '@/images/mcp-banner.jpg';
import mcpBannerEn from '@/images/mcp-banner-en.jpg';
import TableEmpty from '@/components/table-empty/Index.vue';

const { t, locale } = useI18n();
const router = useRouter();
const featureFlagStore = useFeatureFlag();

const search = ref<string>('');
const isPublic = ref<boolean>(false);
const mcpAllList = ref<IMarketplaceItem[]>([]);
const tableEmptyConf = ref<{
  emptyType: string
  isAbnormal: boolean
}>({
  emptyType: '',
  isAbnormal: false,
});

const pagination = ref({
  current: 1,
  limit: 12,
  count: 0,
});

const isEnablePrompt = computed(() => featureFlagStore?.flags?.ENABLE_MCP_SERVER_PROMPT);

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
  const res = await getMcpMarketplace({
    limit: pagination.value.limit,
    offset: pagination.value.limit * (pagination.value.current - 1),
    keyword: search.value,
  });

  pagination.value.count = res.count;
  mcpAllList.value = res.results;
};
getList();

const handleInput = () => {
  if (!search.value) {
    handleSearch();
  }
};

const handleCopy = (str: string) => {
  copy(str);
};

const goDetails = (id: number) => {
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
  getList();
};

const handleSearch = () => {
  pagination.value.current = 1;
  getList();
};

const handlePaginationChange = () => {
  getList();
};

const handlePaginationLimitChange = (limit: number) => {
  pagination.value.limit = limit;
  getList();
};

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

  .card-list {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-start;
    box-sizing: border-box;

    .card {
      padding: 0 24px;
      cursor: pointer;
      background: #FFF;
      border-radius: 2px;
      box-shadow: 0 2px 4px 0 #1919290d;
      box-sizing: border-box;

      .header {
        border-bottom: 1px solid #eaebf0;
      }

      .content {
        padding: 16px 0 4px;

        .info-item {
          display: flex;
          align-items: center;
          margin-bottom: 12px;
          font-size: 12px;
          line-height: 20px;

          .label {
            font-size: 14px;
            color: #4D4F56;
          }

          .value {
            overflow: hidden;
            font-size: 14px;
            color: #313238;
            text-overflow: ellipsis;
            white-space: nowrap;
            flex: 1;

            .copy-wrapper {
              width: 28px;
              text-align: right;
            }

            .icon {
              color: #3A84FF;
            }
          }
        }
      }
    }
  }

  .empty-wrapper {
    padding-top: 120px;
  }
}

@media (max-width: 1599.98px) {

  .main {
    width: 1280px;
  }

  .card-list {
    gap: 20px 25px;

    .card {
      width: 410px;
    }
  }
}

@media (min-width: 1600px) {

  .main {
    width: 1600px;
  }

  .card-list {
    gap: 20px 26.67px;

    .card {
      width: 380px;
    }
  }
}
</style>
