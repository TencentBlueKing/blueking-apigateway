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
            </div>
          </div>

          <div class="permission-guide">
            <!-- <BkLink
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
              </BkLink> -->
            <bk-button
              theme="primary"
              @click="handleApplyPermission"
            >
              {{ t('申请权限') }}
            </bk-button>
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
          <div class="info-item">
            <div class="label">
              {{ t('分类') }}:
            </div>
            <div class="value lh-22px">
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

    <BkDialog
      v-model:is-show="isShowApplyPermissionDialog"
      :title="t('申请权限')"
      :quick-close="false"
      width="480"
      @closed="handleCloseApplyPermissionDialog"
    >
      <BkForm
        ref="formRef"
        :model="permissionFormData"
        :rules="rules"
        form-type="vertical"
      >
        <BkFormItem
          :label="t('选择应用')"
          property="application"
          class="relative"
          required
        >
          <BkSelect
            v-model="permissionFormData.application"
            :placeholder="t('请选择要申请权限的应用')"
          >
            <BkOption
              v-for="app in applicableApps"
              :key="app.bk_app_code"
              :label="app.name"
              :value="app.bk_app_code"
            />
          </BkSelect>
          <div
            class="new-application flex align-items-center cursor-pointer"
            @click="handleCreateNewApp"
          >
            <AgIcon
              name="add-small"
              size="22"
              color="#3A84FF"
            />
            <span class="color-#3A84FF ml--2px">{{ t('新建应用') }}</span>
          </div>
        </BkFormItem>
      </BkForm>
      <template #footer>
        <BkButton
          theme="primary"
          class="mr-8px"
          @click="handleApplyConfirm"
        >
          {{ t('确定') }}
        </BkButton>
        <BkButton @click="handleCloseApplyPermissionDialog()">
          {{ t('取消') }}
        </BkButton>
      </template>
    </BkDialog>
  </div>
</template>

<script lang="tsx" setup>
// @ts-nocheck
import { copy } from '@/utils';
import { useMcpConfigDivideRatio } from '@/hooks';
import {
  useEnv,
  useFeatureFlag,
} from '@/stores';
import {
  InfoBox,
} from 'bkui-vue';
import AgIcon from '@/components/ag-icon/Index.vue';
import {
  type IMarketplaceConfig,
  type IMarketplaceDetails,
  getApplicableApps,
  getMcpAIConfigList,
  getMcpServerDetails,
  marketplacePermissionApply,
} from '@/services/source/mcp-market';
import type { IApplicableAppOutput } from '@/services/types/responses/mcp-marketplace.ts';
import ServerTools from '@/views/mcp-server/components/ServerTools.vue';
import ServerPrompts from '@/views/mcp-server/components/ServerPrompts.vue';
import Guideline from './components/GuideLine.vue';
import EditMember from '@/views/basic-info/components/EditMember.vue';
import DefaultMdGuideSlider from '@/views/mcp-market/components/DefaultMdGuideSlider.vue';
import TenantUserSelector from '@/components/tenant-user-selector/Index.vue';
import AgMcpAgentConfig from '@/components/ag-mcp-agent-config/Index.vue';

interface IMarketplaceDetailsWithOverflow extends IMarketplaceDetails {
  isOverflow?: boolean
}

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const featureFlagStore = useFeatureFlag();
const envStore = useEnv();
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
const formRef = ref('');
const applicableApps = ref<IApplicableAppOutput[]>([]);
const itsmTicketUrl = ref('');
const permissionFormData = ref<{
  application: string
}>({
  application: '',
});
const rules = {
  application: [
    {
      required: true,
      message: t('请选择应用'),
    },
  ],
};

const mcpId = computed(() => {
  return route.params.id;
});
const isEnablePrompt = computed(() => featureFlagStore?.flags?.ENABLE_MCP_SERVER_PROMPT);
const isEnabledOAuth = computed(() =>
  featureFlagStore?.flags?.ENABLE_MCP_SERVER_OAUTH2_PUBLIC_CLIENT && mcpDetails.value?.oauth2_public_client_enabled,
);
const isShowConfig = computed(() => ['tools', 'guide'].includes(active.value) && mcpConfigList.value.length > 0);

const selectedAppName = computed(() => {
  const app = applicableApps.value.find(a => a.bk_app_code === permissionFormData.value.application);
  return app?.name ?? '';
});

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

const handleApplyPermission = async () => {
  try {
    const res = await getApplicableApps();
    applicableApps.value = res ?? [];
    isShowApplyPermissionDialog.value = true;
  }
  catch (e) {
    console.error(e);
  }
};

const handleCreateNewApp = () => {
  const url = envStore.env.PAAS_APP_CREATE_LINK;
  if (url) {
    window.open(url, '_blank');
  }
};

const handleApplyConfirm = async () => {
  try {
    await formRef.value?.validate();
    const name = selectedAppName.value;

    const res = await marketplacePermissionApply(Number(mcpId.value), {
      reason: t('申请权限'),
      bk_app_code: permissionFormData.value.application,
    });

    itsmTicketUrl.value = res[0]?.itsm_ticket_url ?? '';
    permissionFormData.value.application = '';
    isShowApplyPermissionDialog.value = false;

    InfoBox({
      type: 'success',
      title: t('权限申请已提交'),
      confirmText: t('完成'),
      content: () => (
        <div class="info-content">
          <div class="py-12px px-16px text-align-left bg-#f5f7fa mb-16px">
            {t('申请成功后，{name} 应用将拥有 {mcp} MCP 所有工具的权限。权限审批通过后即可正常使用。',
              { name,
                mcp: mcpDetails.value?.title ?? '' })}
          </div>
          {
            itsmTicketUrl.value && (
              <div
                class="color-#3A84FF font-size-14px cursor-pointer"
                onClick={() => window.open(itsmTicketUrl.value, '_blank')}
              >
                {t('查看审批进度')}
                <AgIcon name="jump" color="#3A84FF" size="16" class="ml-6px" />
              </div>
            )
          }
        </div>
      ),
    });
  }
  catch (e) {
    console.error(e);
  }
};

const handleCloseApplyPermissionDialog = () => {
  permissionFormData.value.application = '';
  isShowApplyPermissionDialog.value = false;
  formRef.value?.clearValidate();
};

const handleMouseenter = (e: MouseEvent & { target: HTMLElement }, row: IMarketplaceDetailsWithOverflow) => {
  const cell = e.target.closest('.truncate') as HTMLElement | null;
  if (cell) {
    row.isOverflow = cell.scrollWidth > cell.offsetWidth;
  }
};

const handleMouseleave = (_: MouseEvent, row: IMarketplaceDetailsWithOverflow) => {
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
      margin-bottom: 16px;
      background-color: #fff;
      border-radius: 2px;
      box-shadow: 0 2px 4px 0 #1919290d;

      .header {
        height: 52px;
        padding: 0 24px;
        border-bottom: 1px solid #eaebf0;

        .title {
          margin-right: 8px;
          font-size: 20px;
          font-weight: 700;
          color: #313238;
        }
      }

      .info-content {
        padding: 24px 24px 20px;

        .info-item {
          display: flex;
          align-items: baseline;
          font-size: 14px;
          line-height: 40px;

          .label {
            margin-right: 12px;
            color: #4d4f56;
            text-align: right;
            flex-shrink: 0;
          }

          .value {
            line-height: 22px;
            color: #313238;
            flex: 1;
            min-width: 0;

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

.new-application {
  cursor: pointer;
  position: absolute;
  top: -32px;
  right: 0;
}

</style>
