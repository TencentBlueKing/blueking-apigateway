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
  <CustomTop :server="server" />
  <div class="page-wrapper">
    <section class="server-info">
      <div class="flex items-center justify-between header">
        <div class="flex items-center max-w-[calc(100%-300px)] gap-8px">
          <div class="flex items-center min-w-0 title">
            <BkOverflowTitle
              type="tips"
              class="truncate"
            >
              {{ server?.title }}
            </BkOverflowTitle>
            <BkOverflowTitle
              type="tips"
              class="truncate ml-4px text-14px"
            >
              ({{ server?.name }})
            </BkOverflowTitle>
          </div>
          <div class="flex items-center gap-8px flex-shrink-0">
            <BkTag
              class="h-18px"
              :class="statusTag.color"
            >
              <AgIcon :name="statusTag.icon" />
              {{ statusTag.text }}
            </BkTag>
            <BkTag
              v-if="server.stage?.name"
              theme="info"
              class="h-18px"
            >
              {{ server.stage.name }}
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
        <div class="operate">
          <BkButton
            theme="primary"
            @click="handleEdit"
          >
            {{ t('编辑') }}
          </BkButton>
          <BkButton @click="handleSuspendToggle">
            {{ t(Boolean(server.status) ? '停用' : '启用') }}
          </BkButton>
          <BkDropdown
            v-model:is-show="showDropdown"
            trigger="hover"
          >
            <BkButton
              class="more-cls"
              @click="showDropdown = true"
            >
              <AgIcon name="gengduo" />
            </BkButton>
            <template #content>
              <BkDropdownMenu ext-cls="stage-more-actions">
                <BkDropdownItem
                  v-bk-tooltips="{
                    content: t('请先停用再删除'),
                    disabled: !server.status,
                  }"
                  :class="[{'cursor-not-allowed!': Boolean(server.status) }]"
                  @click.stop="handleDelete"
                >
                  <BkButton
                    :disabled="Boolean(server.status)"
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
      <div class="info-content">
        <div class="info-column">
          <div class="info-item">
            <div class="label">
              {{ t('访问地址') }}:
            </div>
            <div class="w-full flex items-baseline value">
              <BkOverflowTitle
                type="tips"
                :popover-options="{
                  extCls: 'break-all'
                }"
                class="max-w-full truncate"
              >
                {{ server?.url || '--' }}
              </BkOverflowTitle>
              <AgIcon
                name="copy"
                size="16"
                class="shrink-0 ml-8px icon"
                @click.self.stop="copy(server.url)"
              />
            </div>
          </div>
          <div class="info-item">
            <div class="label">
              {{ t('描述') }}:
            </div>
            <div class="value">
              <BkOverflowTitle
                type="tips"
                :popover-options="{
                  extCls: 'break-all'
                }"
                class="truncate"
              >
                {{ server?.description || '--' }}
              </BkOverflowTitle>
            </div>
          </div>
        </div>
        <div class="info-column">
          <div class="info-item">
            <div class="label">
              {{ t('是否公开') }}:
            </div>
            <div class="flex flex-wrap gap-8px lh-22px value">
              <BkTag :theme="server?.is_public ? 'success' : 'warning'">
                {{ t(server?.is_public ? '公开' : '不公开') }}
              </BkTag>
            </div>
          </div>
          <div class="info-item">
            <div class="label">
              {{ t('分类') }}:
            </div>
            <div class="flex flex-wrap gap-8px lh-22px value">
              <template v-if="server?.categories?.length">
                <BkTag
                  v-for="category of server?.categories"
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
            <div class="lh-22px value">
              <div
                v-if="server?.labels?.length"
                class="flex flex-wrap gap-8px w-full"
              >
                <template
                  v-for="label of server.labels"
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
    </section>
    <section
      :class="[
        `tab-wrapper mcp-detail-${active}`,
        {'flex items-baseline': isShowConfig }
      ]"
    >
      <BkResizeLayout
        placement="right"
        :border="false"
        :initial-divide="isShowConfig ? divideRatio : 0"
        :class="isShowConfig ? 'w-full gap-16px' : ''"
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
            class="mcp-tab"
            type="card-tab"
          >
            <BkTabPanel
              v-for="item in filteredPanels"
              :key="item.name"
              :name="item.name"
              render-directive="if"
            >
              <template #label>
                <div class="flex items-center">
                  {{ item.label }}
                  <div
                    v-if="item.count > 0"
                    class="count"
                    :class="[active === item.name ? 'on' : 'off']"
                  >
                    {{ item.count }}
                  </div>
                </div>
              </template>
              <div class="panel-content">
                <ServerTools
                  v-if="item.name === 'tools'"
                  :server="server"
                  @update-count="(count: number) => updateCount(count, item.name)"
                />
                <ServerPrompts
                  v-if="item.name === 'prompts'"
                  :server="server"
                  @update-count="(count: number) => updateCount(count, item.name)"
                />
                <AuthApplications
                  v-if="item.name === 'auth'"
                  :mcp-server-id="serverId"
                />
                <Guideline
                  v-if="item.name === 'guide'"
                  v-model:is-exist-custom-guide="isExistCustomGuide"
                  show-usage-guide
                  :markdown-str="markdownStr"
                  :config-list="mcpConfigList"
                  :gateway-id="gatewayId"
                  @guide-change="handleGuideChange"
                />
              </div>
            </BkTabPanel>
          </BkTab>
        </template>
      </BkResizeLayout>
    </section>
  </div>
  <CreateSlider
    ref="createSliderRef"
    :server-id="editingServerId"
    @updated="handleUpdated"
  />
</template>

<script lang="ts" setup>
import { Message } from 'bkui-vue';
import { copy } from '@/utils';
import {
  type IMCPAIConfig,
  deleteServer,
  getCustomServerGuideDoc,
  getMcpAIConfigList,
  getServer,
  getServerGuideDoc,
  patchServerStatus,
} from '@/services/source/mcp-server';
import { useMcpConfigDivideRatio, usePopInfoBox } from '@/hooks';
import { useFeatureFlag, useGateway } from '@/stores';
import { MCP_TAB_LIST } from '@/constants';
import router from '@/router';
import CreateSlider from '@/views/mcp-server/components/CreateSlider.vue';
import AuthApplications from '@/views/mcp-server/components/AuthApplications.vue';
import CustomTop from '@/views/mcp-server/components/CustomTop.vue';
import Guideline from '@/views/mcp-market/components/GuideLine.vue';
import ServerTools from '@/views/mcp-server/components/ServerTools.vue';
import ServerPrompts from '@/views/mcp-server/components/ServerPrompts.vue';
import AgMcpAgentConfig from '@/components/ag-mcp-agent-config/Index.vue';

type IPanelType = {
  name: string
  label: string
  count: number
  show: boolean
};

interface IProps { gatewayId?: number }

const { gatewayId = 0 } = defineProps<IProps>();

const { t } = useI18n();
const route = useRoute();
const gatewayStore = useGateway();
const featureFlagStore = useFeatureFlag();
const { divideRatio } = useMcpConfigDivideRatio();

const createSliderRef = ref<InstanceType<typeof CreateSlider>>();
const serverId = ref(0);
const server = ref<any>({
  id: 0,
  name: '',
  description: '',
  is_public: false,
  oauth2_public_client_enabled: false,
  labels: [],
  resource_names: [],
  tools_count: 0,
  url: '',
  status: 1,
  stage: {
    id: 0,
    name: '',
  },
});
const showDropdown = ref(false);
const isExistCustomGuide = ref(false);
const markdownStr = ref('');
const active = ref('tools');
const panels = ref<IPanelType[]>(MCP_TAB_LIST);
const mcpConfigList = ref<IMCPAIConfig[]>([]);
const editingServerId = ref<number>();

const isShowConfig = computed(() => ['guide'].includes(active.value) && mcpConfigList.value.length > 0);
const isEnablePrompt = computed(() => featureFlagStore?.flags?.ENABLE_MCP_SERVER_PROMPT);
const isEnabledOAuth = computed(() =>
  featureFlagStore?.flags?.ENABLE_MCP_SERVER_OAUTH2_PUBLIC_CLIENT && server.value?.oauth2_public_client_enabled,
);
const isEnablePersonalClient = computed(() =>
  featureFlagStore?.flags?.ENABLE_MCP_SERVER_OAUTH2_PERSONAL_CLIENT && server.value?.oauth2_personal_client_enabled,
);
const statusTag = computed(() => {
  const enabled = Boolean(server.value?.status);
  return {
    text: enabled ? t('启用中') : t('已停用'),
    icon: enabled ? 'yiqiyong' : 'minus-circle',
    color: enabled ? 'color-#14a568 bg-#e4faf0 hover-bg-#e4faf0' : 'color-#63656e bg-#f0f1f5',
  };
});
const filteredPanels = computed(() => {
  if (!isEnablePrompt.value) {
    panels.value = panels.value.filter((item: any) => !['prompts'].includes(item.name));
  }
  return panels.value.filter((item: IPanelType) => item.show);
});

const fetchServer = async () => {
  server.value = await getServer(gatewayId, serverId.value);
};

const fetchGuide = async () => {
  const { content } = await getServerGuideDoc(gatewayId, serverId.value);
  markdownStr.value = content;
};

const fetchCustomGuide = async () => {
  const res = await getCustomServerGuideDoc(gatewayId, serverId.value);
  markdownStr.value = res?.content ?? '';
  isExistCustomGuide.value = markdownStr.value.length > 0;
};

const fetchMcpAIConfigList = async () => {
  const res = await getMcpAIConfigList(gatewayId, serverId.value);
  mcpConfigList.value = res?.configs ?? [];
};

const handleUpdated = async () => {
  await Promise.all([
    fetchServer(),
    fetchGuide(),
    fetchCustomGuide(),
  ]);
  updateCount();
};

const handleGuideChange = (tabName: string) => {
  const tabMap: Record<string, () => Promise<void>> = {
    default: () => {
      return fetchGuide();
    },
    custom: () => {
      return fetchCustomGuide();
    },
  };
  return tabMap[tabName as keyof typeof tabMap]?.();
};

watch(
  () => [route.params.id, route.params.serverId],
  ([id, mcpId]) => {
    if (id && mcpId) {
      serverId.value = Number(mcpId);
      if (gatewayId === Number(id)) {
        Promise.allSettled([handleUpdated(), fetchMcpAIConfigList()]);
      }
    }
  },
  { immediate: true },
);

watch(() => gatewayStore.currentGateway, (newGateway, oldGateway) => {
  // 切换了网关，需要返回列表页
  if (!oldGateway || (newGateway?.id === oldGateway.id)) {
    return;
  }
  router.replace({
    name: 'MCPServer',
    params: { id: newGateway!.id },
  });
});

watch(() => active.value, (tab: string) => {
  if (['guide'].includes(tab)) {
    handleGuideChange('default');
  }
});

const handleEdit = () => {
  editingServerId.value = server.value.id;
  createSliderRef.value?.show();
};

const handleSuspendToggle = async () => {
  if (server.value.status === 0) {
    await patchServerStatus(gatewayId, server.value.id, { status: 1 });
    Message({
      theme: 'success',
      message: t('已启用'),
    });
    await fetchServer();
    return;
  }
  usePopInfoBox({
    isShow: true,
    type: 'warning',
    title: t('确认停用 {n}？', { n: server.value.name }),
    subTitle: t('停用后，{n} 下所有工具不可访问，请确认！', { n: server.value.name }),
    confirmText: t('确认停用'),
    cancelText: t('取消'),
    onConfirm: async () => {
      await patchServerStatus(gatewayId, server.value.id, { status: 0 });
      Message({
        theme: 'success',
        message: t('已停用'),
      });
      await fetchServer();
    },
  });
};

const handleDelete = () => {
  if (server.value.status) return;

  usePopInfoBox({
    isShow: true,
    type: 'warning',
    title: t('确定删除 {n}？', { n: server.value.name }),
    subTitle: t('删除后，{n} 不可恢复，请谨慎操作！', { n: server.value.name }),
    confirmText: t('删除'),
    cancelText: t('取消'),
    confirmButtonTheme: 'danger',
    onConfirm: async () => {
      await deleteServer(gatewayId, server.value.id);
      Message({
        theme: 'success',
        message: t('删除成功'),
      });
      router.replace({ name: 'MCPServer' });
    },
  });
};

/**
 * 更新面板计数并控制prompts面板显隐
 * @param count - 目标面板的自定义计数
 * @param panelName - 目标面板名称
 */
const updateCount = (count?: number, panelName?: string) => {
  const { tools_count, prompts } = server.value ?? {} as any;
  const panelCountMap: Record<string, () => number> = {
    tools: () => tools_count ?? 0,
    prompts: () => (prompts as any[])?.length ?? 0,
    ...(panelName ? { [panelName]: () => count ?? 0 } : {}),
  };
  panels.value.forEach((item: IPanelType) => {
    const getCount = panelCountMap[item.name];
    if (getCount) {
      item.count = getCount?.();
      item.show = getCount?.() < 1 && ['prompts'].includes(item.name) ? false : true;
    }
  });
};
</script>

<style lang="scss" scoped>
.page-wrapper {
  height: 100%;
  padding: 20px;

  .tab-wrapper {
    box-shadow: 0 2px 4px 0 #1919290d;
    border-radius: 0 0 2px 2px;

    :deep(.bk-tab-header) {

      .bk-tab-header-item:last-child {

        &::after {
          display: none;
        }
      }
    }

    :deep(.bk-tab-content) {
      padding: 0;
      background-color: #fff;
    }

    .bk-resize-layout-right {

      :deep(>.bk-resize-layout-aside) {
        display: none;
      }
    }

    &.mcp-detail-guide {

      .bk-resize-layout-right {

        :deep(>.bk-resize-layout-aside) {
          display: block;

          .bk-resize-trigger {
            background-color: #fff;
          }
        }
      }
    }
  }
}

.server-info {
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

      .label {
        padding: 9px 0;
        margin-right: 8px;
        color: #4d4f56;
        text-align: right;
      }

      .value {
        padding: 9px 0;
        line-height: 22px;
        min-width: 0;
        color: #313238;

        .icon {
          color: #3a84ff;
          cursor: pointer;
        }
      }
    }
  }

  .operate {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-shrink: 0;
    margin-left: 40px;
  }

  :deep(.external-oauth-tag) {
    position: relative;
    width: 18px;
    height: 18px;
    font-size: 0;
    line-height: 1;
    flex-shrink: 0;
    border-radius: 2px;
    box-sizing: border-box;

    .apigateway-icon {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
    }
  }
}

.stage-more-actions {

  :deep(.disabled) {
    color: #c4c6cc !important;
    cursor: not-allowed;
    background-color: #fff !important;
    border-color: #dcdee5 !important;
  }
}

.more-cls {
  padding: 5px 7px;

  i {
    font-size: 16px;
    transform: rotate(90deg);
  }
}

.stress {
  color: red;
}

.count {
  padding: 2px 8px;
  margin-left: 8px;
  font-size: 12px;
  line-height: 12px;
  border-radius: 8px;

  &.on {
    color: #3a84ff;
    background-color: #e1ecff;
  }

  &.off {
    color: #4d4f56;
  }
}
</style>
