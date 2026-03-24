/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2026 Tencent. All rights reserved.
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
    class="flex items-center"
    v-bind="$attrs"
  >
    <span :class="`mr-10px w-6px h-6px rounded-50% ${bgColor}`" />
    <span>{{ text }}</span>
  </div>
</template>

<script lang="ts" setup>
interface IProps {
  type: 'success' | 'error'
  text: string
}

const { type, text } = defineProps<IProps>();

const bgColor = computed(() => {
  const colorMap = {
    success: 'bg-#2caf5e shadow-[0_0_0_4px_rgba(34,197,94,0.1)]',
    error: 'bg-#ea3636 shadow-[0_0_0_4px_rgba(239,68,68,0.1)]',
  };

  return colorMap[type || 'error'];
});
</script>
