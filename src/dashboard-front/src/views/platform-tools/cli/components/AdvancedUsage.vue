<template>
  <div class="tab-content advanced-usage">
    <!-- 标题区 -->
    <div class="advanced-usage-header">
      <div class="advanced-usage-icon">
        <AgIcon
          name="star"
          size="24"
          color="#3A84FF"
        />
      </div>
      <div class="advanced-usage-info">
        <div class="advanced-usage-title">
          {{ t('进阶用法') }}
        </div>
        <div class="advanced-usage-desc">
          {{ t('掌握高级特性，提升 CLI 使用效率和安全性') }}
        </div>
      </div>
    </div>

    <div class="advanced-usage-content-wrapper">
      <!-- 多上下文管理 -->
      <div class="step-section">
        <div class="step-header">
          <div class="header-icon-wrapper">
            <AgIcon
              name="feedback-fankui"
              size="16"
              color="#3A84FF"
            />
          </div>
          <span class="step-title">{{ t('多上下文管理') }}</span>
        </div>
        <CodeBlock :code="multiContextCode" />
      </div>

      <!-- Dry Run（预览） -->
      <div class="step-section">
        <div class="step-header">
          <div class="header-icon-wrapper">
            <AgIcon
              name="insights"
              size="16"
              color="#3A84FF"
            />
          </div>
          <span class="step-title">{{ t('Dry Run（预览）') }}</span>
        </div>
        <BkAlert
          theme="info"
          class="step-alert"
        >
          <template #title>
            {{ t('建议对有副作用的命令（创建、更新、删除）使用 --dry-run 预览请求，避免误操作。') }}
          </template>
        </BkAlert>
        <CodeBlock :code="dryRunCode" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import CodeBlock from './CodeBlock.vue';

const { t } = useI18n();

// 代码内容留空，由用户自行填写
const multiContextCode = `# 创建不同环境的上下文
$ bk-cli context create clouds \\
  --bk_api_url_tmpl"https://bkapi.clouds.example.com/api/{gateway_name}/"

# 在上下文之间切换
$ bk-cli context use clouds

# 列出所有上下文
$ bk-cli context list

# 单个命令覆盖上下文
$ bk-cli api bk-iam GET /api/v2/systems/ --context devops`;
const dryRunCode = `# 预览请求而不实际执行
$ bk-cli api bk-demo POST /api/v2/resources/ \\
  --body '{"name": "test"}' \\
  --dry-run`;
</script>

<style scoped lang="scss">
.advanced-usage {

  .advanced-usage-header {
    display: flex;
    padding: 18px 24px;
    background: #FAFBFD;
    align-items: flex-start;
    gap: 16px;
    border-bottom: 1px solid #DCDEE5;

    .advanced-usage-icon {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 48px;
      height: 48px;
      background: #fff;
      border-radius: 4px;
      flex-shrink: 0;
      box-shadow: 0 0 8px 0 #374a641a;
    }

    .advanced-usage-info {

      .advanced-usage-title {
        font-size: 14px;
        font-weight: 700;
        line-height: 22px;
        color: #313238;
      }

      .advanced-usage-desc {
        margin-top: 4px;
        font-size: 12px;
        line-height: 20px;
        color: #979ba5;
      }
    }
  }

  .advanced-usage-content-wrapper {
    padding: 24px;

    .step-section {
      padding-bottom: 24px;
      margin-bottom: 24px;
      font-size: 12px;
      border-bottom: 1px solid #EAEBF0;

      &:last-child {
        padding-bottom: 0;
        margin-bottom: 0;
        border-bottom: none;
      }

      .step-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 16px;

        .header-icon-wrapper {
          display: flex;
          width: 20px;
          height: 20px;
          background: #E1ECFF;
          border-radius: 2px;
          align-items: center;
          justify-content: center;
        }

        .step-title {
          font-weight: 700;
          line-height: 22px;
          color: #313238;
        }
      }

      .step-alert {
        margin-bottom: 12px;
      }
    }
  }
}
</style>
