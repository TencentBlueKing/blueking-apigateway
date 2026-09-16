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
  <div class="detail-field">
    <div
      class="detail-field-label"
      :style="{ width: `${labelWidth}px` }"
    >
      {{ label }}：
    </div>
    <div class="detail-field-value">
      <slot>{{ displayValue }}</slot>
    </div>
  </div>
</template>

<script lang="ts" setup>
interface IProps {
  label?: string
  value?: string
  labelWidth?: number
}

const {
  label = '',
  value = '',
  labelWidth = 132,
} = defineProps<IProps>();

const displayValue = computed(() => value || '--');
</script>

<style lang="scss" scoped>
.detail-field {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  font-size: 14px;
  line-height: 22px;

  &:last-child {
    margin-bottom: 0;
  }
}

.detail-field-label {
  flex-shrink: 0;
  padding-right: 16px;
  color: #63656e;
  text-align: right;
  white-space: nowrap;
}

.detail-field-value {
  display: flex;
  flex: 1;
  min-width: 0;
  color: #313238;
  word-break: break-all;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;

  :deep(.copy-icon),
  :deep(.action-icon) {
    flex-shrink: 0;
  }
}
</style>
