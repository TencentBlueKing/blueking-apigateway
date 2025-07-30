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
      ref="topBarRef"
      v-model:mode="mode"
      :stage-id="stageId"
      @change-stage="handleStageIdChange"
    />
    <RouterView v-slot="{ Component }">
      <component
        :is="Component"
        @updated="handleStageUpdated"
      />
    </RouterView>
  </div>
</template>

<script lang="ts" setup>
import TopBar from './components/TopBar.vue';

const route = useRoute();
const router = useRouter();

const mode = ref('');
const stageId = ref(0);
const topBarRef = ref();

watch(
  [
    () => route.name,
    () => route.params,
  ],
  () => {
    if (route.name === 'StageOverviewCardMode') {
      mode.value = 'card-mode';
    }
    else if (route.name === 'StageOverviewDetailMode') {
      stageId.value = Number(route.params.stageId);
      mode.value = 'detail-mode';
    }
  },
  { immediate: true },
);

watch(mode, () => {
  if (mode.value === 'card-mode') {
    router.replace({ name: 'StageOverviewCardMode' });
  }
  else if (mode.value === 'detail-mode') {
    router.replace({
      name: 'StageOverviewDetailMode',
      params: { stageId: stageId.value },
    });
  }
});

const handleStageIdChange = (id: number) => {
  stageId.value = id;
  if (mode.value === 'detail-mode') {
    router.replace({
      name: 'StageOverviewDetailMode',
      params: { stageId: stageId.value },
    });
  }
};

const handleStageUpdated = () => {
  topBarRef.value.reload();
};
</script>
