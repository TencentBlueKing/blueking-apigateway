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
  <BkDialog
    v-model:is-show="isShow"
    :width="640"
    :title="t('复制 MCP Server 接入配置')"
    dialog-type="show"
    draggable
  >
    <AgMcpAgentConfig
      :show-title="false"
      :list="list"
      class="h-full bg-white"
    />
  </BkDialog>
</template>

<script lang="ts" setup>
import { t } from '@/locales';
import type { IMCPAIConfig } from '@/services/source/mcp-server';
import AgMcpAgentConfig from '@/components/ag-mcp-agent-config/Index.vue';

interface IProps { list?: IMCPAIConfig[] }

const isShow = defineModel('isShow', {
  type: Boolean,
  default: false,
});

const { list = [] } = defineProps<IProps>();
</script>

<style lang="scss" scoped>
:deep(.custom-configure-wrapper) {

  .bk-tab-header {
    padding-left: 0;
    padding-right: 0;
  }

  .ag-mcp-agent-guide {
    padding: 24px 0 0;
  }
}
</style>
