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
  <TopBar @tab-change="handleTabChange" />
  <ApplyTable
    ref="tableCom"
    apply-status="handled"
    :active-tab="personalWorkbenchTab"
    :remote-method="tabItem[personalWorkbenchTab]"
  />
</template>

<script lang="ts" setup>
import type { ICountAndResults } from '@/services/types/utils.ts';
import type { IPersonalWorkbenchListQuery, ITabKey } from '@/services/types/query/personal-workbench.ts';
import type { IPersonalWorkbenchListResponse } from '@/services/types/responses/personal-workbench.ts';
import { getGatewayHandledList, getMcpHandledList } from '@/services/source/personal-workbench.ts';
import { usePersonalWorkbench } from '@/hooks';
import TopBar from '@/views/personal-workbench/components/TopBar.vue';
import ApplyTable from '@/views/personal-workbench/components/Table.vue';

const tabItem: Record<ITabKey, (
  params: IPersonalWorkbenchListQuery,
) => Promise<ICountAndResults<IPersonalWorkbenchListResponse>>> = {
  gateway: getGatewayHandledList,
  mcp: getMcpHandledList,
};

const tableCom = ref<InstanceType<typeof ApplyTable> | null>(null);

const { personalWorkbenchTab } = usePersonalWorkbench();

const handleTabChange = (value: ITabKey) => {
  personalWorkbenchTab.value = value;
  nextTick(() => {
    tableCom.value?.handleClearFilter();
  });
};
</script>
