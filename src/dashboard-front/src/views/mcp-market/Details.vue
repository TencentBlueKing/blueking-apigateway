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
                class="truncate text-14px ml-4px"
              >
                ({{ mcpDetails?.name }})
              </BkOverflowTitle>
            </div>
            <div class="flex items-center gap-8px flex-shrink-0">
              <BkTag
                v-if="mcpDetails?.is_official"
                theme="success"
                class="h-18px"
              >
                {{ t('官方') }}
              </BkTag>
              <BkTag
                theme="info"
                class="h-18px"
              >
                {{ mcpDetails?.stage?.name }}
              </BkTag>
              <div
                v-if="isEnabledOAuth"
                v-bk-tooltips="t('已开启 OAuth2 公开客户端模式，用户通过浏览器授权即可使用')"
                class="external-oauth-tag bg-#e1ecff cursor-pointer"
              >
                <AgIcon
                  name="deqiu"
                  size="14"
                  color="#3a84ff"
                />
              </div>
              <div
                v-if="isEnablePersonalClient"
                v-bk-tooltips="t('可用个人令牌调用该 MCP Server')"
                class="external-oauth-tag bg-#e1ecff cursor-pointer"
              >
                <AgIcon
                  name="key-fill"
                  size="14"
                  color="#3a84ff"
                />
              </div>
            </div>
          </div>

          <div class="permission-guide">
            <bk-button
              theme="primary"
              @click="handleApplyPermission"
            >
              {{ t('申请权限') }}
            </bk-button>
          </div>
        </div>
        <div class="info-content">
          <div class="info-column">
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
                  extCls: 'max-w-[calc(100%-100px)] break-all'
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
          <div class="info-column">
            <div class="info-item">
              <div class="label">
                {{ t('分类') }}:
              </div>
              <div class="value flex flex-wrap gap-8px lh-22px">
                <template v-if="mcpDetails?.categories?.length">
                  <BkTag
                    v-for="category of mcpDetails?.categories"
                    :key="category"
                    class="flex-shrink-0 max-w-full break-all"
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
                {{ t('标签') }}:
              </div>
              <div class="value lh-22px">
                <div
                  v-if="mcpDetails?.labels?.length"
                  class="flex flex-wrap gap-8px w-full"
                >
                  <template
                    v-for="label of mcpDetails.labels"
                    :key="label"
                  >
                    <BkTag
                      class="flex-shrink-0 max-w-full break-all"
                      :title="label"
                    >
                      {{ label }}
                    </BkTag>
                  </template>
                </div>
                <template v-else>
                  --
                </template>
              </div>
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
          :initial-divide="isShowConfig ? divideRatio : 0"
          :class="isShowConfig ? 'gap-16px' : ''"
        >
          <template
            v-if="isShowConfig"
            #aside
          >
            <!-- 配置 -->
            <AgMcpAgentConfig
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
                    :server="mcpServerInfo"
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
                    :server="mcpServerInfo"
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

    <ApplyPermissionDialog
      v-model:is-show="isShowApplyPermissionDialog"
      :mcp-id="Number(mcpId)"
      :mcp-name="mcpDetails?.title ?? ''"
    />
  </div>
</template>

<script lang="tsx" setup>
import { copy } from '@/utils';
import { useMcpConfigDivideRatio } from '@/hooks';
import { useFeatureFlag } from '@/stores';
import AgIcon from '@/components/ag-icon/Index.vue';
import {
  type IMCPMarketCategory,
  type IMarketplaceConfig,
  getMcpAIConfigList,
  getMcpServerDetails,
} from '@/services/source/mcp-market';
import type { IMCPServerRetrieveOutput } from '@/services/types/responses/mcp-marketplace.ts';
import type { getServer } from '@/services/source/mcp-server';
import ServerTools from '@/views/mcp-server/components/ServerTools.vue';
import ServerPrompts from '@/views/mcp-server/components/ServerPrompts.vue';
import Guideline from './components/GuideLine.vue';
import EditMember from '@/views/basic-info/components/EditMember.vue';
import DefaultMdGuideSlider from '@/views/mcp-market/components/DefaultMdGuideSlider.vue';
import ApplyPermissionDialog from '@/views/mcp-market/components/ApplyPermissionDialog.vue';
import TenantUserSelector from '@/components/tenant-user-selector/Index.vue';
import AgMcpAgentConfig from '@/components/ag-mcp-agent-config/Index.vue';

type MCPServerType = Awaited<ReturnType<typeof getServer>>;

type IMarketplaceDetailsWithOverflow = Omit<IMCPServerRetrieveOutput, 'categories' | 'stage'> & {
  categories?: IMCPMarketCategory[]
  stage?: { name?: string }
  oauth2_public_client_enabled?: boolean
  oauth2_personal_client_enabled?: boolean
  isOverflow?: boolean
};

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const featureFlagStore = useFeatureFlag();
const { divideRatio } = useMcpConfigDivideRatio([
  {
    maxWidth: 1440,
    divide: '40%',
  },
  {
    minWidth: 1440,
    maxWidth: 1919,
    divide: '34%',
  },
  {
    minWidth: 1920,
    divide: '30%',
  },
]);

const active = ref('tools');
const toolsCount = ref(0);
const promptCount = ref(0);
const mcpDetails = ref<IMarketplaceDetailsWithOverflow>();
const defaultMarkdownStr = ref('');
const markdownStr = ref('');
const isExistCustomGuide = ref(false);
const isShowGuideSlider = ref(false);
const mcpConfigList = ref<IMarketplaceConfig[]>([]);
const isShowApplyPermissionDialog = ref<boolean>(false);

const mcpId = computed(() => {
  return route.params.id;
});
const isEnablePrompt = computed(() => featureFlagStore?.flags?.ENABLE_MCP_SERVER_PROMPT);
const isEnabledOAuth = computed(() =>
  featureFlagStore?.flags?.ENABLE_MCP_SERVER_OAUTH2_PUBLIC_CLIENT && mcpDetails.value?.oauth2_public_client_enabled,
);
const isEnablePersonalClient = computed(() =>
  featureFlagStore?.flags?.ENABLE_MCP_SERVER_OAUTH2_PERSONAL_CLIENT && mcpDetails.value?.oauth2_personal_client_enabled,
);
const isShowConfig = computed(() => ['tools', 'guide'].includes(active.value) && mcpConfigList.value.length > 0);
const mcpServerInfo = computed(() => (mcpDetails.value ?? {}) as unknown as MCPServerType);

const handleCopy = (str?: string) => {
  copy(str ?? '');
};

const goBack = () => {
  router.push({ name: 'McpMarket' });
};

const getDetails = async () => {
  const res = await getMcpServerDetails(mcpId.value as string);
  mcpDetails.value = (res ?? {}) as unknown as IMarketplaceDetailsWithOverflow;
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
  const res = await getMcpAIConfigList(Number(mcpId.value));
  mcpConfigList.value = (res?.configs ?? []).map(item => ({
    ...item,
    install_url: item.install_url ?? '',
  }));
};

const handleShowGuide = () => {
  isShowGuideSlider.value = true;
};

const handleApplyPermission = () => {
  isShowApplyPermissionDialog.value = true;
};

const handleMouseenter = (e: MouseEvent, row?: IMarketplaceDetailsWithOverflow) => {
  const cell = (e.target as HTMLElement | null)?.closest('.truncate') as HTMLElement | null;
  if (cell && row) {
    row.isOverflow = cell.scrollWidth > cell.offsetWidth;
  }
};

const handleMouseleave = (_: MouseEvent, row?: IMarketplaceDetailsWithOverflow) => {
  if (row) {
    row.isOverflow = false;
  }
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
    z-index: 999;
    height: 52px;
    padding: 0 24px;
    background-color: #fff;
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
    padding: 0 80px;
    margin: 24px auto;
    background-color: #f5f7fa;
    box-sizing: border-box;

    .base-info {
      padding: 16px 16px 7px 16px;
      margin-bottom: 16px;
      background-color: #fff;
      border-radius: 2px;
      box-shadow: 0 2px 4px 0 #1919290d;
      box-sizing: border-box;

      .header {
        height: auto;
        padding-bottom: 11px;
        border-bottom: 1px solid #eaebf0;

        .title {
          font-size: 16px;
          font-weight: 700;
          color: #313238;
        }
      }

      .info-content {
        display: grid;
        align-items: start;
        grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
        gap: 24px;
        padding-top: 3px;
        padding-left: 8px;

        .info-column {
          display: grid;
          align-items: start;
          align-content: start;
          grid-template-columns: max-content minmax(0, 1fr);
          min-width: 0;
        }

        .info-item {
          display: contents;
          font-size: 14px;
          line-height: 22px;
          color: #4d4f56;

          .label {
            padding: 9px 0;
            margin-right: 8px;
            text-align: right;
          }

          .value {
            padding: 9px 0;
            line-height: 22px;
            min-width: 0;

            .icon {
              color: #3a84ff;
              cursor: pointer;
            }

            :deep(.edit-content),
            :deep(.member-item) {
              line-height: 22px !important;
            }
          }

        }
      }
    }

    // 屏幕宽度小于1680px时，padding自动适配
    @media (max-width: 1680px) {
      padding: 0 calc(100vw / 24) 24px; // 小屏幕按比例缩放边距
    }

    // 极小屏幕强制最小边距，避免挤压
    @media (max-width: 768px) {
      padding: 0 24px 24px;
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
      background-color: #cce0ff;
    }

    &.off {
      color: #4d4f56;
      background-color: #dcdee5;
    }
  }

  .tab-wrapper {
    box-shadow: 0 2px 4px 0 #1919290d;
    border-radius: 0 0 2px 2px;

    :deep(.bk-tab-content) {
      padding: 0;
      background-color: #fff;
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
            background-color: #fff;
          }
        }

        :deep(>.bk-resize-layout-main) {
          width: 62.5% !important;
        }
      }
    }
  }

  :deep(.external-oauth-tag) {
    width: 18px;
    height: 18px;
    position: relative;
    font-size: 0;
    line-height: 1;
    flex-shrink: 0;
    border-radius: 2px;
    box-sizing: border-box;

    .apigateway-icon {
      position: absolute;
      left: 50%;
      top: 50%;
      transform: translate(-50%, -50%);
    }
  }
}

</style>
