<template>
  <!--  查看 SDK 弹窗  -->
  <bk-dialog
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
        <SdkDetail :sdk="curSdk" is-apigw />
      </div>
    </main>
  </bk-dialog>
</template>

<script setup lang="ts">
import {
  computed,
  defineModel,
  ref,
  toRefs,
  watchEffect,
} from 'vue';
import LangSelector from '@/views/apiDocs/components/lang-selector.vue';
import {
  ISdk,
  LanguageType,
} from '@/views/apiDocs/types';
import SdkDetail from '@/views/apiDocs/components/sdk-detail.vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const isShow = defineModel<boolean>({
  required: true,
  default: false,
});

interface IProps {
  sdks: ISdk[];
  targetName: string;
  languages: LanguageType[];
  maintainers: string[];
}

const props = withDefaults(defineProps<IProps>(), {
  sdks: () => [],
  targetName: '',
  maintainers: () => [],
});

const { sdks, targetName, languages } = toRefs(props);

const language = ref<LanguageType>('python');

const curSdk = computed(() => {
  return sdks.value.find(item => item.language === language.value) ?? null;
});

const title = computed(() => {
  return targetName.value ? t('{name} SDK', { name: targetName.value }) : t('查看 SDK');
});

watchEffect(() => {
  language.value = sdks.value[0]?.language || 'python';
});

</script>

<style scoped lang="scss">
.custom-main-dialog {
  :deep(.bk-dialog-title) {
    line-height: 28px;
  }

  :deep(.bk-dialog-content) {
    margin-top: 20px;
    padding-right: 8px;
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
            text-align: right;
            padding-right: 10px;
          }

          .value {
            flex: 1;
            white-space: nowrap;
            color: #313238;
          }
        }
      }
    }
  }
}
</style>
