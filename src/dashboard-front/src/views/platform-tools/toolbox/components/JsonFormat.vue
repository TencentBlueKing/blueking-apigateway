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
      <div class="section-header encode-section-header">
        <span class="header-title">JSON</span>
        <span class="header-subtitle">{{ t('（可以在文本框内粘贴待转化的内容）') }}</span>
      </div>
      <div
        class="section-main"
        @click="handleInputClick"
      >
        <BkInput
          ref="jsonInputRef"
          v-model="jsonString"
          class="encoded-input-comp"
          type="textarea"
          :placeholder="t('请输入')"
          clearable
          autosize
          :resize="false"
        />
      </div>
      <div class="section-footer">
        <BkButton
          theme="primary"
          class="w-330px"
          @click="handleDecodeClick"
        >
          {{ t('格式化') }}
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
      <div class="decode-section-header">
        <div class="section-header">
          <span class="header-title">{{ t('转化结果') }}</span>
          <span class="header-subtitle">{{ t('（以下是转化的结果）') }}</span>
        </div>
        <div class="header-operate">
          <BkButton
            theme="primary"
            text
            class="copy-btn"
            @click="handleCopyClick"
          >
            <AgIcon
              class="icon"
              name="copy"
            />
            <span>{{ t('复制') }}</span>
          </BkButton>
        </div>
      </div>
      <div class="section-main">
        <div
          v-if="!errorMsg"
          class="decode-result"
        >
          <pre v-dompurify-html="highlightJson(result)" />
        </div>
        <div
          v-else
          class="decode-result decode-error-message"
        >
          <span>{{ t('转化失败') }}:</span>
          <span>{{ errorMsg }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import AgIcon from '@/components/ag-icon/Index.vue';
import { copy as copyToClipboard } from '@/utils';
import highlightJs from 'highlight.js';

const { t } = useI18n();

const jsonString = ref<string>('');
const result = ref<string>('');
const errorMsg = ref<string>('');

const jsonInputRef = ref();

const handleInputClick = () => {
  jsonInputRef.value?.focus();
};

const handleDecodeClick = () => {
  errorMsg.value = '';
  try {
    result.value = JSON.stringify(JSON.parse(jsonString.value), null, 4);
  }
  catch (e) {
    const err = e as Error;
    errorMsg.value = err.message;
    result.value = '';
  }
};

const handleClear = () => {
  errorMsg.value = '';
  jsonString.value = '';
  result.value = '';
};

const handleCopyClick = () => {
  copyToClipboard(result.value);
};

const highlightJson = (value: string) => {
  if (!value) {
    return '';
  }

  return highlightJs.highlight(value, { language: 'json' }).value;
};

</script>

<style lang="scss" scoped>

.jwt-decoder-wrapper {
  height: 100%;
  display: flex;
  gap: 16px;

  .encoded-section-wrapper, .decode-section-wrapper {

    .encode-section-header,
    .decode-section-header {
      margin-bottom: 12px;
    }

    .section-header {
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

    .section-main {
      flex-grow: 1;
      margin-bottom: 16px;

      .encoded-input-comp {
        height: 100%;
      }
    }

  }

  .encoded-section-wrapper {
    width: 500px;
    height: 100%;
    display: flex;
    flex-direction: column;
    padding-bottom: 26px;

    .section-footer {
      display: flex;
      justify-content: space-between;
    }
  }

  .decode-section-wrapper {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    padding-bottom: 58px;

    .decode-section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .copy-btn {
        font-size: 12px;
        span {
          margin-left: 2px;
        }
      }
    }

    .decode-result {
      height: 100%;
      background: #FAFBFD;
      padding: 12px 28px;
      pre {
        white-space: pre-wrap;
      }
    }

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
