<template>
  <div class="tab-content quick-start">
    <div class="tab-description">
      {{ t('三步完成从安装到第一次 API 调用，Agent 即刻获得蓝鲸 API 能力。') }}
    </div>
    <div class="section-divider" />

    <div class="quick-start-content-wrapper">
      <!-- 1. 安装 CLI -->
      <div class="step-section">
        <div class="step-header">
          <span class="step-number">1</span>
          <span class="step-title">{{ t('安装 CLI') }}</span>
          <span class="step-subtitle">{{ t('选择适合你的安装方式') }}</span>
        </div>
        <div class="step-body">
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
      </div>

      <!-- 2. 初始化上下文 -->
      <div class="step-section">
        <div class="step-header">
          <span class="step-number">2</span>
          <span class="step-title">{{ t('初始化上下文') }}</span>
          <span class="step-subtitle">{{ t('首次使用前必须初始化') }}</span>
        </div>
        <div class="step-body">
          <div class="step-desc">
            {{ t('初始化 default 上下文，配置蓝鲸网关 URL 模板') }}
          </div>
          <CodeBlock :code="initContextCode" />
        </div>
      </div>

      <!-- 3. 认证配置 -->
      <div class="step-section">
        <div class="step-header">
          <span class="step-number">3</span>
          <span class="step-title">{{ t('认证配置') }}</span>
          <span class="step-subtitle">{{ t('存储凭据到当前上下文') }}</span>
        </div>
        <div class="step-body">
          <BkTab
            v-model:active="authTab"
            class="auth-tabs"
            type="unborder-card"
            :label-height="36"
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
              :label="t('访问令牌（access_token）')"
            >
              <div class="step-desc">
                {{ t('仅使用访问令牌进行认证。') }}
              </div>
              <CodeBlock :code="authAccessTokenCode" />
            </BkTabPanel>
          </BkTab>
        </div>
      </div>

      <!-- 4. 发起 API 调用 -->
      <div class="step-section">
        <div class="step-header">
          <span class="step-number">4</span>
          <span class="step-title">{{ t('发起 API 调用') }}</span>
          <span class="step-subtitle">{{ t('调用任意蓝鲸网关 API') }}</span>
        </div>
        <div class="step-body">
          <div class="step-desc">
            {{ t('使用原始 API 命令调用任意网关 API，支持路径参数、查询参数和请求体。') }}
          </div>
          <CodeBlock :code="apiCallCode" />
        </div>
      </div>

      <!-- 5. 使用系统子命令 -->
      <div class="step-section">
        <div class="step-header">
          <span class="step-number">5</span>
          <span class="step-title">{{ t('使用系统子命令') }}</span>
          <span class="step-subtitle">{{ t('高层语义命令') }}</span>
        </div>
        <div class="step-body">
          <div class="step-desc">
            {{ t('使用带命名参数的高层命令，更直观地调用 API。') }}
          </div>
          <CodeBlock :code="systemCommandCode" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import CodeBlock from './CodeBlock.vue';
import { useEnv, useFeatureFlag, useUserInfo } from '@/stores';

const { t } = useI18n();
const envStore = useEnv();
const featureFlagStore = useFeatureFlag();
const userStore = useUserInfo();

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

const initContextCode = computed(() => {
  let firstCommand = `# ${t('初始化 default 上下文')}
$ bk-cli context init \\
  --bk_api_url_tmpl="${envStore.env.CLI.BK_API_URL_TMPL}"`;

  if (featureFlagStore.isTenantMode) {
    firstCommand += `
  --tenant_id=${userStore.info.tenant_id || 'system'}`;
  }

  let secondCommand = `

# ${t('可选：设置默认请求超时（默认 60s，最大 300s）')}
$ bk-cli context init \\
  --bk_api_url_tmpl="${envStore.env.CLI.BK_API_URL_TMPL}" \\`;

  if (featureFlagStore.isTenantMode) {
    secondCommand += `
  --tenant_id=${userStore.info.tenant_id || 'system'}`;
  }

  secondCommand += `
  --timeout 90s`;

  return `${firstCommand}${secondCommand}`;
});

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
  display: flex;
  flex-direction: column;
  gap: 16px;

  .tab-description {
    font-size: 12px;
    line-height: 20px;
    color: #4d4f56;
  }

  .section-divider {
    height: 1px;
    background: #eaebf0;
  }

  .quick-start-content-wrapper {
    display: flex;
    flex-direction: column;
    gap: 16px;

    .step-section {
      position: relative;
      font-size: 12px;

      &::before {
        position: absolute;
        top: 32px;
        bottom: 8px;
        left: 12px;
        border-left: 1px solid #dcdee5;
        content: '';
      }

      .step-header {
        display: flex;
        align-items: center;
        height: 24px;
        gap: 8px;

        .step-number {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 24px;
          height: 24px;
          font-family: Arial, sans-serif;
          font-size: 14px;
          line-height: 22px;
          color: #1768ef;
          background: #e1ecff;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .step-title {
          font-weight: 700;
          line-height: 20px;
          color: #313238;
        }

        .step-subtitle {
          line-height: 20px;
          color: #979ba5;
        }
      }

      .step-body {
        padding: 8px 0 8px 32px;
      }

      .step-desc {
        margin-bottom: 16px;
        line-height: 20px;
        color: #4d4f56;
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
            height: 20px;
            margin-bottom: 16px;

            .install-column-title {
              font-size: 12px;
              line-height: 20px;
              color: #4d4f56;
            }

            :deep(.bk-tag) {
              height: 16px;
              padding: 0 6px;
              font-size: 10px;
              line-height: 16px;
              color: #1768ef;
              background: #e1ecff;
              border: 0;
            }
          }
        }
      }

      .auth-tabs {

        :deep(.bk-tab-header) {
          padding: 0 24px;
        }

        :deep(.bk-tab-header-item) {
          padding: 0;
          margin-right: 32px;
          font-size: 12px;

          &:last-child {
            margin-right: 0;
          }
        }

        :deep(.bk-tab-content) {
          padding: 16px 0 0;
        }
      }
    }
  }
}
</style>
