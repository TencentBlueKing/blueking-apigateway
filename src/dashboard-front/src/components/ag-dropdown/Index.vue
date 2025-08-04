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
  <BkDropdown
    :trigger="triggerType"
    class="mr-8px"
    :placement="placement"
    @show="isOpen = true"
    @hide="isOpen = false"
  >
    <template v-if="isText">
      <div class="dropdown-text">
        {{ text }} <AngleRight class="text-22px" />
      </div>
    </template>
    <BkButton
      v-else
      :disabled="isDisabled"
    >
      {{ text }}
      <AgIcon
        name="down-small"
        class="apigateway-select-icon"
        :class="[{ 'is-open': isOpen }]"
      />
    </BkButton>
    <template #content>
      <BkDropdownMenu v-if="isOpen">
        <template v-if="slots?.default">
          <slot />
        </template>
        <template v-else>
          <BkDropdownItem
            v-for="item in dropdownList"
            :key="item.value"
            v-bk-tooltips="{ content: item?.tooltips, disabled: !item?.tooltips || !item.disabled }"
            :class="{ disabled: item.disabled }"
            @click="() => handleDropdownClick(item)"
          >
            {{ item.label }}
          </BkDropdownItem>
        </template>
      </BkDropdownMenu>
    </template>
  </BkDropdown>
</template>

<script setup lang="ts">
import { type IDropList } from '@/types/common';
import { AngleRight } from 'bkui-lib/icon';
import { t } from '@/locales';

interface ApigwIDropList extends IDropList { tooltips?: string }

interface IProps {
  text?: string
  triggerType?: string
  dropdownList?: ApigwIDropList[]
  isDisabled?: boolean
  isText?: boolean
  placement?: string
}

const {
  text = t('下拉菜单'),
  triggerType = 'click',
  dropdownList = [],
  isDisabled = false,
  isText = false,
  placement = 'bottom',
} = defineProps<IProps>();

const emit = defineEmits<{ 'on-change': [data: IDropList] }>();

const slots = useSlots();

const isOpen = ref(false);

const handleDropdownClick = (data: IDropList) => {
  if (data.disabled) return;
  isOpen.value = false;
  emit('on-change', data);
};
</script>

<style scoped lang="scss">
.disabled{
  color: #dcdee5;
  cursor: not-allowed;
}

.dropdown-text {
  display: flex;
  align-items: center;
  padding: 0 16px;
  line-height: 34px;
  cursor: pointer;
}

.apigateway-select-icon {
  font-size: 20px !important;
  transition: transform .5s !important;

  &.is-open {
    transform: rotate(180deg) !important;
  }
}
</style>
