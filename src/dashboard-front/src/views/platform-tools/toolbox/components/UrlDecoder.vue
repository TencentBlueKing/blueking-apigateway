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
  <div class="flex h-100% url-decoder-wrapper">
    <div class="flex flex-col min-w-500px h-100% pb-20px encoded-section-wrapper">
      <div class="mb-12px section-header">
        <span class="header-title">URL</span>
        <span class="header-subtitle">{{ t('（可以在文本框内粘贴待转化的内容）') }}</span>
      </div>
      <div
        class="flex-grow mb-16px section-main"
        @click="handleInputClick"
      >
        <BkInput
          ref="urlInputRef"
          v-model="urlContent"
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

const urlInputRef = ref<InstanceType<typeof Input>>();
const urlContent = ref('');
const result = ref('');
const errorMsg = ref('');

/**
 * MLT URL 编码
 * @param {string} str - 需要编码的字符串
 * @returns {string} - 编码后的字符串
 */
const mltUrlEncode = (str: string) => {
  // 标准URL编码，确保空格转换为%20而非+
  return encodeURIComponent(str)
    .replace(/!/g, '%21')
    .replace(/'/g, '%27')
    .replace(/\(/g, '%28')
    .replace(/\)/g, '%29')
    .replace(/\*/g, '%2A')
    // .replace(/%20/g, '+') // 如果需要空格转义为+
    .replace(/\+/g, '%20'); // 强制空格为%20
};

/**
 * MLT URL 解码
 * @param {string} str - 需要解码的字符串
 * @returns {string} - 解码后的字符串
*/
const mltUrlDecode = (str: string) => {
  try {
    return decodeURIComponent(str.replace(/\+/g, '%20'));
  }
  catch (e) {
    console.error('Invalid URL encoding:', e.message);
    return str;
  }
};

const handleInputClick = () => {
  urlInputRef.value?.focus();
};

// url编码
const handleEncodeClick = () => {
  errorMsg.value = '';
  try {
    result.value = mltUrlEncode(urlContent.value);
  }
  catch (err) {
    errorMsg.value = err.message;
    result.value = '';
  }
};

// url解码
const handleDecodeClick = () => {
  errorMsg.value = '';
  try {
    result.value = mltUrlDecode(urlContent.value);
  }
  catch (err: Error) {
    errorMsg.value = err.message;
    result.value = '';
  }
};

const handleClear = () => {
  errorMsg.value = '';
  urlContent.value = '';
  result.value = '';
};

const handleCopyClick = () => {
  copy(result.value);
};

const highlightString = (value: string) => {
  if (!value) {
    return '';
  }

  return highlightJs.highlight(value, { language: 'json' }).value;
};

</script>

<style lang="scss" scoped>
@use '@/styles/toolbox-base64';
</style>
