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
  <div>
    <div class="top-bar flex-row items-center">
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
        <div class="pt-18px pb-12px flex items-center justify-between w-full header">
          <div class="flex items-center flex-wrap gap-8px">
            <div class="flex items-center max-w-[960px] min-w-0 title">
              <BkOverflowTitle
                type="tips"
                class="truncate max-w-1/2"
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
            <div class="flex items-center flex-shrink-0">
              <BkTag
                v-if="mcpDetails?.gateway?.is_official"
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
            >
              <AgIcon
                name="jump"
                size="16"
                class="icon"
              />
              {{ t('权限申请指引') }}
            </BkLink>
          </div>
        </div>
        <div class="content">
          <div class="info-item">
            <div class="label">
              {{ t('访问地址') }}:
            </div>
            <div class="value">
              {{ mcpDetails?.url }}
              <AgIcon
                name="copy"
                size="16"
                class="icon"
                @click="() => handleCopy(mcpDetails?.url)"
              />
            </div>
          </div>
          <div class="info-item">
            <div class="label">
              {{ t('描述') }}:
            </div>
            <div class="value">
              {{ mcpDetails?.description }}
            </div>
          </div>
          <div class="info-item">
            <div class="label">
              {{ t('标签') }}:
            </div>
            <div class="value">
              <BkTag
                v-for="label in mcpDetails?.labels"
                :key="label"
                class="mr8"
              >
                {{ label }}
              </BkTag>
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
          v-if="isEnablePrompt"
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
            />
          </div>
        </BkTabPanel>
      </BkTab>
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
// import { useGetGlobalProperties } from '@/hooks';
import { type IMarketplaceDetails, getMcpServerDetails } from '@/services/source/mcp-market';
import { getCustomServerGuideDoc } from '@/services/source/mcp-server';
import ServerTools from '@/views/mcp-server/components/ServerTools.vue';
import ServerPrompts from '@/views/mcp-server/components/ServerPrompts.vue';
import Guideline from './components/GuideLine.vue';
import EditMember from '@/views/basic-info/components/EditMember.vue';
import TenantUserSelector from '@/components/tenant-user-selector/Index.vue';
import DefaultMdGuideSlider from '@/views/mcp-market/components/DefaultMdGuideSlider.vue';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const featureFlagStore = useFeatureFlag();
const envStore = useEnv();
// const globalProperties = useGetGlobalProperties();
// const { GLOBAL_CONFIG } = globalProperties;

const active = ref('tools');
const toolsCount = ref<number>(0);
const promptCount = ref(0);
const mcpDetails = ref<IMarketplaceDetails>();
const defaultMarkdownStr = ref('');
const markdownStr = ref('');
const isExistCustomGuide = ref(false);
const isShowGuideSlider = ref(false);

const mcpId = computed(() => {
  return route.params.id;
});
const isEnablePrompt = computed(() => featureFlagStore?.flags?.ENABLE_MCP_SERVER_PROMPT);

const handleCopy = (str: string) => {
  copy(str);
};

const goBack = () => {
  router.push({ name: 'McpMarket' });
};

const getDetails = async () => {
  const res = await getMcpServerDetails(mcpId.value as string);
  mcpDetails.value = res ?? {};
  const { tools_count = 0, prompts_count = 0, guideline = '' } = mcpDetails.value;
  toolsCount.value = tools_count;
  promptCount.value = prompts_count;
  [markdownStr.value, defaultMarkdownStr.value] = [guideline, guideline];
  if (res?.gateway?.id) {
    await fetchCustomGuide(res?.gateway?.id);
  }
};

const fetchCustomGuide = async (gatewayId) => {
  const res = await getCustomServerGuideDoc(gatewayId, mcpId.value);
  if (res?.content) {
    markdownStr.value = res.content;
  }
  isExistCustomGuide.value = res?.content?.length > 0;
};

const handleShowGuide = () => {
  isShowGuideSlider.value = true;
};

watch(
  () => mcpId.value,
  () => {
    getDetails();
  },
  { immediate: true },
);

</script>

<style lang="scss" scoped>
.top-bar {
  position: sticky;
  top: 0;
  height: 64px;
  padding: 0 24px;
  background: #ffffff;
  z-index: 9;
  box-shadow: 0 3px 4px 0 #0000000a;

  .icon {
    margin-right: 4px;
    color: #3A84FF;
    cursor: pointer;
  }

  .top-bar-title {
    font-size: 16px;
    color: #313238;
  }
}

.main {
  width: 1280px;
  height: calc(100vh - 116px);
  padding: 24px 0 42px;
  margin: 0 auto;
  background-color: #f5f7fa;
  box-sizing: border-box;

  .base-info {
    padding: 0 24px;
    margin-bottom: 16px;
    background: #FFF;
    border-radius: 2px;
    box-shadow: 0 2px 4px 0 #1919290d;

    .header {
      border-bottom: 1px solid #EAEBF0;

      .title {
        margin-right: 16px;
        font-size: 20px;
        font-weight: bold;
        color: #313238;
      }

      .permission-guide {

        .icon {
          margin-right: 6px;
        }
      }
    }

    .content {
      padding: 12px 0 4px;

      .info-item {
        display: flex;
        align-items: center;
        margin-bottom: 20px;

        .label {
          font-size: 14px;
          color: #4D4F56;
        }

        .value {
          font-size: 14px;
          color: #313238;
          margin-left: 8px;

          .icon {
            color: #3A84FF;
            cursor: pointer;
          }
        }
      }
    }
  }
}

.count {
  padding: 2px 8px;
  margin-left: 8px;
  font-size: 12px;
  line-height: 12px;
  border-radius: 8px;

  &.on {
    color: #3A84FF;
    background: #E1ECFF;
  }

  &.off {
    color: #4D4F56;

    // background: #C4C6CC;
  }
}

.mcp-tab {

  :deep(.bk-tab-content) {
    padding: 0;
    background-color: #ffffff;
  }

  .panel-content {
    background: #FFF;
  }
}

</style>
