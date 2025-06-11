<template>
  <CustomTop :server="server" />
  <div class="page-wrapper">
    <section class="server-info">
      <div :class="{ 'no-release': server.status === 0 }" class="server-name">
        <div v-if="server.status === 1" class="status-tag">
          <BkTag theme="success">{{ t('启用中') }}</BkTag>
        </div>
        <div v-else class="status-tag">
          <BkTag theme="warning">{{ t('未启用') }}</BkTag>
        </div>
        <span class="name">
          {{ server.name }}
        </span>
      </div>
      <div class="info">
        <div class="column">
          <div class="apigw-form-item">
            <div class="label">{{ `${t('访问地址')}：` }}</div>
            <div class="value url">
              <p v-bk-tooltips="server.url" class="link">
                {{ server.url || '--' }}
              </p>
              <i
                class="apigateway-icon icon-ag-copy-info"
                @click.self.stop="copy(server.url)"
              ></i>
            </div>
          </div>
          <div class="apigw-form-item">
            <div class="label">{{ `${t('环境')}：` }}</div>
            <div class="value">
              {{ server.stage?.name || '--' }}
            </div>
          </div>
          <div class="apigw-form-item">
            <div class="label">{{ `${t('描述')}：` }}</div>
            <div class="value">
              {{ server.description || '--' }}
            </div>
          </div>
        </div>
      </div>
      <div class="operate">
        <div class="line"></div>
        <bk-button
          class="mr10"
          theme="primary"
          @click="handleEdit"
        >
          {{ t('编辑') }}
        </bk-button>
        <bk-button class="mr10" @click="handleSuspendToggle">
          {{ server.status === 1 ? t('停用') : t('启用') }}
        </bk-button>
        <bk-dropdown v-model:is-show="showDropdown" trigger="click">
          <bk-button class="more-cls" @click="showDropdown = true">
            <i class="apigateway-icon icon-ag-gengduo" />
          </bk-button>
          <template #content>
            <bk-dropdown-menu ext-cls="stage-more-actions">
              <bk-dropdown-item>
                <BkButton
                  v-bk-tooltips="{
                    content: t('请先停用再删除'),
                    disabled: server.status === 0,
                  }"
                  :disabled="server.status === 1"
                  text
                  @click="handleDelete"
                >
                  {{ t('删除') }}
                </BkButton>
              </bk-dropdown-item>
            </bk-dropdown-menu>
          </template>
        </bk-dropdown>
      </div>
    </section>
    <section class="tab-wrapper">
      <bk-tab
        v-model:active="active"
        class="mcp-tab"
        type="card-tab"
      >
        <bk-tab-panel
          v-for="item in panels"
          :key="item.name"
          :name="item.name"
          :num="item.count"
          num-display-type="elliptic"
        >
          <template #label>
            <div class="flex-row align-items-center">
              {{ item.label }}
              <div v-if="item.count > 0" :class="['count', active === item.name ? 'on' : 'off']">
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
            <AuthApplications
              :mcp-server-id="serverId"
              v-if="item.name === 'auth'" />
          </div>
        </bk-tab-panel>
      </bk-tab>
    </section>
  </div>
  <CreateSlider v-model="isCreateSliderShow" :server-id="editingServerId" @updated="handleUpdated" />
</template>

<script lang="ts" setup>
import { copy } from '@/common/util';
import { useI18n } from 'vue-i18n';
import { useCommon } from '@/store';
import {
  deleteServer,
  getServer,
  patchServerStatus,
} from '@/http/mcp-server';
import {
  ref,
  watch,
} from 'vue';
import ServerTools from '@/views/mcp-server/components/ServerTools.vue';
import { useRoute } from 'vue-router';
import {
  InfoBox,
  Message,
} from 'bkui-vue';
import router from '@/router';
import CreateSlider from '@/views/mcp-server/components/CreateSlider.vue';
import AuthApplications from '@/views/mcp-server/components/AuthApplications.vue';
import CustomTop from '@/views/mcp-server/components/CustomTop.vue';

type MCPServerType = Awaited<ReturnType<typeof getServer>>;

const { t } = useI18n();
const common = useCommon();
const route = useRoute();

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

const active = ref('tools');
const panels = ref([
  {
    name: 'tools',
    label: t('工具'),
    count: 0,
  },
  {
    name: 'auth',
    label: t('已授权应用'),
    count: 0,
  },
  {
    name: 'guide',
    label: t('使用指引'),
    count: 0,
  },
]);
const isCreateSliderShow = ref(false);
const editingServerId = ref<number>();

const fetchServer = async () => {
  server.value = await getServer(common.apigwId, serverId.value);
};

watch(() => route.params, () => {
  const { serverId: id } = route.params;
  if (id) {
    serverId.value = Number(id);
    fetchServer();
  }
}, { immediate: true, deep: true });

const handleEdit = () => {
  editingServerId.value = server.value.id;
  isCreateSliderShow.value = true;
};

const handleSuspendToggle = async () => {
  if (server.value.status === 0) {
    await patchServerStatus(common.apigwId, server.value.id, { status: 1 });
    Message({
      theme: 'success',
      message: t('已启用'),
    });
    await fetchServer();
    return;
  }
  InfoBox({
    title: t('确定停用 {n}？', { n: server.value.name }),
    infoType: 'warning',
    subTitle: t('停用后，{n} 下所有工具不可访问，请确认！', { n: server.value.name }),
    onConfirm: async () => {
      await patchServerStatus(common.apigwId, server.value.id, { status: 0 });
      Message({
        theme: 'success',
        message: t('已停用'),
      });
      await fetchServer();
    },
  });
};

const handleUpdated = () => {
  router.replace({ name: route.name, params: { ...route.params } });
};

const handleDelete = async () => {
  InfoBox({
    title: t('确定删除 {n}？', { n: server.value.name }),
    infoType: 'danger',
    subTitle: t('删除后，{n} 不可恢复，请谨慎操作！', { n: server.value.name }),
    onConfirm: async () => {
      await deleteServer(common.apigwId, server.value.id);
      Message({
        theme: 'success',
        message: t('已删除'),
      });
      router.replace({ name: 'mcpServer' });
    },
  });
};

const updateCount = (count: number, panelName: string) => {
  const panel = panels.value.find(panel => panel.name === panelName);
  if (panel) {
    panel.count = count;
  }
};
</script>

<style lang="scss" scoped>
.page-wrapper {
  padding: 20px;
  height: 100%;

  .tab-wrapper {
    :deep(.bk-tab-content) {
      padding: 0;
    }
  }
}

.server-info {
  display: flex;
  min-height: 128px;
  padding: 24px;
  background: #fff;
  box-shadow: 0 2px 4px 0 #1919290d;
  margin-bottom: 16px;

  .server-name {
    padding-inline: 24px;
    height: 80px;
    margin-right: 35px;
    background-color: #f0f5ff;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;

    .status-tag {
      position: absolute;
      left: 0;
      top: 0;
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
      border: 1px solid #c4c6cc;
      background: #f0f1f5;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      margin-right: 2px;
    }

    .no-release-label {
      position: absolute;
      background-color: #fafbfd;
      top: 3px;
      left: 3px;
      border-radius: 2px;
      color: #63656e;
      font-size: 12px;
      padding: 2px 6px;
    }

    .no-release-icon {
      color: #979ba5;
      background-color: #fff;
      border-radius: 4px;
      font-size: 14px;
      position: absolute;
      right: 3px;
      top: 3px;
      padding: 4px;
      cursor: pointer;
    }
  }

  .name {
    padding: 0 3px;
    font-weight: 700;
    font-size: 16px;
    color: #3a84ff;
    display: inline-block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .info {
    display: flex;
    width: 300px;

    .column {
      transform: translateY(-8px);
    }

    .apigw-form-item {
      font-size: 12px;
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      line-height: 32px;
      color: #4d4f56;

      .value {
        flex: 1;
        color: #313238;

        &.url {
          max-width: 230px;
          display: flex;
          align-items: center;

          .link {
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
          }

          i {
            cursor: pointer;
            color: #3a84ff;
            margin-left: 3px;
            font-size: 12px;
            padding: 3px;
          }
        }
      }

      .unrelease {
        display: inline-block;
        font-size: 10px;
        // color: #fe9c00;
        // background: #fff1db;
        border-radius: 2px;
        padding: 2px 5px;
        line-height: 1;
      }
    }
  }

  .operate {
    display: flex;
    margin-left: 40px;

    .line {
      height: 32px;
      width: 1px;
      background: #dcdee5;
      margin-right: 20px;
    }
  }
}

.stage-more-actions {
  :deep(.disabled) {
    color: #c4c6cc !important;
    background-color: #fff !important;
    border-color: #dcdee5 !important;
    cursor: not-allowed;
  }
}

.more-cls {
  padding: 5px 7px;

  i {
    transform: rotate(90deg);
    font-size: 16px;
  }
}

.stress {
  color: red;
}

.count {
  padding: 2px 8px;
  font-size: 12px;
  line-height: 12px;
  border-radius: 8px;
  margin-left: 8px;

  &.on {
    color: #3a84ff;
    background: #e1ecff;
  }

  &.off {
    color: #4d4f56;
  }
}
</style>
