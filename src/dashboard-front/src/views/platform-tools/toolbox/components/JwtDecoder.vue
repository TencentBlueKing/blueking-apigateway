/*
 * TencentBlueKing is pleased to support the open source community by making
 * 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
 * Copyright (C) 2025 Tencent. All rights reserved.
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
  <div class="jwt-decoder-wrapper">
    <div class="encoded-section-wrapper">
      <div class="section-header">
        <span class="header-title">Encoded</span>
        <span class="header-subtitle">{{ t('（可以在文本框内粘贴令牌）') }}</span>
      </div>
      <div
        class="section-main"
        @click="handleInputClick"
      >
        <BkInput
          ref="tokenInputRef"
          v-model="token"
          class="encoded-input-comp"
          type="textarea"
          :placeholder="t('请输入')"
          clearable
          :resize="false"
        />
      </div>
      <div class="section-footer">
        <BkButton
          theme="primary"
          class="w-330px"
          @click="handleDecodeClick"
        >
          {{ t('解密') }}
        </BkButton>
        <BkButton
          class="w-160px"
          @click="handleClear"
        >
          {{ t('清空') }}
        </BkButton>
      </div>
    </div>
    <div class="decode-section-wrapper">
      <div class="section-header">
        <span class="header-title">Decode</span>
        <span class="header-subtitle">{{ t('（以下是解密的内容）') }}</span>
      </div>
      <div class="section-main">
        <Collapse title="Header">
          <pre v-dompurify-html="highlightJson(decodedHeader)" />
        </Collapse>
        <Collapse title="Payload">
          <pre v-dompurify-html="highlightJson(decodedPayload)" />
        </Collapse>
        <div
          v-if="decodeErrorMsg"
          class="decode-error-message"
        >
          <span>{{ t('Decode 失败') }}:</span>
          <span>{{ decodeErrorMsg }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import {
  type JwtHeader,
  type JwtPayload,
  jwtDecode,
} from 'jwt-decode';
import highlightJs from 'highlight.js';
import Collapse from '@/views/platform-tools/components/Collapse.vue';

const { t } = useI18n();

const token = ref('');
const decodedHeader = ref<JwtHeader>({});
const decodedPayload = ref<JwtPayload>({});
const decodeErrorMsg = ref('');

const tokenInputRef = ref();

const handleInputClick = () => {
  tokenInputRef.value?.focus();
};

const handleDecodeClick = () => {
  decodeErrorMsg.value = '';
  try {
    decodedHeader.value = jwtDecode<JwtHeader>(token.value, { header: true });
    decodedPayload.value = jwtDecode<JwtPayload>(token.value);
  }
  catch (e) {
    const err = e as Error;
    decodeErrorMsg.value = err.message;
    decodedHeader.value = {};
    decodedPayload.value = {};
  }
};

const handleClear = () => {
  decodeErrorMsg.value = '';
  token.value = '';
  decodedHeader.value = {};
  decodedPayload.value = {};
};

const highlightJson = (value) => {
  return highlightJs.highlight(JSON.stringify(value, null, 4), { language: 'json' }).value;
};

</script>

<style lang="scss" scoped>

.jwt-decoder-wrapper {
  height: 100%;
  display: flex;
  gap: 16px;

  .encoded-section-wrapper, .decode-section-wrapper {

    .section-header {
      margin-bottom: 12px;

      .header-title {
        font-weight: 700;
        font-size: 14px;
        color: #313238;
      }

      .header-subtitle {
        font-size: 12px;
        color: #979ba5;
        line-height: 20px;
      }
    }

  }

  .encoded-section-wrapper {
    width: 500px;
    height: 100%;
    display: flex;
    flex-direction: column;
    padding-bottom: 26px;

    .section-main {
      flex-grow: 1;
      margin-bottom: 16px;

      .encoded-input-comp {
        height: 100%;
        position: relative;
        :deep(textarea) {
          height: 100%;
          padding: 10px 16px;
        }
        :deep(.show-clear-only-hover.bk-textarea--clear-icon) {
          display: block !important;
          position: absolute;
          right: -2px;
          top: 8px;
        }
      }
    }

    .section-footer {
      display: flex;
      justify-content: space-between;
    }
  }

  .decode-section-wrapper {
    flex-grow: 1;

    .decode-error-message {
      color: #ff5656;
    }
  }
}
.w-330px {
  width: 330px;
}
.w-160px {
  width: 160px;
}
</style>
