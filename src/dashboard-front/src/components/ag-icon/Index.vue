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
  <i
    v-if="!svg"
    :class="`icon-ag-${name}`"
    :style="{ fontSize: `${size}px` }"
    class="icon apigateway-icon"
  />
  <svg
    v-else
    :style="{ width: `${size}px`, height: `${size}px` }"
    class="icon svg-icon"
  >
    <use :xlink:href="`#icon-ag-${name}`" />
  </svg>
</template>

<script lang="ts" setup>
interface IProps {
  name: string
  size?: string
  svg?: boolean
}

const { name, size = '14', svg = false } = defineProps<IProps>();
</script>
