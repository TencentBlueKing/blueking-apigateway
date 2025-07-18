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
  <BkForm
    label-position="right"
    label-width="100"
    v-bind="$attrs"
  >
    <BkFormItem
      :label="t('授权期限')"
      required
    >
      <BkRadioGroup v-model="expireDays">
        <BkRadioButton
          v-for="option in EXPIRE_DAYS_CONSTANTS"
          :key="option.value"
          :label="option.value"
          style="width: 90px;"
        >
          {{ option.label }}
        </BkRadioButton>
      </BkRadioGroup>
    </BkFormItem>
  </BkForm>
</template>

<script setup lang="ts">
import { EXPIRE_DAYS_CONSTANTS } from '@/constants';
import { t } from '@/locales';

const expireDays = defineModel('expireDays', {
  type: Number,
  required: true,
  default: 0,
});
</script>
