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
  <div>
    <TopBar />
    <VersionList
      v-if="resourceVersionStore.tabActive === 'edition'"
      :version="curQueryVersion"
    />
    <SDKList
      v-else
      @on-show-version="handleShowVersion"
    />
  </div>
</template>

<script setup lang="ts">
import { useResourceVersion } from '@/stores';
import TopBar from './components/TopBar.vue';
import VersionList from './components/VersionList.vue';
import SDKList from './components/SDKList.vue';

const resourceVersionStore = useResourceVersion();

const curQueryVersion = ref('');

watch(
  () => resourceVersionStore.tabActive,
  (tab) => {
    if (tab === 'edition') {
      resourceVersionStore.setResourceFilter({});
    }
  },
);

const handleShowVersion = (version: string) => {
  resourceVersionStore.setTabActive('edition');
  curQueryVersion.value = version;
};

onBeforeUnmount(() => {
  resourceVersionStore.setTabActive('edition');
});

</script>
