<template>
  <!--  查看 SDK 弹窗  -->
  <BkDialog
    v-model:is-show="isShow"
    :title="title"
    class="custom-main-dialog"
    width="640"
    mask-close
  >
    <main class="dialog-content">
      <div class="dialog-main">
        <LangSelector
          v-model="language"
          :sdk-languages="sdks.map(item => item.language)"
          :lang-list="languages"
          :maintainers="maintainers"
        />
        <SdkDetail
          v-if="curSdk"
          :sdk="curSdk"
          is-apigw
        />
      </div>
    </main>
  </BkDialog>
</template>

<script setup lang="ts">
import LangSelector from './LangSelector.vue';
import {
  type ISdk,
  type LanguageType,
} from '../types';
import SdkDetail from './SDKDetail.vue';
import { useI18n } from 'vue-i18n';

interface IProps {
  sdks: ISdk[]
  targetName: string
  languages: LanguageType[]
  maintainers: string[]
}

const isShow = defineModel<boolean>({
  required: true,
  default: false,
});

const {
  sdks = [],
  targetName = '',
  maintainers = [],
} = defineProps<IProps>();

const { t } = useI18n();

const language = ref<LanguageType>('python');

const curSdk = computed(() => {
  return sdks.find(item => item.language === language.value) ?? null;
});

const title = computed(() => {
  return targetName ? t('{name} SDK', { name: targetName }) : t('查看 SDK');
});

watchEffect(() => {
  language.value = sdks[0]?.language || 'python';
});

</script>

<style scoped lang="scss">
.custom-main-dialog {

  :deep(.bk-dialog-title) {
    line-height: 28px;
  }

  :deep(.bk-dialog-content) {
    padding-right: 8px;
    margin-top: 20px;
  }

  :deep(.bk-modal-footer) {
    display: none;
  }

  .dialog-content {

    .dialog-main {

      .data-box {
        padding: 24px 12px;
        background: #f5f7fa;

        .row-item {
          display: flex;
          line-height: 40px;

          .key {
            width: 100px;
            padding-right: 10px;
            text-align: right;
          }

          .value {
            color: #313238;
            white-space: nowrap;
            flex: 1;
          }
        }
      }
    }
  }
}
</style>
