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
        <bk-input
          ref="tokenInputRef"
          v-model="token"
          class="encoded-input-comp"
          type="textarea"
          :placeholder="t('请输入')"
          clearable
          autosize
          :resize="false"
        />
      </div>
      <div class="section-footer">
        <bk-button theme="primary" style="width:330px;" @click="handleDecodeClick">{{ t('解密') }}</bk-button>
        <bk-button style="width:160px;" @click="handleClear">{{ t('清空') }}</bk-button>
      </div>
    </div>
    <div class="decode-section-wrapper">
      <div class="section-header">
        <span class="header-title">Decode</span>
        <span class="header-subtitle">{{ t('（以下是解密的内容）') }}</span>
      </div>
      <div class="section-main">
        <collapse title="Header">
          <pre v-dompurify-html="highlightJson(decodedHeader)"></pre>
        </collapse>
        <collapse title="Payload">
          <pre v-dompurify-html="highlightJson(decodedPayload)"></pre>
        </collapse>
        <div v-if="decodeErrorMsg" class="decode-error-message">
          <span>{{ t('Decode 失败') }}:</span>
          <span>{{ decodeErrorMsg }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import Collapse from '@/views/platform-tools/components/collapse.vue';
import {
  jwtDecode,
  JwtHeader,
  JwtPayload,
} from 'jwt-decode';
import highlightJs from 'highlight.js';

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
  } catch (e) {
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

const highlightJson = (value: any) => {
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

</style>
