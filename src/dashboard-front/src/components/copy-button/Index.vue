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
  <AgIcon
    class="copy-icon"
    name="copy-info"
    size="16"
    v-bind="$attrs"
    @click="handleClick"
  />
</template>

<script setup lang="ts">
import { copy } from '@/utils';

interface IProps {
  // 复制的内容，不传入就使用自定义的事件处理器，需要在外部监听 click 事件
  source?: string
}

const { source = '' } = defineProps<IProps>();

const handleClick = () => {
  if (source) {
    copy(source);
  }
};
</script>

<style scoped lang="scss">
.copy-icon {
  color: #3A84FF;
  cursor: pointer;
}
</style>
