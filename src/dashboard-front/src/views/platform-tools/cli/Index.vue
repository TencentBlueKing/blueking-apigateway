<template>
  <div
    class="platform-tools-cli-page-content"
    :class="{ 'is-top-level': isTopLevel }"
  >
    <!-- 顶部横幅 -->
    <div class="cli-banner">
      <div class="banner-left">
        <img
          class="banner-logo"
          :src="mainLogo"
          alt=""
        >
        <div class="banner-info">
          <div class="banner-title">
            bk-cli
          </div>
          <div class="banner-desc">
            {{ t('面向 Agent 和自动化场景的命令行工具，自动发现蓝鲸体系内所有公开 API，天然支持跨网关 API 发现和调用') }}
          </div>
        </div>
      </div>
      <div class="banner-right">
        <IconButton
          class="banner-detail-button"
          theme="primary"
          icon="link"
          @click="openDetailUrl"
        >
          {{ t('查看详情') }}
        </IconButton>
      </div>
    </div>

    <!-- 特性卡片 -->
    <div class="feature-cards">
      <div class="feature-card">
        <div class="feature-heading">
          <img
            class="feature-icon"
            :src="agentLogo"
            alt=""
          >
          <div class="feature-title">
            {{ t('Agent 原生设计') }}
          </div>
        </div>
        <div class="feature-desc">
          {{ t('零交互、非阻塞、可预测。统一错误码和输出结构，Agent 可用固定逻辑解析所有响应') }}
        </div>
      </div>
      <div class="feature-card">
        <div class="feature-heading">
          <img
            class="feature-icon"
            :src="coverageLogo"
            alt=""
          >
          <div class="feature-title">
            {{ t('覆盖面广') }}
          </div>
        </div>
        <div class="feature-desc">
          {{ t('覆盖 10+ 核心蓝鲸系统（配置平台、作业平台、蓝盾、蓝鲸监控等），一个工具打通所有蓝鲸能力') }}
        </div>
      </div>
      <div class="feature-card">
        <div class="feature-heading">
          <img
            class="feature-icon"
            :src="crossGatewayLogo"
            alt=""
          >
          <div class="feature-title">
            {{ t('跨网关编排') }}
          </div>
        </div>
        <div class="feature-desc">
          {{ t('天然支持跨网关 API 发现和调用。查主机、跑脚本、看告警，一个 CLI 打通多个系统') }}
        </div>
      </div>
    </div>

    <!-- 安全与风险提示 -->
    <BkAlert
      class="risk-notice"
      theme="warning"
      closable
    >
      <template #title>
        <div class="notice-title">
          {{ t('安全与风险提示（使用前必读）') }}
        </div>
        <div class="notice-list">
          <div class="notice-item">
            {{ t('本工具可供 AI Agent 调用以自动化操作蓝鲸所有平台，存在模型幻觉、执行不可控、提示词注入等固有风险') }}
          </div>
          <div class="notice-item">
            {{ t('配置应用和用户凭证后，AI Agent 将以您的用户身份在授权范围内执行操作，可能导致敏感数据泄露、越权操作等高风险后果，请您谨慎操作和使用') }}
          </div>
          <div class="notice-item highlight">
            {{ t('建议为 cli 申请单独的应用 ID 和 access_token，避免使用具有高权限的凭证') }}
          </div>
        </div>
      </template>
    </BkAlert>

    <div class="tab-wrapper">
      <BkTab
        v-model:active="activeTab"
        class="main-tabs"
        type="unborder-card"
        :label-height="42"
      >
        <BkTabPanel
          name="overview"
          :label="t('功能概览')"
        >
          <FunctionOverview />
        </BkTabPanel>
        <BkTabPanel
          name="quickstart"
          :label="t('快速开始')"
        >
          <QuickStart />
        </BkTabPanel>
        <BkTabPanel
          name="advanced"
          :label="t('进阶用法')"
        >
          <AdvancedUsage />
        </BkTabPanel>
      </BkTab>
    </div>
  </div>
</template>

<script setup lang="ts">
import AdvancedUsage from './components/AdvancedUsage.vue';
import FunctionOverview from './components/FunctionOverview.vue';
import QuickStart from './components/QuickStart.vue';
import agentLogo from '@/images/bk-cli/agent.png';
import coverageLogo from '@/images/bk-cli/coverage.png';
import crossGatewayLogo from '@/images/bk-cli/cross-gateway.png';
import mainLogo from '@/images/bk-cli/main-logo.png';
import { useEnv } from '@/stores/useEnv';

const { t } = useI18n();
const route = useRoute();
const envStore = useEnv();

const activeTab = ref('overview');

const isTopLevel = computed(() => route.name === 'BkCli');

const openDetailUrl = () => {
  window.open(envStore.env.CLI.DETAIL_URL, '_blank');
};
</script>

<style lang="scss" scoped>
.platform-tools-cli-page-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  padding: 24px;
  box-sizing: border-box;

  &.is-top-level {
    width: 80%;
    max-width: 1280px;
    min-width: 1200px;
    padding: 16px 0 32px;
    margin: 0 auto;
  }

  .cli-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 108px;
    padding: 24px;
    background: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 4px 0 #1919290d;

    .banner-left {
      display: flex;
      align-items: center;
      min-width: 0;
      gap: 12px;
    }

    .banner-logo {
      display: block;
      width: 64px;
      height: 64px;
      flex-shrink: 0;
    }

    .banner-info {
      min-width: 0;

      .banner-title {
        font-size: 16px;
        font-weight: 700;
        line-height: 24px;
        color: #313238;
      }

      .banner-desc {
        margin-top: 4px;
        font-size: 12px;
        line-height: 20px;
        color: #4d4f56;
      }
    }

    .banner-right {
      flex-shrink: 0;
      margin-left: 24px;
    }

    .banner-detail-button {
      width: 110px;
    }
  }

  .feature-cards {
    display: flex;
    gap: 16px;

    .feature-card {
      display: flex;
      flex: 1;
      flex-direction: column;
      justify-content: center;
      height: 152px;
      min-width: 0;
      padding: 24px;
      background: #fff;
      border-radius: 4px;
      box-shadow: 0 2px 4px 0 #1919290d;

      .feature-heading {
        display: flex;
        align-items: center;
        gap: 16px;
      }

      .feature-icon {
        display: block;
        width: 48px;
        height: 48px;
        flex-shrink: 0;
      }

      .feature-title {
        font-size: 14px;
        font-weight: 700;
        line-height: 22px;
        color: #313238;
      }

      .feature-desc {
        margin-top: 16px;
        font-size: 12px;
        line-height: 20px;
        color: #4d4f56;
      }
    }
  }

  .risk-notice {
    color: #f59500;
    background: #fdf4e8;
    border-color: #fce5c0;
    border-radius: 4px;
    box-shadow: 0 2px 2px 0 #1919290d;

    :deep(.bk-alert-wraper) {
      align-items: flex-start;
      padding: 16px;
    }

    :deep(.bk-alert-icon-info) {
      margin-top: 2px;
      color: #f59500;
    }

    :deep(.bk-alert-title) {
      line-height: 20px;
    }

    :deep(.bk-alert-close) {
      color: #f59500;
    }

    .notice-title {
      font-weight: 700;
    }

    .notice-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
      margin-top: 10px;
    }

    .notice-item {
      position: relative;
      padding-left: 12px;
      font-size: 12px;
      line-height: 20px;

      &::before {
        position: absolute;
        top: 7px;
        left: 0;
        width: 6px;
        height: 6px;
        background: currentcolor;
        border-radius: 50%;
        content: '';
      }

      &.highlight {
        font-weight: 700;
      }
    }
  }

  .tab-wrapper {
    overflow: hidden;
    background: #fff;
    border-radius: 4px;
    box-shadow: 0 2px 2px 0 #1919290d;

    :deep(.main-tabs > .bk-tab-header) {
      padding: 0 24px;
    }

    :deep(.main-tabs > .bk-tab-header .bk-tab-header-item) {
      padding: 0;
      margin-right: 32px;
      font-size: 14px;

      &:last-child {
        margin-right: 0;
      }
    }

    :deep(.main-tabs > .bk-tab-content) {
      padding: 16px 24px 24px;
    }
  }
}
</style>
