<template>
  <div class="page-wrapper">
    <div class="server-list">
      <ServerItemCard
        v-for="server in serverList"
        :key="server.id"
        :server="server"
        @delete="handleDelete"
        @edit="handleEdit"
        @enable="handleEnable"
        @suspend="handleSuspend"
      />
      <!-- 添加按钮卡片 -->
      <div class="add-server-card" @click="handleAddServerClick">
        <AgIcon name="add-small" size="40" />
      </div>
    </div>
    <CreateSlider v-model="isCreateSliderShow" :server-id="editingServerId" />
  </div>
</template>

<script lang="ts" setup>
import {
  onMounted,
  ref,
} from 'vue';
import ServerItemCard from './components/ServerItemCard.vue';
import AgIcon from '@/components/ag-icon.vue';
import CreateSlider from './components/CreateSlider.vue';
import {
  deleteServer,
  getServers,
  patchServerStatus,
} from '@/http/mcp-server';
import { useCommon } from '@/store';
import { Message } from 'bkui-vue';
import { useI18n } from 'vue-i18n';

type MCPServerType = Awaited<ReturnType<typeof getServers>>['results'][number];

const { t } = useI18n();
const common = useCommon();

const serverList = ref<MCPServerType[]>([
  // {
  //   id: 1,
  //   name: 'mcp server',
  //   description: 'mcp server description',
  //   is_public: true,
  //   labels: [
  //     'label1',
  //     'label2',
  //   ],
  //   resource_names: [
  //     'resource1',
  //     'resource2',
  //   ],
  //   tools_count: 10,
  //   url: 'http://bkapi.woa.com/api/bk-iam//sse/',
  //   status: 1,
  //   stage: 'stage1',
  // },
  // {
  //   id: 2,
  //   name: 'mcp server',
  //   description: 'mcp server description',
  //   is_public: true,
  //   labels: [
  //     'label1',
  //     'label2',
  //   ],
  //   resource_names: [
  //     'resource1',
  //     'resource2',
  //   ],
  //   tools_count: 10,
  //   url: 'http://bkapi.woa.com/api/bk-iam//sse/',
  //   status: 0,
  //   stage: 'stage1',
  // },
]);
const isCreateSliderShow = ref(false);
const editingServerId = ref<number>();

const fetchServerList = async () => {
  const response = await getServers(common.apigwId);
  serverList.value = response?.results || [];
};

const handleAddServerClick = () => {
  editingServerId.value = undefined;
  isCreateSliderShow.value = true;
};

const handleEdit = (id: number) => {
  editingServerId.value = id;
  isCreateSliderShow.value = true;
};

const handleSuspend = async (id: number) => {
  await patchServerStatus(common.apigwId, id, { status: 0 });
  await fetchServerList();
  Message({
    theme: 'success',
    message: t('已停用'),
  });
};

const handleEnable = async (id: number) => {
  await patchServerStatus(common.apigwId, id, { status: 1 });
  await fetchServerList();
  Message({
    theme: 'success',
    message: t('已启用'),
  });
};

const handleDelete = async (id: number) => {
  await deleteServer(common.apigwId, id);
  await fetchServerList();
  Message({
    theme: 'success',
    message: t('已删除'),
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

    .add-server-card {
      width: 533px;
      height: 228px;
      background: #fff;
      box-shadow: 0 2px 4px 0 #1919290d;
      border-radius: 2px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #979ba5;

      &:hover {
        color: #3a84ff;
      }
    }
  }
}
</style>
