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
  <div
    class="flex items-center api-gateways-exception"
    :style="{ 'backgroundColor': background }"
  >
    <BkException
      scene="part"
      v-bind="exceptionAttrs"
    >
      <template v-if="[exceptionAttrs.type, emptyType].includes('search-empty')">
        <div class="mt-8px text-12px color-#979ba5 search-empty-tips">
          {{ t('可以尝试 调整关键词 或') }}
          <span
            class="color-#3a84ff cursor-pointer"
            @click="handlerClearFilter"
          >
            {{ t('清空搜索条件') }}
          </span>
        </div>
      </template>
      <BkButton
        v-if="[500].includes(exceptionAttrs.type)"
        text
        theme="primary"
        @click="handleRefresh"
      >
        {{ t("刷新") }}
      </BkButton>
    </BkException>
  </div>
</template>

<script lang="ts" setup>
import { useI18n } from 'vue-i18n';
import { cloneDeep } from 'lodash-es';

interface IProps {
  emptyType?: 'empty' | 'search-empty' | 'searchEmpty' | 'refresh'
  error?: Record<string, any> | null
  queryListParams?: any[]
  background?: string
}

const {
  emptyType = 'empty',
  background = '#ffffff',
  error = null,
  queryListParams = [],
} = defineProps<IProps>();

const emit = defineEmits<{
  'clear-filter': void
  'refresh': void
}>();

const { t } = useI18n();

const exceptionAttrs = computed(() => {
  if (error) {
    return {
      type: 500,
      title: t('数据获取异常'),
    };
  }

  const queryParams = cloneDeep(queryListParams?.[0] ?? {});
  delete queryParams.limit;
  delete queryParams.offset;
  Object.keys(queryParams).forEach((key) => {
    if ((typeof queryParams[key] === 'string' && !queryParams[key]) || ['offset', 'limit'].includes(key)) {
      delete queryParams[key];
    }
  });
  if (Object.keys(queryParams).length > 0 || ['search-empty', 'searchEmpty'].includes(emptyType)) {
    return {
      type: 'search-empty',
      title: t('搜索结果为空'),
    };
  }

  return {
    type: 'empty',
    title: t('暂无数据'),
  };
});

const handlerClearFilter = () => {
  emit('clear-filter');
};

const handleRefresh = () => {
  emit('refresh');
};

</script>

<style lang="scss" scoped>
.api-gateways-exception {
  width: auto !important;
  margin: 0 auto;

  :deep(.bk-exception) {
    .bk-exception-title {
      font-size: 14px;
      color: #63656e;
    }

    .bk-exception-img {
      width: 100%;
    }

    .bk-exception-footer {
      margin-top: 0;
    }
  }
}
</style>
