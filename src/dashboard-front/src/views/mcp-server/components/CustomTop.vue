<template>
  <div class="resource-top-bar" :style="stage.getNotUpdatedStages?.length ? 'top: 42px' : 'top: -1px'">
    <div class="top-title-wrapper">
      <div class="title">
        <i
          class="icon apigateway-icon icon-ag-return-small"
          @click="handleBack"
        />
        {{ server?.name }}
      </div>
      <div class="history" @click="handleClick(server?.id)">
        <span>{{ t('权限审批') }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useStage, useCommon } from '@/store';
import {
  getServer,
} from '@/http/mcp-server';

type MCPServerType = Awaited<ReturnType<typeof getServer>>;

interface IProps {
  server: MCPServerType,
}

const { server } = defineProps<IProps>();

const router = useRouter();
const common = useCommon();
const stage = useStage();
const { t } = useI18n();

const handleClick = (id: number) => {
  router.push({
    name: 'mcpPermission',
    params: {
      id: common.apigwId,
    },
    query: {
      serverId: id,
    },
  });
};

const handleBack = () => {
  router.push({
    name: 'mcpServer',
    params: {
      id: common.apigwId,
    },
  });
};

</script>

<style lang="scss" scoped>
.resource-top-bar {
  position: absolute;
  width: 100%;
  height: 52px;
  box-sizing: border-box;
  padding: 0 24px;
  background: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: space-between;
  //min-width: 1280px;
  .top-title-wrapper {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    .title {
      font-size: 16px;
      color: #313238;
      display: flex;
      align-items: center;
      .icon-ag-return-small {
        font-size: 32px;
        color: #3a84ff;
        cursor: pointer;
      }
    }
    .history {
      color: #3A84FF;
      cursor: pointer;
      span {
        font-size: 12px;
      }
    }
  }
}
</style>
