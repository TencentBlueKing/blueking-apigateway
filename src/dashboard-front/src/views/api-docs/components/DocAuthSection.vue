/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) Tencent. All rights reserved.
 * Licensed under the MIT License (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 *     http://opensource.org/licenses/MIT
 *
 * Unless required by applicable law or agreed to in writing, software distributed under
 * the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
 * either express or implied. See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * We undertake not to change the open source license (MIT license) applicable
 * to the current version of the project delivered to anyone in the future.
 */

<template>
  <div>
    <article
      v-if="showSection"
      class="doc-auth-section ag-markdown-view"
    >
      <header
        class="auth-header"
        @click="isExpanded = !isExpanded"
      >
        <AgIcon
          name="down-shape"
          class="auth-toggle-icon"
          :class="{ fold: !isExpanded }"
        />
        <h3 id="doc-heading-认证方式">
          {{ t('认证方式') }}
        </h3>
      </header>
      <div
        v-show="isExpanded"
        class="auth-body"
      >
        <p>
          {{ introText }}
          <BkLink
            class="auth-doc-link"
            :disabled="!authDocUrl"
            theme="primary"
            :href="authDocUrl"
            target="_blank"
          >
            {{ t('查看文档') }}
            <AgIcon
              name="jump"
              size="12"
              class="auth-doc-link-icon"
            />
          </BkLink>
        </p>

        <table>
          <thead>
            <tr>
              <th>{{ t('请求头') }}</th>
              <th>{{ t('示例') }}</th>
              <th>{{ t('必选') }}</th>
              <th>{{ t('描述') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="header in headerRows"
              :key="header.name"
            >
              <td>{{ header.name }}</td>
              <td>{{ header.example }}</td>
              <td>{{ header.required ? t('是') : t('否') }}</td>
              <td>
                {{ header.description }}
                <BkTag
                  v-if="header.tag"
                  class="ml-8px"
                  size="small"
                  theme="success"
                >
                  {{ t('推荐') }}
                </BkTag>
              </td>
            </tr>
          </tbody>
        </table>

        <h4>{{ t('请求示例') }}</h4>
        <BkTab
          v-model:active="exampleTab"
          type="unborder-card"
          class="example-tab"
        >
          <BkTabPanel
            name="curl"
            label="cURL"
          >
            <div class="pre-wrapper">
              <CopyButton
                :source="recommendedCurl"
                class="example-copy"
              />
              <pre><code>{{ recommendedCurl }}</code></pre>
            </div>
          </BkTabPanel>
          <BkTabPanel
            name="python"
            label="Python"
          >
            <div class="pre-wrapper">
              <CopyButton
                :source="pythonExample"
                class="example-copy"
              />
              <pre><code>{{ pythonExample }}</code></pre>
            </div>
          </BkTabPanel>
        </BkTab>
      </div>
    </article>
  </div>
</template>

<script lang="ts" setup>
import {
  HEADER_API_KEY,
  HEADER_AUTHORIZATION,
  HEADER_BKAPI_AUTHORIZATION,
  HEADER_BK_TENANT_ID,
  HEADER_BK_USERNAME,
  buildCurlCommand,
  getAccessTokenSource,
  isUsernameHeaderRequired,
  needsAuthSection,
} from '../utils/compose-doc';
import type { IDocsResourceDocPlugin } from '@/services/types/responses/docs.ts';
import { useEnv, useFeatureFlag } from '@/stores';

interface IHeaderRow {
  name: string
  example: string
  required: boolean
  description: string
  tag?: 'recommended'
}

interface IProps {
  plugins?: IDocsResourceDocPlugin[]
  verifiedAppRequired?: boolean
  verifiedUserRequired?: boolean
  resourceUrl?: string
  method?: string
}

const {
  plugins = [],
  verifiedAppRequired = false,
  verifiedUserRequired = false,
  resourceUrl = 'http://example.com/api',
  method = 'GET',
} = defineProps<IProps>();

const { t } = useI18n();
const featureFlagStore = useFeatureFlag();
const envStore = useEnv();

const exampleTab = ref('curl');
const isExpanded = ref(false);

const loginTicketKey = 'bk_token';

const requestMethod = computed(() => (method || 'GET').toUpperCase());
const pythonRequestMethod = computed(() => {
  const name = requestMethod.value.toLowerCase();
  return ['get', 'post', 'put', 'patch', 'delete', 'head', 'options'].includes(name) ? name : 'request';
});

const tokenSource = computed(() => getAccessTokenSource(plugins));
const usernameRequired = computed(() => isUsernameHeaderRequired(plugins));
const isTenantMode = computed(() => featureFlagStore.isTenantMode);
const authDocUrl = computed(() => envStore.env.DOC_LINKS.AUTH);
const showSection = computed(() => needsAuthSection({
  plugins,
  verifiedAppRequired,
  verifiedUserRequired,
  isTenantMode: isTenantMode.value,
}));

const introText = computed(() => {
  if (tokenSource.value === 'bearer') {
    return t('请求须在 Header 中传递 {header}。', { header: 'Authorization: Bearer {access_token}' });
  }
  if (tokenSource.value === 'api_key') {
    return t('请求须在 Header 中传递 {header}。', { header: 'X-API-KEY: {access_token}' });
  }
  if (verifiedAppRequired || verifiedUserRequired) {
    return t('请求须在 Header 中传递应用及用户认证信息。');
  }
  if (usernameRequired.value) {
    return t('请求须在 Header 中传递 {header}。', { header: HEADER_BK_USERNAME + ': {username}' });
  }
  return t('请求须在 Header 中传递 {header}。', { header: HEADER_BK_TENANT_ID + ': {tenant_id}' });
});

const headerRows = computed<IHeaderRow[]>(() => {
  const rows: IHeaderRow[] = [];
  if (tokenSource.value === 'bearer') {
    rows.push({
      name: HEADER_AUTHORIZATION,
      example: 'Bearer {access_token}',
      required: true,
      description: t('应用 / 用户 access_token，Bearer 格式'),
      tag: 'recommended',
    });
  }
  else if (tokenSource.value === 'api_key') {
    rows.push({
      name: HEADER_API_KEY,
      example: '{access_token}',
      required: true,
      description: t('应用 / 用户 access_token'),
      tag: 'recommended',
    });
  }
  if (!tokenSource.value && (verifiedAppRequired || verifiedUserRequired)) {
    rows.push({
      name: HEADER_BKAPI_AUTHORIZATION,
      example: '{"bk_app_code":"x","bk_app_secret":"y"}',
      required: true,
      description: t('值为 JSON 格式字符串，用于传递应用和用户认证信息'),
    });
  }
  if (usernameRequired.value) {
    rows.push({
      name: HEADER_BK_USERNAME,
      example: '{username}',
      required: true,
      description: t('当前用户名，须在请求头中传递'),
    });
  }
  if (isTenantMode.value) {
    rows.push({
      name: HEADER_BK_TENANT_ID,
      example: '{tenant_id}',
      required: true,
      description: t('租户 ID。单租户应用使用所属租户，全租户应用必须指定租户'),
    });
  }
  return rows;
});

const curlOptions = computed(() => ({
  method,
  resourceUrl,
  plugins,
  verifiedAppRequired,
  verifiedUserRequired,
  isTenantMode: isTenantMode.value,
  loginTicketKey,
}));
const recommendedCurl = computed(() => buildCurlCommand(curlOptions.value));

const pythonExample = computed(() => {
  const headers: string[] = [];
  const usesBkapiAuthorization = !tokenSource.value && (verifiedAppRequired || verifiedUserRequired);
  if (tokenSource.value === 'bearer') {
    headers.push(`        "${HEADER_AUTHORIZATION}": "Bearer {access_token}",`);
  }
  else if (tokenSource.value === 'api_key') {
    headers.push(`        "${HEADER_API_KEY}": "{access_token}",`);
  }
  else if (usesBkapiAuthorization) {
    const payload: Record<string, string> = {};
    if (verifiedAppRequired) {
      payload.bk_app_code = 'x';
      payload.bk_app_secret = 'y';
    }
    if (verifiedUserRequired) {
      payload[loginTicketKey] = 'z';
    }
    headers.push(`        "${HEADER_BKAPI_AUTHORIZATION}": json.dumps(${JSON.stringify(payload)}),`);
  }
  if (usernameRequired.value) {
    headers.push(`        "${HEADER_BK_USERNAME}": "{username}",`);
  }
  if (isTenantMode.value) {
    headers.push(`        "${HEADER_BK_TENANT_ID}": "{tenant_id}",`);
  }
  const call = pythonRequestMethod.value === 'request'
    ? `requests.request("${requestMethod.value}",`
    : `requests.${pythonRequestMethod.value}(`;
  return [
    ...(usesBkapiAuthorization ? ['import json'] : []),
    'import requests',
    '',
    call,
    `    "${resourceUrl}",`,
    '    headers={',
    ...headers,
    '    },',
    ')',
  ].join('\n');
});

watch(() => resourceUrl, () => {
  isExpanded.value = false;
});
</script>

<style scoped lang="scss">
.doc-auth-section {
  margin-bottom: 24px;

  .auth-header {
    display: flex;
    align-items: center;
    margin-bottom: 0;
    cursor: pointer;

    h3 {
      margin: 0 !important;
      font-size: 16px;
      font-weight: 700;
      line-height: 22px;
    }
  }

  .auth-toggle-icon {
    flex-shrink: 0;
    margin-right: 8px;
    font-size: 12px;
    color: #979ba5;
    transition: transform .2s;

    &.fold {
      transform: rotate(-90deg);
    }
  }

  .auth-body {
    margin-top: 12px;
  }

  .auth-doc-link {
    display: inline-flex;
    align-items: center;
    margin-left: 8px;
    font-size: 14px;
    vertical-align: baseline;
  }

  .auth-doc-link-icon {
    margin-left: 4px;
  }

  table {

    td:first-child,
    th:first-child {
      white-space: nowrap;
    }
  }

  .example-tab {
    margin-top: 8px;
  }

  .pre-wrapper {
    position: relative;

    .example-copy {
      position: absolute;
      top: 8px;
      right: 8px;
      z-index: 1;
    }

    pre {
      padding: 10px;
      margin: 14px 0;
      overflow: auto;
      font-size: 14px;
      line-height: 24px;
      background: #f5f7fa;
      border-radius: 2px;
    }
  }
}
</style>
