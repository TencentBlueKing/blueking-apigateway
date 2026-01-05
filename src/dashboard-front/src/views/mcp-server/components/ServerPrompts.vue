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
    ref="mcpPromptRef"
    class="mcp-prompt-wrapper"
  >
    <BkResizeLayout
      :border="false"
      :min="293"
      initial-divide="293px"
      placement="left"
      collapsible
      @collapse-change="handlePromptCollapseChange"
    >
      <template #aside>
        <div :class="`${promptCollapseMargin} left-aside-wrap`">
          <main
            class="mcp-prompt-list custom-scroll-bar"
            :style="{ height: setPageMaxH }"
          >
            <div
              v-for="prompt in promptList"
              :key="prompt.id"
              :class="{ active: prompt.id === curPromptData?.id }"
              class="flex items-center justify-between color-#4d4f56 prompt-item"
              @click="handlePromptClick(prompt)"
            >
              <div
                v-bk-tooltips="{
                  placement:'top',
                  content: `${prompt.name} (${prompt.code})`,
                  disabled: !prompt.isOverflow,
                }"
                class="truncate color-#4d4f56 text-12px mr-4px prompt-item-name"
                @mouseenter="(e: MouseEvent) => handlePromptMouseenter(e, prompt)"
                @mouseleave="() => handlePromptMouseleave(prompt)"
              >
                <span>{{ prompt.name }}</span>
                <span class="ml-4px">({{ prompt.code }})</span>
              </div>
              <BkTag
                :theme="prompt.is_public ? 'success' : 'warning'"
              >
                {{ t(prompt.is_public ? '公开' : '私有') }}
              </BkTag>
            </div>
          </main>
        </div>
      </template>
      <template #main>
        <BkLoading :loading="promptDetailLoading">
          <div
            class="w-full pl-24px pr-24px main-content-wrap"
            :style="{ height: setPageMaxH }"
          >
            <div
              v-if="Object.keys(curPromptData)?.length"
              class="w-full p-16px mt-16px mb-16px prompt-detail-content"
            >
              <div class="flex items-center gap-4px">
                <div class="min-w-0 flex text-14px font-700 color-#4d4f56">
                  <div
                    v-bk-tooltips="{
                      placement:'top',
                      content: `${curPromptData.name} (${curPromptData.code})`,
                      disabled: !curPromptData.isOverflow,
                    }"
                    class="w-full truncate"
                    @mouseenter="(e: MouseEvent) => handlePromptMouseenter(e, curPromptData)"
                    @mouseleave="() => handlePromptMouseleave(curPromptData)"
                  >
                    <span>{{ curPromptData?.name ?? '--' }}</span>
                    <span class="ml-8px">
                      ({{ curPromptData?.code ?? '--' }})
                    </span>
                  </div>
                </div>
                <div class="flex-shrink-0">
                  <BkTag
                    :theme="curPromptData?.is_public ? 'success' : 'warning'"
                  >
                    {{ t( curPromptData?.is_public ? '公开' : '私有') }}
                  </BkTag>
                </div>
              </div>
              <AgDescription
                v-if="curPromptData?.content?.length"
                class="mt-12px lh-22px text-14px color-#4d4f56 break-all gap-16px"
                :dynamic-max-height="500"
              >
                <template #description>
                  {{ curPromptData?.content }}
                </template>
              </AgDescription>
              <div
                v-if="curPromptData?.labels?.length"
                class="mt-16px"
              >
                <BkTag
                  v-for="label of curPromptData?.labels"
                  :key="label"
                  class="mr-4px"
                >
                  {{ label }}
                </BkTag>
              </div>
            </div>
          </div>
        </BkLoading>
      </template>
    </BkResizeLayout>
  </div>
</template>

<script lang="ts" setup>
import { useFeatureFlag, useGateway } from '@/stores';
import {
  type IMCPServerPrompt,
  getServer,
  getServerPromptsDetail,
} from '@/services/source/mcp-server';
import AgDescription from '@/components/ag-description/Index.vue';

type MCPServerType = Awaited<ReturnType<typeof getServer>>;

interface IProps {
  server: MCPServerType
  page?: string
}

const { server, page = 'server' } = defineProps<IProps>();

const emit = defineEmits<{ 'update-count': [count: number] }>();

const { t } = useI18n();
const featureFlagStore = useFeatureFlag();
const gatewayStore = useGateway();

const mcpPromptRef = ref<HTMLDivElement | null>(null);
const curPromptData = ref<IMCPServerPrompt>({});
const promptCollapseMargin = ref('mt-16px');
const promptDetailLoading = ref(false);

const isShowNoticeAlert = computed(() => featureFlagStore.isEnabledNotice);
const setPageMaxH = computed(() => {
  const offsetH = page === 'market'
    ? (isShowNoticeAlert.value ? 600 : 494)
    : (isShowNoticeAlert.value ? 420 : 380);
  return `calc(100vh - ${offsetH}px)`;
});
const promptList = computed<IMCPServerPrompt[]>(() => {
  const results = server?.prompts ?? [];
  if (results.length) {
    curPromptData.value = results?.[0];
    emit('update-count', results.length);
  }
  return results;
});

const fetchPromptDetail = async () => {
  promptDetailLoading.value = true;
  try {
    const res = await getServerPromptsDetail(gatewayStore.currentGateway?.id, { ids: [curPromptData.value.id] });
    curPromptData.value = Object.assign(curPromptData.value, res?.prompts?.[0] ?? {});
  }
  catch {
    curPromptData.value = {};
  }
  finally {
    promptDetailLoading.value = false;
  }
};

const handlePromptCollapseChange = (isCollapse: boolean) => {
  if (isCollapse) {
    promptCollapseMargin.value = 'hidden mt-0';
  }
  else {
    promptCollapseMargin.value = 'mt-16px';
  }
};

const handlePromptClick = (row: IMCPServerPrompt) => {
  const isRepeat = `${curPromptData.value.id}&${curPromptData.value.code}` === `${row.id}&${row.code}`;
  if (!isRepeat) {
    curPromptData.value = row;
    fetchPromptDetail();
  }
};

const handlePromptMouseenter = (e: MouseEvent, row: IMCPServerPrompt) => {
  const cell = (e.target as HTMLElement).closest('.truncate');
  if (cell) {
    row.isOverflow = cell.scrollWidth > cell.clientWidth;
  }
};

const handlePromptMouseleave = (row: IMCPServerPrompt) => {
  delete row.isOverflow;
};
</script>

<style lang="scss" scoped>
@use "sass:color";

.mcp-prompt-wrapper {
  flex: 1;
  height: 100%;
  box-shadow: 0 2px 4px 0 #1919290d;

  .left-aside-wrap {
    background-color: #ffffff;
    border-radius: 2px;

    .mcp-prompt-list {
      overflow-y: auto;

      .prompt-item {
        height: 32px;
        line-height: 32px;
        padding: 0 24px;

        &:hover,
        &.active {
          background-color: #f0f5ff;
          cursor: pointer;
        }

        &.active {
          .prompt-item-name {
            color: #3a84ff;
          }
        }
      }
    }
  }

  .main-content-wrap {
    overflow-y: auto;

    .prompt-detail-content {
      color: #4d4f56;
      border: 1px solid #dcdee5;
      border-radius: 2px;

      &:hover {
        box-shadow: 0 2px 4px 0 #1919290d;
        cursor: pointer;
      }
    }
  }
}

.custom-scroll-bar {
  &::-webkit-scrollbar {
    width: 4px;
    background-color: color.scale(#c4c6cc, $lightness: 80%);
  }

  &::-webkit-scrollbar-thumb {
    height: 5px;
    background-color: #c4c6cc;
    border-radius: 2px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }
}

:deep(.bk-resize-layout.bk-resize-layout-left) {
  flex: 1;
}
</style>
