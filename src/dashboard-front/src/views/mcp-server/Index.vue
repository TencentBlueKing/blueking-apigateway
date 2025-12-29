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
  <div class="page-wrapper">
    <BkLoading
      :loading="isLoading"
      :z-index="99"
    >
      <div class="server-list">
        <ServerItemCard
          v-for="server in serverList"
          :key="server.id"
          :server="server"
          @delete="handleDelete"
          @edit="handleEdit"
          @enable="handleEnable"
          @suspend="handleSuspend"
          @click="() => handleCardClick(server.id)"
        />
        <!-- 添加按钮卡片 -->
        <div
          class="flex items-center justify-center add-server-card"
          @click="handleAddServerClick"
        >
          <AgIcon
            name="add-small"
            size="40"
          />
        </div>
      </div>
    </BkLoading>
    <CreateSlider
      ref="createSliderRef"
      :server-id="editingServerId"
      @updated="handleServerUpdated"
    />
  </div>
</template>

<script lang="ts" setup>
import { Message } from 'bkui-vue';
import {
  deleteServer,
  getServers,
  patchServerStatus,
} from '@/services/source/mcp-server';
import { usePopInfoBox } from '@/hooks';
import CreateSlider from './components/CreateSlider.vue';
import ServerItemCard from '@/components/ag-mcp-card/Index.vue';

type MCPServerType = Awaited<ReturnType<typeof getServers>>['results'][number];

interface IProps { gatewayId?: number }

const { gatewayId = 0 } = defineProps<IProps>();

const { t } = useI18n();
const router = useRouter();

const createSliderRef = ref<InstanceType<typeof CreateSlider>>();
const serverList = ref<MCPServerType[]>([]);
const editingServerId = ref();
const isLoading = ref(true);

const fetchServerList = async () => {
  try {
    const response = await getServers(gatewayId);
    serverList.value = response?.results || [];
  }
  finally {
    isLoading.value = false;
  }
};

const handleAddServerClick = () => {
  editingServerId.value = undefined;
  createSliderRef.value?.show();
};

const handleEdit = (id: number) => {
  editingServerId.value = id;
  createSliderRef.value?.show();
};

const handleSuspend = async (id: number) => {
  const server = serverList.value.find(server => server.id === id);
  usePopInfoBox({
    isShow: true,
    type: 'warning',
    title: t('确认停用 {n}？', { n: server.name }),
    subTitle: t('停用后，{n} 下所有工具不可访问，请确认！', { n: server.name }),
    confirmText: t('确认停用'),
    cancelText: t('取消'),
    onConfirm: async () => {
      await patchServerStatus(gatewayId, id, { status: 0 });
      Message({
        theme: 'success',
        message: t('已停用'),
      });
      await fetchServerList();
    },
  });
};

const handleEnable = async (id: number) => {
  await patchServerStatus(gatewayId, id, { status: 1 });
  await fetchServerList();
  Message({
    theme: 'success',
    message: t('已启用'),
  });
};

const handleDelete = async (id: number) => {
  const server = serverList.value.find(server => server.id === id);
  if (server) {
    usePopInfoBox({
      isShow: true,
      type: 'warning',
      title: t('确定删除 {n}？', { n: server.name }),
      subTitle: t('删除后，{n} 不可恢复，请谨慎操作！', { n: server.name }),
      confirmText: t('删除'),
      cancelText: t('取消'),
      confirmButtonTheme: 'danger',
      onConfirm: async () => {
        await deleteServer(gatewayId, id);
        Message({
          theme: 'success',
          message: t('已删除'),
        });
        await fetchServerList();
      },
    });
  }
};

const handleServerUpdated = () => {
  fetchServerList();
};

const handleCardClick = (id: number) => {
  router.replace({
    name: 'MCPServerDetail',
    params: { serverId: id },
  });
};

onMounted(() => {
  fetchServerList();
});
</script>

<style lang="scss" scoped>
.page-wrapper {
  padding: 20px 24px;

  .server-list {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;
    box-sizing: border-box;

    .add-server-card {
      min-height: 228px;
      color: #979ba5;
      border-radius: 2px;
      background-color: #ffffff;
      box-shadow: 0 2px 4px 0 #1919290d;
      cursor: pointer;

      &:hover {
        color: #3a84ff;
      }
    }

    :deep(.ag-mcp-card-wrapper) {
      padding: 20px 40px;

      .mcp-card-title {
        max-width: calc(100% - 80px);
      }

      .mcp-footer-content {
        right: 40px;
        left: 40px;
      }
    }
  }
}

@media (min-width: 768px) {
  .add-server-card {
    width: calc(50% - 12px);
  }
}

@media (min-width: 1200px) {
  .add-server-card {
    width: calc(33.333% - 16px);
  }
}

@media (min-width: 768px) {
  :deep(.ag-mcp-card-wrapper) {
    width: calc(50% - 12px);
  }
}

@media (min-width: 1200px) {
  :deep(.ag-mcp-card-wrapper) {
    width: calc(33.333% - 16px);
  }
}
</style>
