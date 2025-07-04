<template>
  <div>
    <div class="top-bar flex-row align-items-center">
      <ag-icon name="return-small" size="32" class="icon" @click="goBack" />
      <span class="top-bar-title">
        {{ mcpDetails?.name }}
      </span>
    </div>

    <div class="main">
      <div class="base-info">
        <div class="header">
          <div class="flex-row align-items-center">
            <div class="title">
              {{ mcpDetails?.name }}
            </div>
            <bk-tag theme="success" class="mr8" v-if="mcpDetails?.is_public">{{ t('官方') }}</bk-tag>
            <bk-tag theme="info">{{ mcpDetails?.stage?.name }}</bk-tag>
          </div>

          <div class="permission-guide">
            <bk-link theme="primary" :href="GLOBAL_CONFIG.DOC.MCP_SERVER_PERMISSION_APPLY" target="_blank">
              <ag-icon name="jump" size="16" class="icon" />
              {{ t('权限申请指引') }}
            </bk-link>
          </div>
        </div>
        <div class="content">
          <div class="info-item">
            <div class="label">{{ t('访问地址') }}：</div>
            <div class="value">
              {{ mcpDetails?.url }}
              <ag-icon name="copy" size="16" class="icon" @click="handleCopy(mcpDetails?.url)" />
            </div>
          </div>
          <div class="info-item">
            <div class="label">{{ t('描述') }}：</div>
            <div class="value">{{ mcpDetails?.description }}</div>
          </div>
          <div class="info-item">
            <div class="label">{{ t('标签') }}：</div>
            <div class="value">
              <bk-tag class="mr8" v-for="label in mcpDetails?.labels" :key="label">{{ label }}</bk-tag>
            </div>
          </div>
          <div class="info-item">
            <div class="label">{{ t('负责人') }}：</div>
            <div class="value">{{ mcpDetails?.maintainers?.join(',') }}</div>
          </div>
        </div>
      </div>

      <bk-tab
        v-model:active="active"
        type="card-tab"
        class="mcp-tab"
      >
        <bk-tab-panel
          v-for="item in panels"
          :key="item.name"
          :name="item.name"
        >
          <template #label>
            <div class="flex-row align-items-center">
              {{ item.label }}
              <div :class="['count', active === item.name ? 'on' : 'off']" v-if="item.count > 0">
                {{ item.count }}
              </div>
            </div>
          </template>
          <div class="panel-content">
            <ServerTools
              v-show="active === 'tools'"
              :server="mcpDetails"
              page="market"
            />
            <Guideline v-show="active === 'guide'" :markdown-str="markdownStr" />
          </div>
        </bk-tab-panel>
      </bk-tab>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { copy } from '@/common/util';
import AgIcon from '@/components/ag-icon.vue';
import { useGetGlobalProperties } from '@/hooks';
import { getMcpServerDetails, IMarketplaceDetails } from '@/http/mcp-market';
import ServerTools from '@/views/mcp-server/components/ServerTools.vue';
import Guideline from './guideline.vue';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const globalProperties = useGetGlobalProperties();
const { GLOBAL_CONFIG } = globalProperties;

const active = ref('tools');
const panels = ref([
  { name: 'tools', label: t('工具'), count: 0 },
  { name: 'guide', label: t('使用指引'), count: 0 },
]);
const mcpDetails = ref<IMarketplaceDetails>();
const markdownStr = ref<string>('');

const mcpId = computed(() => {
  return route.params.id;
});

const handleCopy = (str: string) => {
  copy(str);
};

const goBack = () => {
  router.push({
    name: 'mcpMarket',
  });
};

const getDetails = async () => {
  const res = await getMcpServerDetails(mcpId.value as string);
  mcpDetails.value = res;
  panels.value[0].count = res.tools_count;
  markdownStr.value = res.guideline;
};

watch(
  () => mcpId.value,
  () => {
    getDetails();
  },
  {
    immediate: true,
  },
);

</script>

<style lang="scss" scoped>
.top-bar {
  height: 64px;
  background: #FFFFFF;
  box-shadow: 0 3px 4px 0 #0000000a;
  padding: 0 24px;
  .icon {
    color: #3A84FF;
    margin-right: 4px;
    cursor: pointer;
  }
  .top-bar-title {
    font-size: 16px;
    color: #313238;
  }
}

.main {
  width: 1280px;
  margin: 0 auto;
  height: calc(100vh - 116px);
  padding: 24px 0px 42px;
  box-sizing: border-box;
  background-color: #f5f7fa;
  .base-info {
    padding: 0 24px;
    margin-bottom: 16px;
    border-radius: 2px;
    background: #FFFFFF;
    box-shadow: 0 2px 4px 0 #1919290d;
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid #EAEBF0;
      height: 54px;
      .title {
        color: #313238;
        font-size: 20px;
        font-weight: Bold;
        line-height: 54px;
        margin-right: 16px;
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
  font-size: 12px;
  line-height: 12px;
  border-radius: 8px;
  margin-left: 8px;
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
  }
  .panel-content {
    background: #FFFFFF;
  }
}

</style>
