<template>
  <div class="tab-content quick-start">
    <!-- 标题区 -->
    <div class="quick-start-header">
      <div class="quick-start-icon">
        <AgIcon
          name="lightning"
          size="24"
          color="#3A84FF"
        />
      </div>
      <div class="quick-start-info">
        <div class="quick-start-title">
          {{ t('快速开始') }}
        </div>
        <div class="quick-start-desc">
          {{ t('三步完成从安装到第一次 API 调用，Agent 即刻获得蓝鲸 API 能力。') }}
        </div>
      </div>
    </div>

    <div class="quick-start-content-wrapper">
      <!-- 1. 安装 CLI -->
      <div class="step-section">
        <div class="step-header">
          <span class="step-number">1</span>
          <span class="step-title">{{ t('安装 CLI') }}</span>
          <span class="step-subtitle">{{ t('选择适合你的安装方式') }}</span>
        </div>
        <div class="install-columns">
          <div class="install-column">
            <div class="install-column-header">
              <span class="install-column-title">{{ t('npm 安装') }}</span>
              <BkTag
                size="small"
                theme="info"
              >
                {{ t('推荐') }}
              </BkTag>
            </div>
            <CodeBlock :code="installNpmCode" />
          </div>
          <div class="install-column">
            <div class="install-column-header">
              <span class="install-column-title">{{ t('从源码安装') }}</span>
            </div>
            <CodeBlock :code="installSourceCode" />
          </div>
        </div>
      </div>

      <!-- 2. 初始化上下文 -->
      <div class="step-section">
        <div class="step-header">
          <span class="step-number">2</span>
          <span class="step-title">{{ t('初始化上下文') }}</span>
          <span class="step-subtitle">{{ t('首次使用前必须初始化') }}</span>
        </div>
        <div class="step-desc">
          {{ t('初始化 default 上下文，配置蓝鲸网关 URL 模板') }}
        </div>
        <CodeBlock :code="initContextCode" />
      </div>

      <!-- 3. 认证配置 -->
      <div class="step-section">
        <div class="step-header">
          <span class="step-number">3</span>
          <span class="step-title">{{ t('认证配置') }}</span>
          <span class="step-subtitle">{{ t('存储凭据到当前上下文') }}</span>
        </div>
        <BkTab
          v-model:active="authTab"
          type="unborder-card"
        >
          <BkTabPanel
            name="app_user"
            :label="t('应用 + 用户令牌')"
          >
            <div class="step-desc">
              {{ t('初始化 default 上下文，配置蓝鲸网关 URL 模板') }}
            </div>
            <CodeBlock :code="authAppUserCode" />
          </BkTabPanel>
          <BkTabPanel
            name="accesstoken"
            :label="t('访问令牌（accesstoken）')"
          >
            <div class="step-desc">
              {{ t('仅使用访问令牌进行认证。') }}
            </div>
            <CodeBlock :code="authAccessTokenCode" />
          </BkTabPanel>
        </BkTab>
      </div>

      <!-- 4. 发起 API 调用 -->
      <div class="step-section">
        <div class="step-header">
          <span class="step-number">4</span>
          <span class="step-title">{{ t('发起 API 调用') }}</span>
          <span class="step-subtitle">{{ t('调用任意蓝鲸网关 API') }}</span>
        </div>
        <div class="step-desc">
          {{ t('使用原始 API 命令调用任意网关 API，支持路径参数、查询参数和请求体。') }}
        </div>
        <CodeBlock :code="apiCallCode" />
      </div>

      <!-- 5. 使用系统子命令 -->
      <div class="step-section">
        <div class="step-header">
          <span class="step-number">5</span>
          <span class="step-title">{{ t('使用系统子命令') }}</span>
          <span class="step-subtitle">{{ t('高层语义命令') }}</span>
        </div>
        <div class="step-desc">
          {{ t('使用带命名参数的高层命令，更直观地调用 API。') }}
        </div>
        <CodeBlock :code="systemCommandCode" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import CodeBlock from './CodeBlock.vue';
import { useEnv } from '@/stores';

const { t } = useI18n();
const envStore = useEnv();

const authTab = ref('app_user');

const installNpmCode = computed(() => `# ${t('安装 CLI')}
$ ${envStore.env.CLI.NPM_INSTALL_CMD}

# ${t('安装 CLI SKILL（必需）')}
$ ${envStore.env.CLI.SKILL_NPM_INSTALL_CMD}`);

const installSourceCode = computed(() => `# ${t('克隆仓库')}
$ git clone ${envStore.env.CLI.GIT_REPO_URL}
$ cd cli
$ make install

# ${t('安装 CLI SKILL（必需）')}
$ ${envStore.env.CLI.SKILL_NPM_INSTALL_CMD}`);

const initContextCode = computed(() => `# ${t('初始化 default 上下文')}
$ bk-cli context init \\
  --bk_api_url_tmpl="${envStore.env.CLI.BK_API_URL_TMPL}"

# ${t('可选：设置默认请求超时（默认 60s，最大 300s）')}
$ bk-cli context init \\
  --bk_api_url_tmpl="${envStore.env.CLI.BK_API_URL_TMPL}" \\
  --timeout 90s`);

const authAppUserCode = computed(() => `# ${t('存储应用 + 用户令牌 + {token} 有效期 {day} 天', {
  token: envStore.env.CLI.USER_KEY,
  day: envStore.env.CLI.USER_KEY_EXPIRE_DAYS,
})}
$ bk-cli auth login \\
  --bk_app_code="your_app" \\
  --bk_app_secret="your_secret" \\
  --${envStore.env.CLI.USER_KEY}="your_token"

# ${t('检查认证状态')}
$ bk-cli auth status`);

const authAccessTokenCode = computed(() => `# ${t('仅使用访问令牌 access_token 有效期 {day} 天', { day: envStore.env.CLI.ACCESS_TOKEN_EXPIRE_DAYS })}
$ bk-cli auth login --access_token="your_access_token"

# ${t('检查认证状态')}
$ bk-cli auth status`);

const apiCallCode = computed(() => `# ${t('获取帮助')}
$ bk-cli api -h

# ${t('调用 API Gateway 网关')}, ${t('携带查询参数')}
$ bk-cli api bk-apigateway GET /api/v2/open/gateways/ \\
  --query '{"name": "bk-iam", "fuzzy": true}'

# ${t('路径占位符替换')}
$ bk-cli api bk-apigateway GET /api/v2/open/gateways/{gateway_name}/resources/ \\
  --path '{"gateway_name": "bk-iam"}'

# ${t('携带请求体发起 POST')}
$ bk-cli api bk-demo POST /api/v2/resources/ \\
  --body '{"name": "test"}'

# ${t('仅预览，不实际执行')}
$ bk-cli api bk-demo GET /api/v2/foo/ --dry-run`);

const systemCommandCode = computed(() => `# ${t('获取帮助')}
$ bk-cli apigateway -h

# ${t('API Gateway 系统子命令')}
$ bk-cli apigateway list_gateways --name bk-iam --fuzzy
$ bk-cli apigateway list_gateway_apis --gateway_name bk-iam
$ bk-cli apigateway retrieve_gateway_api_details --gateway_name bk-iam --api_name v2_management_groups_policies_list
`);

</script>

<style scoped lang="scss">

.quick-start {

  .quick-start-header {
    display: flex;
    padding: 18px 24px;
    background: #FAFBFD;
    align-items: flex-start;
    gap: 16px;
    border-bottom: 1px solid #DCDEE5;

    .quick-start-icon {
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

    .quick-start-info {

      .quick-start-title {
        font-size: 14px;
        font-weight: 700;
        line-height: 22px;
        color: #313238;
      }

      .quick-start-desc {
        margin-top: 4px;
        font-size: 12px;
        line-height: 20px;
        color: #979ba5;
      }
    }
  }

  .quick-start-content-wrapper {
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

        .step-number {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 20px;
          height: 20px;
          font-weight: 700;
          color: #3A84FF;
          background: #E1ECFF;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .step-title {
          font-weight: 700;
          line-height: 22px;
          color: #313238;
        }

        .step-subtitle {
          line-height: 20px;
          color: #979ba5;
        }
      }

      .step-desc {
        margin-bottom: 12px;
        line-height: 20px;
        color: #63656e;
      }

      .install-columns {
        display: flex;
        gap: 16px;

        .install-column {
          flex: 1;
          min-width: 0;

          .install-column-header {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;

            .install-column-title {
              font-size: 12px;
              line-height: 20px;
              color: #4D4F56;
            }
          }
        }
      }

      :deep(.bk-tab-header) {
        line-height: 36px !important;

        // background: transparent;
      }

      :deep(.bk-tab-content) {
        padding: 16px 0 0;
      }
    }
  }
}

</style>
