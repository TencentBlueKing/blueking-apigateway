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
  <div class="flex h-100% base64-decoder-wrapper">
    <div class="flex flex-col min-w-500px h-100% pb-20px encoded-section-wrapper">
      <div class="mb-12px section-header">
        <span class="header-title">Base64</span>
        <span class="header-subtitle">{{ t('（可以在文本框内粘贴待转化的内容）') }}</span>
      </div>
      <div
        class="flex-grow mb-16px section-main"
        @click="handleInputClick"
      >
        <BkInput
          ref="base64InputRef"
          v-model="base64Content"
          class="relative h-100% encoded-input-comp"
          type="textarea"
          clearable
          :resize="false"
        />
      </div>
      <div class="flex justify-between section-footer">
        <BkButton
          theme="primary"
          class="w-160px"
          @click="handleEncodeClick"
        >
          {{ t('编码') }}
        </BkButton>
        <BkButton
          theme="primary"
          class="w-160px"
          @click="handleDecodeClick"
        >
          {{ t('解码') }}
        </BkButton>
        <BkButton
          class="w-160px"
          @click="handleClear"
        >
          {{ t('清空') }}
        </BkButton>
      </div>
    </div>
    <div class="flex-grow flex flex-col pb-58px decode-section-wrapper">
      <div class="mb-12px flex items-center justify-between decode-section-header">
        <div class="section-header">
          <span class="header-title">{{ t('转化结果') }}</span>
          <span class="header-subtitle">{{ t('（以下是转化的结果）') }}</span>
        </div>
        <div class="header-operate">
          <BkButton
            theme="primary"
            text
            class="text-12px"
            @click="handleCopyClick"
          >
            <AgIcon
              class="icon"
              name="copy"
            />
            <span class="mr-2px">{{ t('复制') }}</span>
          </BkButton>
        </div>
      </div>
      <div class="flex-grow mb-16px section-main">
        <div
          v-if="!errorMsg"
          class="decode-result"
        >
          <pre v-dompurify-html="highlightString(result)" />
        </div>
        <div
          v-else
          class="decode-result color-#ff5656"
        >
          <span>{{ t('转化失败') }}:</span>
          <span>{{ errorMsg }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { Input } from 'bkui-vue';
import { copy } from '@/utils';
import highlightJs from 'highlight.js';
import AgIcon from '@/components/ag-icon/Index.vue';

const { t } = useI18n();

const base64InputRef = ref<InstanceType<typeof Input>>();
const base64Content = ref('');
const result = ref('');
const errorMsg = ref('');

/**
 * MLT base64 编码
 * @param {string} str - 需要编码的字符串
 * @returns {string} - 编码后的字符串
 */
const mltBase64Encode = (str: string) => {
  // 标准 Base64 编码
  const base64 = btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g,
    (match, encode) => String.fromCharCode('0x' + encode)));

  // 转换为 URL 安全格式并去除填充字符
  return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
};

/**
 * MLT base64 解码
 * @param {string} str - 需要解码的字符串
 * @returns {string} - 解码后的字符串
*/
const mltBase64Decode = (str: string) => {
  try {
    // 还原为标准 Base64 格式
    let base64 = str.replace(/-/g, '+').replace(/_/g, '/');

    // 添加缺失的填充字符
    while (base64.length % 4) {
      base64 += '=';
    }

    return decodeURIComponent(Array.prototype.map.call(atob(base64),
      code => '%' + ('00' + code.charCodeAt(0).toString(16)).slice(-2)).join(''));
  }
  catch (e) {
    console.error('Invalid MLT Base64 encoding:', e.message);
    return str;
  }
};

const handleInputClick = () => {
  base64InputRef.value?.focus();
};

// base64编码
const handleEncodeClick = () => {
  errorMsg.value = '';
  try {
    result.value = mltBase64Encode(base64Content.value);
  }
  catch (err) {
    errorMsg.value = err.message;
    result.value = '';
  }
};

// base64解码
const handleDecodeClick = () => {
  errorMsg.value = '';
  try {
    result.value = mltBase64Decode(base64Content.value);
  }
  catch (err: Error) {
    errorMsg.value = err.message;
    result.value = '';
  }
};

const handleClear = () => {
  errorMsg.value = '';
  base64Content.value = '';
  result.value = '';
};

const handleCopyClick = () => {
  copy(result.value);
};

const highlightString = (value: string) => {
  if (!value) {
    return '';
  }

  return highlightJs.highlight(value, { language: 'no-highlight' }).value;
};

</script>

<style lang="scss" scoped>
@use '@/styles/toolbox-base64';
</style>
