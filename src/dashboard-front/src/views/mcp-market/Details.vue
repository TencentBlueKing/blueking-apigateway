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
  <div class="mcp-market-detail-wrapper">
    <div class="top-bar flex items-center">
      <AgIcon
        name="return-small"
        size="32"
        class="icon"
        @click="goBack"
      />
      <div class="flex items-center w-full">
        <BkOverflowTitle
          type="tips"
          class="truncate color-#313238 text-16px max-w-1/2"
        >
          {{ mcpDetails?.title }}
        </BkOverflowTitle>
        <BkOverflowTitle
          type="tips"
          class="truncate color-#979ba5 text-14px ml-8px"
        >
          ({{ mcpDetails?.name }})
        </BkOverflowTitle>
      </div>
    </div>

    <div class="main">
      <div class="base-info">
        <div class="flex items-center justify-between header">
          <div class="flex items-center max-w-[calc(100%-300px)] gap-8px">
            <div class="flex items-center min-w-0 title">
              <BkOverflowTitle
                type="tips"
                class="truncate"
              >
                {{ mcpDetails?.title }}
              </BkOverflowTitle>
              <BkOverflowTitle
                type="tips"
                class="truncate ml-8px"
              >
                ({{ mcpDetails?.name }})
              </BkOverflowTitle>
            </div>
            <div class="flex items-baseline flex-shrink-0">
              <BkTag
                v-if="mcpDetails?.is_official"
                theme="success"
                class="mr-8px"
              >
                {{ t('官方') }}
              </BkTag>
              <BkTag theme="info">
                {{ mcpDetails?.stage?.name }}
              </BkTag>
            </div>
          </div>

          <div class="permission-guide">
            <BkLink
              theme="primary"
              :href="envStore.env.DOC_LINKS.MCP_SERVER_PERMISSION_APPLY"
              target="_blank"
              class="text-12px"
            >
              <AgIcon
                name="jump"
                size="12"
                class="mr-6px icon"
              />
              {{ t('权限申请指引') }}
            </BkLink>
          </div>
        </div>
        <div class="info-content">
          <div class="info-item">
            <div class="label">
              {{ t('访问地址') }}:
            </div>
            <div class="w-full flex items-baseline value">
              <div
                v-bk-tooltips="{
                  content: mcpDetails?.url ?? '',
                  disabled: !mcpDetails?.isOverflow,
                  extCls: 'max-w-[calc(100%-100px)]'
                }"
                class="max-w-[calc(100%-100px)] truncate"
                @mouseenter="(e: MouseEvent) => handleMouseenter(e, mcpDetails)"
                @mouseleave="(e: MouseEvent) => handleMouseleave(e, mcpDetails)"
              >
                {{ mcpDetails?.url }}
              </div>
              <AgIcon
                name="copy"
                size="16"
                class="shrink-0 ml-8px icon"
                @click="() => handleCopy(mcpDetails?.url)"
              />
            </div>
          </div>
          <div class="info-item">
            <div class="label">
              {{ t('描述') }}:
            </div>
            <div
              v-bk-tooltips="{
                content: mcpDetails?.description ?? '',
                disabled: !mcpDetails?.isOverflow,
                extCls: 'max-w-[calc(100%-100px)]'
              }"
              class="truncate value"
              @mouseenter="(e: MouseEvent) => handleMouseenter(e, mcpDetails)"
              @mouseleave="(e: MouseEvent) => handleMouseleave(e, mcpDetails)"
            >
              {{ mcpDetails?.description }}
            </div>
          </div>
          <div class="info-item">
            <div class="label">
              {{ t('标签') }}:
            </div>
            <div class="value">
              <template v-if="mcpDetails?.labels?.length">
                <BkTag
                  v-for="label in mcpDetails?.labels"
                  :key="label"
                  class="mt-8px mr-8px"
                >
                  {{ label }}
                </BkTag>
              </template>
              <template v-else>
                --
              </template>
            </div>
          </div>
          <div class="info-item">
            <div class="label">
              {{ t('分类') }}:
            </div>
            <div class="value lh-22px!">
              <template v-if="mcpDetails?.categories?.length">
                <BkTag
                  v-for="category of mcpDetails?.categories"
                  :key="category"
                  class="mr-8px"
                >
                  {{ category.display_name }}
                </BkTag>
              </template>
              <template v-else>
                --
              </template>
            </div>
          </div>
          <div class="info-item">
            <div class="label">
              {{ t('负责人') }}:
            </div>
            <div class="value">
              <TenantUserSelector
                v-if="featureFlagStore.isEnableDisplayName"
                :content="mcpDetails?.maintainers"
                field="maintainers"
                mode="detail"
                width="600px"
              />
              <EditMember
                v-else
                mode="detail"
                width="600px"
                field="maintainers"
                :content="mcpDetails?.maintainers"
              />
            </div>
          </div>
        </div>
      </div>

      <section
        :class="[
          `tab-wrapper mcp-detail-${active}`,
        ]"
      >
        <BkResizeLayout
          placement="right"
          :border="false"
          :initial-divide="isShowConfig ? '31.12%' : 0"
          :class="isShowConfig ? 'gap-16px' : ''"
        >
          <template
            v-if="isShowConfig"
            #aside
          >
            <!-- 配置 -->
            <ServerConfig
              :list="mcpConfigList"
              class="h-full bg-white mcp-detail-config"
            />
          </template>
          <template #main>
            <BkTab
              v-model:active="active"
              type="card-tab"
              class="mcp-tab"
            >
              <BkTabPanel
                name="tools"
              >
                <template #label>
                  <div class="flex-row items-center">
                    {{ t('工具') }}
                    <div
                      v-if="toolsCount > 0"
                      class="count"
                      :class="[active === 'tools' ? 'on' : 'off']"
                    >
                      {{ toolsCount }}
                    </div>
                  </div>
                </template>
                <div class="panel-content">
                  <ServerTools
                    :server="mcpDetails"
                    page="market"
                  />
                </div>
              </BkTabPanel>
              <BkTabPanel
                v-if="isEnablePrompt && promptCount > 0"
                name="prompts"
              >
                <template #label>
                  <div class="flex-row items-center">
                    Prompts
                    <div
                      v-if="promptCount"
                      class="count"
                      :class="[active === 'prompts' ? 'on' : 'off']"
                    >
                      {{ promptCount }}
                    </div>
                  </div>
                </template>
                <div class="panel-content">
                  <ServerPrompts
                    :server="mcpDetails"
                    page="market"
                  />
                </div>
              </BkTabPanel>
              <BkTabPanel
                name="guide"
              >
                <template #label>
                  <div class="flex-row items-center">
                    {{ t('使用指引') }}
                  </div>
                </template>
                <div class="panel-content">
                  <div
                    v-if="isExistCustomGuide"
                    class="p-t-24px! p-r-24px! w-full text-align-right"
                  >
                    <BkButton
                      theme="primary"
                      text
                      @click="handleShowGuide"
                    >
                      <AgIcon
                        name="wenjian"
                        size="16"
                        class="mr-8px"
                      />
                      {{ t('查看默认使用指引') }}
                    </BkButton>
                  </div>
                  <Guideline
                    :markdown-str="markdownStr"
                    :show-usage-guide="false"
                    :config-list="mcpConfigList"
                    page="market"
                  />
                </div>
              </BkTabPanel>
            </BkTab>
          </template>
        </BkResizeLayout>
      </section>
    </div>

    <DefaultMdGuideSlider
      v-model:is-show="isShowGuideSlider"
      :markdown-text="defaultMarkdownStr"
    />
  </div>
</template>

<script lang="ts" setup>
import { copy } from '@/utils';
import {
  useEnv,
  useFeatureFlag,
} from '@/stores';
import AgIcon from '@/components/ag-icon/Index.vue';
import {
  type IMarketplaceConfig,
  type IMarketplaceDetails,
  getMcpAIConfigList,
  getMcpServerDetails,
} from '@/services/source/mcp-market';
import ServerTools from '@/views/mcp-server/components/ServerTools.vue';
import ServerPrompts from '@/views/mcp-server/components/ServerPrompts.vue';
import ServerConfig from '@/views/mcp-server/components/ServerConfig.vue';
import Guideline from './components/GuideLine.vue';
import EditMember from '@/views/basic-info/components/EditMember.vue';
import TenantUserSelector from '@/components/tenant-user-selector/Index.vue';
import DefaultMdGuideSlider from '@/views/mcp-market/components/DefaultMdGuideSlider.vue';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const featureFlagStore = useFeatureFlag();
const envStore = useEnv();

const active = ref('tools');
const toolsCount = ref<number>(0);
const promptCount = ref(0);
const mcpDetails = ref<IMarketplaceDetails>();
const defaultMarkdownStr = ref('');
const markdownStr = ref('');
const isExistCustomGuide = ref(false);
const isShowGuideSlider = ref(false);
const mcpConfigList = ref<IMarketplaceConfig[]>([]);

const mcpId = computed(() => {
  return route.params.id;
});
const isEnablePrompt = computed(() => featureFlagStore?.flags?.ENABLE_MCP_SERVER_PROMPT);
const isShowConfig = computed(() => ['tools', 'guide'].includes(active.value) && mcpConfigList.value.length > 0);

const handleCopy = (str: string) => {
  copy(str);
};

const goBack = () => {
  router.push({ name: 'McpMarket' });
};

const getDetails = async () => {
  const res = await getMcpServerDetails(mcpId.value as string);
  mcpDetails.value = res ?? {};
  const { tools_count = 0, prompts_count = 0, guideline = '', user_custom_doc = '' } = mcpDetails.value;
  toolsCount.value = tools_count;
  promptCount.value = prompts_count;
  [markdownStr.value, defaultMarkdownStr.value] = [guideline, guideline];
  if (user_custom_doc) {
    markdownStr.value = user_custom_doc;
    isExistCustomGuide.value = user_custom_doc.length > 0;
  }
};

const fetchMcpAIConfigList = async () => {
  const res = await getMcpAIConfigList(mcpId.value);
  mcpConfigList.value = res?.configs ?? [];
};

const handleShowGuide = () => {
  isShowGuideSlider.value = true;
};

const handleMouseenter = (e: MouseEvent & { target: HTMLElement }, row: IMarketplaceDetails) => {
  const cell = e.target.closest('.truncate');
  if (cell) {
    row.isOverflow = cell.scrollWidth > cell.offsetWidth;
  }
};

const handleMouseleave = (_: MouseEvent, row: IMarketplaceDetails) => {
  row.isOverflow = false;
};

watch(
  () => mcpId.value,
  () => {
    Promise.allSettled([getDetails(), fetchMcpAIConfigList()]);
  },
  { immediate: true },
);
</script>

<style lang="scss" scoped>
.mcp-market-detail-wrapper {
  box-sizing: border-box;

  .top-bar {
    position: sticky;
    top: 0;
    height: 52px;
    padding: 0 24px;
    background-color: #ffffff;
    z-index: 999;
    box-shadow: 0 3px 4px 0 #0000000a;

    .icon {
      margin-right: 4px;
      color: #3a84ff;
      cursor: pointer;
    }

    .top-bar-title {
      font-size: 16px;
      color: #313238;
    }
  }

  .main {
    max-width: 1920px;
    margin: 24px auto;
    padding: 0 80px;
    background-color: #f5f7fa;
    box-sizing: border-box;

    .base-info {
      margin-bottom: 16px;
      background-color: #ffffff;
      border-radius: 2px;
      box-shadow: 0 2px 4px 0 #1919290d;

      .header {
        padding: 0 24px;
        height: 52px;
        border-bottom: 1px solid #eaebf0;

        .title {
          margin-right: 16px;
          font-size: 20px;
          font-weight: 700;
          color: #313238;
        }
      }

      .info-content {
        padding: 24px 24px 20px 24px;

        .info-item {
          display: flex;
          align-items: baseline;
          font-size: 14px;
          line-height: 40px;

          .label {
            flex-shrink: 0;
            color: #4d4f56;
            margin-right: 12px;
            text-align: right;
          }

          .value {
            flex: 1;
            color: #313238;
            line-height: 22px;

            .icon {
              color: #3a84ff;
              cursor: pointer;
            }

            .member-item {
              line-height: 22px;
            }
          }

        }
      }
    }

    // 屏幕宽度小于1680px时，padding自动适配
    @media (max-width: 1680px) {
      padding: 0 calc(100vw / 24); // 小屏幕按比例缩放边距
    }

    // 极小屏幕强制最小边距，避免挤压
    @media (max-width: 768px) {
      padding: 0 24px;
    }
  }

  .count {
    padding: 2px 8px;
    margin-left: 8px;
    font-size: 12px;
    line-height: 12px;
    border-radius: 8px;

    &.on {
      color: #3a84ff;
      background: #E1ECFF;
    }

    &.off {
      color: #4d4f56;
    }
  }

  .tab-wrapper {
    :deep(.bk-tab-content) {
      padding: 0;
      background-color: #ffffff;
    }

    .bk-resize-layout-right {
      :deep(>.bk-resize-layout-aside) {
        display: none;
      }
    }

    &.mcp-detail-tools,
    &.mcp-detail-guide {
      width: 100%;

      .bk-resize-layout-right {

        :deep(>.bk-resize-layout-aside) {
          display: block;

          .bk-resize-trigger {
            background-color: #ffffff;
          }
        }

        :deep(>.bk-resize-layout-main) {
          width: 62.5% !important;
        }
      }
    }
  }
}

</style>
