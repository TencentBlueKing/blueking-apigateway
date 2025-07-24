<template>
  <div
    class="resource-top-bar"
    :style="stage.getNotUpdatedStages?.length ? 'top: 42px' : 'top: -1px'"
  >
    <div class="top-title-wrapper">
      <div class="title">
        <AgIcon
          size="32"
          class="icon"
          name="return-small"
          @click="handleBack"
        />
        {{ server?.name }}
      </div>
      <div
        class="history"
        @click="() => handleClick(server?.id)"
      >
        <span>{{ t('权限审批') }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useGateway, useStage } from '@/stores';
import { getServer } from '@/services/source/mcp-server';

type MCPServerType = Awaited<ReturnType<typeof getServer>>;

interface IProps { server: MCPServerType }

const { server } = defineProps<IProps>();

const { t } = useI18n();
const router = useRouter();
const gatewayStore = useGateway();
const stage = useStage();

const handleClick = (id: number) => {
  router.push({
    name: 'MCPServerPermission',
    params: { id: gatewayStore.currentGateway!.id! },
    query: { serverId: id },
  });
};

const handleBack = () => {
  router.push({
    name: 'MCPServer',
    params: { id: gatewayStore.currentGateway!.id! },
  });
};

</script>

<style lang="scss" scoped>
.resource-top-bar {
  position: absolute;
  display: flex;
  width: 100%;
  height: 52px;
  padding: 0 24px;
  background: #FFF;
  box-sizing: border-box;
  align-items: center;
  justify-content: space-between;

  // min-width: 1280px;

  .top-title-wrapper {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;

    .title {
      display: flex;
      font-size: 16px;
      color: #313238;
      align-items: center;

      .icon {
        font-size: 32px;
        color: #3a84ff;
        cursor: pointer;
      }
    }

    .history {
      color: #3A84FF;
      cursor: pointer;

      span {
        font-size: 14px;
      }
    }
  }
}
</style>
