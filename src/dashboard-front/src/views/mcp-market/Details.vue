<template>
  <div>
    <div class="top-bar flex-row align-items-center">
      <AgIcon
        name="return-small"
        size="32"
        class="icon"
        @click="goBack"
      />
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
            <BkTag
              v-if="mcpDetails?.is_public"
              theme="success"
              class="mr8"
            >
              {{ t('官方') }}
            </BkTag>
            <BkTag theme="info">
              {{ mcpDetails?.stage?.name }}
            </BkTag>
          </div>

          <div class="permission-guide">
            <BkLink
              theme="primary"
              :href="envStore.doc.MCP_SERVER_PERMISSION_APPLY"
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
              {{ t('访问地址') }}：
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
              {{ t('描述') }}：
            </div>
            <div class="value">
              {{ mcpDetails?.description }}
            </div>
          </div>
          <div class="info-item">
            <div class="label">
              {{ t('标签') }}：
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
              {{ t('负责人') }}：
            </div>
            <div class="value">
              <EditMember
                v-if="!featureFlagStore.isTenantMode"
                mode="detail"
                width="600px"
                field="maintainers"
                :content="mcpDetails?.maintainers"
              />
              <TenantUserSelector
                v-else
                :content="mcpDetails?.maintainers"
                field="maintainers"
                mode="detail"
                width="600px"
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
            <div class="flex-row align-items-center">
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
          name="guide"
        >
          <template #label>
            <div class="flex-row align-items-center">
              {{ t('使用指引') }}
            </div>
          </template>
          <div class="panel-content">
            <Guideline
              :markdown-str="markdownStr"
            />
          </div>
        </BkTabPanel>
      </BkTab>
    </div>
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
import ServerTools from '@/views/mcp-server/components/ServerTools.vue';
import Guideline from './components/GuideLine.vue';
import EditMember from '@/views/basic-info/components/EditMember.vue';
import TenantUserSelector from '@/components/tenant-user-selector/Index.vue';

const { t } = useI18n();
const router = useRouter();
const route = useRoute();
const featureFlagStore = useFeatureFlag();
const envStore = useEnv();
// const globalProperties = useGetGlobalProperties();
// const { GLOBAL_CONFIG } = globalProperties;

const active = ref('tools');
const toolsCount = ref<number>(0);
const mcpDetails = ref<IMarketplaceDetails>();
const markdownStr = ref<string>('');

const mcpId = computed(() => {
  return route.params.id;
});

const handleCopy = (str: string) => {
  copy(str);
};

const goBack = () => {
  router.push({ name: 'McpMarket' });
};

const getDetails = async () => {
  const res = await getMcpServerDetails(mcpId.value as string);
  mcpDetails.value = res;
  toolsCount.value = res.tools_count;
  markdownStr.value = res.guideline;
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
  height: 64px;
  padding: 0 24px;
  background: #FFF;
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
      display: flex;
      height: 54px;
      border-bottom: 1px solid #EAEBF0;
      align-items: center;
      justify-content: space-between;

      .title {
        margin-right: 16px;
        font-size: 20px;
        font-weight: bold;
        line-height: 54px;
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
  }

  .panel-content {
    background: #FFF;
  }
}

</style>
