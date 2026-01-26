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
      <div
        :class="{ 'no-release': server.status === 0 }"
        class="server-name"
      >
        <div
          v-if="server.status === 1"
          class="status-tag"
        >
          <BkTag theme="success">
            {{ t('启用中') }}
          </BkTag>
        </div>
        <div
          v-else
          class="status-tag"
        >
          <BkTag theme="warning">
            {{ t('未启用') }}
          </BkTag>
        </div>
        <div class="mt-8px flex items-center flex-col">
          <BkOverflowTitle
            type="tips"
            class="text-16px truncate name"
          >
            {{ server?.title }}
          </BkOverflowTitle>
          <BkOverflowTitle
            type="tips"
            class="text-14px truncate name"
          >
            ({{ server?.name }})
          </BkOverflowTitle>
        </div>
      </div>
      <div class="info">
        <div class="column">
          <div class="apigw-form-item">
            <div class="label">
              {{ t('访问地址') }}:
            </div>
            <div class="value url">
              <p
                v-bk-tooltips="server.url"
                class="truncate"
              >
                {{ server.url || '--' }}
              </p>
              <i
                class="apigateway-icon icon-ag-copy-info"
                @click.self.stop="copy(server.url)"
              />
            </div>
          </div>
          <div class="apigw-form-item">
            <div class="label">
              {{ t('环境') }}:
            </div>
            <div class="value">
              {{ server.stage?.name || '--' }}
            </div>
          </div>
          <div class="apigw-form-item">
            <div class="label">
              {{ t('描述') }}:
            </div>
            <div
              class="value description max-w-256px!"
            >
              <p
                v-bk-tooltips="{
                  content: server?.description,
                  disabled: server?.description?.length < 1,
                  extCls: 'max-w-480px'
                }"
                class="truncate"
              >
                {{ server?.description || '--' }}
              </p>
            </div>
          </div>
          <div class="apigw-form-item">
            <div class="label">
              {{ t('分类') }}:
            </div>
            <div class="value lh-22px!">
              <template v-if="server?.categories?.length">
                <BkTag
                  v-for="category of server?.categories"
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
        </div>
      </div>
      <div class="operate">
        <div class="line" />
        <BkButton
          class="mr-10px"
          theme="primary"
          @click="handleEdit"
        >
          {{ t('编辑') }}
        </BkButton>
        <BkButton
          class="mr-10px"
          @click="handleSuspendToggle"
        >
          {{ t(server.status === 1 ? '停用' : '启用') }}
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
              <BkDropdownItem @click="handleDelete">
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
        :min="isShowConfig ? 416 : 0"
        :initial-divide="isShowConfig ? '416px' : 0"
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
                  @update-count="(count) => updateCount(count, item.name)"
                />
                <ServerPrompts
                  v-if="item.name === 'prompts'"
                  :server="server"
                  @update-count="(count) => updateCount(count, item.name)"
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
import { Message } from 'bkui-vue';
import { usePopInfoBox } from '@/hooks';
import { useFeatureFlag, useGateway } from '@/stores';
import { MCP_TAB_LIST } from '@/constants';
import router from '@/router';
import CreateSlider from '@/views/mcp-server/components/CreateSlider.vue';
import AuthApplications from '@/views/mcp-server/components/AuthApplications.vue';
import CustomTop from '@/views/mcp-server/components/CustomTop.vue';
import Guideline from '@/views/mcp-market/components/GuideLine.vue';
import ServerTools from '@/views/mcp-server/components/ServerTools.vue';
import ServerPrompts from '@/views/mcp-server/components/ServerPrompts.vue';
import ServerConfig from '@/views/mcp-server/components/ServerConfig.vue';

type MCPServerType = Awaited<ReturnType<typeof getServer>>;

interface IProps { gatewayId?: number }

const { gatewayId = 0 } = defineProps<IProps>();

const { t } = useI18n();
const route = useRoute();
const gatewayStore = useGateway();
const featureFlagStore = useFeatureFlag();

const createSliderRef = ref();
const serverId = ref(0);
const server = ref<MCPServerType>({
  id: 0,
  name: '',
  description: '',
  is_public: false,
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
const panels = ref(MCP_TAB_LIST);
const mcpConfigList = ref<IMCPAIConfig[]>([]);
const editingServerId = ref<number>();

const isShowConfig = computed(() => ['guide'].includes(active.value));
const isEnablePrompt = computed(() => featureFlagStore?.flags?.ENABLE_MCP_SERVER_PROMPT);
const filteredPanels = computed(() => {
  if (!isEnablePrompt.value) {
    panels.value = panels.value.filter(item => !['prompts'].includes(item.name));
  }
  return panels.value.filter(item => item.show);
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
  const tabMap = {
    default: () => {
      return fetchGuide();
    },
    custom: () => {
      return fetchCustomGuide();
    },
  };
  return tabMap[tabName]?.();
};

watch(() => route.params, async () => {
  const { serverId: id } = route.params;
  if (id) {
    serverId.value = Number(id);
    Promise.allSettled([handleUpdated(), fetchMcpAIConfigList()]);
  }
}, {
  immediate: true,
  deep: true,
});

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
    subTitle: t('停用后，{n} 下所有工具不可访问，请确认！', { n: server.name }),
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

const handleDelete = async () => {
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
  const { tools_count, prompts } = server.value ?? {};
  const panelCountMap = {
    tools: () => tools_count ?? 0,
    prompts: () => prompts?.length ?? 0,
    [panelName]: () => count ?? 0,
  };
  panels.value.forEach((item) => {
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

    :deep(.bk-tab-header) {
      .bk-tab-header-item:last-child {
        &::after {
          display: none;
        }
      }
    }

    :deep(.bk-tab-content) {
      padding: 0;
      background-color: #ffffff;
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
            background-color: #ffffff;
          }
        }
      }
    }
  }
}

.server-info {
  display: flex;
  align-items: center;
  padding: 24px;
  margin-bottom: 16px;
  background: #fff;
  box-shadow: 0 2px 4px 0 #1919290d;

  .server-name {
    position: relative;
    display: flex;
    min-height: 120px;
    margin-right: 16px;
    background-color: #f0f5ff;
    border-radius: 8px;
    padding-inline: 24px;
    align-items: center;
    justify-content: center;

    .status-tag {
      position: absolute;
      top: 0;
      left: 0;
      overflow: hidden;
      border-top-left-radius: 8px;
    }

    &.no-release {
      background-color: #f0f1f5;

      .name {
        color: #979ba5;
      }
    }

    .no-release-dot {
      width: 8px;
      height: 8px;
      margin-right: 2px;
      background: #f0f1f5;
      border: 1px solid #c4c6cc;
      border-radius: 50%;
    }

    .no-release-label {
      position: absolute;
      top: 3px;
      left: 3px;
      padding: 2px 6px;
      font-size: 12px;
      color: #63656e;
      background-color: #fafbfd;
      border-radius: 2px;
    }

    .no-release-icon {
      position: absolute;
      top: 3px;
      right: 3px;
      padding: 4px;
      font-size: 14px;
      color: #979ba5;
      cursor: pointer;
      background-color: #fff;
      border-radius: 4px;
    }
  }

  .name {
    padding: 0 3px;
    font-weight: 700;
    color: #3a84ff;
  }

  .info {
    display: flex;

    .apigw-form-item {
      display: flex;
      font-size: 12px;
      line-height: 32px;
      color: #4d4f56;
      align-items: baseline;
      flex-wrap: wrap;

      .value {
        flex: 1;
        color: #313238;
        margin-left: 8px;

        &.url,
        &.description {
          max-width: 230px;
          display: flex;
          align-items: baseline;

          i {
            padding: 3px;
            margin-left: 3px;
            font-size: 12px;
            color: #3a84ff;
            cursor: pointer;
          }
        }
      }

      .unrelease {
        display: inline-block;
        padding: 2px 5px;
        font-size: 10px;
        line-height: 1;
        border-radius: 2px;
      }
    }
  }

  .operate {
    display: flex;
    margin-left: 40px;

    .line {
      width: 1px;
      height: 32px;
      margin-right: 20px;
      background: #dcdee5;
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
    background: #e1ecff;
  }

  &.off {
    color: #4d4f56;
  }
}
</style>
