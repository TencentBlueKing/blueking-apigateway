<template>
  <div class="platform-tools-cli-page-content">
    <!-- 顶部横幅 -->
    <div class="cli-banner">
      <div class="banner-left">
        <div class="banner-icon">
          <AgIcon
            name="cli-o"
            size="28"
            color="#fff"
          />
        </div>
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
        <div class="feature-icon blue">
          <AgIcon
            name="roboto"
            size="24"
            color="#3A84FF"
          />
        </div>
        <div class="feature-title">
          {{ t('Agent 原生设计') }}
        </div>
        <div class="feature-desc">
          {{ t('零交互、非阻塞、可预测。统一错误码和输出结构，Agent 可用固定逻辑解析所有响应') }}
        </div>
      </div>
      <div class="feature-card">
        <div class="feature-icon green">
          <AgIcon
            name="cardd"
            size="24"
            color="#3A84FF"
          />
        </div>
        <div class="feature-title">
          {{ t('覆盖面广') }}
        </div>
        <div class="feature-desc">
          {{ t('覆盖 10+ 核心蓝鲸系统（配置平台、作业平台、蓝盾、蓝鲸监控等），一个工具打通所有蓝鲸能力') }}
        </div>
      </div>
      <div class="feature-card">
        <div class="feature-icon orange">
          <AgIcon
            name="kuawangguan"
            size="24"
            color="#3A84FF"
          />
        </div>
        <div class="feature-title">
          {{ t('跨网关编排') }}
        </div>
        <div class="feature-desc">
          {{ t('天然支持跨网关 API 发现和调用。查主机、跑脚本、看告警，一个 CLI 打通多个系统') }}
        </div>
      </div>
    </div>

    <!-- 安全与风险提示 -->
    <div class="risk-notice">
      <div class="notice-header">
        <AgIcon
          name="remind"
          size="16"
          color="#FF9C01"
        />
        <span class="notice-title">{{ t('安全与风险提示（使用前必读）') }}</span>
      </div>
      <div class="notice-list">
        <div class="notice-item">
          <span class="pr-4px color-#F59500 text-18px">•</span>
          {{ t('本工具可供 AI Agent 调用以自动化操作蓝鲸所有平台，存在模型幻觉、执行不可控、提示词注入等固有风险') }}
        </div>
        <div class="notice-item">
          <span class="pr-4px color-#F59500 text-18px">•</span>
          {{ t('配置应用和用户凭证后，AI Agent 将以您的用户身份在授权范围内执行操作，可能导致敏感数据泄露、越权操作等高风险后果，请您谨慎操作和使用') }}
        </div>
        <div class="notice-item highlight">
          <span class="pr-4px color-#F59500 text-18px">•</span>
          {{ t('建议为 cli 申请单独的应用 ID 和 access_token，避免使用具有高权限的凭证') }}
        </div>
      </div>
    </div>

    <div class="tab-wrapper">
      <BkTab
        v-model:active="activeTab"
        type="unborder-card"
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
import FunctionOverview from './components/FunctionOverview.vue';
import QuickStart from './components/QuickStart.vue';
import AdvancedUsage from './components/AdvancedUsage.vue';
import { useEnv } from '@/stores/useEnv';

const { t } = useI18n();
const envStore = useEnv();

const activeTab = ref('overview');

const openDetailUrl = () => {
  window.open(envStore.env.CLI.DETAIL_URL, '_blank');
};
</script>

<style lang="scss" scoped>

.platform-tools-cli-page-content {
  padding: 24px;

  .cli-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 24px;
    background: #fff;
    border-radius: 2px;
    box-shadow: 0 2px 6px 0 rgb(0 0 0 / 10%);

    .banner-left {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .banner-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 48px;
      height: 48px;
      background: #3A84FF;
      border-radius: 4px;
      flex-shrink: 0;
    }

    .banner-info {

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
        color: #979ba5;
      }
    }

    .banner-right {
      flex-shrink: 0;
      margin-left: 24px;
    }
  }

  .feature-cards {
    display: flex;
    gap: 16px;
    margin-top: 16px;

    .feature-card {
      flex: 1;
      padding: 24px;
      background: #fff;
      border-radius: 2px;
      box-shadow: 0 2px 6px 0 rgb(0 0 0 / 10%);

      .feature-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: 8px;

        &.blue {
          background: #e1ecff;
        }

        &.green {
          background: #e1ecff;
        }

        &.orange {
          background: #e1ecff;
        }
      }

      .feature-title {
        margin-top: 16px;
        font-size: 14px;
        font-weight: 700;
        line-height: 22px;
        color: #313238;
      }

      .feature-desc {
        margin-top: 8px;
        font-size: 12px;
        line-height: 20px;
        color: #979ba5;
      }
    }
  }

  .risk-notice {
    margin-top: 16px;
    background: #FDF4E8;
    border: 1px solid #F9D090;
    border-radius: 2px;

    .notice-header {
      display: flex;
      height: 38px;
      padding: 8px;
      border-bottom: 1px solid #F9D090;
      align-items: center;
      gap: 8px;

      .notice-title {
        font-size: 14px;
        font-weight: 700;
        line-height: 22px;
        color: #ff9c01;
      }
    }

    .notice-list {
      display: flex;
      flex-direction: column;
      padding: 12px 24px;
      gap: 8px;

      .notice-item {
        padding-left: 6px;
        font-size: 12px;
        line-height: 20px;
        color: #8B4113;

        &.highlight {
          padding-block: 4px;
          font-weight: 700;
          background: #FCE5C0;
        }
      }
    }
  }

  .tab-wrapper {
    margin-top: 16px;
    background: #FFF;
    border-radius: 2px;
    box-shadow: 0 0 8px 0 #374a641a;

    :deep(.bk-tab-header) {
      padding-left: 24px;
    }

    :deep(.bk-tab-content) {
      padding: 0;
    }
  }
}
</style>
