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

      <!-- 更多用法 -->
      <div class="step-section">
        <div class="step-header">
          <!--          <div class="header-icon-wrapper"> -->
          <!--            <AgIcon -->
          <!--              name="insights" -->
          <!--              size="16" -->
          <!--              color="#3A84FF" -->
          <!--            /> -->
          <!--          </div> -->
          <span class="step-title">{{ t('更多用法') }}</span>
          <span class="step-sub-title">{{ t('通过查看帮助信息探索所有支持的系统及操作') }}</span>
        </div>
        <CodeBlock :code="moreUsageCode" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import CodeBlock from './CodeBlock.vue';
import { useEnv } from '@/stores';

const { t } = useI18n();
const envStore = useEnv();

const multiContextCode = computed(() => `# ${t('创建不同环境的上下文')}
$ bk-cli context create clouds \\
  --bk_api_url_tmpl="${envStore.env.CLI.BK_API_URL_TMPL}"

# ${t('在上下文之间切换')}
$ bk-cli context use clouds

# ${t('列出所有上下文')}
$ bk-cli context list

# ${t('单个命令覆盖上下文')}
$ bk-cli api bk-iam GET /api/v2/systems/ --context devops`);

const dryRunCode = computed(() => `# ${t('预览请求而不实际执行')}
$ bk-cli api bk-demo POST /api/v2/resources/ \\
  --body '{"name": "test"}' \\
  --dry-run`);

const moreUsageCode = computed(() => `# ${t('查看帮助')}
$ bk-cli -h

Available Commands:
  api         [root] Make raw API calls to BlueKing API gateways
  apigateway  [system] BlueKing API Gateway management - discover gateways and APIs
  auth        [root] Manage authentication credentials
  cmdb        [system] BlueKing CMDB system commands
  completion  [root] Generate the autocompletion script for the specified shell
  context     [root] Manage CLI contexts (BlueKing deployments)
  devops      [system] BlueKing CI/CD (DevOps) pipeline commands
  gse         [system] BlueKing GSE agent management commands
  help        [root] Help about any command
  job         [system] BlueKing Job platform (BK-JOB) commands
  nodeman     [system] BlueKing Node Management commands
  sops        [system] BlueKing Standard OPS (SOPS) commands
  update      [root] Update bk-cli to the latest version
  version     [root] Show version and context information

# ${t('查看子命令帮助')} bk-cli {subcommand} -h
$ bk-cli  apigateway -h

Available Commands:
  demo_action                  Example Go-implemented orchestration action
  list_gateway_apis            List APIs of a specific gateway
  list_gateways                List all API gateways
  retrieve_gateway_api_details Get detailed API schema for a specific resource

# ${t('查看子命令action的帮助')} bk-cli {subcommand} {action} -h
$ bk-cli apigateway list_gateways -h

Usage:
  bk-cli apigateway list_gateways [flags]

Examples:
  bk-cli apigateway list_gateways --name bk-iam
  bk-cli apigateway list_gateways --name iam --fuzzy
  bk-cli apigateway list_gateways --keyword monitor

Flags:
      --body string          [Optional] JSON request body
      --fuzzy                Enable fuzzy name matching
      --header stringArray   [Optional] Additional headers (key:value, repeatable; auth/tenant overrides allowed)
  -h, --help                 help for list_gateways
      --keyword string       Search keyword in description
      --name string          Gateway name filter
      --stage string         [Optional] API gateway stage (default "prod")
`);

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

        .step-sub-title {
          line-height: 22px;
          color: #979ba5;
        }
      }

      .step-alert {
        margin-bottom: 12px;
      }
    }
  }
}
</style>
