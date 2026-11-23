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
  <div
    v-if="curResource"
    class="ag-resource-item"
    :class="{ 'show-diff': onlyShowDiff }"
  >
    <p
      class="title always-visible"
      :class="{
        'ag-diff':
          checkDiff('name') ||
          checkDiff('path') ||
          checkDiff('description') ||
          checkDiff('api_labels') ||
          authTypeChanged ||
          checkDiff('is_public') ||
          checkDiff(
            'contexts.resource_auth.config.resource_perm_required'
          ) ||
          userAuthMethodsChanged ||
          applyPermissionChanged,
      }"
    >
      {{ t('基本信息') }}
    </p>
    <BkContainer
      class="ag-kv-box"
      :col="15"
      :margin="6"
    >
      <BkRow
        class="always-visible"
        :class="{ 'ag-diff': checkDiff('name') }"
      >
        <BkCol :span="5">
          <label class="ag-key">{{ t('资源名称') }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.name || '--' }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow :class="{ 'ag-diff': checkDiff('path') }">
        <BkCol :span="5">
          <label class="ag-key">{{ t('资源地址') }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.path || '--' }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow :class="{ 'ag-diff': checkDiff('description') }">
        <BkCol :span="5">
          <label class="ag-key">{{ t('描述') }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.description || '--' }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow :class="{ 'ag-diff': checkDiff('api_labels') }">
        <BkCol :span="5">
          <label class="ag-key">{{ t('标签') }}:</label>
        </BkCol>
        <BkCol
          style="margin-bottom: -4px;"
          :span="10"
        >
          <template v-if="localData.api_labels?.length">
            <BkTag
              v-for="tag in labels?.filter((label: any) =>
                localData.api_labels?.includes(label.id) || localData.api_labels?.includes(String(label.id)))"
              :key="tag.id"
              class="ag-value mb-4px ml-4px"
            >
              {{ tag.name }}
            </BkTag>
          </template>
          <div
            v-else
            class="ag-value"
          >
            --
          </div>
        </BkCol>
      </BkRow>

      <BkRow
        :class="{ 'ag-diff': authTypeChanged }"
      >
        <BkCol :span="5">
          <label class="ag-key">{{ t('认证方式') }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ getAuthTypeLabel(authConfig, t, gatewayStore.isResourceAuthV2) }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow
        :class="{ 'ag-diff': userAuthMethodsChanged }"
      >
        <BkCol :span="5">
          <label class="ag-key">{{ gatewayStore.isResourceAuthV2 ? t('用户认证方式') : t('个人令牌') }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ getUserAuthMethodsLabel(authConfig, t, gatewayStore.isResourceAuthV2) }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow :class="{ 'ag-diff': checkDiff('is_public') }">
        <BkCol :span="5">
          <label class="ag-key">{{ t('是否公开') }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.is_public ? t('是') : t('否') }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow
        v-if="canApplyPermission || applyPermissionChanged"
        :class="{ 'ag-diff': applyPermissionChanged }"
      >
        <BkCol :span="5">
          <label class="ag-key">{{ t('允许申请权限') }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ canApplyPermission && localData.allow_apply_permission ? t('是') : t('否') }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow
        v-if="showResourcePermission"
        :class="{ 'ag-diff': resourcePermissionChanged }"
      >
        <BkCol :span="5">
          <label class="ag-key">{{ t('校验应用权限') }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ authConfig?.resource_perm_required ? t('是') : t('否') }}
          </div>
        </BkCol>
      </BkRow>
    </BkContainer>

    <p
      class="title mt-15px"
      :class="{
        'ag-diff': checkDiff('method') || checkDiff('path') ||
          checkDiff('match_subpath') || checkDiff('enable_websocket'),
      }"
    >
      {{ t('请求配置') }}
    </p>
    <BkContainer
      class="ag-kv-box"
      :col="15"
      :margin="6"
    >
      <BkRow :class="{ 'ag-diff': checkDiff('method') }">
        <BkCol :span="5">
          <label class="ag-key">{{ t('请求方法') }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.method }}
          </div>
        </BkCol>
      </BkRow>

      <BkRow :class="{ 'ag-diff': checkDiff('path') }">
        <BkCol :span="5">
          <label class="ag-key">{{ t('请求路径') }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.path }}
          </div>
        </BkCol>
      </BkRow>
      <template v-if="localData.kind !== 'ai'">
        <BkRow :class="{ 'ag-diff': checkDiff('match_subpath') }">
          <BkCol :span="5">
            <label class="ag-key">{{ t('匹配所有子路径') }}:</label>
          </BkCol>
          <BkCol :span="10">
            <div class="ag-value">
              {{ localData.match_subpath ? t('是') : t('否') }}
            </div>
          </BkCol>
        </BkRow>

        <BkRow :class="{ 'ag-diff': checkDiff('enable_websocket') }">
          <BkCol :span="5">
            <label class="ag-key">{{ t('启用 WebSocket') }}:</label>
          </BkCol>
          <BkCol :span="10">
            <div class="ag-value">
              {{ localData.enable_websocket ? t('是') : t('否') }}
            </div>
          </BkCol>
        </BkRow>
      </template>
    </BkContainer>

    <template v-if="localData.kind !== 'ai'">
      <p
        :class="{
          'ag-diff': checkDiff('openapi_schema'),
        }"
        class="title mt-15px"
      >
        {{ t('请求/响应参数') }}
      </p>
      <BkContainer
        :col="15"
        :margin="6"
        class="ag-kv-box"
      >
        <BkRow :class="{ 'ag-diff': checkDiff('openapi_schema') }">
          <BkCol :span="5">
            <label class="ag-key">&nbsp;</label>
          </BkCol>
          <BkCol :span="10">
            <div class="ag-value">
              {{ isSource ? '--' : (checkDiff('openapi_schema') ? t('有更新') : '--') }}
            </div>
          </BkCol>
        </BkRow>
      </BkContainer>
    </template>

    <template v-if="localData.proxy?.backend_id && localData.kind !== 'ai'">
      <p
        class="title mt-16px"
        :class="{ 'ag-diff': checkDiff('proxy') }"
      >
        {{ t('后端配置') }}
      </p>
      <BkContainer
        class="ag-kv-box"
        :col="15"
        :margin="6"
        :class="{ 'box-diff': checkDiff('proxy.type') }"
      >
        <BkRow
          :class="{ 'ag-diff': checkDiff('proxy.backend_id') }"
        >
          <BkCol :span="5">
            <label class="ag-key">{{ t('后端服务:') }}</label>
          </BkCol>
          <BkCol :span="10">
            <div class="ag-value">
              {{ localData.proxy.backend_name || '--' }}
            </div>
          </BkCol>
        </BkRow>

        <template v-if="localData.proxy.type === 'http'">
          <BkRow
            :class="{ 'ag-diff': checkDiff('proxy.config.method') }"
          >
            <BkCol :span="5">
              <label class="ag-key">{{ t('请求方法') }}:</label>
            </BkCol>
            <BkCol :span="10">
              <div class="ag-value">
                {{ localData.proxy.config.method || '--' }}
              </div>
            </BkCol>
          </BkRow>

          <BkRow
            :class="{
              'ag-diff': checkDiff('proxy.config.timeout'),
            }"
          >
            <BkCol :span="5">
              <label class="ag-key">{{ t('自定义超时时间:') }}</label>
            </BkCol>
            <BkCol :span="10">
              <div class="ag-value">
                {{ localData.proxy.config.timeout }}
              </div>
            </BkCol>
          </BkRow>

          <BkRow
            :class="{ 'ag-diff': checkDiff('proxy.config.path') }"
          >
            <BkCol :span="5">
              <label class="ag-key">{{ t('请求路径:') }}</label>
            </BkCol>
            <BkCol :span="10">
              <div class="ag-value">
                {{ localData.proxy.config.path || '--' }}
              </div>
            </BkCol>
          </BkRow>
        </template>

        <template v-if="localData.proxy.type === 'mock'">
          <BkRow
            :class="{ 'ag-diff': checkDiff('proxy.config.code') }"
          >
            <BkCol :span="5">
              <label class="ag-key">Status Code:</label>
            </BkCol>
            <BkCol :span="10">
              <div class="ag-value">
                {{ localData.proxy.config.code || '--' }}
              </div>
            </BkCol>
          </BkRow>

          <BkRow
            :class="{ 'ag-diff': checkDiff('proxy.config.body') }"
          >
            <BkCol :span="5">
              <label class="ag-key">Response Body:</label>
            </BkCol>
            <BkCol :span="10">
              <div class="ag-value">
                <pre
                  v-if="localData.proxy.config.body"
                  class="ag-pre mt0"
                >{{
                    localData.proxy.config.body || '--'
                  }}</pre>
                <span v-else>--</span>
              </div>
            </BkCol>
          </BkRow>

          <BkRow
            :class="{ 'ag-diff': checkDiff('proxy.config.headers') }"
          >
            <BkCol :span="5">
              <label class="ag-key">Headers:</label>
            </BkCol>
            <BkCol :span="10">
              <div v-if="hasHeaders">
                <ul class="ag-list">
                  <li
                    v-for="(headerItem, index) in localData.proxy.config
                      .headers"
                    :key="index"
                  >
                    {{ index }} : {{ headerItem }}
                  </li>
                </ul>
              </div>
              <span v-else>--</span>
            </BkCol>
          </BkRow>
        </template>
      </BkContainer>
    </template>

    <template v-if="localData.kind === 'ai'">
      <p
        class="title mt-16px"
        :class="{ 'ag-diff': checkDiff('proxy.backend_id') }"
      >
        {{ t('模型服务配置') }}
      </p>
      <BkContainer
        class="ag-kv-box"
        :col="15"
        :margin="6"
      >
        <BkRow :class="{ 'ag-diff': checkDiff('proxy.backend_id') }">
          <BkCol :span="5">
            <label class="ag-key">{{ t('模型服务') }}:</label>
          </BkCol>
          <BkCol :span="10">
            <div class="ag-value">
              {{ localData.proxy.backend_name || '--' }}
            </div>
          </BkCol>
        </BkRow>
      </BkContainer>
    </template>

    <p
      class="title mt-15px"
      :class="{ 'ag-diff': checkDiff('doc_updated_time') }"
    >
      {{ t('文档') }}
    </p>
    <BkContainer
      class="ag-kv-box"
      :col="15"
      :margin="6"
    >
      <BkRow :class="{ 'ag-diff': checkDiff('doc_updated_time.zh') }">
        <BkCol :span="5">
          <label class="ag-key">{{ t('中文文档更新时间') }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.doc_updated_time.zh || '--' }}
          </div>
        </BkCol>
      </BkRow>
      <BkRow :class="{ 'ag-diff': checkDiff('doc_updated_time.en') }">
        <BkCol :span="5">
          <label class="ag-key">{{ t('英文文档更新时间') }}:</label>
        </BkCol>
        <BkCol :span="10">
          <div class="ag-value">
            {{ localData.doc_updated_time.en || '--' }}
          </div>
        </BkCol>
      </BkRow>
    </BkContainer>

    <!--  插件  -->
    <div v-if="localData.plugins?.length">
      <template
        v-for="plugin in localData.plugins"
        :key="plugin.id"
      >
        <div
          class="plugin-diff"
          :class="getPluginDiffClass(plugin.type, curResource.diff, diffData, isSource)"
        >
          <p class="plugin-title mt-15px">
            {{ t('插件:{name}', { name: plugin.name }) }}
          </p>
          <ConfigDisplayTable
            :plugin="plugin"
            first-col-width="auto"
          />
        </div>
      </template>
    </div>
  </div>
  <div v-else>
    --
  </div>
</template>

<script setup lang="ts">
import ConfigDisplayTable from '@/components/plugin/plugin-manage/config-display/Index.vue';
import { useGateway } from '@/stores';
import {
  createDiffIndex,
  getPluginDiffClass,
  normalizeResource,
} from '../resource-diff';
import type {
  IResourceVersionDiffResource,
  ResourceVersionDiff,
} from '@/services/types/gateway/resource-version';
import type { IBackendListOutput } from '@/services/types/gateway/backend';
import {
  canAllowApplyPermission,
  canConfigureResourcePerm,
  getAuthTypeLabel,
  getUserAuthMethodsLabel,
  parseResourceAuthConfig,
} from '@/utils/auth-config';

interface IProps {
  curResource?: IResourceVersionDiffResource | null
  diffData?: ResourceVersionDiff | null
  onlyShowDiff?: boolean
  backendsList?: IBackendListOutput[]
  // 是否作为旧版本资源展示
  isSource?: boolean
}

const {
  curResource = null,
  diffData = {},
  onlyShowDiff = false,
  backendsList = [],
  isSource = false,
} = defineProps<IProps>();

const { t } = useI18n();
const gatewayStore = useGateway();

// 展示值与差异索引独立派生，资源、另一侧差异或后端列表变化时自动更新。
const localData = computed(() => normalizeResource(curResource, backendsList));
const diffIndex = computed(() => createDiffIndex(curResource?.diff, diffData));
const checkDiff = (path: string) => diffIndex.value.has(path);

const hasHeaders = computed(() => Object.keys(localData.value.proxy.config.headers ?? {}).length > 0);

const authConfig = computed(() => parseResourceAuthConfig(localData.value.contexts?.resource_auth?.config));
const userRequiredChanged = computed(() => checkDiff('contexts.resource_auth.config.auth_verified_required'));
const appRequiredChanged = computed(() => checkDiff('contexts.resource_auth.config.app_verified_required'));
const authTypeChanged = computed(() => userRequiredChanged.value || (
  appRequiredChanged.value && (!gatewayStore.isResourceAuthV2 || !authConfig.value?.auth_verified_required)
));
const userAuthMethodsChanged = computed(() =>
  checkDiff('contexts.resource_auth.config.oauth2_personal_client_enabled')
  || (gatewayStore.isResourceAuthV2 && (
    checkDiff('contexts.resource_auth.config.oauth2_public_client_enabled')
    || userRequiredChanged.value
    || (authConfig.value?.auth_verified_required && appRequiredChanged.value)
  )),
);
const canApplyPermission = computed(() => canAllowApplyPermission(!!localData.value.is_public, authConfig.value));
const resourcePermissionChanged = computed(() =>
  checkDiff('contexts.resource_auth.config.resource_perm_required'),
);
const applyPermissionChanged = computed(() =>
  checkDiff('allow_apply_permission')
  || checkDiff('is_public')
  || resourcePermissionChanged.value,
);
const showResourcePermission = computed(() =>
  canConfigureResourcePerm(authConfig.value)
  || authConfig.value?.resource_perm_required
  || resourcePermissionChanged.value
  || appRequiredChanged.value,
);

// 网关标签
const labels = computed(() => gatewayStore.labels || []);
</script>

<style lang="scss" scoped>
.ag-dl {
  padding: 15px 40px 5px 30px;
}

.ag-diff {

  .ag-value {
    color: #fe9c00 !important;
  }

  .ag-pre {
    color: #fe9c00;
    background: #fbf4e9;
  }

  .ag-list {
    background: #fbf4e9;
  }
}

.ag-user-type {
  position: relative;
  width: 560px;
  height: 80px;
  padding: 17px 20px 0;
  overflow: hidden;
  background: #fafbfd;
  border: 1px solid #dcdee5;
  border-radius: 2px;

  .apigateway-icon {
    position: absolute;
    top: 15px;
    right: 20px;
    z-index: 0;
    font-size: 80px;
    color: #ecf2fc;
  }

  strong {
    display: block;
    margin-bottom: 10px;
    font-size: 13px;
    line-height: 1;
  }

  p {
    font-size: 12px;
    color: #63656e;
  }
}

.detail-wrapper {
  padding: 10px 20px 10px 10px;
  margin-top: 6px;
  background: #f0f1f5;
  border-radius: 2px;

  &.wrapper-diff {
    background: #fbf4e9;
  }

  .content-item {
    display: flex;
    font-size: 13px;
    line-height: 26px;
  }

  .key {
    display: inline-block;
    width: 100px;
    line-height: 28px;
    color: #63656e;
    text-align: right;
    vertical-align: middle;
  }

  .value {
    color: #313238;
    flex: 1;
  }
}

.ag-list {
  font-size: 13px;
  background: #fff;
  border: 1px solid #dcdee5;
  border-radius: 2px;

  > li {
    display: flex;
    padding: 5px 10px;
    line-height: 22px;
    background: #fff;

    .ds-key {
      white-space: nowrap;
    }

    .ds-value {
      padding-left: 5px;
      word-break: break-all;
      white-space: normal;
    }

    & + li {
      border-top: 1px solid #dcdee5;
    }
  }
}

.ag-tab-button {
  cursor: default;

  &:hover {
    color: #63656e;
    border-color: #c4c6cc;
  }

  &.is-selected {
    color: #3a84ff !important;
    border-color: #3a84ff !important;

    a {
      color: #3a84ff !important;
    }
  }
}

.ag-value {
  word-break: break-all;
  white-space: normal;
}

.bk-host-table {

  tr {
    background: #fff !important;
  }

  td,
  th {
    height: 36px;
    background: #fff !important;
  }
}

.plugin-diff {
  padding: 2px 8px;
  margin: 18px 0;

  .plugin-title {
    padding-bottom: 10px;
    margin-bottom: 17px;
    font-size: 12px;
    font-weight: bold;
    color: #63656e;
    border-bottom: 1px solid #dcdee5;
  }

  &.item-added {
    background-color: rgb(45 203 86 / 10%);
  }

  &.item-updated {
    background-color: rgb(255 156 1 / 10%);
  }

  &.item-deleted {
    background-color: rgb(234 54 54 / 10%);
  }
}

.ag-kv-box {

  &.box-diff {
    padding-top: 10px;
    padding-bottom: 10px;
    background: #fbf4e9;
    border-radius: 2px;

    .ag-value,
    .ag-list {
      color: #fe9c00;
    }
  }

  .ag-key,
  .ag-value {
    font-size: 12px;
  }
}

.ag-resource-item {
  padding: 20px 30px;
  margin: 0 -30px;

  .title {
    padding-bottom: 10px;
    margin-bottom: 17px;
    font-size: 12px;
    font-weight: bold;
    color: #63656e;
    border-bottom: 1px solid #dcdee5;
  }

  &.show-diff {

    .title {
      display: none;

      &.ag-diff,
      &.always-visible {
        display: block;
      }
    }

    .bk-grid-row {
      display: none;

      &.ag-diff,
      &.always-visible {
        display: block;
      }
    }

    .box-diff {

      .bk-grid-row {
        display: block;
      }
    }

    .plugin-diff.no-diff {
      display: none;
    }
  }
}
</style>

<style lang="scss">
.bk-button-group .readonly-value {
  height: 32px;
  font-size: 13px;
  line-height: 32px;
  color: #313238;
}

.source-version {

  .detail-wrapper.wrapper-diff {
    background: #f0f1f5;
  }

  .ag-diff .ag-pre {
    color: #fff;
    background: #313238;
  }

  .ag-value,
  .ag-list {
    color: #313238 !important;
  }

  .ag-diff .ag-list {
    background: #fff;
  }

  .ag-diff .ag-value {
    color: #313238 !important;
  }

  .ag-kv-box.box-diff {
    background: #fff;
  }
}

.ag-kv-box {

  .bk-grid-row {
    margin-bottom: 12px;
  }

  .ag-key {
    display: block;
    padding-right: 0;
    font-size: 14px;
    color: #63656e;
    text-align: right;
  }

  .ag-value {
    font-size: 14px;
    color: #313238;
  }
}
</style>
