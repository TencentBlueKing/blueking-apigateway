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
    class="resource-top-bar"
    :style="stage.getNotUpdatedStages?.length ? 'top: 42px' : 'top: -1px'"
  >
    <div class="top-title-wrapper">
      <div class="title w-90%">
        <AgIcon
          size="32"
          class="icon"
          name="return-small"
          @click="handleBack"
        />
        <div class="flex items-center w-full">
          <BkOverflowTitle
            type="tips"
            class="truncate color-#313238 text-16px max-w-1/2"
          >
            {{ server?.title }}
          </BkOverflowTitle>
          <BkOverflowTitle
            type="tips"
            class="truncate color-#979ba5 text-14px ml-8px"
          >
            ({{ server?.name }})
          </BkOverflowTitle>
        </div>
      </div>
      <div
        class="history"
        @click="() => handleClick(server?.id)"
      >
        <span>{{ t('权限审批') }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useGateway, useStage } from '@/stores';
import { getServer } from '@/services/source/mcp-server';

type MCPServerType = Awaited<ReturnType<typeof getServer>>;

interface IProps { server: MCPServerType }

const { server } = defineProps<IProps>();

const { t } = useI18n();
const router = useRouter();
const gatewayStore = useGateway();
const stage = useStage();

const handleClick = (id: number) => {
  router.push({
    name: 'MCPServerPermission',
    params: { id: gatewayStore.currentGateway!.id! },
    query: { serverId: id },
  });
};

const handleBack = () => {
  router.push({
    name: 'MCPServer',
    params: { id: gatewayStore.currentGateway!.id! },
  });
};

</script>

<style lang="scss" scoped>
.resource-top-bar {
  position: absolute;
  display: flex;
  width: 100%;
  height: 52px;
  padding: 0 24px;
  background: #FFF;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;

  // min-width: 1280px;

  .top-title-wrapper {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;

    .title {
      display: flex;
      font-size: 16px;
      color: #313238;
      align-items: center;

      .icon {
        font-size: 32px;
        color: #3a84ff;
        cursor: pointer;
      }
    }

    .history {
      color: #3A84FF;
      cursor: pointer;

      span {
        font-size: 14px;
      }
    }
  }
}
</style>
