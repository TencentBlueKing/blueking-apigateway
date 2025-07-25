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
    class="card-container"
    :class="{'has-hover-shadow': hoverShadow}"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
interface IProps { hoverShadow?: boolean }
const { hoverShadow = true } = defineProps<IProps>();
</script>

<style scoped lang="scss">
.card-container {
  background: #fff;
  border-radius: 2px;
  box-shadow: 0 2px 4px 0 #1919290d;

  &.has-hover-shadow:hover {
    box-shadow: 0 2px 4px 0 #0000001a, 0 2px 4px 0 #1919290d;
  }
}
</style>
