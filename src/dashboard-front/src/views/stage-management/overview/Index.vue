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
  <div class="py-20px px-24px">
    <!-- 自定义头部 -->
    <TopBar
      v-model:mode="mode"
      v-model:stage-id="stageId"
    />
    <OverviewMode v-if="mode === 'overview'" />
    <DetailMode
      v-else-if="mode === 'detail' && stageId"
      :stage-id="stageId"
    />
  </div>
</template>

<script lang="ts" setup>
import OverviewMode from './components/OverviewMode.vue';
import TopBar from './components/TopBar.vue';
import DetailMode from './components/DetailMode.vue';

const mode = ref('overview');
const stageId = ref(0);
</script>
