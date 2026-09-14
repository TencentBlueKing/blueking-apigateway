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
    ref="searchInputRef"
    class="search-input-container"
  >
    <BkDropdown
      :popover-options="popoverOptions"
      :disabled="queryHistory.length === 0"
      style="width: 100%;"
    >
      <BkInput
        v-model="localValue"
        class="search-input"
        :placeholder="localPlaceholder"
        clearable
        @enter="handleEnter"
      >
        <!-- <template #suffix>
          <BkButton theme="primary" class="search-input-button" @click="handleSearch"> {{ t("搜索") }} </BkButton>
          </template> -->
      </BkInput>
      <template #content>
        <BkDropdownMenu>
          <BkDropdownItem
            v-for="item in queryHistory"
            :key="item"
            @click="() => handleHistoryClick(item)"
          >
            {{ item }}
          </BkDropdownItem>
        </BkDropdownMenu>
      </template>
    </BkDropdown>
  </div>
</template>

<script lang="ts" setup>
// import { useGetGlobalProperties } from '@/hooks';
import { useStorage } from '@vueuse/core';

interface IProps {
  modeValue?: string
  placeholder?: string
  // width?: string
}

const {
  modeValue = '',
  placeholder = '',
  // width = '612px',
} = defineProps<IProps>();

const emit = defineEmits<{
  'update:modeValue': [data: string]
  'search': [data: string]
}>();

const { t } = useI18n();
// const globalProperties = useGetGlobalProperties();

// 从本地存储获取搜索历史
const queryHistory = useStorage('access-log-query-history', []);
// const { GLOBAL_CONFIG } = globalProperties;

const popoverOptions = {
  trigger: 'click',
  placement: 'bottom-start',
};

const searchInputRef = ref(null);
const localValue = ref('');
const localPlaceholder = ref('');
localPlaceholder.value = placeholder || t('请输入查询语句');

watch(
  () => modeValue,
  (payload: string) => {
    localValue.value = payload;
  },
);

watch(
  () => localValue.value,
  (payload: string) => {
    emit('update:modeValue', payload);
  },
);

const handleEnter = () => {
  emit('search', localValue.value);
};

const handleHistoryClick = (item: string) => {
  localValue.value = item;
};

defineExpose({ searchInputRef: searchInputRef.value });
</script>

<style lang="scss" scoped>
.search-input {

  .search-input-button {
    height: auto;
    border: none;
    border-radius: 0;
  }
}
</style>
