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
  <div class="observability-wrapper">
    <!-- 顶部tab -->
    <ObservabilityTopBar
      v-model:active-tab="activeTab"
      @tab-change="handleTabChange"
    />
    <!-- 内容区域 -->
    <Component
      :is="observabilityCompMap[activeTab as keyof typeof observabilityCompMap]"
      :key="activeTab"
    />
  </div>
</template>

<script lang="ts" setup>
import ObservabilityTopBar from '@/views/mcp-server/components/ObservabilityTopBar.vue';
import ObservabilityFlowLog from '@/views/mcp-server/components/ObservabilityFlowLog.vue';
import ObservabilityDashboard from '@/views/mcp-server/components/ObservabilityDashboard.vue';

const observabilityCompMap = {
  FlowLog: ObservabilityFlowLog,
  Dashboard: ObservabilityDashboard,
};

const activeTab = shallowRef('FlowLog');

// 切换重置tab滚动条
const handleResetScroll = () => {
  const scrollEl = document.querySelector('.default-header-view');
  if (scrollEl?.scrollTop > 0) {
    scrollEl.scrollTop = 0;
  }
};

const handleTabChange = () => {
  handleResetScroll();
};

onMounted(() => {
  handleResetScroll();
});
</script>

<style lang="scss" scoped>
.observability-wrapper {
  box-sizing: border-box;

  .observability-tab {
    padding: 0 24px;
    background-color: #ffffff;

    &-header {
      display: flex;
      align-items: items-center;

      .tab-item {
        padding: 10px 20px;
        position: relative;
        cursor: pointer;

        &.active {
          color: #3a84ff;

          &::after {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 0;
            width: 100%;
            height: 2px;
            background-color: #409eff;
          }
        }
      }
    }

    &-content {
      padding: 0 24px;
    }
  }
}
</style>
