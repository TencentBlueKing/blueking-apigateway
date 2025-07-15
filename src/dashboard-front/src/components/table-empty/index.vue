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
  <div class="gateways-empty-table-search">
    <BkException
      v-if="!isLoading"
      class="exception-wrap-item exception-part"
      :type="exceptionType"
      scene="part"
    >
      <div class="exception-part-title">
        {{ exceptionTitle }}
      </div>
      <template v-if="!['empty'].includes(exceptionType)">
        <div
          v-if="abnormal"
          class="refresh-tips"
          @click="handleRefresh"
        >
          {{ t("刷新") }}
        </div>
        <template v-else>
          <div
            v-if="['search-empty'].includes(exceptionType)"
            class="search-empty-tips"
          >
            {{ t("可以尝试 调整关键词 或") }}
            <span
              class="clear-search"
              @click="handlerClearFilter"
            >
              {{ t("清空搜索条件") }}
            </span>
          </div>
        </template>
      </template>
    </BkException>
  </div>
</template>

<script lang="ts" setup>
import { t } from '@/locales';

interface IProps {
  isLoading?: boolean
  abnormal?: boolean
  emptyType?: string
  emptyTitle?: string
  refVal?: string
}

interface Emits {
  (e: 'clear-filter', value?: string): void
  (e: 'refresh'): void
}

const {
  isLoading = false,
  abnormal = false,
  emptyType = '',
  emptyTitle = t('暂无数据'),
  refVal = '',
} = defineProps<IProps>();
const emits = defineEmits<Emits>();

const exceptionType = computed(() => {
  if (abnormal) {
    return 500;
  }
  if (['searchEmpty'].includes(emptyType)) {
    return 'search-empty';
  }
  return 'empty';
});

const exceptionTitle = computed(() => {
  if (abnormal) {
    return t('数据获取异常');
  }
  if (['searchEmpty'].includes(emptyType)) {
    return t('搜索结果为空');
  }
  return emptyTitle;
});

const handlerClearFilter = () => {
  emits('clear-filter', refVal);
};

const handleRefresh = () => {
  emits('clear-filter');
  emits('refresh');
};
</script>

<style lang="scss" scoped>
.gateways-empty-table-search {
  max-height: 280px;
  width: auto !important;
  display: flex;
  align-items: center;
  margin: 0 auto;

  .search-empty-tips {
    font-size: 12px;
    margin-top: 8px;
    color: #979ba5;

    .clear-search {
      cursor: pointer;
      color: #3a84ff;
    }
  }

  .empty-tips {
    color: #63656e;
  }

  .exception-part-title {
    color: #63656e;
    font-size: 14px;
    margin-bottom: 5px;
  }

  .refresh-tips {
    color: #3a84ff;
    cursor: pointer;
  }

  .exception-wrap-item .bk-exception-img.part-img {
    height: 130px;
  }

  .bk-table-empty-text {
    padding: 0 !important;
  }

  :deep(.bk-exception-footer) {
    margin-top: 0;
  }
}
</style>
