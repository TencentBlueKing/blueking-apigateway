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
  <BkFormItem
    :label="t('认证协议')"
    property="oauth2_app_enabled"
    required
  >
    <BkRadioGroup
      v-model="enabled"
      class="protocol-options"
    >
      <BkRadioButton
        v-for="protocol in protocols"
        :key="protocol.name"
        :label="protocol.enabled"
      >
        {{ t(protocol.name) }}
        <BkTag
          v-if="protocol.enabled"
          theme="success"
          size="small"
        >
          {{ t('推荐') }}
        </BkTag>
      </BkRadioButton>
    </BkRadioGroup>
    <div
      v-if="enabled"
      class="protocol-description"
    >
      <p>{{ t('蓝鲸认证 V2 支持 OAuth2 授权、个人令牌等方式。') }}</p>
      <p class="protocol-warning">
        <AgIcon
          name="exclamation-circle-fill"
          class="color-#ff9c01"
        />
        {{ t('使用蓝鲸认证 V2 时，如果 API 本身使用了 Authorization: Bearer 请求头，会被平台覆盖。') }}
      </p>
    </div>
  </BkFormItem>
</template>

<script lang="ts" setup>
const enabled = defineModel<boolean>({ required: true });

const { t } = useI18n();
const protocols = [
  {
    name: '蓝鲸认证 V1',
    enabled: false,
  },
  {
    name: '蓝鲸认证 V2',
    enabled: true,
  },
] as const;
</script>

<style lang="scss" scoped>
.protocol-options {
  display: flex;

  :deep(.bk-radio-button) {
    flex: 1;
  }
}

.protocol-description {
  padding: 8px 12px;
  margin-top: 8px;
  font-size: 12px;
  line-height: 20px;
  color: #63656e;
  background: #f5f7fa;
  border-radius: 2px;

  p {
    margin: 0;
  }

  .protocol-warning {
    display: flex;
    gap: 6px;
    align-items: baseline;
    margin-top: 4px;
  }
}
</style>
