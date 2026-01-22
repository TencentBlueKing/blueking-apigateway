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
  <div class="ag-mcp-card-wrapper">
    <header class="w-full flex items-baseline justify-between card-header">
      <!-- mcp启用、停用、精选状态 -->
      <slot name="mcpStatus" />
      <div class="flex items-center header-title-wrapper">
        <div class="w-full flex items-baseline">
          <AgDescription
            class="color-#313238 text-16px font-700 lh-24px break-all mcp-card-title"
            :max-lines="2"
            :font-size="16"
            :line-height="'24px'"
            :show-expand-icon="false"
          >
            <template #description>
              {{ server?.title }}
            </template>
          </AgDescription>
          <slot name="officialTag" />
        </div>
      </div>
      <div
        v-if="showActions"
        class="header-actions"
      >
        <div class="ml-8px mr-8px button-group">
          <BkButton
            v-if="server.status"
            size="small"
            theme="primary"
            @click.stop="handleEditClick"
          >
            {{ t("编辑") }}
          </BkButton>
          <BkButton
            v-else
            size="small"
            @click.stop="handleEnableClick"
          >
            {{ t("启用") }}
          </BkButton>
        </div>
        <div
          class="dropdown-wrapper"
          @click.stop="preventDefault"
        >
          <BkDropdown trigger="hover">
            <AgIcon
              class="flex items-center justify-center w-16px h-16px cursor-pointer dropdown-wrapper-icon"
              name="more-fill"
              size="18"
            />
            <template #content>
              <BkDropdownMenu>
                <BkDropdownItem
                  v-if="server.status === 1"
                  @click="handleSuspendClick"
                >
                  <BkButton
                    size="small"
                    text
                  >
                    {{ t("停用") }}
                  </BkButton>
                </BkDropdownItem>
                <BkDropdownItem @click.stop="handleDeleteClick">
                  <BkButton
                    v-bk-tooltips="{
                      content: t('请先停用再删除'),
                      disabled: server.status === 0,
                    }"
                    :disabled="server.status === 1"
                    text
                  >
                    {{ t("删除") }}
                  </BkButton>
                </BkDropdownItem>
              </BkDropdownMenu>
            </template>
          </BkDropdown>
        </div>
      </div>
    </header>

    <AgDescription
      class="color-#979ba5 text-12px lh-20px mt-2px break-all"
      :show-expand-icon="false"
      :max-lines="1"
      :font-size="12"
      :line-height="'20px'"
    >
      <template #description>
        {{ server.name }}
      </template>
    </AgDescription>

    <BkOverflowTitle
      type="tips"
      class="max-w-56px mr-8px mt-12px"
    >
      <BkTag
        v-bk-tooltips="{
          content: server.stage?.name,
          disabled: server.stage?.name?.length < 4,
          extCls: 'max-w-480px',
        }"
        class="bg-#e1ecff! color-#1768ef! border-transparent!"
      >
        {{ server.stage?.name }}
      </BkTag>
    </BkOverflowTitle>

    <div class="divider" />

    <div class="mb-57px card-main">
      <AgDescription
        v-if="server?.description"
        class="color-#4d4f56 text-12px lh-20px break-all"
        :show-expand-icon="false"
        :line-height="'20px'"
        :font-size="12"
      >
        <template #description>
          {{ server?.description }}
        </template>
      </AgDescription>
    </div>

    <div class="text-14px lh-20px color-#979ba5 absolute bottom-24px left-24px right-24px mcp-footer-content">
      <div class="flex items-center justify-between text-12px content-item">
        <div
          v-bk-tooltips="{
            content: `${t('发布于')} ${getUtcTimeAgo(server?.updated_time)}`,
            disabled: !isOverflow,
          }"
          class="flex items-baseline gap-8px min-w-100px item-label"
          :style="{ maxWidth: `calc(100% - ${operateIconWidth}px)` }"
        >
          <i class="apigateway-icon icon-ag-time-circle color-#979ba5 text-14px" />
          <div
            class="truncate"
            @mouseenter="(e: MouseEvent) => handleMouseenter(e)"
            @mouseleave="handleMouseleave"
          >
            {{ t("发布于") }} {{ getUtcTimeAgo(server?.updated_time) }}
          </div>
        </div>
        <div
          :ref="(el: HTMLElement) => setMapRefs(el, operateIconRefs, 'item-value-')"
          class="flex items-center item-value"
        >
          <div
            v-bk-tooltips="{
              content: `${t('工具数量')}: ${String(server?.tools_count)}`,
            }"
            class="flex items-baseline gap-8px"
          >
            <i class="apigateway-icon icon-ag-manual-shoudongchuli color-#979ba5 text-14px" />
            <div class="truncate max-w-60px">
              {{ server?.tools_count }}
            </div>
          </div>
          <div
            v-if="isEnablePrompt"
            v-bk-tooltips="{
              content: `${t('Prompt数量')}: ${String(server?.prompts_count)}`,
              disabled: !isEnablePrompt,
            }"
            class="flex items-baseline gap-8px ml-24px"
          >
            <i class="apigateway-icon icon-ag-tishici color-#979ba5 text-14px" />
            <div class="truncate max-w-60px">
              {{ server?.prompts_count }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { locale, t } from '@/locales';
import { type IMCPServer } from '@/services/source/mcp-server"';
import { useFeatureFlag } from '@/stores';
import { getUtcTimeAgo, setupDayjsLocale } from '@/utils/dayUtc';
import AgDescription from '@/components/ag-description/Index.vue';

interface IProps {
  server?: IMCPServer
  showActions?: boolean
}

interface IEmits {
  edit: [id: number]
  suspend: [id: number]
  enable: [id: number]
  delete: [id: number]
}

const { server = {}, showActions = true } = defineProps<IProps>();

const emit = defineEmits<IEmits>();

const featureFlagStore = useFeatureFlag();

const isEnablePrompt = computed(() => featureFlagStore?.flags?.ENABLE_MCP_SERVER_PROMPT && server?.prompts_count > 0);

const operateIconRefs: Ref<Map<string, HTMLElement | null>> = ref(new Map());
const isOverflow = ref(false);
const operateIconWidth = ref(0);

setupDayjsLocale(locale.value);

const setMapRefs = (el: HTMLElement, anyRef: Ref, prefix: string) => {
  if (el) {
    anyRef?.set(`${prefix}${server?.id}`, el);
  }
};

const getOperateWidth = () => {
  nextTick(() => {
    operateIconWidth.value = operateIconRefs.value.get(`item-value-${server?.id}`)?.offsetWidth + 8 || 0;
  });
};
getOperateWidth();

const handleEditClick = () => {
  emit('edit', server.id);
};

const handleSuspendClick = () => {
  emit('suspend', server.id);
};

const handleEnableClick = () => {
  emit('enable', server.id);
};

const handleDeleteClick = () => {
  if (server.status === 1) {
    return;
  }
  emit('delete', server.id);
};

const handleMouseenter = (e: MouseEvent) => {
  const cell = (e.target as HTMLElement).closest('.truncate');
  if (cell) {
    isOverflow.value = cell.scrollWidth > cell.clientWidth;
  }
};

const handleMouseleave = () => {
  isOverflow.value = false;
};

const preventDefault = (e: MouseEvent) => {
  e.preventDefault();
};

onUnmounted(() => {
  operateIconRefs.value?.clear();
});
</script>

<style lang="scss" scoped>
.ag-mcp-card-wrapper {
  position: relative;
  padding: 24px;
  background-color: #ffffff;
  border-radius: 2px;
  box-shadow: 0 2px 4px 0 #1919290d;
  box-sizing: border-box;
  cursor: pointer;

  .card-header {

    :deep(.bk-tag-text) {
      font-size: 12px !important;
    }

    .header-actions {
      display: flex;
      align-items: center;

      .dropdown-wrapper {
        width: 0;
        margin-right: 12px;

        &-icon {
          width: 24px;
          height: 24px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          border: none;
          cursor: pointer;

          &:hover {
            background-color: #e5e6eb;
          }
        }
      }
    }
  }

  .divider {
    width: 100%;
    height: 1px;
    background-color: #eaebf0;
    margin-block: 16px;
  }

  :deep(.card-header-status) {
    min-width: 52px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding: 0 6px 1px 6px;
    gap: 8px;
    position: absolute;
    top: 0;
    right: 0;
    font-size: 12px;
    color: #ffffff;
    border-radius: 0 2px 0 99px;
  }

  &:hover {
    background: linear-gradient(149deg, #d7e8ff 0%, #fff 57.14%);
    box-shadow: 0 4px 6px 0 #1919291f;
    border-radius: 0 2px 2px 2px;
  }
}
</style>
