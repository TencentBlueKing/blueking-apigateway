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
    v-bk-tooltips="tooltipOptions"
    class="ai-blueking-button"
    :style="{ background: `url(${logo}) center center / 18px 18px no-repeat` }"
    v-bind="$attrs"
  />
</template>

<script lang="ts" setup>
import AIBluekingLogo from '@/images/ai-blueking.svg';
import { t } from '@/locales';

interface IProps { tooltipOptions?: Record<string, any> | string }

const { tooltipOptions = t('问问AI') } = defineProps<IProps>();

const logo = AIBluekingLogo;
</script>

<style lang="scss" scoped>
.ai-blueking-button {
  width: 18px;
  height: 18px;
  margin-right: 8px;
  cursor: pointer;
}
</style>
