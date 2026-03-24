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
  <div class="observability-top-bar">
    <BkTab
      :active="activeTab"
      type="unborder-card"
      @change="handleTabChange"
    >
      <BkTabPanel
        name="FlowLog"
        :label="t('流水日志')"
      />
      <BkTabPanel
        name="Dashboard"
        :label="t('仪表盘')"
      />
    </BkTab>
    <!-- 定时选择器 -->
    <template v-if="['Dashboard'].includes(activeTab)">
      <ObservabilityTimeInterval
        class="mb-4px"
      />
    </template>
  </div>
</template>

<script  lang="ts" setup>
import { t } from '@/locales';
import ObservabilityTimeInterval from '@/views/mcp-server/components/ObservabilityTimeInterval.vue';

interface IEmits { 'tab-change': [value: string] }

const activeTab = defineModel('activeTab', { type: String });

const emit = defineEmits<IEmits>();

const handleTabChange = (tab: string) => {
  activeTab.value = tab;
  emit('tab-change', tab);
};
</script>

<style lang="scss" scoped>
.observability-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background-color: #ffffff;
  box-shadow: 0 3px 4px rgb(64 112 203 / 5.88%);
  position: sticky;
  top: 0;
  z-index: 99;

  :deep(.bk-tab) {

    .bk-tab-header {
      border-bottom: none;
      line-height: 36px !important;

      &-item {
        padding: 0;
        font-size: 14px;
        margin-right: 32px;
      }
    }

    .bk-tab-content {
      padding: 0;
    }
  }
}
</style>
