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
  <div class="ag-mcp-card-wrapper">
    <header class="w-full flex items-baseline justify-between card-header">
      <div class="max-w-[calc(100%-138px)] flex items-center gap-8px header-title-wrapper">
        <div class="w-full flex items-center gap-8px">
          <BkOverflowTitle
            type="tips"
            class="color-#313238 text-16px font-700 lh-22px mcp-card-title"
          >
            {{ server.title }}
          </BkOverflowTitle>
          <BkTag
            size="small"
            :theme="server.status === 1 ? 'success' : 'default'"
          >
            {{ t(server.status === 1 ? '启用中' : '已停用') }}
          </BkTag>
          <BkOverflowTitle
            type="tips"
            class="max-w-56px mr-8px"
          >
            <BkTag
              v-bk-tooltips="{
                content: server.stage?.name ,
                disabled: server.stage?.name?.length < 4,
                extCls: 'max-w-480px'
              }"
              theme="info"
              class="w-full"
            >
              {{ server.stage?.name }}
            </BkTag>
          </BkOverflowTitle>
        </div>
      </div>
      <div
        v-if="showActions"
        class="header-actions"
      >
        <div class="button-group">
          <BkButton
            :disabled="server.status === 0"
            size="small"
            theme="primary"
            @click.stop="handleEditClick"
          >
            {{ t('编辑') }}
          </BkButton>
        </div>
        <div
          class="dropdown-wrapper"
          @click.stop="preventDefault"
        >
          <BkDropdown trigger="hover">
            <AgIcon
              class="dropdown-trigger hover:bg-transparent!"
              name="more-fill"
              size="22"
            />
            <template #content>
              <BkDropdownMenu>
                <BkDropdownItem
                  @click.stop="() => { server.status === 1 ? handleSuspendClick() : handleEnableClick() }"
                >
                  <BkButton
                    size="small"
                    text
                  >
                    {{ t(server.status === 1 ? '停用' : '启用') }}
                  </BkButton>
                </BkDropdownItem>
                <BkDropdownItem @click="handleDeleteClick">
                  <BkButton
                    v-bk-tooltips="{
                      content: t('请先停用再删除'),
                      disabled: server.status === 0,
                    }"
                    :disabled="server.status === 1"
                    text
                  >
                    {{ t('删除') }}
                  </BkButton>
                </BkDropdownItem>
              </BkDropdownMenu>
            </template>
          </BkDropdown>
        </div>
      </div>
    </header>

    <AgDescription
      class="color-#979ba5 text-14px lh-22px mt-12px break-all"
      :show-expand-icon="false"
      :max-lines="1"
    >
      <template #description>
        {{ server.name }}
      </template>
    </AgDescription>

    <div class="divider" />

    <div class="mb-44px card-main">
      <AgDescription
        v-if="server?.description"
        :show-expand-icon="false"
        class="color-#4d4f56 break-all"
      >
        <template #description>
          {{ server?.description }}
        </template>
      </AgDescription>
    </div>

    <div class="text-14px lh-22px color-#979ba5 absolute bottom-24px mcp-footer-content">
      <div class="flex items-center justify-between content-item">
        <div
          v-bk-tooltips="{
            content: `${t('发布于')} ${getUtcTimeAgo(server?.updated_time)}`,
            disabled: !isOverflow
          }"
          class="flex items-center gap-4px min-w-100px item-label"
          :style="{ maxWidth: `calc(100% - ${operateIconWidth}px)` }"
        >
          <i class="apigateway-icon icon-ag-time-circle color-#979ba5 text-16px" />
          <div
            class="truncate"
            @mouseenter="(e: MouseEvent) => handleMouseenter(e)"
            @mouseleave="handleMouseleave"
          >
            {{ t('发布于') }} {{ getUtcTimeAgo(server?.updated_time) }}
          </div>
        </div>
        <div
          :ref="(el: HTMLElement) => setMapRefs(el, operateIconRefs,'item-value-')"
          class="flex items-center item-value"
        >
          <div class="flex items-center gap-4px">
            <i class="apigateway-icon icon-ag-manual color-#979ba5 text-16px" />
            <div
              v-bk-tooltips="{
                content: `${t('工具')}: ${String(server?.tools_count)}`,
                disabled: String(server?.tools_count).length < 6
              }"
              class="truncate max-w-60px"
            >
              {{ server?.tools_count }}
            </div>
          </div>
          <div
            v-if="isEnablePrompt"
            class="flex items-center gap-4px ml-20px"
          >
            <i class="apigateway-icon icon-ag-nocomment color-#979ba5 text-16px" />
            <div
              v-bk-tooltips="{
                content: `Prompts: ${String(server?.prompts_count)}`,
                disabled: String(server?.prompts_count).length < 6
              }"
              class="truncate max-w-60px"
            >
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
import { type IMCPServer } from '@/services/source/mcp-server';
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
  border-radius: 2px;
  background-color: #ffffff;
  box-shadow: 0 2px 4px 0 #1919290d;
  box-sizing: border-box;
  cursor: pointer;

  .card-header {

    .header-title-wrapper {

      :deep(.bk-tag-text) {
        font-size: 12px !important;
      }
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;

      .button-group {
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .dropdown-wrapper {

        .dropdown-trigger {
          display: flex;
          width: 26px;
          height: 26px;
          font-size: 16px;
          cursor: pointer;
          border-radius: 2px;
          justify-content: center;
          align-items: center;

          &:hover {
            background: #f0f1f5;
          }
        }
      }
    }
  }

  .divider {
    width: 100%;
    height: 1px;
    background-color: #eaebf0;
    margin-block: 12px;
  }
}
</style>
