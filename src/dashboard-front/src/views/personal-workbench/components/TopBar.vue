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
  <div class="personal-workbench-top-bar">
    <BkTab
      :active="activeTab"
      type="unborder-card"
      @change="handleTabChange"
    >
      <BkTabPanel
        name="gateway"
        :label="t('API 网关')"
      />
      <BkTabPanel
        name="mcp"
        label="MCP server"
      />
    </BkTab>
  </div>
</template>

<script  lang="ts" setup>
import { t } from '@/locales';
import type { ITabKey } from '@/services/types/query/personal-workbench.ts';

interface IEmits { 'tab-change': [tab: ITabKey] }

const emit = defineEmits<IEmits>();

const activeTab = ref('gateway');

const handleTabChange = (tab: ITabKey) => {
  activeTab.value = tab;
  emit('tab-change', tab);
};
</script>

<style lang="scss" scoped>
.personal-workbench-top-bar {
  position: sticky;
  top: 0;
  z-index: 99;
  display: flex;
  padding: 0 24px;
  background-color: #ffffff;
  box-shadow: 0 3px 4px rgb(64 112 203 / 5.88%);

  :deep(.bk-tab) {

    .bk-tab-header {
      line-height: 36px !important;
      border-bottom: none;

      &-item {
        padding: 0;
        margin-right: 32px;
        font-size: 14px;
      }
    }

    .bk-tab-content {
      padding: 0;
    }
  }
}
</style>
