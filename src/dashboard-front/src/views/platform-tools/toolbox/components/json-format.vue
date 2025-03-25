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
        <bk-input
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
        <bk-button theme="primary" style="width:330px;" @click="handleDecodeClick">{{ t('格式化') }}</bk-button>
        <bk-button style="width:160px;" @click="handleClear">{{ t('清空') }}</bk-button>
      </div>
    </div>
    <div class="decode-section-wrapper">
      <div class="decode-section-header">
        <div class="section-header">
          <span class="header-title">{{ t('转化结果') }}</span>
          <span class="header-subtitle">{{ t('（以下是转化的结果）') }}</span>
        </div>
        <div class="header-operate">
          <bk-button theme="primary" text class="copy-btn" @click="handleCopyClick">
            <copy />
            <span>复制</span>
          </bk-button>
        </div>
      </div>
      <div class="section-main">
        <div class="decode-result" v-if="!errorMsg">
          <pre v-dompurify-html="highlightJson(result)"></pre>
        </div>
        <div class="decode-result decode-error-message" v-else>
          <span>{{ t('转化失败') }}:</span>
          <span>{{ errorMsg }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, useTemplateRef } from 'vue';
import { useI18n } from 'vue-i18n';
import { Copy } from 'bkui-vue/lib/icon';
import { copy as copeFn } from '@/common/util';
import highlightJs from 'highlight.js';

const { t } = useI18n();

const jsonString = ref<string>('');
const result = ref<string>('');
const errorMsg = ref<string>('');

const jsonInputRef = useTemplateRef<HTMLInputElement>('jsonInputRef');

const handleInputClick = () => {
  jsonInputRef.value?.focus();
};

const handleDecodeClick = () => {
  errorMsg.value = '';
  try {
    result.value = JSON.stringify(JSON.parse(jsonString.value), null, 4);
  } catch (e) {
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
  copeFn(result.value);
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
    }

    .decode-error-message {
      color: #ff5656;
    }
  }
}

</style>
